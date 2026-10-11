#!/usr/bin/env python3
"""Build a local Windows test ZIP; this script never publishes a release."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'LICENSE', 'Windows-Start.cmd', 'tools/windows_patcher.py', 'tools/patcher.py',
    'tools/compatibility-windows.json', 'tools/compatibility.json',
    'tools/windows-runtime.json', 'tools/package_windows.py', 'tools/run-python.cjs',
    'locales/zh-CN.json', 'src/runtime.js', 'dist/antigravity-zh-cn.js',
    'docs/WINDOWS.md', 'docs/WINDOWS-VALIDATION.md', 'docs/WINDOWS-TEST-RECORD.md',
    'tests/test_windows_patcher.py', 'tests/test_patcher.py', 'tests/runtime.test.cjs',
    'package.json', 'package-lock.json',
]


def package(runtime, output):
    rule = json.loads((ROOT / 'tools/windows-runtime.json').read_text(encoding='utf-8'))
    data = runtime.read_bytes()
    if hashlib.sha256(data).hexdigest() != rule['sha256']:
        raise ValueError('Python runtime SHA-256 does not match the official release')
    version = json.loads((ROOT / 'tools/compatibility-windows.json').read_text(encoding='utf-8'))['patch_version']
    prefix = f'antigravity-zh-cn-{version}'
    output.mkdir(parents=True, exist_ok=True)
    target = output / (prefix + '.zip')
    with zipfile.ZipFile(runtime) as source:
        names = source.namelist()
        if len(names) != len(set(names)) or 'LICENSE.txt' not in names or 'python.exe' not in names:
            raise ValueError('Unexpected Python runtime contents')
        if any('/' in n or '\\' in n or n in ('.', '..') for n in names):
            raise ValueError('Unexpected runtime path')
        with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
            hashes = {}
            def add(name, content):
                info = zipfile.ZipInfo(prefix + '/' + name, date_time=(2026, 10, 11, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                out.writestr(info, content)
                hashes[name] = hashlib.sha256(content).hexdigest()
            for name in FILES:
                content = (ROOT / name).read_bytes()
                if name.endswith('.cmd'):
                    content = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
                add(name, content)
            add('README.md', (ROOT / 'docs/WINDOWS.md').read_bytes())
            add('开始测试.txt', ('请先阅读 README.md，再双击 Windows-Start.cmd。\r\n'
                '本包仅供 Windows 11 x64 实机验证，不是正式发布版本。\r\n'
                '已内置 Python 运行环境，无需另行安装 Python 或 Node.js。\r\n'
                '如系统或单位策略阻止运行，请记录提示，不要关闭安全防护。\r\n').encode('utf-8-sig'))
            for name in sorted(names):
                content = source.read(name)
                if name.endswith('._pth'):
                    # Isolated standard library + this tool directory; no user site packages.
                    content = b'python313.zip\r\n.\r\n../tools\r\n'
                add('runtime/' + name, content)
            add('PACKAGE-SHA256.json', json.dumps(hashes, indent=2, ensure_ascii=False).encode('utf-8'))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-zip', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    target = package(args.runtime_zip, args.output)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    sums = target.with_name('SHA256SUMS.txt')
    sums.write_text(digest + '  ' + target.name + '\n', encoding='utf-8')
    print(json.dumps({'path': str(target), 'sha256': digest, 'bytes': target.stat().st_size}, indent=2))


if __name__ == '__main__':
    main()
