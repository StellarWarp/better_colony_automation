from __future__ import annotations

import sys
import unittest
from pathlib import Path


MOD_BUILDER_DIR = Path(__file__).resolve().parents[1]
if str(MOD_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(MOD_BUILDER_DIR))

import generate


class GenerateMetadataTests(unittest.TestCase):
    def test_job_regulation_templates_use_first_line_metadata(self):
        expected_templates = [
            "common/button_effects/bca_job_regulation_panel_buttons.txt.j2",
            "common/colony_automation_exceptions/00_bca_job_manage.txt.j2",
            "common/script_values/bca_job_production_base.txt.j2",
            "common/script_values/bca_job_regulation_display_values.txt.j2",
            "common/script_values/bca_job_regulation_factors.txt.j2",
            "common/scripted_effects/bca_job_regulation_calc.txt.j2",
            "common/scripted_effects/bca_job_regulation_effect.txt.j2",
            "common/scripted_effects/bca_job_regulation_flags.txt.j2",
            "common/scripted_effects/bca_job_regulation_gear_apply.txt.j2",
            "common/scripted_effects/bca_job_regulation_map_effect.txt.j2",
            "common/scripted_loc/bca_job_regulation_scripted_loc.txt.j2",
            "common/scripted_triggers/bca_job_regulation_triggers.txt.j2",
            "common/scripted_variables/bca_job_regulation_module.txt.j2",
            "events/bca_job_regulation_event.txt.j2",
            "interface/bca_job_regulation_icons.gfx.j2",
            "localisation/bca_job_regulation_l_all.yml.j2",
        ]

        for template_path in expected_templates:
            with self.subTest(template_path=template_path):
                metadata = generate.read_template_metadata(template_path)
                self.assertEqual(metadata.submod, "job_regulation")

    def test_global_settings_gui_has_main_and_submod_variants(self):
        template_path = "interface/bca_global_setting_panel.gui.j2"
        metadata = generate.read_template_metadata(template_path)
        self.assertEqual(metadata.compile_variants, ("main", "job_regulation"))

        variants = generate.get_render_variants(
            template_path,
            "bca_global_setting_panel.gui",
        )
        self.assertEqual(
            [(variant.output_name, variant.submod, variant.published_file_name)
             for variant in variants],
            [
                ("bca_global_setting_panel.gui", None, None),
                (
                    "bca_global_setting_panel_job_regulation.gui",
                    "job_regulation",
                    "bca_global_setting_panel.gui",
                ),
            ],
        )

    def test_generated_header_puts_publish_metadata_first(self):
        content = generate.prepend_generated_warning(
            "example = yes\n",
            "common/example.txt.j2",
            submod="job_regulation",
            published_file_name="renamed.txt",
        )
        self.assertEqual(
            content.splitlines()[0],
            "# submod job_regulation file_name renamed.txt",
        )


if __name__ == "__main__":
    unittest.main()
