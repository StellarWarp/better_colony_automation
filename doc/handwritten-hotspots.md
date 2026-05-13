# Handwritten Hotspots

See also:

- [Source Of Truth Map](source-of-truth.md)
- [Maintenance Playbook](maintenance-playbook.md)

## Why This File Exists

A common failure mode for future maintainers is to over-focus on `mod_builder/templates/` and miss the handwritten files that still shape core runtime behavior.

This document lists the most important handwritten hotspots.

## 1. Monthly scheduler

- [`../events/bca_planet_monthly_iteration_entry.txt`](../events/bca_planet_monthly_iteration_entry.txt)

Why it matters:

- Defines the actual monthly execution order.
- Determines which planning stages run and in which sequence.
- Changes here can invalidate assumptions in every generated planner.

## 2. Generic gating triggers

- [`../common/scripted_triggers/bt_st_tool.txt`](../common/scripted_triggers/bt_st_tool.txt)

Why it matters:

- `requires_more_job` controls when planning starts.
- `bca_has_minerals_to_build` enforces reserve policy.
- These handwritten triggers are depended on almost everywhere else.

## 3. Building demolition

- [`../common/scripted_effects/bca_building_destruction.txt`](../common/scripted_effects/bca_building_destruction.txt)

Why it matters:

- This is a large handwritten ruleset.
- It is not just a thin wrapper around generated logic.
- If a bug is about removing the wrong building, start here before touching templates.

## 4. Panel-level settings and UI mode toggles

- [`../common/button_effects/bca_planet_setting_panel.txt`](../common/button_effects/bca_planet_setting_panel.txt)

Why it matters:

- Holds many non-generated planet setting toggles.
- Owns preconstruction, auto-destruction toggles, storage world mode, arcology-prep mode, and some designation change actions.
- Works together with generated zone selector logic rather than being replaced by it.

## 5. On-actions

- [`../common/on_actions/colony_automation_on_action.txt`](../common/on_actions/colony_automation_on_action.txt)
- [`../common/on_actions/01_bca_intro_on_action.txt`](../common/on_actions/01_bca_intro_on_action.txt)

Why it matters:

- These handwritten files decide when the runtime actually enters the automation system.
- They are the first place to inspect when a feature "never triggers".

## 6. Intro/update/runtime message events

- [`../events/bca_intro_event.txt`](../events/bca_intro_event.txt)
- [`../events/bca_update_event.txt`](../events/bca_update_event.txt)
- [`../events/bac_colony_transform_events.txt`](../events/bac_colony_transform_events.txt)

Why it matters:

- Some user-facing behavior and initialization-like flows live here.
- Not all event behavior belongs to generated automation templates.

## 7. Decisions and policies

- [`../common/decisions/`](../common/decisions/)
- [`../common/policies/bac_policies.txt`](../common/policies/bac_policies.txt)

Why it matters:

- These define user-facing control points for enabling, disabling, or biasing automation.
- Many runtime triggers assume these policy values or flags already exist.

## 8. Handwritten automation exceptions

Many files under [`../common/colony_automation_exceptions/`](../common/colony_automation_exceptions/) are handwritten even though some large files there are generated.

Examples:

- [`../common/colony_automation_exceptions/03_bca_building_rare_resources.txt`](../common/colony_automation_exceptions/03_bca_building_rare_resources.txt)
- [`../common/colony_automation_exceptions/02_bca_building_medical.txt`](../common/colony_automation_exceptions/02_bca_building_medical.txt)
- [`../common/colony_automation_exceptions/40_bca_building_rural_job.txt`](../common/colony_automation_exceptions/40_bca_building_rural_job.txt)

Why it matters:

- These files implement actual building choices and are often where design-specific exceptions live.
- A bug in "what gets built" may be here even if the plan flags are correct.

## 9. Handwritten runtime constants and helper files

Check these when a planner seems numerically wrong:

- [`../common/scripted_variables/bca_constants.txt`](../common/scripted_variables/bca_constants.txt)
- [`../common/script_values/bca_sv.txt`](../common/script_values/bca_sv.txt)
- [`../common/script_values/bca_planet_job.txt`](../common/script_values/bca_planet_job.txt)
- [`../common/script_values/bca_planet_job_estimation.txt`](../common/script_values/bca_planet_job_estimation.txt)

## Practical Triage Rule

If a bug report sounds like one of these, check handwritten hotspots first:

- "automation never starts"
- "mineral reserve is ignored"
- "wrong building gets demolished"
- "policy or decision toggle does nothing"
- "feature works in planner but not in gameplay"

If the bug sounds like one of these, check templates first:

- "zone selector shows the wrong candidate set"
- "default zone type is wrong"
- "generated state flags or counts are inconsistent"
- "all types of a certain generated thing are wrong in the same way"
