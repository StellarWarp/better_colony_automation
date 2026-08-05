from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
EXCEPTIONS_DIR = ROOT_DIR / "common/colony_automation_exceptions"


class ExceptionBuildingQueueGuardTests(unittest.TestCase):
    def test_crime_and_amenity_buildings_allow_only_one_matching_queue_item(self):
        expected_buildings = {
            "02_bca_building_crime_management.txt": (
                "building_fe_security_1",
                "building_precinct_house",
                "building_state_academy",
                "building_sentinel_posts",
            ),
            "21_bca_building_amenity_management.txt": (
                "building_medical_2",
                "building_holo_theatres",
                "building_xeno_zoo",
                "building_drone_storage",
                "building_hive_warren",
            ),
        }

        for file_name, buildings in expected_buildings.items():
            content = (EXCEPTIONS_DIR / file_name).read_text(encoding="utf-8")
            for building in buildings:
                self.assertIn(
                    f"num_buildings = {{ type = {building} "
                    "in_construction = yes value < 1 }",
                    content,
                )

    def test_rare_resource_buildings_can_replace_job_only_industry(self):
        rare_resources = (
            EXCEPTIONS_DIR / "03_bca_building_rare_resources.txt"
        ).read_text(encoding="utf-8")
        destruction_triggers = (
            ROOT_DIR / "common/scripted_triggers/bca_destruction_triggers.txt"
        ).read_text(encoding="utf-8")
        industry_config = (
            ROOT_DIR / "mod_builder/configs/buildings/industry.yaml"
        ).read_text(encoding="utf-8")

        retain_flag = "has_country_flag = bca_retain_low_level_rare_resource_buildings"
        self.assertEqual(rare_resources.count(retain_flag), 3)
        self.assertIn("bca_has_minerals_to_build = yes", destruction_triggers)
        for resource in ("rare_crystals", "volatile_motes", "exotic_gases"):
            self.assertIn(
                f"bca_planet_build_needs_{resource} = yes",
                destruction_triggers,
            )

        replacement_trigger = "bca_industrial_building_repalce_for_rare_resources"
        self.assertEqual(industry_config.count(replacement_trigger), 2)
        trigger_start = destruction_triggers.index(f"{replacement_trigger} = {{")
        trigger_body = destruction_triggers[trigger_start:]
        self.assertNotIn(
            "NOT = { has_building = building_archaeo_refinery }\n\tOR = {",
            trigger_body,
        )

    def test_low_tier_rare_resource_buildings_are_retained_by_default(self):
        bootstrap_template = (
            ROOT_DIR
            / "mod_builder/templates/events/bca_global_settings_bootstrap.txt.j2"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "set_country_flag = bca_retain_low_level_rare_resource_buildings",
            bootstrap_template,
        )
        self.assertNotIn(
            "remove_country_flag = bca_retain_low_level_rare_resource_buildings",
            bootstrap_template,
        )


if __name__ == "__main__":
    unittest.main()
