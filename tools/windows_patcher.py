#!/usr/bin/env python3
"""Windows 11 x64 test installer. Python 3.9+, standard library only.

Only resources/app.asar is replaced. The executable, Electron fuses, registry,
system security policy and user profile are never modified.
"""
import argparse
from contextlib import contextmanager
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile

from patcher import Archive, ROOT, build, digest

FUSE_SENTINEL = b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX'
ASAR = 'resources/app.asar'


def rules():
    return json.loads((ROOT / 'tools/compatibility-windows.json').read_text(encoding='utf-8'))


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def reject_link(path):
    """Reject Windows junctions/reparse points as well as POSIX symlinks."""
    s = path.lstat()
    if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
        raise ValueError('不支持符号链接、目录联接或云端占位文件：' + str(path))
    if stat.S_ISREG(s.st_mode) and s.st_nlink > 1:
        raise ValueError('不支持硬链接文件：' + str(path))
    return s


def safe_path(path, missing=False):
    path = Path(os.path.abspath(path))
    if os.name == 'nt' and (str(path).startswith('\\\\') or ':' in str(path)[2:]):
        raise ValueError('请选择本地磁盘上的普通路径，不支持网络路径或备用数据流')
    for part in reversed((path, *path.parents)):
        if part.exists() or part.is_symlink():
            reject_link(part)
        elif not missing or part != path:
            raise ValueError('路径不存在：' + str(part))
    return path


def app_path(value):
    path = Path(value)
    if path.name.casefold() == 'antigravity.exe':
        path = path.parent
    return safe_path(path, missing=True)


def backup_path(app):
    return app.with_name(app.name + '.zh-cn-backup')


def snapshot(root):
    """Hash every regular file; retain empty directories in the manifest."""
    safe_path(root)
    if not root.is_dir():
        raise ValueError('应用或备份不是目录：' + str(root))
    result = {}
    names = set()
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            p = Path(base) / name
            s = reject_link(p)
            relative = p.relative_to(root).as_posix()
            if relative.casefold() in names:
                raise ValueError('文件名存在大小写冲突：' + relative)
            names.add(relative.casefold())
            if stat.S_ISDIR(s.st_mode):
                result[relative] = {'type': 'directory'}
            elif stat.S_ISREG(s.st_mode):
                result[relative] = {'type': 'file', 'size': s.st_size, 'sha256': file_hash(p)}
            else:
                raise ValueError('不支持的文件类型：' + relative)
    return result


def inspect_files(app, allowed_asar=None):
    safe_path(app)
    rule = rules()
    exe, asar = app / rule['exe'], app / ASAR
    safe_path(exe)
    safe_path(asar)
    if file_hash(exe) != rule['exe_sha256']:
        raise ValueError('主程序与已核对的 Windows x64 2.22.0 不一致；未修改应用')
    with exe.open('rb') as f:
        header = f.read(64)
        if len(header) != 64 or header[:2] != b'MZ':
            raise ValueError('无效的 Windows 主程序')
        f.seek(struct.unpack_from('<I', header, 0x3c)[0])
        if f.read(6) != b'PE\0\0\x64\x86':
            raise ValueError('主程序不是 Windows x64')
        f.seek(rule['fuse_offset'])
        wire = FUSE_SENTINEL + bytes((1, len(rule['fuses_v1']))) + rule['fuses_v1'].encode('ascii')
        if f.read(len(wire)) != wire or rule['fuses_v1'][4] != '0':
            raise ValueError('Electron 校验配置不受支持；不会修改安全开关')
    raw = asar.read_bytes()
    sha = digest(raw)
    if sha not in (rule['asar_sha256'], allowed_asar):
        raise ValueError('界面资源不是受支持的原版或本次备份记录中的汉化版')
    archive = Archive(raw)
    package = json.loads(archive.read('package.json'))
    if package.get('name') != 'antigravity' or package.get('version') != rule['version']:
        raise ValueError('请选择 Antigravity Desktop 2.22.0，不能使用 Antigravity IDE')
    if sha == rule['asar_sha256'] and digest(archive.read(rule['entry'])) != rule['preload_sha256']:
        raise ValueError('翻译入口指纹不匹配')
    return {'version': rule['version'], 'asar_sha256': sha,
            'exe_sha256': rule['exe_sha256'], 'patched': sha != rule['asar_sha256']}


