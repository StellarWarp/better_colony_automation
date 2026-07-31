from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CALC_TEMPLATE = (
    ROOT_DIR
    / "mod_builder"
    / "templates"
    / "common"
    / "scripted_effects"
    / "bca_job_regulation_calc.txt.j2"
)
MAP_TEMPLATE = (
    ROOT_DIR
    / "mod_builder"
    / "templates"
    / "common"
    / "scripted_effects"
    / "bca_job_regulation_map_effect.txt.j2"
)


class JobRegulationOpenJobsTests(unittest.TestCase):
    def test_open_jobs_are_derived_from_deprioritized_free_jobs(self):
        template = CALC_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("include_deprioritized_jobs = yes", template)
        self.assertIn("variable = bca_jr_acc_all_free_job_count_$JOB$", template)
        self.assertIn("value = bca_jr_acc_total_job_count_$JOB$", template)
        self.assertIn("value = bca_jr_acc_all_free_job_count_$JOB$", template)
        self.assertIn("value = bca_jr_acc_free_job_count_$JOB$", template)
        self.assertNotIn(
            "is_variable_set = bca_jr_acc_all_free_job_count_$JOB$", template
        )
        self.assertNotIn(
            "is_variable_set = bca_jr_acc_free_job_count_$JOB$", template
        )
        self.assertNotIn(
            "bca_jr_acc_open_job_count_$JOB$ value < 0", template
        )
        self.assertNotIn(
            "bca_jr_acc_open_job_count_$JOB$ value > bca_jr_acc_total_job_count_$JOB$",
            template,
        )

    def test_automated_workforce_uses_total_supply_and_open_job_cap(self):
        template = CALC_TEMPLATE.read_text(encoding="utf-8")
        finalize = template.split("bca_jr_finalize_single_job_stats = {", 1)[1].split(
            "bca_jr_finalize_job_stats = {", 1
        )[0]

        open_jobs = finalize.index("which = bca_jr_acc_open_job_count_$JOB$")
        automation = finalize.index("which = bca_jr_acc_automated_capacity_workforce_$JOB$")
        self.assertLess(open_jobs, automation)
        self.assertIn(
            "value = modifier:job_$JOB$_automated_workforce_mult", finalize
        )
        self.assertIn(
            "value > bca_jr_acc_open_job_count_$JOB$", finalize
        )
        self.assertIn(
            "value = bca_jr_acc_open_job_count_$JOB$", finalize
        )
        self.assertNotIn(
            "bca_jr_acc_automated_capacity_workforce_$JOB$ value > bca_jr_acc_total_job_count_$JOB$",
            finalize,
        )
        self.assertNotIn(
            "bca_jr_acc_automated_capacity_workforce_$JOB$ value < 0", finalize
        )
        self.assertNotIn(
            "bca_jr_acc_pop_capacity_limit_$JOB$ value < 0", finalize
        )

    def test_open_capacity_is_not_double_counted_in_slot_mapping(self):
        template = MAP_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn(
            "open_total_capacity value = bca_jr_total_open_job_count_$JOB$",
            template,
        )
        self.assertNotIn(
            "open_total_capacity value = bca_jr_total_automated_capacity_workforce_$JOB$",
            template,
        )


if __name__ == "__main__":
    unittest.main()
