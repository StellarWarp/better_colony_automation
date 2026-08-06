from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
INTRO_EVENT = ROOT_DIR / "events" / "bca_intro_event.txt"
INTRO_ON_ACTION = ROOT_DIR / "common" / "on_actions" / "01_bca_intro_on_action.txt"
MESSAGE_TYPES = ROOT_DIR / "common" / "message_types" / "bac_message_types.txt"
PATCH_README = (
    ROOT_DIR / "submods" / "colony_automation_parallelize_patch" / "README.txt"
)
INTRO_LOCALISATIONS = [
    ROOT_DIR / "localisation" / language / f"bca_intro_l_{language}.yml"
    for language in ("english", "simp_chinese", "japanese", "russian")
]


class IntroNotificationsTests(unittest.TestCase):
    def test_v212_update_and_patch_notifications_are_registered(self):
        event = INTRO_EVENT.read_text(encoding="utf-8-sig")
        on_action = INTRO_ON_ACTION.read_text(encoding="utf-8-sig")
        message_types = MESSAGE_TYPES.read_text(encoding="utf-8-sig")

        self.assertIn("bca_update_v2_1_2_shown", event)
        self.assertIn(
            "set_variable = { which = bca_reserve_minerals_amount value = 0 }",
            event,
        )
        self.assertIn(
            "set_variable = { which = bca_reserve_alloys_amount value = 0 }",
            event,
        )
        self.assertIn("id = bca_intro_event.3", event)
        self.assertIn("bca_parallel_construction_patch_v0_1_0_shown", event)
        self.assertIn("MESSAGE_BCA_PARALLEL_CONSTRUCTION_PATCH", event)
        self.assertIn("key = MESSAGE_BCA_PARALLEL_CONSTRUCTION_PATCH", message_types)
        self.assertEqual(on_action.count("bca_intro_event.3"), 2)

    def test_all_supported_languages_define_the_patch_notification(self):
        for path in INTRO_LOCALISATIONS:
            with self.subTest(path=path):
                localisation = path.read_text(encoding="utf-8-sig")
                self.assertIn("v2.1.2", localisation)
                self.assertIn("MESSAGE_BCA_STARTUP_desc_log_v212", localisation)
                self.assertIn("MESSAGE_BCA_PARALLEL_CONSTRUCTION_PATCH:", localisation)
                self.assertIn(
                    "MESSAGE_BCA_PARALLEL_CONSTRUCTION_PATCH_desc:",
                    localisation,
                )

    def test_patch_does_not_require_launcher_enablement(self):
        patch_readme = PATCH_README.read_text(encoding="utf-8")

        self.assertIn("does not need to be enabled in the launcher", patch_readme)
        self.assertIn("补丁 Mod 无需在启动器中启用", patch_readme)