def patched_bytes(original):
    archive = Archive(original)
    rule = rules()
    if digest(original) != rule['asar_sha256']:
        raise ValueError('仅允许修改受支持的原版资源')
    payload = archive.read(rule['entry']) + b'\n' + build() + b'\n'
    result = archive.replace(rule['entry'], payload)
    if Archive(result).read(rule['entry']) != payload:
        raise ValueError('汉化资源构建校验失败')
    return result


def require_windows():
    if sys.platform != 'win32':
        raise ValueError('本安装器仅在 Windows 11 x64 上运行')
    version = sys.getwindowsversion()
    if version.build < 22000 or version.product_type != 1:
        raise ValueError('当前测试范围仅包括 Windows 11 客户端，不包括 Windows 10 或 Server')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.IsWow64Process2.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ushort), ctypes.POINTER(ctypes.c_ushort))
    kernel.IsWow64Process2.restype = ctypes.c_int
    process, native = ctypes.c_ushort(), ctypes.c_ushort()
    if not kernel.IsWow64Process2(kernel.GetCurrentProcess(), ctypes.byref(process), ctypes.byref(native)):
        raise ctypes.WinError(ctypes.get_last_error())
    if native.value != 0x8664 or process.value != 0 or struct.calcsize('P') != 8:
        raise ValueError('需要 Intel/AMD x64 Windows 和 64 位 Python；ARM64 模拟环境不在本次范围内')


def ensure_stopped():
    """Use the read-only Toolhelp API; do not terminate any process."""
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    for name in ('Process32FirstW', 'Process32NextW'):
        fn = getattr(kernel, name)
        fn.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessEntry))
        fn.restype = wintypes.BOOL
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        ok = kernel.Process32FirstW(handle, ctypes.byref(entry))
        while ok:
            if entry.szExeFile.casefold() in ('antigravity.exe', 'uninstall antigravity.exe', 'antigravity-x64.exe'):
                raise ValueError('请完全退出 Antigravity，并关闭安装或卸载程序后重试')
            ok = kernel.Process32NextW(handle, ctypes.byref(entry))
        if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(handle)


@contextmanager
def operation_lock(app):
    """OS releases the lock after a crash; the empty lock file may remain."""
    lock = safe_path(app.with_name(app.name + '.zh-cn.lock'), missing=True)
    with lock.open('a+b') as f:
        f.seek(0, 2)
        if f.tell() == 0:
            f.write(b'0')
            f.flush()
        f.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:  # Portable fault-injection tests; CLI still requires Windows.
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError('另一个安装或还原任务正在运行，请稍后重试') from exc
        try:
            yield
        finally:
            f.seek(0)
            if os.name == 'nt':
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())


def load_backup(app):
    root = safe_path(backup_path(app))
    record = safe_path(root / 'manifest.json')
    meta = json.loads(record.read_text(encoding='utf-8'))
    if (meta.get('schema') != 1 or meta.get('platform') != 'windows-x64'
            or not isinstance(meta.get('app'), str) or Path(meta['app']) != app
            or meta.get('version') != rules()['version']):
        raise ValueError('备份记录与应用路径或版本不匹配；请勿移动或修改备份目录')
    original = root / 'original'
    if snapshot(original) != meta.get('original_manifest'):
        raise ValueError('备份文件校验失败，已停止操作')
    inspect_files(original)
    h = meta.get('patched_asar_sha256', '')
    if not isinstance(h, str) or len(h) != 64 or any(c not in '0123456789abcdef' for c in h):
        raise ValueError('备份中的汉化校验值无效')
    return meta


def current_state(app, meta):
    if not app.exists():
        safe_path(app, missing=True)
        return 'missing'
    tree = snapshot(app)
    baseline = meta['original_manifest']
    if tree == baseline:
        return 'original'
    # Everything except the single patched archive must match the full backup.
    archive_entry = tree.pop(ASAR, None)
    other_original = {k: v for k, v in baseline.items() if k != ASAR}
    if tree == other_original:
        if archive_entry is None:
            return 'missing-asar'
        if (archive_entry.get('type') == 'file'
                and archive_entry.get('sha256') == meta['patched_asar_sha256']):
            return 'patched'
    raise ValueError('应用文件已发生其他变化，可能已更新；已停止，避免旧版备份覆盖现有文件')


def check_space(parent, required):
    if shutil.disk_usage(parent).free < required + 64 * 1024 * 1024:
        raise ValueError('磁盘剩余空间不足，无法安全备份和替换资源')


