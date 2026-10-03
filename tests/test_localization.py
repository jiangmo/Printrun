import builtins
import gettext
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from printrun.utils import configure_console_encoding, get_language, install_locale


class LocalizationTests(unittest.TestCase):
    def tearDown(self):
        install_locale('pronterface')

    def test_default_chinese_from_unrelated_working_directory(self):
        old_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            try:
                os.chdir(tmp)
                install_locale('pronterface')
                self.assertEqual(get_language(), 'zh_CN')
                self.assertEqual(builtins._('Load file'), '加载文件')
            finally:
                os.chdir(old_cwd)

    def test_explicit_english(self):
        with patch.dict(os.environ, {'PRINTRUN_LANGUAGE': 'en'}):
            install_locale('pronterface')
            self.assertEqual(builtins._('Load file'), 'Load file')

    def test_frozen_bundle(self):
        root = Path(__file__).resolve().parents[1]
        with patch('sys._MEIPASS', str(root), create=True):
            translation = install_locale('pronterface')
            self.assertIsInstance(translation, gettext.GNUTranslations)
            self.assertEqual(translation.gettext('Connect to the printer'), '连接打印机')

    def test_redirected_english_windows_console(self):
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding='cp1252')
        with patch('sys.stdout', stream), patch('sys.stdin', None), patch('sys.stderr', None):
            configure_console_encoding()
            print('用法：加载文件')
            stream.flush()
        self.assertEqual(buffer.getvalue().decode('utf-8').splitlines(), ['用法：加载文件'])


if __name__ == '__main__':
    unittest.main()
