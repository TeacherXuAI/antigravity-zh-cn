#!/usr/bin/env python3
"""Antigravity macOS localization installer. Python 3.9+, standard library only."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = b'/* TeacherXuAI Antigravity Chinese UI'
MAX_HEADER = 32 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Archive:
    """Read ASAR without extracting vendor files; replace one packed entry."""
    def __init__(self, data):
        if len(data) < 16:
            raise ValueError('ASAR header is truncated')
        size, header_size, payload_size, json_size = struct.unpack_from('<4I', data)
        if (size != 4 or header_size > MAX_HEADER or header_size < 8 or
                payload_size + 4 != header_size or json_size > payload_size - 4 or
                8 + header_size > len(data)):
            raise ValueError('Invalid ASAR header')
        self.raw_header = data[16:16 + json_size]
        self.header = json.loads(self.raw_header)
        self.body = data[8 + header_size:]
        if not isinstance(self.header.get('files'), dict):
            raise ValueError('Missing ASAR file table')

    def entry(self, name):
        if any(part in ('', '.', '..') for part in name.split('/')):
            raise ValueError('Invalid archive path')
        item = self.header
        for part in name.split('/'):
            item = item['files'][part]
        if item.get('unpacked') or 'link' in item or 'files' in item:
            raise ValueError('Expected a packed regular file')
        return item

    def read(self, name):
        entry = self.entry(name)
        offset, size = int(entry['offset']), int(entry['size'])
        if offset < 0 or size < 0 or offset + size > len(self.body):
            raise ValueError('Entry outside ASAR bounds')
        data = self.body[offset:offset + size]
        integrity = entry.get('integrity')
        if integrity:
            if integrity.get('algorithm') != 'SHA256' or integrity.get('hash') != digest(data):
                raise ValueError('Entry checksum mismatch')
        return data

    def replace(self, name, data):
        header = copy.deepcopy(self.header)
        item = header
        for part in name.split('/'):
            item = item['files'][part]
        self.read(name)  # Validate bounds and checksum before replacing.
        block_size = item.get('integrity', {}).get('blockSize', 4 * 1024 * 1024)
        if not isinstance(block_size, int) or not 0 < block_size <= MAX_HEADER:
            raise ValueError('Invalid integrity block size')
        item.update(size=len(data), offset=str(len(self.body)), integrity={
            'algorithm': 'SHA256', 'hash': digest(data), 'blockSize': block_size,
            'blocks': [digest(data[i:i + block_size]) for i in range(0, len(data), block_size)]
        })
        raw = json.dumps(header, separators=(',', ':'), ensure_ascii=False).encode()
        pad = b'\0' * (-len(raw) % 4)
        header_pickle = struct.pack('<II', 4 + len(raw) + len(pad), len(raw)) + raw + pad
        result = struct.pack('<II', 4, len(header_pickle)) + header_pickle + self.body + data
        return result


def build():
    dictionary = json.loads((ROOT / 'locales/zh-CN.json').read_text(encoding='utf-8'))
    if not dictionary or not all(isinstance(k, str) and k.strip() == k and
                                 isinstance(v, str) and v for k, v in dictionary.items()):
        raise ValueError('Invalid translation dictionary')
    source = (ROOT / 'src/runtime.js').read_text(encoding='utf-8')
    token = '/*__DICTIONARY__*/ {}'
    if source.count(token) != 1:
        raise ValueError('Invalid runtime template')
    payload = source.replace(token, json.dumps(dictionary, ensure_ascii=False, sort_keys=True))
    return payload.encode('utf-8')


def assert_app_path(app):
    app = Path(os.path.abspath(app))
    if app.suffix != '.app' or not app.is_dir():
        raise ValueError('Select an existing .app bundle')
    if app.resolve() != app or app.is_symlink():
        raise ValueError('Symlink application paths are not supported')
    for relative in ('Contents/Info.plist', 'Contents/Resources/app.asar'):
        p = app / relative
        if not p.is_file() or p.resolve() != p:
            raise ValueError('Expected regular bundle files: ' + relative)
    return app


def paths(app):
    return app.with_name(app.name + '.zh-cn-original'), app.with_name(app.name + '.zh-cn-state.json')


def inspect(app):
    app = assert_app_path(app)
    plist = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    compatibility = json.loads((ROOT / 'tools/compatibility.json').read_text(encoding='utf-8'))
    if plist.get('CFBundleIdentifier') != compatibility['bundle_id']:
        raise ValueError('This is not Antigravity Desktop')
    version = plist.get('CFBundleShortVersionString')
    rule = compatibility['versions'].get(version)
    if not rule:
        raise ValueError('Unsupported version: ' + str(version) + '; no files changed')
    raw = (app / 'Contents/Resources/app.asar').read_bytes()
    archive = Archive(raw)
    package = json.loads(archive.read('package.json'))
    if package.get('name') != 'antigravity' or package.get('version') != version:
        raise ValueError('Bundle version differs from package version')
    integrity = plist.get('ElectronAsarIntegrity', {}).get('Resources/app.asar')
    if not integrity or integrity.get('algorithm') != 'SHA256' or integrity.get('hash') != digest(archive.raw_header):
        raise ValueError('Bundle ASAR integrity does not match')
    preload = archive.read(rule['entry'])
    patched = MARKER in preload
    if not patched and digest(preload) != rule['preload_sha256']:
        raise ValueError('Unknown preload fingerprint; refusing to patch')
    return {'version': version, 'archive': archive, 'rule': rule, 'plist': plist,
            'asar_sha256': digest(raw), 'patched': patched, 'app': app}


def report(info):
    backup, state = paths(info['app'])
    return {'app': str(info['app']), 'version': info['version'],
            'patched': info['patched'], 'asar_sha256': info['asar_sha256'],
            'translations': len(json.loads((ROOT / 'locales/zh-CN.json').read_text(encoding='utf-8'))),
            'backup': str(backup), 'state_present': state.exists(),
            'native_ui_tested': info['rule']['native_ui_tested'],
            'scope': 'Settings: General, Application, Appearance, Models; fixed navigation',
            'signature_effect': 'local ad-hoc outer signature and explicit app-scoped library-validation exception'}


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def ensure_stopped(app):
    output = run('/bin/ps', '-axo', 'command=').stdout
    executable = str(app / 'Contents/MacOS') + '/'
    if any(executable in line for line in output.splitlines()):
        raise ValueError('Quit Antigravity completely with Cmd+Q, then retry')


def verify_signature(app):
    run('/usr/bin/codesign', '--verify', '--deep', '--strict', str(app))


def patch_bundle(app):
    info = inspect(app)
    if info['patched']:
        raise ValueError('Already patched')
    entry = info['rule']['entry']
    payload = info['archive'].read(entry) + b'\n' + build() + b'\n'
    archive_bytes = info['archive'].replace(entry, payload)
    rebuilt = Archive(archive_bytes)
    if rebuilt.read(entry) != payload:
        raise ValueError('Rebuilt archive verification failed')
    plist = info['plist']
    plist['ElectronAsarIntegrity']['Resources/app.asar']['hash'] = digest(rebuilt.raw_header)
    (app / 'Contents/Resources/app.asar').write_bytes(archive_bytes)
    (app / 'Contents/Info.plist').write_bytes(plistlib.dumps(plist))
    return digest(archive_bytes)


def install(app, acknowledge=False, allow_local_libraries=False):
    if sys.platform != 'darwin':
        raise ValueError('v0.1 supports macOS installation only')
    if not acknowledge:
        raise ValueError('Read README first. Installation requires --acknowledge-signature-change')
    if not allow_local_libraries:
        raise ValueError('Local signing requires an app-scoped library-validation exception; read README and use --allow-local-library-loading')
    info = inspect(app)
    app = info['app']
    if info['patched']:
        raise ValueError('Already patched; restore before installing a different patch version')
    backup, state = paths(app)
    if backup.exists() or state.exists() or backup.is_symlink() or state.is_symlink():
        raise ValueError('Backup/state already exists; refusing to overwrite it')
    ensure_stopped(app)
    verify_signature(app)
    run('/usr/sbin/spctl', '--assess', '--type', 'execute', str(app))
    signature = run('/usr/bin/codesign', '-dv', '--verbose=2', str(app)).stderr
    if 'Authority=Developer ID Application: Google LLC (EQHXZ8M8AV)' not in signature:
        raise ValueError('Original application must have a Google LLC signature')
    staging = Path(tempfile.mkdtemp(prefix='.antigravity-zh-', dir=app.parent))
    staged = staging / app.name
    moved_original = False
    committed = False
    state_created = False
    try:
        run('/usr/bin/ditto', str(app), str(staged))
        patched_hash = patch_bundle(staged)
        # Ad-hoc identities have no Apple Team ID. Explicit opt-in is required to
        # load the original Google-signed frameworks in this locally signed process.
        entitlements_raw = run('/usr/bin/codesign', '-d', '--entitlements', ':-', str(app)).stdout
        entitlements = plistlib.loads(entitlements_raw.encode()) if entitlements_raw.strip() else {}
        entitlements['com.apple.security.cs.disable-library-validation'] = True
        entitlements_path = staging / 'local-entitlements.plist'
        entitlements_path.write_bytes(plistlib.dumps(entitlements))
        run('/usr/bin/codesign', '--force', '--sign', '-',
            '--preserve-metadata=flags,runtime', '--entitlements', str(entitlements_path), str(staged))
        verify_signature(staged)
        ensure_stopped(app)
        # Detect an updater replacing the original while we prepared the copy.
        if inspect(app)['asar_sha256'] != info['asar_sha256']:
            raise ValueError('Original app changed during preparation; retry')
        metadata = {'schema': 1, 'app': str(app), 'version': info['version'],
                    'original_asar': info['asar_sha256'], 'patched_asar': patched_hash,
                    'original_plist': digest((app / 'Contents/Info.plist').read_bytes())}
        # Reserve the manifest exclusively; never overwrite an existing recovery record.
        with state.open('x') as f:
            state_created = True
            json.dump(metadata, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.rename(app, backup)
        moved_original = True
        try:
            os.rename(staged, app)
        except BaseException:
            os.rename(backup, app)
            moved_original = False
            raise
        committed = True
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        if state_created and not committed and not moved_original and state.is_file():
            state.unlink()
    return report(inspect(app))


def restore(app):
    if sys.platform != 'darwin':
        raise ValueError('v0.1 supports macOS restoration only')
    app = Path(os.path.abspath(app))
    backup, state = paths(app)
    if state.is_symlink() or backup.is_symlink() or backup.resolve() != backup:
        raise ValueError('Invalid recovery path')
    metadata = json.loads(state.read_text())
    if metadata.get('schema') != 1 or metadata.get('app') != str(app):
        raise ValueError('Recovery record does not match the application')
    ensure_stopped(app)
    if not backup.exists() and app.exists():
        assert_app_path(app)
        if (digest((app / 'Contents/Resources/app.asar').read_bytes()) == metadata['original_asar'] and
                digest((app / 'Contents/Info.plist').read_bytes()) == metadata['original_plist']):
            verify_signature(app)
            state.unlink()
            return {'restored': True, 'app': str(app), 'version': metadata['version'],
                    'recovered': 'interrupted before original app was moved'}
    if digest((backup / 'Contents/Resources/app.asar').read_bytes()) != metadata['original_asar']:
        raise ValueError('Backup archive checksum mismatch')
    if digest((backup / 'Contents/Info.plist').read_bytes()) != metadata['original_plist']:
        raise ValueError('Backup Info.plist checksum mismatch')
    verify_signature(backup)
    # Missing app is recoverable after interruption between the two directory renames.
    if app.exists():
        assert_app_path(app)
        if digest((app / 'Contents/Resources/app.asar').read_bytes()) != metadata['patched_asar']:
            raise ValueError('Installed app changed (possibly updated). Restore would overwrite it; stopped')
    staging = Path(tempfile.mkdtemp(prefix='.antigravity-zh-restore-', dir=app.parent))
    current = staging / app.name
    try:
        if app.exists():
            os.rename(app, current)
        try:
            os.rename(backup, app)
        except BaseException:
            if current.exists():
                os.rename(current, app)
            raise
        state.unlink()
    finally:
        # If rollback itself fails, retain current as a recoverable copy.
        if app.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return {'restored': True, 'app': str(app), 'version': metadata['version']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('doctor', 'build', 'install', 'restore'))
    parser.add_argument('--app', type=Path, default=Path('/Applications/Antigravity.app'))
    parser.add_argument('--acknowledge-signature-change', action='store_true')
    parser.add_argument('--allow-local-library-loading', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'build':
            target = ROOT / 'dist/antigravity-zh-cn.js'
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(build())
            result = {'built': str(target), 'sha256': digest(target.read_bytes())}
        elif args.command == 'doctor':
            result = report(inspect(args.app))
        elif args.command == 'install':
            result = install(args.app, args.acknowledge_signature_change, args.allow_local_library_loading)
        else:
            result = restore(args.app)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print('Stopped: ' + str(exc), file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr.strip(), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
