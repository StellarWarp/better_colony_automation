# Architecture Overview

See also:

- [Runtime Flow](runtime-flow.md)
- [Source Of Truth Map](source-of-truth.md)
- [Generation Pipeline](generation-pipeline.md)

## Mental Model

This mod is best understood as four layers:

1. Runtime orchestration
2. Runtime state model
3. UI/state mutation layer
4. Parse/extraction plus template generation layer

These layers are not perfectly separated. Some features are fully generated, some are fully handwritten, and some are split across both.

## 1. Runtime Orchestration

The main scheduler is the monthly country pulse:

- [`../common/on_actions/colony_automation_on_action.txt`](../common/on_actions/colony_automation_on_action.txt)
- [`../events/bca_planet_monthly_iteration_entry.txt`](../events/bca_planet_monthly_iteration_entry.txt)

For each owned planet, the mod roughly does:

1. Ensure the planet is initialized.
2. Refresh secondary defaults when needed.
3. Clear stale planning flags.
4. Recompute resource-world district plans.
5. Plan district construction.
6. Plan district demolition.
7. Plan zone construction/replacement.
8. Plan zone demolition.
9. Run building demolition logic.

## 2. Runtime State Model

Most persistent planet state is stored in:

- `planet_flag`
- `planet variable`

Important examples:

- Selected zone type per slot: `bca_pf_ps_selected_zone_type_*`
- Selected concrete zone per slot: `bca_pf_ps_selected_zone_*`
- District plan counts: `bca_ps_plan_district_count_z3/z4/z5`
- Build command flags: `bca_pf_plan_build_*`
- Initialization flag: `bca_pf_ps_initialized`

The naming scheme is largely defined in template macros:

- [`../mod_builder/templates/component/planet_flag_ps.j2`](../mod_builder/templates/component/planet_flag_ps.j2)
- [`../mod_builder/templates/component/planet_variable.j2`](../mod_builder/templates/component/planet_variable.j2)

## 3. UI And State Mutation

The GUI does not contain the business logic by itself. Instead:

- GUI widgets trigger button effects.
- Button effects mutate flags/variables or call scripted effects.
- Scripted effects implement selector updates, default selection, sync with current layout, and district math.

Key files:

- GUI layout: [`../interface/bca_district_gui.gui`](../interface/bca_district_gui.gui)
- GUI template: [`../mod_builder/templates/interface/bca_district_gui.gui.j2`](../mod_builder/templates/interface/bca_district_gui.gui.j2)
- Zone button effects: [`../common/button_effects/bca_planet_setting_zones.txt`](../common/button_effects/bca_planet_setting_zones.txt)
- Panel button effects: [`../common/button_effects/bca_planet_setting_panel.txt`](../common/button_effects/bca_planet_setting_panel.txt)
- Zone selector effects: [`../common/scripted_effects/bca_planet_setting_zones_0_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_0_effect.txt)
- Layout/designation sync: [`../common/scripted_effects/bca_planet_setting_zones_1_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_1_effect.txt)

## 4. Parse/Extraction And Template Generation

Generated runtime files are rendered by:

- [`../mod_builder/generate.py`](../mod_builder/generate.py)

Generation input comes from:

- Handwritten templates in `../mod_builder/templates/`
- Handwritten config YAML in `../mod_builder/configs/`
- Generated YAML in `../mod_builder/templates/generated_configs/`
- Parsed Stellaris definitions via `../mod_builder/parse/` and `../mod_builder/synthetipy/`

One especially important pattern:

- `zone_type_fitness.yaml` defines ranking preferences.
- `mod_builder/configs/` is the only hand-edited config source.
- `templates/generated_configs/` is generated and should never be edited directly.
- `parse/copy_configs.py` and the parser scripts populate `templates/generated_configs/`.
- Parser scripts such as `zone_condition_gen.py` derive additional YAML from Stellaris definitions.
- Templates convert the merged generated-config layer into script values and selector logic.
- Generated runtime files then use those values to pick defaults and candidate options.

See:

- [`../mod_builder/configs/zone_type_fitness.yaml`](../mod_builder/configs/zone_type_fitness.yaml)
- [`../mod_builder/parse/copy_configs.py`](../mod_builder/parse/copy_configs.py)
- [`../mod_builder/parse/zone_condition_gen.py`](../mod_builder/parse/zone_condition_gen.py)
- [`../mod_builder/synthetipy/`](../mod_builder/synthetipy/)
- [`../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2`](../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2)

## Important Consequence

This mod does not have a single authoritative location for "the automation logic".

Instead, a feature can be split like this:

- Triggering conditions in handwritten `common/scripted_triggers`
- State mutations in generated `common/scripted_effects`
- Event orchestration in generated `events`
- Automation categories/exceptions in handwritten or generated `common/colony_automation*`
- GUI entry points in generated `interface` and button effects

That is why the [Source Of Truth Map](source-of-truth.md) matters before making changes.
