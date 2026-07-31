from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
PLAYER_TEXT_FILES = [
    ROOT_DIR / "localisation" / "english" / "bca_gui_l_english.yml",
    ROOT_DIR / "localisation" / "english" / "bca_intro_l_english.yml",
    ROOT_DIR / "localisation" / "english" / "bt_main_3_l_english.yml",
    ROOT_DIR / "workshop_en.txt",
]


class EnglishPlayerTerminologyTests(unittest.TestCase):
    def test_uses_official_district_specialization_term(self):
        for path in PLAYER_TEXT_FILES:
            with self.subTest(path=path.name):
                content = path.read_text(encoding="utf-8-sig")
                prose = content.replace("£zone£", "")

                self.assertIsNone(re.search(r"\bzones?\b", prose, re.IGNORECASE))
                self.assertIn("district specialization", prose.lower())


if __name__ == "__main__":
    unittest.main()
