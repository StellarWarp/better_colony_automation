# State Model

See also:

- [Architecture Overview](overview.md)
- [Runtime Flow](runtime-flow.md)
- [DSL Style Guide](../maintenance/dsl-style-guide.md)

## Overview

The mod stores most planet-local intent in flags and variables instead of recomputing everything from scratch each tick.

Important consequence:

- bugs often come from stale state, not only wrong trigger logic
- initialization, reset, transfer, planet class changes, and post-build cleanup are critical

## State Categories

### Planet initialization and mode flags

Examples:

- `bca_pf_ps_initialized`
- `bca_pf_planet_pre_construction`
- `bca_pf_disable_planet_auto_destruction_building`
- `bca_pf_disable_planet_auto_destruction_district`
- `bca_pf_disable_planet_auto_destruction_zone`
- `bca_pf_ps_show_detailed_secondary_districts`
- `bca_pf_can_build_extra_zones_for_storage`

Relevant files:

- [`../../common/button_effects/bca_planet_setting_panel.txt`](../../common/button_effects/bca_planet_setting_panel.txt)
- [`../../events/bca_update_default_selection.txt`](../../events/bca_update_default_selection.txt)

### Selected zone plan per slot

Each visible logical slot has a selected type flag and a selected concrete zone flag.

Slots:

- Primary-facing slots: `z1`, `z2`
- Secondary slots: `z3`, `z4`, `z5`
- Aggregate/advanced secondary slot: `zx`

Generated naming rules:

- [`../../mod_builder/templates/component/planet_flag_ps.j2`](../../mod_builder/templates/component/planet_flag_ps.j2)

### Selector state

Selector UI state is transient and stored in flags/variables.

Examples:

- `bca_pf_ps_ext_zone_z1`
- `bca_pf_ps_zone_option_elected_s1_trade`
- `bca_pf_ps_option_map_trade_zone_trade`
- `zone_selector_options_count`

Relevant logic:

- [`../../common/scripted_effects/bca_planet_setting_zones_0_effect.txt`](../../common/scripted_effects/bca_planet_setting_zones_0_effect.txt)
- [`../../common/button_effects/bca_planet_setting_zones.txt`](../../common/button_effects/bca_planet_setting_zones.txt)

### Planned district counts

District planning is stored numerically, especially for secondary district slots:

- `bca_ps_plan_district_count_z3`
- `bca_ps_plan_district_count_z4`
- `bca_ps_plan_district_count_z5`

These are manipulated by:

- [`../../common/scripted_effects/bca_planet_district_setting_effect.txt`](../../common/scripted_effects/bca_planet_district_setting_effect.txt)
- [`../../common/scripted_effects/bca_resource_planet_controller.txt`](../../common/scripted_effects/bca_resource_planet_controller.txt)

### Build command flags

These flags bridge planning logic to Stellaris automation entries.

Examples:

- `bca_pf_plan_build_district_d0`
- `bca_pf_plan_build_primary_zone_type_trade`
- `bca_pf_plan_build_secondary_zone_type_energy`
- `bca_plan_build_new_zone`

These are consumed by files under:

- [`../../common/colony_automation/`](../../common/colony_automation/)
- [`../../common/colony_automation_exceptions/`](../../common/colony_automation_exceptions/)

### Country-level global settings

The global settings panel stores defaults and thresholds in country flags/variables.

Examples:

- `bca_default_disable_auto_destruction_building`
- `bca_default_disable_auto_destruction_district`
- `bca_default_disable_auto_destruction_zone`
- `bca_reserve_minerals_amount`
- `bca_reserve_alloys_amount`
- `bca_reserve_influence_amount`
- `bca_reserve_job_amount`
- `bca_expect_output_rare_crystals`

Default values are initialized by:

- [`../../events/bca_global_settings_bootstrap.txt`](../../events/bca_global_settings_bootstrap.txt)

## Synchronization Effects

Several effects keep internal state aligned with real planet layout.

Important examples:

- `bca_designation_sync_with_system`
- `bca_primary_zone_setting_set_by_current_zones`
- `bca_secondary_zone_setting_set_by_current_zones`
- `clear_open_selector`
- `bca_clean_flags_zone_selector`

First inspect synchronization before changing planner math.

## Arithmetic State

The mod relies heavily on generated script values for counting and ratios.

Examples:

- `bca_num_primary_districts_plan`
- `bca_num_secondary_districts_plan`
- `num_primary_zones_of_type_*`
- `num_primary_zone_plan_of_type_*`
- `bca_planet_setting_zone_rank_*`

Generated from:

- [`../../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2`](../../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2)
- [`../../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2`](../../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2)

## Failure Patterns

Stale selected plan flags:

- GUI icon does not match actual built zones.
- Wrong zone type is planned after transfer or planet class change.

District plan drift:

- slider or plus/minus controls behave strangely
- secondary district slots overcommit or undercommit

Selector state leakage:

- stale option list
- invalid selector options after context changes

For these bugs, inspect initialization/reset events, current-layout sync effects, and cleanup events before changing ranking or build logic.
