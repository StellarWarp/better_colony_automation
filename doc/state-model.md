# State Model

See also:

- [Architecture Overview](architecture.md)
- [Runtime Flow](runtime-flow.md)
- [Source Of Truth Map](source-of-truth.md)

## Overview

The mod stores most planet-local intent in flags and variables rather than recomputing it from scratch each time.

Important consequence:

- Bugs often come from stale state, not just wrong trigger logic.
- Initialization, reset, and post-build cleanup are critical.

## State Categories

### 1. Planet initialization and mode flags

Examples:

- `bca_pf_ps_initialized`
- `bca_pf_planet_pre_construction`
- `bca_pf_disable_planet_auto_destruction_building`
- `bca_pf_disable_planet_auto_destruction_district`
- `bca_pf_disable_planet_auto_destruction_zone`
- `bca_pf_ps_show_detailed_secondary_districts`
- `bca_pf_can_build_extra_zones_for_storage`

Relevant files:

- [`../common/button_effects/bca_planet_setting_panel.txt`](../common/button_effects/bca_planet_setting_panel.txt)
- [`../events/bca_update_default_selection.txt`](../events/bca_update_default_selection.txt)

### 2. Selected zone plan per slot

Each visible logical slot has a selected type flag and a selected concrete zone flag.

Slots:

- Primary-facing slots: `z1`, `z2`
- Secondary slots: `z3`, `z4`, `z5`
- Aggregate/advanced secondary slot: `zx`

Generated naming rules:

- [`../mod_builder/templates/component/planet_flag_ps.j2`](../mod_builder/templates/component/planet_flag_ps.j2)

Examples:

- `bca_pf_ps_selected_zone_type_z1_trade`
- `bca_pf_ps_selected_zone_z1_zone_trade`
- `bca_pf_ps_selected_zone_type_z3_energy`

### 3. Selector state

Selector UI state is transient and also stored in flags/variables.

Examples:

- `bca_pf_ps_ext_zone_z1`
- `bca_pf_ps_zone_option_elected_s1_trade`
- `bca_pf_ps_option_map_trade_zone_trade`
- `zone_selector_options_count`

Relevant logic:

- [`../common/scripted_effects/bca_planet_setting_zones_0_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_0_effect.txt)
- [`../common/button_effects/bca_planet_setting_zones.txt`](../common/button_effects/bca_planet_setting_zones.txt)

### 4. Planned district counts

District planning is stored numerically, especially for secondary district slots:

- `bca_ps_plan_district_count_z3`
- `bca_ps_plan_district_count_z4`
- `bca_ps_plan_district_count_z5`

These are manipulated by:

- [`../common/scripted_effects/bca_planet_district_setting_effect.txt`](../common/scripted_effects/bca_planet_district_setting_effect.txt)
- [`../common/scripted_effects/bca_resource_planet_controller.txt`](../common/scripted_effects/bca_resource_planet_controller.txt)

### 5. Build command flags

These flags are the bridge from planning logic to Stellaris automation entries.

Examples:

- `bca_pf_plan_build_district_d0`
- `bca_pf_plan_build_district_d1`
- `bca_pf_plan_build_primary_zone_type_trade`
- `bca_pf_plan_build_secondary_zone_type_energy`
- `bca_plan_build_new_zone`

These are consumed by files under:

- [`../common/colony_automation/`](../common/colony_automation/)
- [`../common/colony_automation_exceptions/`](../common/colony_automation_exceptions/)

## Synchronization Effects

Several effects exist to keep internal state aligned with real planet layout.

### Designation sync

- `bca_designation_sync_with_system`
- Source: [`../common/scripted_effects/bca_planet_setting_zones_1_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_1_effect.txt)

This converts the current game designation into internal designation flags.

### Current-zone sync

- `bca_primary_zone_setting_set_by_current_zones`
- `bca_secondary_zone_setting_set_by_current_zones`

These inspect built zones and infer the mod's selected plan flags.

### Selector cleanup

- `clear_open_selector`
- `bca_clean_flags_zone_selector`
- `bca_clean_flags_zone_selector_secondary_district`

These prevent stale selector overlays and option mappings from leaking into later actions.

## Arithmetic State

The mod relies heavily on generated script values for counting and ratios.

Examples:

- `bca_num_primary_districts_plan`
- `bca_num_secondary_districts_plan`
- `num_primary_zones_of_type_*`
- `num_primary_zone_plan_of_type_*`
- `bca_planet_setting_zone_rank_*`

Generated from:

- [`../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2`](../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2)
- [`../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2`](../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2)

## Failure Patterns To Watch

### Stale selected plan flags

Symptoms:

- GUI icon does not match actual built zones.
- Wrong zone type is planned after transfer or planet class change.

First places to inspect:

- initialization/reset events
- current-zone sync effects
- completion cleanup events

### District plan and real district count drift

Symptoms:

- slider or plus/minus controls behave strangely
- zone slots appear to overcommit or undercommit secondary districts

First places to inspect:

- `bca_set_district_plan_by_ratio`
- `try_set_secondary_districts_plan_zero_to_one`
- `try_set_secondary_districts_plan_one_to_zero`

### Selector state leakage

Symptoms:

- stale option list
- selector showing invalid options after context changes

First places to inspect:

- `clear_open_selector`
- `bca_clean_flags_zone_selector`
- button effects that open or close selectors
