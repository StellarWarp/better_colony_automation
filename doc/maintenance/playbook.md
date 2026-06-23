# Maintenance Playbook

See also:

- [DSL Style Guide](dsl-style-guide.md)
- [Change Entrypoints](change-entrypoints.md)
- [Generation Pipeline](../architecture/generation-pipeline.md)
- [Runtime Flow](../architecture/runtime-flow.md)

## Goal

This document is written for future AI agents and contributors making changes under time pressure.

Development reality:

- Stellaris mod logic does not hot reload.
- Every logic change must be validated by re-entering the game.
- Event-window tests are the fastest feedback loop for scripted logic.
- Use IntelliJ IDEA if possible, and pair it with a file watcher that re-renders templates on save.

## Before You Edit Anything

1. Classify the change by layer: config/frontend, template, game logic, presentation, or documentation.
2. Check whether the file is generated. Generated warning headers are the first edit-site signal.
3. If generated, go back to the template, handwritten config, or parser/extraction tool.
4. Check whether the same behavior also has handwritten siblings.
5. If DSL syntax, scope, or API usage is uncertain, check [DSL Style Guide](dsl-style-guide.md) and the Stellaris user document `logs/script_documentation`.

Useful starting questions:

- "Am I changing runtime execution, state naming, UI behavior, ranking data, or automation categories?"
- "Am I looking at handwritten config in `configs/`, generated config in `templates/generated_configs/`, a template, or runtime output?"

## Change Recipes

### Change default zone preference

Start with:

1. [`../../mod_builder/configs/zone_type_fitness.yaml`](../../mod_builder/configs/zone_type_fitness.yaml)
2. [`../../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2`](../../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2)
3. [`../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2)
4. [`../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2)

Why:

- ranking affects default option ordering
- selector generation and current-layout sync must agree on the same type universe

### Change district ratio or manual district plan behavior

Start with:

1. [`../../common/button_effects/bca_planet_setting_zones_buttons_aux.txt`](../../common/button_effects/bca_planet_setting_zones_buttons_aux.txt)
2. [`../../mod_builder/templates/common/scripted_effects/bca_planet_district_setting_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_planet_district_setting_effect.txt.j2)
3. [`../../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2`](../../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2)

### Change when construction starts

Start with:

1. [`../../common/scripted_triggers/bt_st_tool.txt`](../../common/scripted_triggers/bt_st_tool.txt)
2. [`../../events/bca_planet_monthly_iteration_entry.txt`](../../events/bca_planet_monthly_iteration_entry.txt)
3. relevant files under [`../../common/colony_automation_exceptions/`](../../common/colony_automation_exceptions/)

### Change zone replacement or removal behavior

Start with:

1. [`../../mod_builder/templates/events/bca_mix_zones_controller.txt.j2`](../../mod_builder/templates/events/bca_mix_zones_controller.txt.j2)
2. [`../../mod_builder/templates/common/scripted_effects/bca_controller_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_controller_effect.txt.j2)
3. [`../../common/colony_automation/500_bca_mixed_zones.txt`](../../common/colony_automation/500_bca_mixed_zones.txt)

### Change building demolition

Start with:

- [`../../common/scripted_effects/bca_building_destruction.txt`](../../common/scripted_effects/bca_building_destruction.txt)

Do not start in templates unless you confirm the target building logic is generated elsewhere.

### Change default auto-demolition behavior

Start with:

1. [`../../common/button_effects/bca_global_settings_panel.txt`](../../common/button_effects/bca_global_settings_panel.txt)
2. [`../../mod_builder/templates/events/bca_update_default_selection.txt.j2`](../../mod_builder/templates/events/bca_update_default_selection.txt.j2)
3. [`../../events/bca_auto_destruction_global_events.txt`](../../events/bca_auto_destruction_global_events.txt)
4. related files under [`../../localisation/`](../../localisation/)

Important distinction:

- the global settings panel writes country flags for default behavior
- the same panel triggers bulk country-level application flows for
  already-owned colonies, which then fan out into per-colony `carrier_event`
  work

### Change empire settings center GUI

Start with:

