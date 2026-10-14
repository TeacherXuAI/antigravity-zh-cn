import importlib.util
import json
from pathlib import Path
import plistlib
import struct
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import shutil

spec = importlib.util.spec_from_file_location('patcher', Path(__file__).parents[1] / 'tools/patcher.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def make_archive(files):
    entries, body = {}, b''
    for name, data in files.items():
        target = entries
        parts = name.split('/')
        for part in parts[:-1]:
            target = target.setdefault(part, {'files': {}})['files']
        target[parts[-1]] = {'size': len(data), 'offset': str(len(body)), 'integrity': {
            'algorithm': 'SHA256', 'hash': p.digest(data), 'blockSize': 4,
            'blocks': [p.digest(data[i:i+4]) for i in range(0, len(data), 4)]}}
        body += data
    raw = json.dumps({'files': entries}, separators=(',', ':')).encode()
    pad = b'\0' * (-len(raw) % 4)
    hp = struct.pack('<II', 4 + len(raw) + len(pad), len(raw)) + raw + pad
    return struct.pack('<II', 4, len(hp)) + hp + body


class ArchiveTests(unittest.TestCase):
    def test_replacement_retains_other_files_and_correct_integrity(self):
        original = p.Archive(make_archive({'dist/preload.js': b'hello', 'asset': b'\0\xffdata'}))
        rebuilt = p.Archive(original.replace('dist/preload.js', '中文 test'.encode()))
        self.assertEqual(rebuilt.read('dist/preload.js'), '中文 test'.encode())
        self.assertEqual(rebuilt.read('asset'), b'\0\xffdata')
        self.assertEqual(rebuilt.entry('dist/preload.js')['integrity']['blocks'],
                         [p.digest('中文 test'.encode()[i:i+4]) for i in range(0, len('中文 test'.encode()), 4)])

    def test_corrupt_header_bounds_and_checksums_rejected(self):
        for bad in (b'', b'0'*16, struct.pack('<4I', 4, 2**30, 0, 0)):
            with self.assertRaises(ValueError): p.Archive(bad)
        a = p.Archive(make_archive({'file': b'foo'}))
        a.header['files']['file']['offset'] = '999999'
        with self.assertRaises(ValueError): a.read('file')
        a = p.Archive(make_archive({'file': b'foo'})); a.body = b'bar'
        with self.assertRaises(ValueError): a.read('file')

    def test_rejects_unpacked_symlink_and_traversal(self):
        a = p.Archive(make_archive({'file': b'foo'}))
        for key in ('unpacked', 'link'):
            b = p.Archive(make_archive({'file': b'foo'})); b.header['files']['file'][key] = True
            with self.assertRaises(ValueError): b.read('file')
        with self.assertRaises(ValueError): a.read('../file')


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.app = self.root / 'Antigravity.app'
        (self.app / 'Contents/Resources').mkdir(parents=True)
        preload = b'/* test preload */'
        data = make_archive({'package.json': json.dumps({'name':'antigravity','version':'2.22.0'}).encode(),
                             'dist/preload.js': preload, 'asset': b'unchanged'})
        self.asar = self.app / 'Contents/Resources/app.asar'
        self.asar.write_bytes(data)
        self.plist = self.app / 'Contents/Info.plist'
        self.plist.write_bytes(plistlib.dumps({'CFBundleIdentifier':'com.google.antigravity',
            'CFBundleShortVersionString':'2.22.0', 'ElectronAsarIntegrity':{'Resources/app.asar':{
                'algorithm':'SHA256','hash':p.digest(p.Archive(data).raw_header)}}}))
        self.original = data
        self.real_inspect = p.inspect
        self.real_json_loads = json.loads
        def loads(data, *args, **kwargs):
            value = self.real_json_loads(data, *args, **kwargs)
            if isinstance(value, dict) and value.get('target') == 'Antigravity Desktop (not Antigravity IDE)':
                for ver in ('2.22.0', '2.23.0'):
                    if ver in value['versions']:
                        value['versions'][ver]['preload_sha256'] = p.digest(preload)
            return value
        self.loads_patch = patch.object(p.json, 'loads', side_effect=loads)
        self.loads_patch.start()

    def tearDown(self):
        self.loads_patch.stop(); self.tmp.cleanup()

    def run_fake(self, *args):
        if args[0] == '/usr/bin/ditto': shutil.copytree(args[1], args[2])
        return subprocess.CompletedProcess(args, 0, '', 'Authority=Developer ID Application: Google LLC (EQHXZ8M8AV)')

    def test_plan_read_only_and_bundle_patch(self):
        before = self.plist.read_bytes()
        self.assertFalse(p.inspect(self.app)['patched'])
        self.assertEqual(self.asar.read_bytes(), self.original)
        self.assertEqual(self.plist.read_bytes(), before)
        p.patch_bundle(self.app)
        info = p.inspect(self.app)
        self.assertTrue(info['patched'])
        self.assertEqual(info['archive'].read('asset'), b'unchanged')

    def test_version_and_symlink_rejected(self):
        # Verify 2.23.0 is accepted when bundle and package.json match 2.23.0
        preload = b'/* test preload */'
        data_223 = make_archive({'package.json': json.dumps({'name':'antigravity','version':'2.23.0'}).encode(),
                                 'dist/preload.js': preload, 'asset': b'unchanged'})
        self.asar.write_bytes(data_223)
        plist_223 = plistlib.loads(self.plist.read_bytes())
        plist_223['CFBundleShortVersionString'] = '2.23.0'
        plist_223['ElectronAsarIntegrity']['Resources/app.asar']['hash'] = p.digest(p.Archive(data_223).raw_header)
        self.plist.write_bytes(plistlib.dumps(plist_223))
        self.assertEqual(p.inspect(self.app)['version'], '2.23.0')

        data = plistlib.loads(self.plist.read_bytes());data['CFBundleShortVersionString']='999.0'
        self.plist.write_bytes(plistlib.dumps(data))
        with self.assertRaises(ValueError): p.inspect(self.app)
        alias = self.root / 'Alias.app';alias.symlink_to(self.app)
        with self.assertRaises(ValueError): p.inspect(alias)

    def test_signature_failure_leaves_original_intact(self):
        def failing(*args):
            if '--force' in args: raise subprocess.CalledProcessError(1,args,stderr='sign failure')
            return self.run_fake(*args)
        with patch.object(p.sys,'platform','darwin'), patch.object(p,'run',side_effect=failing):
            with self.assertRaises(subprocess.CalledProcessError): p.install(self.app,True,True)
        self.assertEqual(self.asar.read_bytes(),self.original)
        self.assertFalse(p.paths(self.app)[0].exists())
        self.assertFalse(p.paths(self.app)[1].exists())

    def test_install_then_restore_full_original(self):
        with patch.object(p.sys,'platform','darwin'), patch.object(p,'run',side_effect=self.run_fake):
            p.install(self.app,True,True)
            self.assertTrue(p.inspect(self.app)['patched'])
            self.assertEqual((p.paths(self.app)[0]/'Contents/Resources/app.asar').read_bytes(),self.original)
            p.restore(self.app)
            self.assertEqual(self.asar.read_bytes(),self.original)
            self.assertFalse(p.paths(self.app)[1].exists())

    def test_updated_app_not_overwritten_by_restore(self):
        with patch.object(p.sys,'platform','darwin'), patch.object(p,'run',side_effect=self.run_fake):
            p.install(self.app,True,True);self.asar.write_bytes(b'new app update')
            with self.assertRaises(ValueError): p.restore(self.app)
            self.assertEqual(self.asar.read_bytes(),b'new app update')
            self.assertTrue(p.paths(self.app)[0].exists())

    def test_interrupted_install_missing_app_recoverable(self):
        with patch.object(p.sys,'platform','darwin'), patch.object(p,'run',side_effect=self.run_fake):
            p.install(self.app,True,True);shutil.rmtree(self.app);p.restore(self.app)
            self.assertEqual(self.asar.read_bytes(),self.original)

    def test_interrupted_before_rename_cleans_only_recovery_record(self):
        backup, state = p.paths(self.app)
        state.write_text(json.dumps({'schema':1,'app':str(self.app),'version':'2.22.0',
            'original_asar':p.digest(self.original),'original_plist':p.digest(self.plist.read_bytes()),
            'patched_asar':'not-yet-installed'}))
        with patch.object(p.sys,'platform','darwin'), patch.object(p,'run',side_effect=self.run_fake):
            p.restore(self.app)
        self.assertFalse(state.exists())
        self.assertEqual(self.asar.read_bytes(), self.original)

    def test_acknowledgement_and_running_app_guards(self):
        with patch.object(p.sys,'platform','darwin'):
            with self.assertRaises(ValueError): p.install(self.app,False)
            with self.assertRaises(ValueError): p.install(self.app,True,False)
        with patch.object(p,'run',return_value=subprocess.CompletedProcess([],0,str(self.app/'Contents/MacOS/Antigravity'),'')):
            with self.assertRaises(ValueError): p.ensure_stopped(self.app)


if __name__ == '__main__': unittest.main()
