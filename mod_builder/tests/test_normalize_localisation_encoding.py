from __future__ import annotations

import codecs
import shutil
import sys
import unittest
from pathlib import Path


MOD_BUILDER_DIR = Path(__file__).resolve().parents[1]
if str(MOD_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(MOD_BUILDER_DIR))

from normalize_localisation_encoding import normalize_localisation_encoding


class NormalizeLocalisationEncodingTests(unittest.TestCase):
    workspace = Path(__file__).parent / "_encoding_test_workspace"

    def setUp(self):
        shutil.rmtree(self.workspace, ignore_errors=True)
        self.workspace.mkdir()

    def tearDown(self):
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_adds_bom_without_changing_content(self):
        path = self.workspace / "english" / "example.yml"
        path.parent.mkdir()
        original = "l_english:\r\n key:0 \"Value\"\r\n".encode("utf-8")
        path.write_bytes(original)

        converted, unchanged = normalize_localisation_encoding(self.workspace)

        self.assertEqual((converted, unchanged), (1, 0))
        self.assertEqual(path.read_bytes(), codecs.BOM_UTF8 + original)

    def test_keeps_existing_bom(self):
        path = self.workspace / "example.yml"
        original = codecs.BOM_UTF8 + b'l_english:\n key:0 "Value"\n'
        path.write_bytes(original)

        converted, unchanged = normalize_localisation_encoding(self.workspace)

        self.assertEqual((converted, unchanged), (0, 1))
        self.assertEqual(path.read_bytes(), original)

    def test_rejects_non_utf8_content(self):
        path = self.workspace / "invalid.yml"
        path.write_bytes(b"\xff\xfe")

        with self.assertRaisesRegex(UnicodeError, "invalid.yml"):
            normalize_localisation_encoding(self.workspace)

    def test_ignores_non_localisation_files(self):
        path = self.workspace / "english" / ".rgignore"
        path.parent.mkdir()
        original = b"example.yml\n"
        path.write_bytes(original)

        converted, unchanged = normalize_localisation_encoding(self.workspace)

        self.assertEqual((converted, unchanged), (0, 0))
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
