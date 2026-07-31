from __future__ import annotations

import sys
import unittest
from pathlib import Path


MOD_BUILDER_DIR = Path(__file__).resolve().parents[1]
if str(MOD_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(MOD_BUILDER_DIR))

import generate


EVENT_TEMPLATE = "events/bca_planet_monthly_iteration_entry.txt.j2"
CAPACITY_TEMPLATE = "common/script_values/bca_parallel_construction_capacity.txt.j2"


class PlanetMonthlyIterationConstructionCapacityTests(unittest.TestCase):
    def test_monthly_iteration_uses_parallel_construction_capacity(self):
        rendered = generate.env.get_template(EVENT_TEMPLATE).render()

        self.assertNotIn("has_building_construction = no", rendered)
        self.assertIn("is_under_colonization = no", rendered)
        self.assertIn("num_buildings = {", rendered)
        self.assertIn("type = any", rendered)
        self.assertIn("in_construction = yes", rendered)
        self.assertIn("owner_type = normal", rendered)
        self.assertIn(
            "value < value:bca_parallel_construction_capacity",
            rendered,
        )
        self.assertLess(
            rendered.index("is_under_colonization = no"),
            rendered.index("num_buildings = {"),
        )
        self.assertGreater(
            rendered.index("bca_jr_monthly_colony = yes"),
            rendered.index("bca_auto_building_destruction_entry = yes"),
        )

    def test_capacity_script_value_includes_base_and_modifier(self):
        rendered = generate.env.get_template(CAPACITY_TEMPLATE).render()

        self.assertIn("bca_parallel_construction_capacity = {", rendered)
        self.assertIn("base = 1", rendered)
        self.assertIn("add = modifier:planet_building_capacity_add", rendered)


if __name__ == "__main__":
    unittest.main()
