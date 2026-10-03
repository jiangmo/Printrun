import builtins
import gettext
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from printrun.utils import get_language, install_locale


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


if __name__ == '__main__':
    unittest.main()
