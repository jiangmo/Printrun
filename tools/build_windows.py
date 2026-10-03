"""Build the same two one-file executables as the upstream Windows release."""
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main():
    if sys.platform != 'win32' or struct.calcsize('P') != 8:
        raise SystemExit('Build requires Windows and 64-bit Python')
    run('tools/check_translations.py')
    run('tools/compile_translations.py')
    run('setup.py', 'build_ext', '--inplace')
    import wx
    wx_locale = Path(wx.__file__).parent / 'locale' / 'zh_CN'
    for name, script, icon, mode in (
        ('Pronterface', 'pronterface.py', 'pronterface.ico', '--windowed'),
        ('Pronsole', 'pronsole.py', 'pronsole.ico', '--console'),
    ):
        run('-m', 'PyInstaller', '--clean', '--noconfirm', '--onefile', mode,
            '--name', name, '--icon', str(ROOT / 'assets_raw/icons' / icon),
            '--add-data', f'{ROOT / "printrun/assets"}:printrun/assets',
            '--add-data', f'{ROOT / "locale"}:locale',
            '--add-data', f'{wx_locale}:wx/locale/zh_CN',
            '--hidden-import', 'printrun.gcoder_line', script)
    # Also ship editable catalogs, upstream documentation and the full GPL.
    shutil.copytree(ROOT / 'locale', ROOT / 'dist/locale', dirs_exist_ok=True)
    for path in [ROOT / 'COPYING', ROOT / 'README.md', *ROOT.glob('???-*.md')]:
        shutil.copy2(path, ROOT / 'dist' / path.name)
    output = subprocess.check_output([sys.executable, 'pronsole.py', '--version'], cwd=ROOT, text=True)
    version = output.strip().split()[-1].replace('+', '-')
    shutil.make_archive(str(ROOT / f'Printrun-{version}-win_x64'), 'zip', ROOT / 'dist')


if __name__ == '__main__':
    main()
