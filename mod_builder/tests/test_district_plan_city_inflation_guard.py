from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CONTROLLER_TEMPLATE = (
    ROOT_DIR
    / "mod_builder/templates/common/scripted_effects/bca_resource_planet_controller.txt.j2"
)
CONTROLLER_RUNTIME = (
    ROOT_DIR / "common/scripted_effects/bca_resource_planet_controller.txt"
)
SETTING_VALUES_TEMPLATE = (
    ROOT_DIR / "mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2"
)
SETTING_VALUES_RUNTIME = (
    ROOT_DIR / "common/script_values/bca_planet_setting_values.txt"
)
DISTRICT_CONTROLLER_TEMPLATE = (
    ROOT_DIR / "mod_builder/templates/events/bca_district_controller.txt.j2"
)
DISTRICT_CONTROLLER_RUNTIME = ROOT_DIR / "events/bca_district_controller.txt"


class SecondaryDistrictPlanClampTests(unittest.TestCase):
    """Secondary district plans must never go below zero.

    A negative secondary plan inflates ``bca_num_primary_districts_plan`` above
    the planet's district capacity, which makes the automation believe the
    colony always needs another city district.
    """

    def test_runtime_controller_clamps_every_secondary_plan(self):
        runtime = CONTROLLER_RUNTIME.read_text(encoding="utf-8-sig")

        for zone_slot in ("z3", "z4", "z5"):
            with self.subTest(zone_slot=zone_slot):
                self.assertIn(
                    "check_variable = "
                    f"{{ which = bca_ps_plan_district_count_{zone_slot} value < 0 }}",
                    runtime,
                )

    def test_template_controller_clamps_every_secondary_plan(self):
        template = CONTROLLER_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("方案钳制", template)
        self.assertIn("value < 0", template)


class DistrictPlanCapacityTests(unittest.TestCase):
    def test_primary_plan_is_bounded_by_district_capacity(self):
        for label, path in (
            ("runtime", SETTING_VALUES_RUNTIME),
            ("template", SETTING_VALUES_TEMPLATE),
        ):
            with self.subTest(target=label):
                text = path.read_text(encoding="utf-8-sig")
                primary = text.split("bca_num_primary_districts_plan = {", 1)[1].split(
                    "bca_num_secondary_districts_plan = {", 1
                )[0]

                self.assertIn("min = 1", primary)
                self.assertIn("max = value:bca_potential_max_districts", primary)

    def test_secondary_plan_total_is_not_negative(self):
        for label, path in (
            ("runtime", SETTING_VALUES_RUNTIME),
            ("template", SETTING_VALUES_TEMPLATE),
        ):
            with self.subTest(target=label):
                text = path.read_text(encoding="utf-8-sig")
                secondary = text.split("bca_num_secondary_districts_plan = {", 1)[1]
                secondary = secondary.split("bca_num_main_districts_from_ratio = {", 1)[0]

                self.assertIn("min = 0", secondary)


class DistrictDemolitionOscillationTests(unittest.TestCase):
    """A plan below the current layout needs two consecutive months before any
    district is demolished, so plan flapping cannot trigger a build/demolish
    loop on the same district slot."""

    GUARD_VARIABLE = "bca_district_demolition_pending"

    def test_runtime_event_requires_two_consecutive_signals(self):
        runtime = DISTRICT_CONTROLLER_RUNTIME.read_text(encoding="utf-8-sig")
        removal_event = runtime.split("id = colony_automation_event.2", 1)[1]
        removal_event = removal_event.split("id = colony_automation_event.11", 1)[0]

        self.assertIn(f"which = {self.GUARD_VARIABLE}", removal_event)
        self.assertIn("value >= 2", removal_event)
        self.assertIn("remove_district = district_city", removal_event)

    def test_template_event_requires_two_consecutive_signals(self):
        template = DISTRICT_CONTROLLER_TEMPLATE.read_text(encoding="utf-8")
        removal_event = template.split("id = colony_automation_event.2", 1)[1]
        removal_event = removal_event.split("{% for district_slot in ['d1', 'd2', 'd3'] %}", 1)[0]

        self.assertIn(f"which = {self.GUARD_VARIABLE}", removal_event)
        self.assertIn("value >= 2", removal_event)


if __name__ == "__main__":
    unittest.main()
