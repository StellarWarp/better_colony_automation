from __future__ import annotations

import importlib.util
import shutil
import sys
import unittest
import uuid
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "update_steam_workshop.py"
SPEC = importlib.util.spec_from_file_location("update_steam_workshop", SCRIPT_PATH)
update_workshop = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = update_workshop
SPEC.loader.exec_module(update_workshop)


class UpdateSteamWorkshopTests(unittest.TestCase):
    def setUp(self):
        self.temp_root = (
            Path(__file__).resolve().parent / "_test_workspace" / uuid.uuid4().hex
        )
        self.temp_root.mkdir(parents=True)
        self.old_root = update_workshop.ROOT_DIR
        self.old_submods = update_workshop.SUBMODS_DIR
        update_workshop.ROOT_DIR = self.temp_root
        update_workshop.SUBMODS_DIR = self.temp_root / "submods"

        self.write_package(
            self.temp_root,
            workshop_id="100",
            english="main english",
            chinese="main chinese",
        )
        self.write_package(
            self.temp_root / "submods" / "job_regulation",
            workshop_id="200",
            english="child english",
            chinese="child chinese",
        )

    def tearDown(self):
        update_workshop.ROOT_DIR = self.old_root
        update_workshop.SUBMODS_DIR = self.old_submods
        shutil.rmtree(self.temp_root)

    @staticmethod
    def write_package(
        directory: Path,
        *,
        workshop_id: str,
        english: str,
        chinese: str,
    ) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "descriptor.mod").write_text(
            f'remote_file_id="{workshop_id}"\n',
            encoding="utf-8",
        )
        (directory / "workshop_en.txt").write_text(english, encoding="utf-8")
        (directory / "workshop_cn.txt").write_text(chinese, encoding="utf-8")

    def test_loads_main_package_from_repository_root(self):
        payload = update_workshop.load_publish_payload("main")

        self.assertEqual(payload["workshop_id"], "100")
        self.assertEqual(payload["descriptions"][0]["description"], "main english")

    def test_loads_submod_package_from_submods_directory(self):
        payload = update_workshop.load_publish_payload("job_regulation")

        self.assertEqual(payload["workshop_id"], "200")
        self.assertEqual(payload["descriptions"][1]["description"], "child chinese")
        self.assertEqual(
            update_workshop.available_packages(),
            ["main", "job_regulation"],
        )

    def test_rejects_unknown_package(self):
        with self.assertRaisesRegex(ValueError, "未知 Workshop 包"):
            update_workshop.load_publish_payload("missing")


if __name__ == "__main__":
    unittest.main()
