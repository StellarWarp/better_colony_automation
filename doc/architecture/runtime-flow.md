# Runtime Flow

See also:

- [Architecture Overview](overview.md)
- [State Model](state-model.md)
- [Maintenance Playbook](../maintenance/playbook.md)

## Startup And Load

Startup and save-load hooks are declared in:

- [`../../common/on_actions/01_bca_intro_on_action.txt`](../../common/on_actions/01_bca_intro_on_action.txt)

They trigger:

- intro/update messages in [`../../events/bca_intro_event.txt`](../../events/bca_intro_event.txt)
- update/load handling in [`../../events/bca_update_event.txt`](../../events/bca_update_event.txt)
- global settings defaults in [`../../events/bca_global_settings_bootstrap.txt`](../../events/bca_global_settings_bootstrap.txt)
- planet initialization sweeps in [`../../events/bca_update_default_selection.txt`](../../events/bca_update_default_selection.txt)

Important initialization events:

- `colony_automation_event.25`: global initialization sweep
- `colony_automation_event.26`: initialize from current layout
- `colony_automation_event.27`: reset to default
- `colony_automation_event.28`: refresh secondary defaults

## Monthly Automation Loop

Main entry:

- [`../../events/bca_planet_monthly_iteration_entry.txt`](../../events/bca_planet_monthly_iteration_entry.txt)

The country event `colony_automation_event.1000` runs on `on_monthly_pulse_country`.

For each eligible owned planet:

1. Initialize if missing `bca_pf_ps_initialized`.
2. Patch secondary defaults.
3. Clear stale plan flags.
4. Recompute resource-world district plans.
5. Plan district construction.
6. Plan district demolition.
7. Plan zone construction/replacement.
8. Plan zone demolition.
9. Run building demolition.

## Gating Conditions

The most important generic gates are in:

- [`../../common/scripted_triggers/bt_st_tool.txt`](../../common/scripted_triggers/bt_st_tool.txt)

Key gates:

- `requires_more_job`
- `really_requires_more_job`
- `bca_has_minerals_to_build`

Operationally:

- district and zone planning often require `requires_more_job = yes`
- construction checks resource reserve settings through `bca_has_minerals_to_build`
- preconstruction bypasses the normal free-job threshold by setting `bca_pf_planet_pre_construction`

## Initialization And Layout Sync

Initialization is not only default setup. It also synchronizes current game state into internal flags.

Core file:

- [`../../events/bca_update_default_selection.txt`](../../events/bca_update_default_selection.txt)

Key effects:

- `bca_designation_sync_with_system`
- `bca_primary_zone_setting_set_by_current_zones`
- `bca_secondary_zone_setting_set_by_current_zones`

These are defined in:

- [`../../common/scripted_effects/bca_planet_setting_zones_1_effect.txt`](../../common/scripted_effects/bca_planet_setting_zones_1_effect.txt)

## Resource-World District Planning

Resource designations use a dedicated district planning effect:

- Event trigger: [`../../events/bca_resource_designation_district_plan.txt`](../../events/bca_resource_designation_district_plan.txt)
- Planner logic: [`../../common/scripted_effects/bca_resource_planet_controller.txt`](../../common/scripted_effects/bca_resource_planet_controller.txt)

This logic sets `bca_ps_plan_district_count_z3/z4/z5` based on designation, auto district management, selected secondary zone types, storage/arcology flags, and special cases.

## District Build/Remove Flow

Main event file:

- [`../../events/bca_district_controller.txt`](../../events/bca_district_controller.txt)

This layer translates plan counts into build/remove flags such as:

- `bca_pf_plan_build_district_d0`
- `bca_pf_plan_build_district_d1`
- `bca_pf_plan_build_district_d2`
- `bca_pf_plan_build_district_d3`

The automation categories that consume these flags are under:

- [`../../common/colony_automation_exceptions/`](../../common/colony_automation_exceptions/)

## Zone Build/Replace/Remove Flow

Main event file:

- [`../../events/bca_mix_zones_controller.txt`](../../events/bca_mix_zones_controller.txt)

This layer compares real zone counts with planned counts, emits build flags, and removes obsolete zones when zone auto-demolition is allowed.

The actual zone automation entries are under:

- [`../../common/colony_automation/`](../../common/colony_automation/)

## Building Demolition

Building demolition is driven by:

- [`../../common/scripted_effects/bca_building_destruction.txt`](../../common/scripted_effects/bca_building_destruction.txt)

This is a large handwritten ruleset. Building demolition bugs often start here, not in generated zone events.

## Direct Planet Hooks

Additional synchronization entry points:

- Colonized / transfer: [`../../common/on_actions/colony_automation_on_action.txt`](../../common/on_actions/colony_automation_on_action.txt)
- Planet class changed: [`../../events/bca_on_pc_change_events.txt`](../../events/bca_on_pc_change_events.txt)
- Build completion cleanup: `colony_automation_event.11`, `.12`, `.13`
