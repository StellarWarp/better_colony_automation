from __future__ import annotations

import sys
import unittest
from pathlib import Path


MOD_BUILDER_DIR = Path(__file__).resolve().parents[1]
if str(MOD_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(MOD_BUILDER_DIR))

import generate


ROOT_DIR = MOD_BUILDER_DIR.parent
QUEUE_EVENT_TEMPLATE = "events/bca_district_queue_events.txt.j2"
DISTRICT_VALUE_TEMPLATE = "common/script_values/bca_planet_setting_values.txt.j2"
DISTRICT_CONTROLLER_TEMPLATE = "events/bca_district_controller.txt.j2"
ARCOLOGY_TEMPLATE = "events/bac_gen_colony_transform_events.txt.j2"


class DistrictQueueTrackingTests(unittest.TestCase):
    def test_queue_events_track_each_district_slot_and_clamp_decrements(self):
        config = generate.load_configs()
        rendered = generate.env.get_template(QUEUE_EVENT_TEMPLATE).render(**config)

        self.assertIn("id = colony_automation_event.15", rendered)
        self.assertIn("id = colony_automation_event.16", rendered)
        self.assertIn("last_district_changed", rendered)
        for district_slot in range(4):
            variable = f"bca_queued_district_d{district_slot}"
            self.assertIn(variable, rendered)
            self.assertIn(f"which = {variable}\n                    value >= 1", rendered)

    def test_queue_lifecycle_on_actions_and_committed_values_share_slot_names(self):
        on_actions = (
            ROOT_DIR / "common/on_actions/colony_automation_on_action.txt"
        ).read_text(encoding="utf-8-sig")
        config = generate.load_configs()
        values = generate.env.get_template(DISTRICT_VALUE_TEMPLATE).render(**config)

        self.assertIn("on_district_queued", on_actions)
        self.assertIn("on_district_unqueued", on_actions)
        self.assertIn("colony_automation_event.16", on_actions)
        self.assertIn("bca_num_queued_districts", values)
        for district_slot in range(4):
            queue_variable = f"bca_queued_district_d{district_slot}"
            self.assertIn(
                f"bca_committed_district_d{district_slot}", values
            )
            self.assertIn(f"add = {queue_variable}", values)
            self.assertNotIn(f"variable:{queue_variable}", values)

    def test_queue_state_gates_district_replacement_and_arcology_candidates(self):
        config = generate.load_configs()
        controller = generate.env.get_template(DISTRICT_CONTROLLER_TEMPLATE).render(
            **config
        )
        arcology = generate.env.get_template(ARCOLOGY_TEMPLATE).render(**config)
        resource_planner = (
            ROOT_DIR / "events/bca_resource_designation_district_plan.txt"
        ).read_text(encoding="utf-8-sig")

        for content in (controller, arcology, resource_planner):
            self.assertIn("which = bca_num_queued_districts", content)
            self.assertIn("value = 0", content)


if __name__ == "__main__":
    unittest.main()
