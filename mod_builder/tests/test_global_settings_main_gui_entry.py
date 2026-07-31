from __future__ import annotations

import sys
import unittest
from pathlib import Path


MOD_BUILDER_DIR = Path(__file__).resolve().parents[1]
if str(MOD_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(MOD_BUILDER_DIR))

import generate


GUI_TEMPLATE = "interface/zz_bca_global_settings_flag_entry.gui.j2"
EFFECT_TEMPLATE = (
    "common/button_effects/bca_global_settings_main_gui.txt.j2"
)


class GlobalSettingsMainGuiEntryTests(unittest.TestCase):
    def test_entry_files_are_main_mod_only(self):
        expected_outputs = {
            GUI_TEMPLATE: "zz_bca_global_settings_flag_entry.gui",
            EFFECT_TEMPLATE: "bca_global_settings_main_gui.txt",
        }

        for template, output_name in expected_outputs.items():
            with self.subTest(template=template):
                variants = generate.get_render_variants(template, output_name)
                self.assertEqual(len(variants), 1)
                self.assertIsNone(variants[0].submod)
                self.assertEqual(variants[0].output_name, output_name)

    def test_flag_entry_preserves_vanilla_controls_and_adds_framed_button(self):
        rendered = generate.env.get_template(GUI_TEMPLATE).render()

        self.assertEqual(rendered.count('name = "maingui_flag"'), 1)
        self.assertIn('name = "topbar_shield_decoration"', rendered)
        self.assertIn('name = "button_topbar_government"', rendered)
        self.assertIn('name = "bca_global_settings_flag_entry"', rendered)
        self.assertIn('size = { width = 48 height = 48 }', rendered)
        self.assertIn('position = { x = 5 y = 5 }', rendered)
        self.assertNotIn('name = "background"', rendered)
        self.assertIn('quadTextureSprite = "gfx_planet_frame_tile"', rendered)
        self.assertIn('quadTextureSprite = "GFX_bca_setting_button"', rendered)
        self.assertIn(
            'effect = "bca_main_gui_open_global_settings"',
            rendered,
        )
        self.assertIn(
            'tooltipText = "edict_bca_open_global_settings_panel_desc"',
            rendered,
        )

    def test_button_effect_opens_one_global_settings_event_from_player(self):
        rendered = generate.env.get_template(EFFECT_TEMPLATE).render()

        self.assertIn("bca_main_gui_open_global_settings = {", rendered)
        self.assertIn("exists = from", rendered)
        self.assertIn("has_active_event = {", rendered)
        self.assertEqual(rendered.count("bca_global_settings_event.1"), 2)
        self.assertIn(
            "country_event = { id = bca_global_settings_event.1 }",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
