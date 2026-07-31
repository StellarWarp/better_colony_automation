from __future__ import annotations

import importlib.util
import shutil
import sys
import unittest
import uuid
from pathlib import Path

import yaml


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "publish_mod.py"
SPEC = importlib.util.spec_from_file_location("publish_mod", SCRIPT_PATH)
publish_mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = publish_mod
SPEC.loader.exec_module(publish_mod)


class PublishModTests(unittest.TestCase):
    def setUp(self):
        self.temp_base = (
            Path(__file__).resolve().parent
            / "_test_workspace"
            / uuid.uuid4().hex
        )
        self.temp_base.mkdir(parents=True)
        self.root = self.temp_base / "repo"
        self.root.mkdir()
        self.old_root = publish_mod.ROOT_DIR
        publish_mod.ROOT_DIR = self.root

        (self.root / "common").mkdir()
        (self.root / "interface").mkdir()
        (self.root / "descriptor.mod").write_text("name=\"main\"\n", encoding="utf-8")
        (self.root / "submod.mod").write_text("name=\"submod\"\n", encoding="utf-8")
        (self.root / "common" / "main.txt").write_text(
            "main_effect = { }\n",
            encoding="utf-8",
        )
        (self.root / "common" / "child.txt").write_text(
            "# submod job_regulation\nchild_effect = { }\n",
            encoding="utf-8",
        )
        (self.root / "interface" / "panel_job_regulation.gui").write_text(
            "# submod job_regulation file_name panel.gui\n"
            "guiTypes = { }\n",
            encoding="utf-8",
        )

        self.main_target = self.temp_base / "targets" / "main"
        self.submod_target = self.temp_base / "targets" / "job_regulation"
        self.config_path = self.root / "publish.yaml"
        config = {
            "source_directories": ["common", "interface"],
            "main": {
                "target": str(self.main_target),
                "root_files": {"descriptor.mod": "descriptor.mod"},
            },
            "submods": {
                "job_regulation": {
                    "target": str(self.submod_target),
                    "root_files": {"submod.mod": "descriptor.mod"},
                }
            },
        }
        self.config_path.write_text(
            yaml.safe_dump(config, sort_keys=False),
            encoding="utf-8",
        )

    def tearDown(self):
        publish_mod.ROOT_DIR = self.old_root
        shutil.rmtree(self.temp_base)

    def test_routes_and_renames_files(self):
        result = publish_mod.publish(self.config_path, dry_run=False)

        self.assertEqual(result["main"]["copied"], 2)
        self.assertEqual(result["job_regulation"]["copied"], 3)
        self.assertTrue((self.main_target / "common" / "main.txt").exists())
        self.assertFalse((self.main_target / "common" / "child.txt").exists())
        self.assertTrue(
            (self.submod_target / "common" / "child.txt").exists()
        )
        self.assertTrue(
            (self.submod_target / "interface" / "panel.gui").exists()
        )
        self.assertFalse(
            (
                self.submod_target
                / "interface"
                / "panel_job_regulation.gui"
            ).exists()
        )

    def test_cleans_only_configured_paths_on_every_publish(self):
        publish_mod.publish(self.config_path, dry_run=False)
        unrelated = self.main_target / "unrelated.txt"
        unrelated.write_text("keep\n", encoding="utf-8")
        old_directory = self.main_target / "old"
        old_directory.mkdir()
        (old_directory / "nested.txt").write_text("remove\n", encoding="utf-8")
        (self.root / "common" / "main.txt").unlink()

        result = publish_mod.publish(self.config_path, dry_run=False)

        self.assertEqual(result["main"]["deleted"], 2)
        self.assertFalse((self.main_target / "common" / "main.txt").exists())
        self.assertTrue(unrelated.exists())
        self.assertTrue(old_directory.exists())
        self.assertTrue((self.main_target / "descriptor.mod").exists())

    def test_dry_run_does_not_replace_target(self):
        self.main_target.mkdir(parents=True)
        unmanaged = self.main_target / "legacy.txt"
        unmanaged.write_text("keep\n", encoding="utf-8")

        result = publish_mod.publish(
            self.config_path,
            dry_run=True,
            selected_packages={"main"},
        )

        self.assertEqual(result["main"]["deleted"], 0)
        self.assertTrue(unmanaged.exists())
        self.assertFalse((self.main_target / "descriptor.mod").exists())

    def test_writes_launcher_descriptor_with_published_target_path(self):
        config = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        launcher_descriptor = self.temp_base / "launcher" / "main.mod"
        config["main"]["launcher_descriptor"] = str(launcher_descriptor)
        self.config_path.write_text(
            yaml.safe_dump(config, sort_keys=False),
            encoding="utf-8",
        )

        result = publish_mod.publish(
            self.config_path,
            dry_run=False,
            selected_packages={"main"},
        )

        text = launcher_descriptor.read_text(encoding="utf-8")
        self.assertIn('name="main"', text)
        self.assertIn(f'path="{self.main_target.resolve().as_posix()}"', text)
        self.assertEqual(result["main"]["copied"], 3)


if __name__ == "__main__":
    unittest.main()