def prepare_backup(app):
    root = backup_path(app)
    if root.exists() or root.is_symlink():
        meta = load_backup(app)
        current_state(app, meta)
        return meta  # Never overwrite an existing backup.
    inspect_files(app)
    before = snapshot(app)
    check_space(app.parent, sum(v.get('size', 0) for v in before.values()) * 2)
    staging = Path(tempfile.mkdtemp(prefix='.antigravity-zh-backup-', dir=app.parent))
    try:
        shutil.copytree(app, staging / 'original')
        if snapshot(staging / 'original') != before or snapshot(app) != before:
            raise ValueError('备份期间应用文件发生变化，未修改应用，请退出应用后重试')
        patched = patched_bytes((staging / 'original' / ASAR).read_bytes())
        meta = {'schema': 1, 'platform': 'windows-x64', 'app': str(app),
                'version': rules()['version'], 'patch_version': rules()['patch_version'],
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'original_manifest': before, 'patched_asar_sha256': digest(patched)}
        write_json(staging / 'manifest.json', meta)
        ensure_stopped()
        if root.exists():
            raise ValueError('备份目录已存在；不会覆盖')
        os.rename(staging, root)
        return load_backup(app)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def replace_archive(app, data, meta, expected_state):
    """Flush, verify and atomically replace one file on the same volume."""
    target = app / ASAR
    check_space(target.parent, len(data))
    # Keep staging OUTSIDE the app, so it cannot contaminate the tree check.
    fd, name = tempfile.mkstemp(prefix='.antigravity-zh-asar-', dir=app.parent)
    staged = Path(name)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if file_hash(staged) != digest(data):
            raise ValueError('临时资源校验失败，未替换应用')
        shutil.copystat(backup_path(app) / 'original' / ASAR, staged)
        ensure_stopped()
        if current_state(app, meta) != expected_state:
            raise ValueError('准备期间应用发生变化，已停止替换')
        os.replace(staged, target)
    finally:
        if staged.exists():
            staged.unlink()


def backup(app):
    require_windows()
    app = app_path(app)
    with operation_lock(app):
        ensure_stopped()
        meta = prepare_backup(app)
        return {'result': '原版备份已校验', 'backup': str(backup_path(app)),
                'application_state': current_state(app, meta)}


def install(app, accept=False):
    require_windows()
    if not accept:
        raise ValueError('这是待实机验证的测试版；阅读说明后使用 --accept-test-build')
    app = app_path(app)
    with operation_lock(app):
        ensure_stopped()
        meta = prepare_backup(app)
        state = current_state(app, meta)
        data = patched_bytes((backup_path(app) / 'original' / ASAR).read_bytes())
        if digest(data) != meta['patched_asar_sha256']:
            raise ValueError('备份对应另一版补丁；请先还原，并保留旧备份后再处理')
        if state == 'patched':
            return {'result': '已安装本测试版，无需重复安装', 'backup': str(backup_path(app))}
        if state != 'original':
            raise ValueError('应用不完整，请先执行还原')
        replace_archive(app, data, meta, 'original')
        if current_state(app, meta) != 'patched':
            raise ValueError('安装后校验未通过，备份已保留，请执行还原')
        return {'result': '测试补丁已安装，等待 Windows 实机验证',
                'app': str(app), 'backup': str(backup_path(app)), 'exe_unchanged': True}


def restore(app):
    require_windows()
    app = app_path(app)
    with operation_lock(app):
        ensure_stopped()
        meta = load_backup(app)
        state = current_state(app, meta)
        original = backup_path(app) / 'original'
        if state == 'missing':
            check_space(app.parent, sum(v.get('size', 0) for v in meta['original_manifest'].values()))
            staging = Path(tempfile.mkdtemp(prefix='.antigravity-zh-restore-', dir=app.parent))
            try:
                shutil.copytree(original, staging / 'app')
                if snapshot(staging / 'app') != meta['original_manifest']:
                    raise ValueError('还原副本校验失败')
                ensure_stopped()
                if app.exists() or app.is_symlink():
                    raise ValueError('应用路径已被其他程序创建，已停止还原')
                os.rename(staging / 'app', app)
            finally:
                shutil.rmtree(staging)
        elif state != 'original':
            replace_archive(app, (original / ASAR).read_bytes(), meta, state)
        if current_state(app, meta) != 'original':
            raise ValueError('还原后校验未通过；原版备份仍然保留')
        return {'result': '原版已还原，全部应用文件与备份一致', 'app': str(app),
                'backup_retained': str(backup_path(app))}


