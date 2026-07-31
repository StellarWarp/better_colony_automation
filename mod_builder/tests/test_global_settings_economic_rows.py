from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
SOURCE_CONFIG = ROOT_DIR / "mod_builder" / "configs" / "global_settings_economic_rows.yaml"
RESERVE_SOURCE_CONFIG = (
    ROOT_DIR / "mod_builder" / "configs" / "global_settings_reserve_rows.yaml"
)
GENERATED_CONFIG = (
    ROOT_DIR
    / "mod_builder"
    / "templates"
    / "generated_configs"
    / "global_settings_economic_rows.yaml"
)
GENERATED_RESERVE_CONFIG = (
    ROOT_DIR
    / "mod_builder"
    / "templates"
    / "generated_configs"
    / "global_settings_reserve_rows.yaml"
)
DISPLAY_VALUES_TEMPLATE = (
    ROOT_DIR
    / "mod_builder"
    / "templates"
    / "common"
    / "script_values"
    / "bca_display_values.txt.j2"
)
ECONOMIC_LOC_TEMPLATE = (
    ROOT_DIR
    / "mod_builder"
    / "templates"
    / "common"
    / "scripted_loc"
    / "bca_global_settings_economic_values.txt.j2"
)
JOB_LOC_TEMPLATE = (
    ROOT_DIR
    / "mod_builder"
    / "templates"
    / "common"
    / "scripted_loc"
    / "bca_job_regulation_scripted_loc.txt.j2"
)
ECONOMIC_STEP_LOCALISATIONS = [
    ROOT_DIR
    / "localisation"
    / language
    / f"bca_global_settings_economic_steps_l_{language}.yml"
    for language in ("english", "simp_chinese", "japanese", "russian")
]


class GlobalSettingsEconomicRowsTests(unittest.TestCase):
    def load_config(self, path: Path) -> dict:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_rows_have_live_resource_contract_and_balanced_steps(self):
        rows = self.load_config(SOURCE_CONFIG)["bca_global_settings_economic_rows"]

        self.assertEqual(len(rows), 13)
        for row in rows:
            with self.subTest(row=row["name"]):
                self.assertTrue(row["resource"])
                self.assertNotIn("status_text", row)
                self.assertTrue(row["summary_text"])
                self.assertTrue(row["difference_text"])
                self.assertEqual(
                    len([step for step in row["steps"] if step["value"] < 0]),
                    3,
                )
                self.assertEqual(
                    len([step for step in row["steps"] if step["value"] > 0]),
                    3,
                )

        self.assertEqual(
            [step["value"] for step in rows[0]["steps"]],
            [-1000, -250, -50, 50, 250, 1000],
        )
        self.assertEqual(
            [step["value"] for step in rows[-1]["steps"]],
            [-100, -25, -5, 5, 25, 100],
        )
        self.assertEqual(
            [rows[0]["steps"][0]["id"], rows[0]["steps"][-1]["id"]],
            ["minus_1k", "plus_1k"],
        )
        self.assertEqual(
            [rows[-1]["steps"][0]["id"], rows[-1]["steps"][-1]["id"]],
            ["minus_100", "plus_100"],
        )

    def test_generated_config_matches_handwritten_source(self):
        self.assertEqual(
            self.load_config(GENERATED_CONFIG),
            self.load_config(SOURCE_CONFIG),
        )
        self.assertEqual(
            self.load_config(GENERATED_RESERVE_CONFIG),
            self.load_config(RESERVE_SOURCE_CONFIG),
        )

    def test_nomadic_stockpile_is_shared_without_sharing_income(self):
        config = self.load_config(SOURCE_CONFIG)
        sources = config["bca_global_settings_economic_stockpile_sources"]
        rows = {
            row["name"]: row
            for row in config["bca_global_settings_economic_rows"]
        }

        self.assertEqual(
            sources["operational_reserves"],
            {
                "trigger": {"is_nomadic": "yes"},
                "situation": "situation_nomad_economy",
                "variable": "bca_gs_operational_reserves",
            },
        )
        self.assertEqual(
            rows["energy"]["stockpile_overrides"],
            ["operational_reserves"],
        )
        self.assertEqual(
            rows["minerals"]["stockpile_overrides"],
            rows["energy"]["stockpile_overrides"],
        )
        self.assertEqual(rows["energy"]["resource"], "energy")
        self.assertEqual(rows["minerals"]["resource"], "minerals")

    def test_compact_formatter_preserves_input_source_type(self):
        formatter = DISPLAY_VALUES_TEMPLATE.read_text(encoding="utf-8")
        economic_loc = ECONOMIC_LOC_TEMPLATE.read_text(encoding="utf-8")
        job_loc = JOB_LOC_TEMPLATE.read_text(encoding="utf-8")

        self.assertNotIn("\n    set = $VALUE$", formatter)
        self.assertIn("[[VALUE]set = $VALUE$]", formatter)
        self.assertIn("[[SCRIPT_VALUE]set = value:$SCRIPT_VALUE$]", formatter)
        self.assertIn(
            "bca_display_number|SCRIPT_VALUE|bca_gs_economic_",
            economic_loc,
        )
        self.assertNotIn(
            "bca_display_number|VALUE|bca_gs_economic_",
            economic_loc,
        )
        self.assertIn("bca_display_number|VALUE|bca_jr_slot_", job_loc)

    def test_reserve_labels_are_generated_for_every_language(self):
        rows = self.load_config(RESERVE_SOURCE_CONFIG)["bca_global_settings_reserve_rows"]
        labelled_steps = {
            step["text"]: step["label"]
            for row in rows
            for step in row["negative_options"] + row["positive_options"]
            if "label" in step
        }

        self.assertEqual(
            labelled_steps,
            {
                "BCA_GLOBAL_SETTINGS_STEP_MINUS_500": "-500",
                "BCA_GLOBAL_SETTINGS_STEP_PLUS_500": "+500",
            },
        )
        for path in ECONOMIC_STEP_LOCALISATIONS:
            localisation = path.read_text(encoding="utf-8-sig")
            for key, label in labelled_steps.items():
                with self.subTest(path=path, key=key):
                    self.assertIn(f'{key}: "{label}"', localisation)


if __name__ == "__main__":
    unittest.main()
