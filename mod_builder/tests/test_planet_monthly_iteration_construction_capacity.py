from __future__ import annotations

import sys
import unittest
from pathlib import Path


MOD_BUILDER_DIR = Path(__file__).resolve().parents[1]
if str(MOD_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(MOD_BUILDER_DIR))

import generate


EVENT_TEMPLATE = "events/bca_planet_monthly_iteration_entry.txt.j2"


class PlanetMonthlyIterationConstructionCapacityTests(unittest.TestCase):
    def test_monthly_iteration_delegates_capacity_to_native_scheduler(self):
        rendered = generate.env.get_template(EVENT_TEMPLATE).render()

        self.assertNotIn("has_building_construction = no", rendered)
        self.assertIn("is_under_colonization = no", rendered)
        self.assertNotIn("num_buildings = {", rendered)
        self.assertNotIn("bca_parallel_construction_capacity", rendered)
        self.assertGreater(
            rendered.index("bca_jr_monthly_colony = yes"),
            rendered.index("bca_auto_building_destruction_entry = yes"),
        )


if __name__ == "__main__":
    unittest.main()
