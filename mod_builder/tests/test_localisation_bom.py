from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
BOM = b"\xef\xbb\xbf"


class LocalisationBomTests(unittest.TestCase):
    """Stellaris ignores localisation files without a UTF-8 BOM.

    When the BOM is missing the game shows raw keys such as
    ``BCA_GLOBAL_SETTINGS_ECONOMIC_DISPLAY_UNIT_K`` in the UI, so every
    localisation file must keep its BOM.
    """

    def setUp(self) -> None:
        self.files = sorted((ROOT_DIR / "localisation").rglob("*.yml"))
        # 岗位调控（子 mod）的本地化已移出主 mod 加载目录，放在暂存目录里，
        # 但仍然属于本仓库，BOM 同样必须保留。
        staging = ROOT_DIR / "submods/job_regulation/source/localisation"
        if staging.is_dir():
            self.files += sorted(staging.rglob("*.yml"))

    def test_localisation_files_exist(self):
        self.assertGreaterEqual(len(self.files), 40)

    def test_every_localisation_file_starts_with_bom(self):
        for path in self.files:
            with self.subTest(path=str(path.relative_to(ROOT_DIR))):
                self.assertTrue(
                    path.read_bytes().startswith(BOM),
                    f"{path.name} is missing the UTF-8 BOM; the game will show raw keys",
                )

    def test_every_localisation_file_declares_its_language(self):
        for path in self.files:
            language = path.name.split("_l_")[-1].removesuffix(".yml")
            text = path.read_text(encoding="utf-8-sig")
            with self.subTest(path=path.name):
                self.assertIn(f"l_{language}:", text)


if __name__ == "__main__":
    unittest.main()
