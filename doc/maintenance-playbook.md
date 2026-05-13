# Maintenance Playbook

See also:

- [Source Of Truth Map](source-of-truth.md)
- [Generation Pipeline](generation-pipeline.md)
- [Runtime Flow](runtime-flow.md)

## Goal

This document is written for future AI agents and contributors making changes under time pressure.

## Before You Edit Anything

1. Classify the change.
2. Identify the source of truth.
3. Check whether the behavior crosses handwritten and generated layers.

Useful starting question:

- "Am I changing runtime execution, state naming, UI selection behavior, ranking data, or automation categories?"

## Change Recipes

### Recipe: change default zone preference

Check these in order:

1. [`../mod_builder/configs/zone_type_fitness.yaml`](../mod_builder/configs/zone_type_fitness.yaml)
2. [`../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2`](../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2)
3. [`../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2)
4. [`../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2)

Why:

- ranking affects default option ordering
- selector generation and current-layout sync must agree on the same type universe

### Recipe: change district ratio or manual district plan behavior

Check:

1. [`../common/button_effects/bca_planet_setting_zones_buttons_aux.txt`](../common/button_effects/bca_planet_setting_zones_buttons_aux.txt)
2. [`../mod_builder/templates/common/scripted_effects/bca_planet_district_setting_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_planet_district_setting_effect.txt.j2)
3. [`../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2`](../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2)

### Recipe: change when construction starts

Check:

1. [`../common/scripted_triggers/bt_st_tool.txt`](../common/scripted_triggers/bt_st_tool.txt)
2. [`../events/bca_planet_monthly_iteration_entry.txt`](../events/bca_planet_monthly_iteration_entry.txt)
3. relevant files under [`../common/colony_automation_exceptions/`](../common/colony_automation_exceptions/)

### Recipe: change zone replacement or removal behavior

Check:

1. [`../mod_builder/templates/events/bca_mix_zones_controller.txt.j2`](../mod_builder/templates/events/bca_mix_zones_controller.txt.j2)
2. [`../mod_builder/templates/common/scripted_effects/bca_controller_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_controller_effect.txt.j2)
3. [`../common/colony_automation/500_bca_mixed_zones.txt`](../common/colony_automation/500_bca_mixed_zones.txt)

### Recipe: change building demolition

Start with:

- [`../common/scripted_effects/bca_building_destruction.txt`](../common/scripted_effects/bca_building_destruction.txt)

Do not start in templates unless you confirm the target building logic is actually generated elsewhere.

### Recipe: change resource-world district slot planning

Check:

1. [`../events/bca_resource_designation_district_plan.txt`](../events/bca_resource_designation_district_plan.txt)
2. [`../common/scripted_effects/bca_resource_planet_controller.txt`](../common/scripted_effects/bca_resource_planet_controller.txt)
3. [`../common/script_values/bca_planet_setting_values.txt`](../common/script_values/bca_planet_setting_values.txt)

## Common Hazards

### Hazard: editing only generated output

Risk:

- future regeneration silently discards the fix

Mitigation:

- check for a matching `.j2` template first

### Hazard: editing only the template when the same concept has handwritten siblings

Example:

- selector state is generated
- panel button effects are partly handwritten
- monthly orchestration is handwritten

Mitigation:

- search the concept name across `common/`, `events/`, and `mod_builder/templates/`

### Hazard: stale checked-in outputs after template changes

Risk:

- code review looks inconsistent
- runtime behavior and source disagree

Mitigation:

- regenerate after template/config changes

### Hazard: state sync bugs

Typical trigger points:

- on colonization
- on transfer
- on planet class change
- after building/zone/district completion

When debugging anything plan-related, inspect synchronization hooks before changing planner math.

## Suggested Debugging Order

1. Confirm the event/effect is actually reached.
2. Confirm gating triggers pass.
3. Confirm internal plan flags/variables are set as expected.
4. Confirm automation categories consume those flags.
5. Confirm cleanup does not immediately erase the state.

## Documentation Maintenance Rule

When changing behavior, also update whichever of these docs becomes stale:

- `runtime-flow.md` if execution order changes
- `source-of-truth.md` if ownership changes
- `state-model.md` if flags/variables or synchronization semantics change
- `generation-pipeline.md` if generator inputs/outputs change
