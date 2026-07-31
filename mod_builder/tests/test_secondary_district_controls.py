from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


class SecondaryDistrictControlTests(unittest.TestCase):
    def test_unify_button_requires_compatible_plans_when_demolition_is_disabled(self):
        effects = (
            ROOT_DIR / "common/button_effects/bca_planet_setting_panel.txt"
        ).read_text(encoding="utf-8-sig")
        button = effects.split(
            "bca_planet_setting_detailed_secondary_districts_advanced_disable = {",
            1,
        )[1]
        button = button.split(
            "bca_planet_setting_show_up_on_designation_changed = {",
            1,
        )[0]

        self.assertIn('fail_text = "BCA_UNIFORM_SECONDARY_DISTRICT_NOT_ALLOW"', button)
        self.assertIn(
            "NOT = { has_carrier_flag = bca_pf_disable_planet_auto_destruction_zone }",
            button,
        )
        self.assertIn("bca_has_identical_secondary_zone_plan = yes", button)

    def test_identical_plan_trigger_compares_all_secondary_slots(self):
        template = (
            ROOT_DIR
            / "mod_builder/templates/common/scripted_triggers/bca_zone_setting_triggers.txt.j2"
        ).read_text(encoding="utf-8-sig")
        trigger = template.split("bca_has_identical_secondary_zone_plan = {", 1)[1]
        trigger = trigger.split(
            "{# These triggers let parameterized sync effects reuse one compatibility check",
            1,
        )[0]

        self.assertIn("{% for item in zones_info %}", trigger)
        self.assertIn(
            "cond.contain_any_zones_of(item.zones, secondary_districts_for_zone)",
            trigger,
        )
        self.assertIn("{% for zone_slot in ['z3','z4','z5'] %}", trigger)
        self.assertIn("pf.flag_selected_zone_type(zone_slot, item.type)", trigger)

    def test_count_button_reset_tooltip_is_localised(self):
        gui_template = (
            ROOT_DIR / "mod_builder/templates/component/zone_component.j2"
        ).read_text(encoding="utf-8-sig")
        self.assertIn(
            'delayedTooltipText = "BCA_SETTING_DISTRICT_COUNT_DESC"',
            gui_template,
        )

        for language in ("english", "simp_chinese", "japanese", "russian"):
            localisation = (
                ROOT_DIR / f"localisation/{language}/bca_gui_l_{language}.yml"
            ).read_text(encoding="utf-8-sig")
            with self.subTest(language=language):
                self.assertIn("BCA_SETTING_DISTRICT_COUNT_DESC:", localisation)
                self.assertIn("BCA_UNIFORM_SECONDARY_DISTRICT_NOT_ALLOW:", localisation)


if __name__ == "__main__":
    unittest.main()
