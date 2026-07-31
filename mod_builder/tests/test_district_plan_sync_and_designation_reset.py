from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


class DistrictPlanSyncTests(unittest.TestCase):
    def test_district_completion_clamps_plan_when_demolition_is_disabled(self):
        on_actions = (
            ROOT_DIR / "common/on_actions/colony_automation_on_action.txt"
        ).read_text(encoding="utf-8-sig")
        events = (
            ROOT_DIR / "events/bca_resource_designation_district_plan.txt"
        ).read_text(encoding="utf-8-sig")

        district_complete = on_actions.split("on_district_complete = {", 1)[1]
        district_complete = district_complete.split("on_zone_complete = {", 1)[0]
        self.assertIn("colony_automation_event.11", district_complete)
        self.assertIn("colony_automation_event.14", district_complete)

        clamp_event = events.split("id = colony_automation_event.14", 1)[1]
        clamp_event = clamp_event.split("id = colony_automation_event.13", 1)[0]
        self.assertIn(
            "has_carrier_flag = bca_pf_disable_planet_auto_destruction_district",
            clamp_event,
        )
        self.assertIn(
            "bca_clamp_district_plan_to_current_layout = yes",
            clamp_event,
        )


class DesignationResetTests(unittest.TestCase):
    def test_reset_enables_zone_demolition_without_changing_other_modes(self):
        template = (
            ROOT_DIR
            / "mod_builder/templates/events/bca_update_default_selection.txt.j2"
        ).read_text(encoding="utf-8-sig")
        reset_event = template.split("id = colony_automation_event.27", 1)[1]
        reset_event = reset_event.split("id = colony_automation_event.28", 1)[0]

        self.assertIn(
            "carrier_event = { id = colony_automation_event.23 }",
            reset_event,
        )
        self.assertNotIn(
            "bca_default_disable_auto_destruction_building",
            reset_event,
        )
        self.assertNotIn(
            "bca_default_disable_auto_destruction_district",
            reset_event,
        )
        self.assertNotIn(
            "bca_default_disable_auto_destruction_zone",
            reset_event,
        )
        self.assertNotIn(
            "bca_pf_disable_planet_auto_destruction_building",
            reset_event,
        )
        self.assertNotIn(
            "bca_pf_disable_planet_auto_destruction_district",
            reset_event,
        )

    def test_reset_button_uses_explicit_warning_tooltip(self):
        gui_template = (
            ROOT_DIR / "mod_builder/templates/interface/bca_district_gui.gui.j2"
        ).read_text(encoding="utf-8-sig")
        key = "BCA_ZONE_SELECTION_RESET_SETTINGS_ON_DESIGNATION_CHANGED_DESC"

        self.assertIn(f'tooltipText = "{key}"', gui_template)
        for language in ("english", "simp_chinese", "japanese", "russian"):
            localisation = (
                ROOT_DIR / f"localisation/{language}/bca_gui_l_{language}.yml"
            ).read_text(encoding="utf-8-sig")
            with self.subTest(language=language):
                self.assertIn(f"{key}:", localisation)


if __name__ == "__main__":
    unittest.main()