1. [`../../mod_builder/templates/component/event_gui_shell.j2`](../../mod_builder/templates/component/event_gui_shell.j2)
2. [`../../mod_builder/templates/component/global_settings_components.j2`](../../mod_builder/templates/component/global_settings_components.j2)
3. [`../../mod_builder/templates/interface/bca_global_setting_panel.gui.j2`](../../mod_builder/templates/interface/bca_global_setting_panel.gui.j2)
4. [`../../events/bca_global_settings_events.txt`](../../events/bca_global_settings_events.txt)

Rules:

- shell macro owns required hidden/displaced event-window fields
- content macro owns visible business controls
- auto-demolition now has one public entry point: the global settings panel
- GUI display text must use `BCA_GLOBAL_SETTINGS_*` localisation keys
- custom GUI must not reuse legacy `policy_*` public-entry text

## Common Hazards

### Editing generated output only

Risk:

- future regeneration silently discards the fix

Mitigation:

- read the generated warning header
- find the matching template or generator input
- update the source layer, then regenerate

### Editing generated-config YAML directly

Risk:

- later copy/generation steps overwrite the change

Mitigation:

- edit `mod_builder/configs/` for handwritten config changes
- edit `mod_builder/parse/` or `mod_builder/synthetipy/` for extracted config logic
- never hand-edit `mod_builder/templates/generated_configs/`

### Breaking custom event GUI shell invariants

Risk:

- event window opens blank
- close behavior breaks
- hidden vanilla event controls bleed into view

Mitigation:

- keep hidden/displaced required event fields centralized in `event_gui_shell.j2`
- update shell first when event GUI structure breaks
- keep business controls isolated from shell-only compatibility fields

### State sync bugs

Typical trigger points:

- colonization
- planet transfer
- planet class change
- building/zone/district completion

When debugging plan-related behavior, inspect synchronization hooks before changing planner math.

## Suggested Debugging Order

1. Confirm the event/effect is reached.
2. Confirm gating triggers pass.
3. Confirm internal plan flags/variables are set as expected.
4. Confirm automation categories consume those flags.
5. Confirm cleanup does not immediately erase state.
6. If generated-config values look wrong, confirm whether the issue starts in `configs/`, `parse/`, or `synthetipy/`.

## Testing Workflow

For scripted logic, prefer a dedicated test event such as [`../../events/test_event.txt`](../../events/test_event.txt) and trigger it manually from the in-game event window.

For template changes, rely on a file watcher to regenerate outputs before re-entering the game.

For auto-demolition changes, test both paths:

- global-settings defaults on a newly initialized or reset planet
- global-settings bulk application on already initialized planets

## Release Workflow

When preparing a public release, update these in one pass:

1. Bump the version flag in [`../../events/bca_intro_event.txt`](../../events/bca_intro_event.txt).
2. Update `MESSAGE_BCA_UPDATE_desc_verson` and prepend the latest `MESSAGE_BCA_STARTUP_desc_log_v*` entry in relevant files under [`../../localisation/`](../../localisation/).
3. Bump the version string in [`../../descriptor.mod`](../../descriptor.mod).
4. Update the public-facing changelog in [`../../README.md`](../../README.md).
5. Update and review the bilingual Workshop descriptions in [`../../workshop_en.txt`](../../workshop_en.txt) and [`../../workshop_cn.txt`](../../workshop_cn.txt), especially the supported game version, Quick Guide entrypoints, compatibility notes, and recent feature summary.

Release note rule:

- keep the intro popup short and player-facing
- keep `README.md` slightly more descriptive
- keep `workshop_en.txt` and `workshop_cn.txt` focused on current features rather than detailed version history
- if a release changes global settings behavior, mention both the new default behavior and the primary entry point

## Documentation Maintenance Rule

When changing behavior, update whichever docs become stale:

- runtime order changes -> [`../architecture/runtime-flow.md`](../architecture/runtime-flow.md)
- state semantics changes -> [`../architecture/state-model.md`](../architecture/state-model.md)
- generator inputs/outputs change -> [`../architecture/generation-pipeline.md`](../architecture/generation-pipeline.md)
- DSL or Jinja conventions change -> [`dsl-style-guide.md`](dsl-style-guide.md)
- common change entrypoints change -> [`change-entrypoints.md`](change-entrypoints.md)
