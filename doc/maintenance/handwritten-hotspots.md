# Handwritten Hotspots

See also:

- [Maintenance Playbook](playbook.md)
- [Change Entrypoints](change-entrypoints.md)

## Why This File Exists

Future maintainers can over-focus on `mod_builder/templates/` and miss handwritten files that still shape core runtime behavior.

These are the most important handwritten hotspots.

## Monthly scheduler

- [`../../events/bca_planet_monthly_iteration_entry.txt`](../../events/bca_planet_monthly_iteration_entry.txt)

Why it matters:

- defines monthly execution order
- determines which planning stages run and in which sequence
- changes here can invalidate assumptions in generated planners

## Generic gating triggers

- [`../../common/scripted_triggers/bt_st_tool.txt`](../../common/scripted_triggers/bt_st_tool.txt)

Why it matters:

- `requires_more_job` controls when planning starts
- `bca_has_minerals_to_build` enforces reserve settings
- these handwritten triggers are depended on almost everywhere else

## Building demolition

- [`../../mod_builder/configs/manual_building_destruction.yaml`](../../mod_builder/configs/manual_building_destruction.yaml)

Why it matters:

- this is the handwritten demolition input for buildings whose construction
  remains in a special automation category
- normal building demolition belongs beside construction config under
  `mod_builder/configs/buildings/`
- the runtime demolition effect is generated; do not patch its building list
  directly

## Panel-level settings and UI mode toggles

- [`../../common/button_effects/bca_planet_setting_panel.txt`](../../common/button_effects/bca_planet_setting_panel.txt)
- [`../../common/button_effects/bca_global_settings_panel.txt`](../../common/button_effects/bca_global_settings_panel.txt)

Why it matters:

- these files own many non-generated toggles and global settings actions
- they bridge GUI buttons to state changes
- they often work beside generated selector logic rather than replacing it

## On-actions

- [`../../common/on_actions/colony_automation_on_action.txt`](../../common/on_actions/colony_automation_on_action.txt)
- [`../../common/on_actions/01_bca_intro_on_action.txt`](../../common/on_actions/01_bca_intro_on_action.txt)

Why it matters:

- these decide when runtime enters the automation system
- inspect them when a feature never triggers

## Intro/update/runtime message events

- [`../../events/bca_intro_event.txt`](../../events/bca_intro_event.txt)
- [`../../events/bca_update_event.txt`](../../events/bca_update_event.txt)
- [`../../events/bac_colony_transform_events.txt`](../../events/bac_colony_transform_events.txt)

Why it matters:

- some user-facing behavior and initialization-like flows live here
- release metadata changes must update these alongside localisation and `descriptor.mod`

## Decisions, edicts, and global settings entrypoints

- [`../../common/decisions/`](../../common/decisions/)
- [`../../common/policies/bac_policies.txt`](../../common/policies/bac_policies.txt)
- [`../../common/edicts/bca_global_settings_panel.txt`](../../common/edicts/bca_global_settings_panel.txt)

Why it matters:

- these files define user-facing control points
- `bac_policies.txt` is now a tombstone documenting that public policy entrypoints were intentionally removed

## Handwritten automation exceptions

Many files under [`../../common/colony_automation_exceptions/`](../../common/colony_automation_exceptions/) are handwritten even though some large files there are generated.

Examples:

- [`../../common/colony_automation_exceptions/03_bca_building_rare_resources.txt`](../../common/colony_automation_exceptions/03_bca_building_rare_resources.txt)
- [`../../common/colony_automation_exceptions/02_bca_building_medical.txt`](../../common/colony_automation_exceptions/02_bca_building_medical.txt)
- [`../../common/colony_automation_exceptions/31_bca_capital.txt`](../../common/colony_automation_exceptions/31_bca_capital.txt)
- [`../../common/colony_automation_exceptions/19_bca_district_housing.txt`](../../common/colony_automation_exceptions/19_bca_district_housing.txt)

General designation building rules are generated in
[`../../common/colony_automation_exceptions/31_bca_designation_buildings.txt`](../../common/colony_automation_exceptions/31_bca_designation_buildings.txt).

Why it matters:

- these implement actual building choices
- a bug in "what gets built" may be in either a retained handwritten exception
  or the building strategy source/template
- special construction should stay here when it depends on scenario-specific
  state that is not represented by a shared strategy

## Runtime constants and helper files

Check these when a planner seems numerically wrong:

- [`../../common/scripted_variables/bca_constants.txt`](../../common/scripted_variables/bca_constants.txt)
- [`../../common/script_values/bca_sv.txt`](../../common/script_values/bca_sv.txt)
- [`../../common/script_values/bca_planet_job.txt`](../../common/script_values/bca_planet_job.txt)
- [`../../common/script_values/bca_planet_job_estimation.txt`](../../common/script_values/bca_planet_job_estimation.txt)

## Practical Triage Rule

Check handwritten hotspots first when the report sounds like:

- "automation never starts"
- "mineral reserve is ignored"
- "wrong building gets demolished"
- "global settings toggle does nothing"
- "feature works in planner but not in gameplay"

Check templates first when the report sounds like:

- "zone selector shows the wrong candidate set"
- "default zone type is wrong"
- "generated state flags or counts are inconsistent"
- "all types of a generated thing are wrong in the same way"
