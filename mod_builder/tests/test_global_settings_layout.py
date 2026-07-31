from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
COMPONENT_TEMPLATE = (
    ROOT_DIR / "mod_builder" / "templates" / "component" / "global_settings_components.j2"
)
PANEL_TEMPLATE = (
    ROOT_DIR
    / "mod_builder"
    / "templates"
    / "interface"
    / "bca_global_setting_panel.gui.j2"
)
ENGLISH_ECONOMY = (
    ROOT_DIR
    / "localisation"
    / "english"
    / "bca_global_settings_economy_l_english.yml"
)


class GlobalSettingsLayoutTests(unittest.TestCase):
    def test_economic_metrics_leave_space_after_resource_names(self):
        template = COMPONENT_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("{% set summary_x = 164 %}", template)
        self.assertIn("{% set difference_x = 276 %}", template)
        self.assertIn("{% set difference_width = 114 %}", template)

    def test_automation_buttons_fit_english_labels(self):
        component = COMPONENT_TEMPLATE.read_text(encoding="utf-8")
        panel = PANEL_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("default_button_width = 112", component)
        self.assertIn("button_width = 118", panel)

    def test_research_resource_labels_do_not_repeat_research(self):
        localisation = ENGLISH_ECONOMY.read_text(encoding="utf-8-sig")

        self.assertIn('BCA_GLOBAL_SETTINGS_ECONOMIC_PHYSICS_RESEARCH: "£physics_research£ Physics"', localisation)
        self.assertIn('BCA_GLOBAL_SETTINGS_ECONOMIC_SOCIETY_RESEARCH: "£society_research£ Society"', localisation)
        self.assertIn('BCA_GLOBAL_SETTINGS_ECONOMIC_ENGINEERING_RESEARCH: "£engineering_research£ Engineering"', localisation)


if __name__ == "__main__":
    unittest.main()
