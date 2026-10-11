import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))
import windows_patcher as w
from test_patcher import make_archive


class WindowsInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.app = self.root / '中文路径 & 空格' / 'Antigravity'
        (self.app / 'resources').mkdir(parents=True)
        (self.app / 'empty directory').mkdir()
        preload = b'/* original preload */'
        original = make_archive({'package.json': b'{"name":"antigravity","version":"2.22.0"}',
                                 'dist/preload.js': preload, 'unchanged': b'asset'})
        (self.app / w.ASAR).write_bytes(original)
        exe = bytearray(1024)
        exe[:2] = b'MZ'
        struct.pack_into('<I', exe, 0x3c, 64)
        exe[64:70] = b'PE\0\0\x64\x86'
        wire = w.FUSE_SENTINEL + b'\x01\x09' + b'101100011'
        exe[128:128 + len(wire)] = wire
        (self.app / 'Antigravity.exe').write_bytes(exe)
        (self.app / 'Uninstall Antigravity.exe').write_bytes(b'installer-specific file')
        (self.app / 'resources' / 'other.bin').write_bytes(b'original asset')
        self.rule = dict(w.rules(), exe_sha256=w.digest(exe), asar_sha256=w.digest(original),
                         preload_sha256=w.digest(preload), fuse_offset=128)
        self.before = w.snapshot(self.app)
        self.patches = [patch.object(w, 'rules', return_value=self.rule),
                        patch.object(w, 'require_windows'), patch.object(w, 'ensure_stopped')]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_doctor_is_read_only(self):
        self.assertFalse(w.doctor(self.app)['patched'])
        self.assertEqual(w.snapshot(self.app), self.before)
        self.assertFalse(w.backup_path(self.app).exists())
        self.assertEqual(sorted(p.name for p in self.app.parent.iterdir()), ['Antigravity'])

    def test_backup_install_restore_full_roundtrip(self):
        w.backup(self.app)
        backup = w.backup_path(self.app)
        original_record = (backup / 'manifest.json').read_bytes()
        w.install(self.app, True)
        after = w.snapshot(self.app)
        changed = [name for name in self.before if after[name] != self.before[name]]
        self.assertEqual(changed, [w.ASAR])
        self.assertTrue(w.doctor(self.app)['patched'])
        self.assertEqual(w.snapshot(backup / 'original'), self.before)
        w.restore(self.app)
        self.assertEqual(w.snapshot(self.app), self.before)
        self.assertEqual((backup / 'manifest.json').read_bytes(), original_record)
        self.assertTrue(backup.exists())

    def test_install_automatically_creates_backup(self):
        w.install(self.app, True)
        self.assertTrue(w.backup_path(self.app).is_dir())
        self.assertEqual(w.load_backup(self.app)['original_manifest'], self.before)

    def test_repeated_actions_are_idempotent(self):
        w.install(self.app, True)
        tree = w.snapshot(self.app)
        for _ in range(2):
            w.install(self.app, True)
            w.backup(self.app)
            self.assertEqual(w.snapshot(self.app), tree)
        w.restore(self.app)
        w.restore(self.app)
        w.install(self.app, True)
        self.assertEqual(w.snapshot(self.app), tree)

    def test_test_build_acknowledgement_before_mutation(self):
        with self.assertRaises(ValueError):
            w.install(self.app)
        self.assertEqual(w.snapshot(self.app), self.before)
        self.assertFalse(w.backup_path(self.app).exists())

    def test_unknown_executable_and_archive_refused(self):
        for target in ('Antigravity.exe', w.ASAR):
            path = self.app / target
            old = path.read_bytes()
            path.write_bytes(old + b'unknown')
            with self.assertRaises(ValueError):
                w.install(self.app, True)
            self.assertEqual(path.read_bytes(), old + b'unknown')
            self.assertFalse(w.backup_path(self.app).exists())
            path.write_bytes(old)

    def test_wrong_architecture_and_integrity_fuse_refused(self):
        exe = self.app / 'Antigravity.exe'
        old = exe.read_bytes()
        altered = bytearray(old)
        altered[68:70] = b'\x64\xaa'  # ARM64
        exe.write_bytes(altered)
        self.rule['exe_sha256'] = w.digest(altered)
        with self.assertRaisesRegex(ValueError, 'x64'):
            w.inspect_files(self.app)
        exe.write_bytes(old)
        self.rule['exe_sha256'] = w.digest(old)
        self.rule['fuses_v1'] = '101110011'
        with self.assertRaisesRegex(ValueError, '安全开关'):
            w.inspect_files(self.app)

    def test_update_prevents_restore_including_non_asar_changes(self):
        w.install(self.app, True)
        asset = self.app / 'resources/other.bin'
        asset.write_bytes(b'new version asset')
        before_restore = w.snapshot(self.app)
        with self.assertRaisesRegex(ValueError, '可能已更新'):
            w.restore(self.app)
        self.assertEqual(w.snapshot(self.app), before_restore)
        self.assertTrue(w.backup_path(self.app).exists())

    def test_updated_asar_not_overwritten(self):
        w.install(self.app, True)
        (self.app / w.ASAR).write_bytes(b'updated archive')
        with self.assertRaises(ValueError):
            w.restore(self.app)
        self.assertEqual((self.app / w.ASAR).read_bytes(), b'updated archive')

    def test_corrupt_backup_prevents_install_and_restore(self):
        w.backup(self.app)
        (w.backup_path(self.app) / 'original/resources/other.bin').write_bytes(b'corrupt')
        for action in (lambda: w.install(self.app, True), lambda: w.restore(self.app)):
            with self.assertRaisesRegex(ValueError, '备份文件校验失败'):
                action()
        self.assertEqual(w.snapshot(self.app), self.before)

    def test_incomplete_or_mismatched_backup_not_overwritten(self):
        root = w.backup_path(self.app)
        root.mkdir()
        (root / 'keep.txt').write_text('keep', encoding='utf-8')
        with self.assertRaises(ValueError):
            w.backup(self.app)
        self.assertEqual((root / 'keep.txt').read_text(), 'keep')
        shutil.rmtree(root)
        w.backup(self.app)
        record = root / 'manifest.json'
        meta = json.loads(record.read_text(encoding='utf-8'))
        meta['app'] = str(self.app.parent / 'Other')
        record.write_text(json.dumps(meta), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '路径或版本'):
            w.restore(self.app)

    def test_process_running_stops_before_backup(self):
        with patch.object(w, 'ensure_stopped', side_effect=ValueError('running')):
            with self.assertRaises(ValueError):
                w.install(self.app, True)
        self.assertEqual(w.snapshot(self.app), self.before)
        self.assertFalse(w.backup_path(self.app).exists())

    def test_process_start_during_install_preserves_original(self):
        w.backup(self.app)
        # install's first check succeeds, final check before replacement fails.
        with patch.object(w, 'ensure_stopped', side_effect=[None, ValueError('running')]):
            with self.assertRaises(ValueError):
                w.install(self.app, True)
        self.assertEqual(w.snapshot(self.app), self.before)

    def test_locked_file_or_atomic_replace_failure_keeps_original(self):
        with patch.object(w.os, 'replace', side_effect=PermissionError('file in use')):
            with self.assertRaises(PermissionError):
                w.install(self.app, True)
        self.assertEqual(w.snapshot(self.app), self.before)
        self.assertEqual(w.load_backup(self.app)['original_manifest'], self.before)
        self.assertFalse(list(self.app.parent.glob('.antigravity-zh-asar-*')))

    @unittest.skipUnless(sys.platform == 'win32', 'Windows native file-sharing check')
    def test_native_open_handle_blocks_replace(self):
        w.backup(self.app)
        with (self.app / w.ASAR).open('rb'):
            with self.assertRaises(PermissionError):
                w.install(self.app, True)
        self.assertEqual(w.snapshot(self.app), self.before)
        self.assertEqual(w.load_backup(self.app)['original_manifest'], self.before)
        w.install(self.app, True)
        w.restore(self.app)

    def test_restore_replace_failure_keeps_patch_and_backup(self):
        w.install(self.app, True)
        before = w.snapshot(self.app)
        with patch.object(w.os, 'replace', side_effect=PermissionError('locked')):
            with self.assertRaises(PermissionError):
                w.restore(self.app)
        self.assertEqual(w.snapshot(self.app), before)
        self.assertEqual(w.load_backup(self.app)['original_manifest'], self.before)
        w.restore(self.app)

    def test_crash_after_atomic_commit_is_recoverable(self):
        replace = os.replace
        def committed_then_crashed(source, target):
            replace(source, target)
            raise KeyboardInterrupt()
        with patch.object(w.os, 'replace', side_effect=committed_then_crashed):
            with self.assertRaises(KeyboardInterrupt):
                w.install(self.app, True)
        self.assertTrue(w.doctor(self.app)['patched'])
        w.restore(self.app)
        self.assertEqual(w.snapshot(self.app), self.before)

    def test_missing_archive_and_missing_app_can_be_restored(self):
        w.install(self.app, True)
        (self.app / w.ASAR).unlink()
        self.assertEqual(w.doctor(self.app)['application_state'], 'missing-asar')
        w.restore(self.app)
        self.assertEqual(w.snapshot(self.app), self.before)
        shutil.rmtree(self.app)
        w.restore(self.app)
        self.assertEqual(w.snapshot(self.app), self.before)

    def test_copy_failure_or_low_space_never_mutates_original(self):
        with patch.object(w.shutil, 'copytree', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                w.install(self.app, True)
        self.assertEqual(w.snapshot(self.app), self.before)
        self.assertFalse(w.backup_path(self.app).exists())
        with patch.object(w, 'check_space', side_effect=ValueError('low space')):
            with self.assertRaises(ValueError):
                w.install(self.app, True)
        self.assertFalse(w.backup_path(self.app).exists())

    def test_update_during_backup_is_detected(self):
        real_copy = shutil.copytree
        def copy_then_update(*args, **kwargs):
            result = real_copy(*args, **kwargs)
            (self.app / 'resources/other.bin').write_bytes(b'updater changed this')
            return result
        with patch.object(w.shutil, 'copytree', side_effect=copy_then_update):
            with self.assertRaisesRegex(ValueError, '备份期间'):
                w.backup(self.app)
        self.assertFalse(w.backup_path(self.app).exists())
        self.assertEqual((self.app / 'resources/other.bin').read_bytes(), b'updater changed this')

    def test_update_between_staging_and_replace_is_detected(self):
        w.backup(self.app)
        def update():
            (self.app / 'resources/other.bin').write_bytes(b'new asset')
        calls = []
        def on_check():
            calls.append(1)
            if len(calls) == 2:
                update()
        with patch.object(w, 'ensure_stopped', side_effect=on_check):
            with self.assertRaises(ValueError):
                w.install(self.app, True)
        self.assertEqual(w.file_hash(self.app / w.ASAR), self.rule['asar_sha256'])

    def test_different_patch_version_does_not_reuse_old_record(self):
        w.backup(self.app)
        with patch.object(w, 'build', return_value=b'new payload'):
            with self.assertRaisesRegex(ValueError, '另一版补丁'):
                w.install(self.app, True)
        self.assertEqual(w.snapshot(self.app), self.before)

    def test_hardlink_and_symlink_rejected(self):
        os.link(self.app / 'resources/other.bin', self.app / 'resources/hardlink.bin')
        with self.assertRaisesRegex(ValueError, '硬链接'):
            w.backup(self.app)
        (self.app / 'resources/hardlink.bin').unlink()
        alias = self.app.parent / 'Alias'
        try:
            alias.symlink_to(self.app, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not permit symlink creation')
        with self.assertRaises(ValueError):
            w.backup(alias)

    def test_concurrent_operations_rejected(self):
        # A separate process exercises the OS lock on both Windows and POSIX.
        script = ('import sys; from pathlib import Path; '
                  'sys.path.insert(0, sys.argv[1]); import windows_patcher as w; '
                  'ctx=w.operation_lock(Path(sys.argv[2])); ctx.__enter__(); print("locked")')
        with w.operation_lock(self.app):
            result = subprocess.run([sys.executable, '-c', script, str(w.ROOT / 'tools'), str(self.app)],
                                    capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('locked', result.stdout)
        with w.operation_lock(self.app):
            pass


class PlatformTests(unittest.TestCase):
    def test_non_windows_refused(self):
        with patch.object(w.sys, 'platform', 'darwin'):
            with self.assertRaisesRegex(ValueError, 'Windows 11'):
                w.require_windows()

    def test_windows_10_and_server_refused(self):
        for version in (SimpleNamespace(build=19045, product_type=1),
                        SimpleNamespace(build=26100, product_type=3)):
            with patch.object(w.sys, 'platform', 'win32'), \
                    patch.object(w.sys, 'getwindowsversion', return_value=version, create=True):
                with self.assertRaisesRegex(ValueError, 'Windows 11 客户端'):
                    w.require_windows()

    def test_native_x64_required_not_arm_emulation(self):
        class Fn:
            def __init__(self, fn): self.fn = fn
            def __call__(self, *args): return self.fn(*args)
        for architecture, process_arch, accepted in ((0x8664, 0, True),
                                                    (0xaa64, 0x8664, False),
                                                    (0x8664, 0x14c, False)):
            def machine(handle, process, native):
                process._obj.value = process_arch
                native._obj.value = architecture
                return 1
            kernel = SimpleNamespace(GetCurrentProcess=Fn(lambda: 42), IsWow64Process2=Fn(machine))
            with patch.object(w.sys, 'platform', 'win32'), \
                    patch.object(w.sys, 'getwindowsversion', create=True,
                                 return_value=SimpleNamespace(build=26100, product_type=1)), \
                    patch.object(w.ctypes, 'WinDLL', create=True, return_value=kernel):
                if accepted:
                    w.require_windows()
                else:
                    with self.assertRaisesRegex(ValueError, 'ARM64'):
                        w.require_windows()

    @unittest.skipUnless(sys.platform == 'win32', 'Windows native API check')
    def test_native_process_enumeration(self):
        # Uses the actual kernel32 API, not a mocked process list.
        w.ensure_stopped()

    @unittest.skipUnless(sys.platform == 'win32', 'Windows native junction check')
    def test_native_junction_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target, link = Path(tmp) / 'target', Path(tmp) / 'link'
            target.mkdir()
            result = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(link), str(target)],
                                    capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            try:
                with self.assertRaises(ValueError):
                    w.safe_path(link)
            finally:
                os.rmdir(link)


if __name__ == '__main__':
    unittest.main()
