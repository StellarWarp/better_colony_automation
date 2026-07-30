from __future__ import annotations

import sys
import unittest
from pathlib import Path


PARSE_DIR = Path(__file__).resolve().parents[1] / "parse"
if str(PARSE_DIR) not in sys.path:
    sys.path.insert(0, str(PARSE_DIR))

from economic_outputs import (  # noqa: E402
    _build_slot_zone_output_conditions,
    _build_slot_zone_outputs,
)


class EconomicOutputsTests(unittest.TestCase):
    def test_slot_zone_outputs_ignore_conditional_only_resources(self):
        profiles = {
            "district_city": {
                "zones": [
                    "zone_fortress",
                    "zone_foundry",
                    "zone_empty_special",
                ],
                "zone_outputs": {
                    "zone_fortress": [
                        "society_research",
                        "engineering_research",
                    ],
                    "zone_foundry": [
                        "alloys",
                        "trade",
                    ],
                },
                "zone_output_conditions": {
                    "zone_fortress": {
                        "society_research": ["soldier_is_necromancer = yes"],
                        "engineering_research": ["soldier_is_necromancer = yes"],
                    },
                    "zone_foundry": {
                        "alloys": [None, "industrial_jobs_are_catalytic_trigger = yes"],
                        "trade": ["trader_is_subterranean = yes"],
                    },
                },
            },
        }

        outputs = _build_slot_zone_outputs(["district_city"], profiles)
        conditions = _build_slot_zone_output_conditions(["district_city"], profiles)

        self.assertEqual(
            outputs,
            {
                "zone_empty_special": [],
                "zone_fortress": [],
                "zone_foundry": ["alloys"],
            },
        )
        self.assertEqual(conditions, {"zone_foundry": {"alloys": [None]}})


if __name__ == "__main__":
    unittest.main()