def doctor(app):
    require_windows()
    app = app_path(app)
    root = backup_path(app)
    if root.exists() or root.is_symlink():
        meta = load_backup(app)
        state = current_state(app, meta)
        result = {'application_state': state, 'backup_verified': True}
        if state in ('original', 'patched'):
            result.update(inspect_files(app, meta['patched_asar_sha256']))
    else:
        result = inspect_files(app)
        result.update(application_state='original', backup_verified=False)
    result.update(app=str(app), backup=str(root), target='Windows 11 x64',
                  patch_version=rules()['patch_version'], native_ui_tested=False)
    return result


def candidates():
    """Read known install locations and uninstall registry; never write registry."""
    values = []
    for variable, tail in [('LOCALAPPDATA', 'Programs/Antigravity'), ('ProgramFiles', 'Antigravity')]:
        if os.environ.get(variable):
            values.append(Path(os.environ[variable]) / tail)
    if sys.platform == 'win32':
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, r'Software\Microsoft\Windows\CurrentVersion\Uninstall') as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            with winreg.OpenKey(key, winreg.EnumKey(key, i)) as sub:
                                if winreg.QueryValueEx(sub, 'DisplayName')[0] == 'Antigravity':
                                    value = winreg.QueryValueEx(sub, 'InstallLocation')[0]
                                    if value:
                                        values.append(Path(value))
                        except OSError:
                            continue
            except OSError:
                continue
    result = []
    for value in values:
        p = Path(os.path.abspath(value))
        if p not in result and ((p / 'Antigravity.exe').is_file() or backup_path(p).exists()):
            result.append(p)
    return result


def select_app(value=None, interactive=False):
    if value:
        return app_path(value)
    found = candidates()
    if len(found) == 1:
        return app_path(found[0])
    if not interactive:
        raise ValueError('未找到唯一安装目录，请使用 --app "含 Antigravity.exe 的目录"')
    if found:
        print('\n检测到以下目录：')
        for i, item in enumerate(found, 1):
            print(f'  {i}. {item}')
    value = input('请输入安装目录完整路径，或上方编号：').strip().strip('"')
    if value.isdigit() and 1 <= int(value) <= len(found):
        return app_path(found[int(value) - 1])
    if not value:
        raise ValueError('未选择应用目录')
    return app_path(value)


def show(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def menu(app):
    print('\nAntigravity 简体中文汉化补丁 · Windows 11 x64 测试版')
    print('本包尚未通过 Windows 桌面实测，不属于正式发布版本。')
    while True:
        print('\n应用目录：' + str(app))
        print('1. 检查环境与备份\n2. 备份原版\n3. 安装汉化\n4. 还原原版\n5. 更换应用目录\n0. 退出')
        choice = input('请选择：').strip()
        try:
            if choice == '0':
                return
            if choice == '1':
                show(doctor(app))
            elif choice == '2':
                print('正在校验并备份完整应用，请稍候……')
                show(backup(app))
            elif choice == '3':
                print('将自动备份完整原版，再修改界面资源；不改账号、聊天数据或系统安全设置。')
                if input('确认安装测试版请输入 INSTALL：').strip() == 'INSTALL':
                    print('正在备份、构建并校验，完成前请勿打开应用……')
                    show(install(app, True))
            elif choice == '4':
                if input('确认还原原版请输入 RESTORE：').strip() == 'RESTORE':
                    show(restore(app))
            elif choice == '5':
                app = app_path(input('请输入新的应用目录：').strip().strip('"'))
        except (OSError, ValueError, KeyError) as exc:
            print('\n操作已停止：' + str(exc))
            print('请保留备份。若为文件占用或权限问题，请先退出应用并检查目录权限。')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('menu', 'doctor', 'backup', 'install', 'restore'))
    parser.add_argument('--app', type=Path)
    parser.add_argument('--accept-test-build', action='store_true')
    args = parser.parse_args(argv)
    try:
        require_windows()
        app = select_app(args.app, args.command == 'menu')
        if args.command == 'menu':
            menu(app)
        elif args.command == 'install':
            show(install(app, args.accept_test_build))
        else:
            show(globals()[args.command](app))
    except (OSError, ValueError, KeyError) as exc:
        print('操作已停止：' + str(exc), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print('\n已取消。请保留原版备份；如操作曾被中断，先运行检查，再执行还原。')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
