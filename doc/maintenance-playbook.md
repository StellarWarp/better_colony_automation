# Maintenance Playbook

See also:

- [Source Of Truth Map](source-of-truth.md)
- [Generation Pipeline](generation-pipeline.md)
- [Runtime Flow](runtime-flow.md)

## Goal

This document is written for future AI agents and contributors making changes under time pressure.

Development reality:

- Stellaris mod logic does not hot reload.
- Every logic change must be validated by re-entering the game.
- Event-window tests are the fastest feedback loop for scripted logic.
- Use IntelliJ IDEA ("IJ") if possible, and pair it with a file watcher that re-renders templates on save.

## Before You Edit Anything

1. Classify the change.
2. Identify the source of truth.
3. Check whether the behavior crosses handwritten and generated layers.

Useful starting question:

- "Am I changing runtime execution, state naming, UI selection behavior, ranking data, or automation categories?"
- "Am I looking at handwritten config in `configs/`, or generated output in `templates/generated_configs/`?"

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

### Recipe: change default auto-demolition behavior

Check:

1. [`../common/button_effects/bca_global_settings_panel.txt`](../common/button_effects/bca_global_settings_panel.txt)
2. [`../mod_builder/templates/events/bca_update_default_selection.txt.j2`](../mod_builder/templates/events/bca_update_default_selection.txt.j2)
3. [`../events/bca_auto_destruction_global_events.txt`](../events/bca_auto_destruction_global_events.txt)
4. related localisation files under [`../localisation/`](../localisation/)

Important distinction:

- the global settings panel writes country flags for default behavior
- the same panel triggers bulk country events for already-owned planets

### Recipe: change empire settings center GUI

Check:

1. [`../mod_builder/templates/component/event_gui_shell.j2`](../mod_builder/templates/component/event_gui_shell.j2)
2. [`../mod_builder/templates/component/global_settings_components.j2`](../mod_builder/templates/component/global_settings_components.j2)
3. [`../mod_builder/templates/interface/bca_global_setting_panel.gui.j2`](../mod_builder/templates/interface/bca_global_setting_panel.gui.j2)
4. [`../events/bca_global_settings_events.txt`](../events/bca_global_settings_events.txt)

Important distinction:

- the shell macro owns required hidden/displaced event-window fields
- the content macro owns visible business controls only
- do not copy shell-only fields into business GUI files
- auto-demolition now has one public entry point: the global settings panel
- GUI display text must use dedicated `BCA_GLOBAL_SETTINGS_*` localisation keys
- do not reuse `policy_*` or other legacy public-entry localisation keys inside the custom GUI
- legacy policy localisation may remain for compatibility, but custom GUI templates must not reference it

## Common Hazards

### Hazard: editing only generated output

Risk:

- future regeneration silently discards the fix

Mitigation:

- check for a matching `.j2` template first
- if the template reads from `templates/generated_configs/`, trace that YAML back to either `configs/` or `parse/`

### Hazard: editing intermediate generated-config YAML directly

Risk:

- later copy/generation steps silently overwrite the fix
- maintainers mistake generated YAML for editable source

Mitigation:

- edit `mod_builder/configs/` for handwritten config changes
- edit `mod_builder/parse/` or `mod_builder/synthetipy/` for generated-config logic changes
- never hand-edit `templates/generated_configs/`

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

### Hazard: missing generated-file warning headers

Risk:

- maintainers accidentally patch generated runtime files by hand

Mitigation:

- keep the warning-header behavior in [`../mod_builder/generate.py`](../mod_builder/generate.py)
- if the header format changes, update the renderer once instead of patching generated outputs individually

### Hazard: breaking custom event GUI shell invariants

Risk:

- event window opens blank
- close behavior breaks
- hidden vanilla event controls bleed back into view

Mitigation:

- keep hidden/displaced required event fields centralized in the shell macro
- update the shell first when event GUI structure breaks
- keep business controls isolated from shell-only compatibility fields

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
6. If generated-config values look wrong, confirm whether the problem starts in `configs/`, `parse/`, or `synthetipy/`.

## Testing Workflow

For scripted logic, prefer a dedicated test event such as [`../events/test_event.txt`](../events/test_event.txt) and trigger it manually from the in-game event window.

For template changes, rely on a file watcher to regenerate outputs before re-entering the game.

For auto-demolition changes, test both paths:

- global-settings defaults on a newly initialized or reset planet
- global-settings bulk application on already initialized planets

## Release Workflow

When preparing a public release, update these in one pass:

1. Bump the version flag in [`../events/bca_intro_event.txt`](../events/bca_intro_event.txt).
2. Update `MESSAGE_BCA_UPDATE_desc_verson` and prepend the latest `MESSAGE_BCA_STARTUP_desc_log_v*` entry in all relevant files under [`../localisation/`](../localisation/), especially [`../localisation/simp_chinese/bca_intro_l_simp_chinese.yml`](../localisation/simp_chinese/bca_intro_l_simp_chinese.yml).
3. Bump the version string in [`../descriptor.mod`](../descriptor.mod).
4. Update the public-facing changelog in [`../README.md`](../README.md).

Suggested order:

1. Finalize user-visible features and wording.
2. Update localisation changelog entries.
3. Bump the intro-event update flag and `descriptor.mod`.
4. Update `README.md`.
5. Re-enter the game and confirm the update popup shows the new version and changelog.

Release note rule:

- keep the intro popup short and player-facing
- keep `README.md` slightly more descriptive
- if a release changes global settings behavior, mention both the new default behavior and the new primary entry point

## Documentation Maintenance Rule

When changing behavior, also update whichever of these docs becomes stale:

- `runtime-flow.md` if execution order changes
- `source-of-truth.md` if ownership changes
- `state-model.md` if flags/variables or synchronization semantics change
- `generation-pipeline.md` if generator inputs/outputs change
