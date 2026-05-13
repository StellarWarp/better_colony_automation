# Runtime Flow

See also:

- [Architecture Overview](architecture.md)
- [State Model](state-model.md)
- [Maintenance Playbook](maintenance-playbook.md)

## Startup And Load

Startup and save-load hooks are declared in:

- [`../common/on_actions/01_bca_intro_on_action.txt`](../common/on_actions/01_bca_intro_on_action.txt)

They trigger:

- Intro/update messages: [`../events/bca_intro_event.txt`](../events/bca_intro_event.txt), [`../events/bca_update_event.txt`](../events/bca_update_event.txt)
- Planet initialization sweep: [`../events/bca_update_default_selection.txt`](../events/bca_update_default_selection.txt)

Important initialization events:

- `colony_automation_event.25`: global initialization sweep
- `colony_automation_event.26`: initialize from current layout
- `colony_automation_event.27`: reset to default
- `colony_automation_event.28`: refresh secondary defaults

## Monthly Automation Loop

Main entry:

- [`../events/bca_planet_monthly_iteration_entry.txt`](../events/bca_planet_monthly_iteration_entry.txt)

The country event `colony_automation_event.1000` runs on `on_monthly_pulse_country`.

### Planet loop sequence

For each eligible owned planet:

1. Initialize if missing `bca_pf_ps_initialized`.
2. Run `colony_automation_event.28` to patch secondary defaults.
3. Run `colony_automation_event.112` to clear plan flags.
4. Run `colony_automation_event.10` for resource designation district planning.
5. Run `colony_automation_event.1` for district construction planning.
6. Run `colony_automation_event.2` for district demolition planning.
7. Run `colony_automation_event.20` for zone construction/replacement planning.
8. Run `colony_automation_event.21` for zone demolition.
9. Run `bca_auto_building_destruction_entry` for building demolition.

## Gating Conditions

The most important generic gates are in:

- [`../common/scripted_triggers/bt_st_tool.txt`](../common/scripted_triggers/bt_st_tool.txt)

Key gates:

- `requires_more_job`
- `really_requires_more_job`
- `bca_has_minerals_to_build`

Operationally:

- District and zone planning often require `requires_more_job = yes`.
- Construction also checks mineral reserve policies through `bca_has_minerals_to_build`.
- Pre-construction bypasses the normal free-job threshold because `requires_more_job` returns true when `bca_pf_planet_pre_construction` is set.

## Initialization And Layout Sync

Initialization is not only "set defaults". It also synchronizes current game state back into the mod's internal flags.

Core file:

- [`../events/bca_update_default_selection.txt`](../events/bca_update_default_selection.txt)

Key effects called from it:

- `bca_designation_sync_with_system`
- `bca_primary_zone_setting_set_by_current_zones`
- `bca_secondary_zone_setting_set_by_current_zones`

Those effects are defined in:

- [`../common/scripted_effects/bca_planet_setting_zones_1_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_1_effect.txt)

## Resource-World District Planning

Resource designations use a dedicated district planning effect:

- Event trigger: [`../events/bca_resource_designation_district_plan.txt`](../events/bca_resource_designation_district_plan.txt)
- Planner logic: [`../common/scripted_effects/bca_resource_planet_controller.txt`](../common/scripted_effects/bca_resource_planet_controller.txt)

This logic sets `bca_ps_plan_district_count_z3/z4/z5` based on:

- designation
- auto district management toggle
- selected secondary zone types
- storage/arcology preparation flags
- special cases such as Betharian energy districts

## District Build/Remove Flow

Main event file:

- [`../events/bca_district_controller.txt`](../events/bca_district_controller.txt)

This layer translates plan counts into build/remove flags such as:

- `bca_pf_plan_build_district_d0`
- `bca_pf_plan_build_district_d1`
- `bca_pf_plan_build_district_d2`
- `bca_pf_plan_build_district_d3`

The automation categories that actually consume these flags are under:

- [`../common/colony_automation_exceptions/500_bca_districts.txt`](../common/colony_automation_exceptions/500_bca_districts.txt)

## Zone Build/Replace/Remove Flow

Main event file:

- [`../events/bca_mix_zones_controller.txt`](../events/bca_mix_zones_controller.txt)

This layer:

- compares actual zone counts vs planned zone counts
- decides whether replacement is required
- emits `bca_pf_plan_build_primary_zone_type_*` and `bca_pf_plan_build_secondary_zone_type_*`
- sets `bca_plan_build_new_zone`
- removes obsolete zones if zone auto-destruction is allowed

The actual zone automation entries are under:

- [`../common/colony_automation/500_bca_mixed_zones.txt`](../common/colony_automation/500_bca_mixed_zones.txt)

## Building Demolition

Building demolition is not handled in the zone events.

It is driven by:

- [`../common/scripted_effects/bca_building_destruction.txt`](../common/scripted_effects/bca_building_destruction.txt)

This file contains a large amount of handwritten, concrete building-category replacement/removal logic.

## Direct Planet Hooks

Additional synchronization entry points:

- Colonized / transfer: [`../common/on_actions/colony_automation_on_action.txt`](../common/on_actions/colony_automation_on_action.txt)
- Planet class changed: [`../events/bca_on_pc_change_events.txt`](../events/bca_on_pc_change_events.txt)
- Build completion cleanup: `colony_automation_event.11`, `.12`, `.13`

These reduce stale state after layout changes or completed construction.
