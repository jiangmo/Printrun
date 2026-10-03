"""Launch the frozen GUI from an unrelated directory and verify Chinese menus."""
import ctypes
from ctypes import wintypes
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import psutil


def main():
    executable = Path(sys.argv[1]).resolve()
    user32 = ctypes.windll.user32
    user32.GetMenu.restype = wintypes.HMENU
    user32.GetMenu.argtypes = [wintypes.HWND]
    user32.GetMenuStringW.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.LPWSTR, ctypes.c_int, wintypes.UINT]
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    with tempfile.TemporaryDirectory(prefix='printrun-中文-') as directory:
        config = Path(directory) / 'smoke.rc'
        config.write_text('set rpc_server False\n', encoding='utf-8')
        process = subprocess.Popen([str(executable), '-c', str(config)], cwd=directory)
        try:
            deadline = time.monotonic() + 90
            found = []
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f'GUI exited before showing its window: {process.returncode}')
                pids = {process.pid, *(p.pid for p in psutil.Process(process.pid).children(recursive=True))}

                @callback_type
                def inspect_window(hwnd, _):
                    pid = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    title = ctypes.create_unicode_buffer(512)
                    user32.GetWindowTextW(hwnd, title, len(title))
                    if pid.value in pids and user32.IsWindowVisible(hwnd) and title.value.startswith('Pronterface'):
                        found.append(hwnd)
                    return True

                user32.EnumWindows(inspect_window, 0)
                if found:
                    break
                time.sleep(0.5)
            if not found:
                raise RuntimeError('No Pronterface window appeared')
            menu = user32.GetMenu(found[0])
            label = ctypes.create_unicode_buffer(128)
            user32.GetMenuStringW(menu, 0, label, len(label), 0x400)
            if '文件' not in label.value:
                raise RuntimeError(f'Menu is not Chinese: {label.value!r}')
            print(f'PASS: frozen GUI launched from a Chinese path, first menu = {label.value}')
            user32.PostMessageW(found[0], 0x10, 0, 0)
            process.wait(timeout=20)
            if process.returncode != 0:
                raise RuntimeError(f'GUI shutdown failed: {process.returncode}')
        finally:
            if process.poll() is None:
                for child in psutil.Process(process.pid).children(recursive=True):
                    child.kill()
                process.kill()


if __name__ == '__main__':
    main()
