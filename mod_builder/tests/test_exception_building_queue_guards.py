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
            resource_trigger = f"bca_planet_build_needs_{resource} = yes"
            self.assertNotIn(resource_trigger, rare_resources)
            self.assertNotIn(resource_trigger, destruction_triggers)

        replacement_trigger = "bca_industrial_building_repalce_for_rare_resources"
        self.assertEqual(industry_config.count(replacement_trigger), 2)
        trigger_start = destruction_triggers.index(f"{replacement_trigger} = {{")
        trigger_body = destruction_triggers[trigger_start:]
        self.assertNotIn(
            "NOT = { has_building = building_archaeo_refinery }\n\tOR = {",
            trigger_body,
        )
        self.assertIn("building1 = building_archaeo_refinery", trigger_body)
        low_tier_potentials = {
            "bca_rare_crystals_buidling_potential": "building_crystal_plant",
            "bca_volatile_motes_building_potential": "building_chemical_plant",
            "bca_exotic_gases_building_potential": "building_refinery",
        }
        for trigger, building in low_tier_potentials.items():
            self.assertIn(f"{trigger} = yes", trigger_body)
            helper_start = destruction_triggers.index(f"{trigger} = {{")
            helper_body = destruction_triggers[helper_start:]
            self.assertIn(f"building1 = {building}", helper_body)

        manual_destruction = (
            ROOT_DIR / "mod_builder/configs/manual_building_destruction.yaml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("low_rare_resource_income", destruction_triggers)
        self.assertIn(
            "bca_advanced_rare_resource_building_replace",
            destruction_triggers,
        )
        self.assertIn(
            "bca_advanced_rare_resource_building_replace",
            manual_destruction,
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

    def test_pop_assembly_gate_and_subtype_policies_are_independent(self):
        pop_assembly = (
            EXCEPTIONS_DIR / "02_bca_building_pop_assemble.txt"
        ).read_text(encoding="utf-8")
        medical = (
            EXCEPTIONS_DIR / "02_bca_building_medical.txt"
        ).read_text(encoding="utf-8")
        amenity_management = (
            EXCEPTIONS_DIR / "21_bca_building_amenity_management.txt"
        ).read_text(encoding="utf-8")
        categories = (
            ROOT_DIR / "common/colony_automation_categories/00_categories.txt"
        ).read_text(encoding="utf-8")
        triggers = (
            ROOT_DIR / "common/scripted_triggers/bca_destruction_triggers.txt"
        ).read_text(encoding="utf-8")
        bootstrap = (
            ROOT_DIR
            / "mod_builder/templates/events/bca_global_settings_bootstrap.txt.j2"
        ).read_text(encoding="utf-8")
        panel = (
            ROOT_DIR
            / "mod_builder/templates/interface/bca_global_setting_panel.gui.j2"
        ).read_text(encoding="utf-8")
        effects = (
            ROOT_DIR
            / "mod_builder/templates/common/button_effects/bca_global_settings_panel.txt.j2"
        ).read_text(encoding="utf-8")
        destruction_config = (
            ROOT_DIR / "mod_builder/configs/manual_building_destruction.yaml"
        ).read_text(encoding="utf-8")
        generated_destruction = (
            ROOT_DIR
            / "mod_builder/templates/generated_configs/destruction_building_strategies.yaml"
        ).read_text(encoding="utf-8")

        self.assertNotIn("planet_automation_robot_assembly", categories)
        self.assertNotIn("planet_automation_robot_assembly", pop_assembly)
        self.assertEqual(pop_assembly.count('category = "planet_automation_pop_assembly"'), 4)
        self.assertEqual(
            pop_assembly.count("bca_can_build_biological_pop_assemble = yes"),
            2,
        )
        self.assertEqual(
            pop_assembly.count("bca_can_build_mechanical_pop_assemble = yes"),
            2,
        )
        self.assertEqual(
            medical.count("has_country_flag = bca_build_medical_buildings"),
            2,
        )
        self.assertEqual(
            amenity_management.count("has_country_flag = bca_build_medical_buildings"),
            2,
        )
        self.assertNotIn("bca_can_build_pop_assemble", medical)
        self.assertNotIn("bca_can_build_pop_assemble", amenity_management)
        self.assertIn("bca_can_build_pop_assemble = {", triggers)
        self.assertIn("bca_can_remove_pop_assemble = {", triggers)
        for condition in (
            "free_district_slots = 0",
            "free_building_slots = 0",
            "free_housing <= 0",
            "free_amenities <= 500",
            "bca_can_build_pop_assemble = no",
        ):
            self.assertIn(condition, triggers)

        policies = {
            "biological_pop_assembly_buildings": (
                "biological_pop_assembly",
                "bca_build_biological_pop_assembly_buildings",
                "bca_remove_biological_pop_assembly_buildings",
                "bca_can_remove_biological_pop_assemble",
            ),
            "mechanical_pop_assembly_buildings": (
                "mechanical_pop_assembly",
                "bca_build_mechanical_pop_assembly_buildings",
                "bca_remove_mechanical_pop_assembly_buildings",
                "bca_can_remove_mechanical_pop_assemble",
            ),
            "medical_buildings": (
                "medical_buildings",
                "bca_build_medical_buildings",
                "bca_remove_medical_buildings",
                "bca_can_remove_medical_buildings",
            ),
        }
        for name, (ui_name, build_flag, remove_flag, destruction_trigger) in policies.items():
            self.assertIn(f'set_country_flag = {build_flag}', bootstrap)
            self.assertIn(f'remove_country_flag = {remove_flag}', bootstrap)
            self.assertIn(f'"name": "{name}"', effects)
            self.assertIn(build_flag, effects)
            self.assertIn(remove_flag, effects)
            self.assertIn(f'name = "{ui_name}"', panel)
            self.assertIn(destruction_trigger, triggers)
            self.assertIn(destruction_trigger, destruction_config)
            self.assertIn(destruction_trigger, generated_destruction)

            trigger_body = (
                f"{destruction_trigger} = {{\n"
                "\tAND = {\n"
                "\t\tbca_can_remove_building = yes\n"
                f"\t\towner = {{ has_country_flag = {remove_flag} }}\n"
                "\t}\n"
                "}"
            )
            self.assertIn(trigger_body, triggers)

        for trigger in (
            "bca_can_build_biological_pop_assemble",
            "bca_can_build_mechanical_pop_assemble",
        ):
            trigger_start = triggers.index(f"{trigger} = {{")
            trigger_body = triggers[trigger_start : trigger_start + 240]
            self.assertIn("bca_can_build_pop_assemble = yes", trigger_body)

        self.assertIn("bca_population_assembly_settings_initialized", bootstrap)
        self.assertIn(
            "remove_country_flag = bca_build_pop_assemble_even_if_no_jobs", bootstrap
        )
        self.assertIn(
            "remove_country_flag = bac_remove_pop_assemble_buildings", bootstrap
        )
        migration = bootstrap[bootstrap.index("bca_population_assembly_settings_initialized") :]
        migration = migration[: migration.index("bca_jr_default_manual_manage_job_initialized")]
        self.assertNotIn("bca_build_pop_assemble_even_if_no_jobs", migration)
        self.assertNotIn("bac_remove_pop_assemble_buildings", migration)

        self.assertIn('name = "pop_assembly"', panel)
        self.assertIn("bca_global_settings_pop_assemble_always_selected", effects)
        self.assertIn("bca_global_settings_pop_assemble_needed_selected", effects)
        self.assertIn("bca_global_settings_pop_assemble_demolish_selected", effects)
        self.assertIn("bca_can_remove_pop_assemble", destruction_config)
        self.assertIn("bca_can_remove_pop_assemble", generated_destruction)
        behavior_rows = (
            "rare_buildings",
            "pop_assembly",
            "biological_pop_assembly",
            "mechanical_pop_assembly",
            "medical_buildings",
            "deurbanization",
        )
        row_positions = [
            panel.index(f'gsc.choice_row(name = "{name}"')
            for name in behavior_rows
        ]
        self.assertEqual(row_positions, sorted(row_positions))


if __name__ == "__main__":
    unittest.main()
