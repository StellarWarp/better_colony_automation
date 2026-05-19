# Better Colony Automation Maintainer Docs

This folder is a maintainer-oriented documentation set for AI agents and human contributors working on this mod.

The project has mixed ownership:

- Some runtime logic is handwritten directly under `common/`, `events/`, and `interface/`.
- Some runtime logic is generated from `mod_builder/templates/`.
- `mod_builder/configs/` contains handwritten configuration only.
- `mod_builder/templates/generated_configs/` is fully program-generated and must not be edited by hand.
- Some generated config data is derived from Stellaris definitions through `mod_builder/parse/` and `mod_builder/synthetipy/`.

Do not assume that a long file under `common/` or `events/` is handwritten. Many large runtime files are generated outputs.
Do not assume that YAML under `templates/generated_configs/` is editable source data. It is generated output.

Development constraints:

- Stellaris mod logic does not support hot reload; after edits, you must re-enter the game to test.
- A practical way to test logic is the event window, using dedicated test events such as [`../events/test_event.txt`](../events/test_event.txt).
- The recommended editor is IntelliJ IDEA ("IJ") because its Stellaris/Paradox syntax support is strong.
- File watcher-based rendering is recommended so template changes are regenerated quickly during development.

## Read This First

1. [Architecture Overview](architecture.md)
2. [Runtime Flow](runtime-flow.md)
3. [Source Of Truth Map](source-of-truth.md)
4. [State Model](state-model.md)
5. [Handwritten Hotspots](handwritten-hotspots.md)
6. [Generation Pipeline](generation-pipeline.md)
7. [Maintenance Playbook](maintenance-playbook.md)

## Code Entry Points

- Monthly automation entry: [`../events/bca_planet_monthly_iteration_entry.txt`](../events/bca_planet_monthly_iteration_entry.txt)
- Initialization/reset events: [`../events/bca_update_default_selection.txt`](../events/bca_update_default_selection.txt)
- District build/remove events: [`../events/bca_district_controller.txt`](../events/bca_district_controller.txt)
- Mixed zone build/remove events: [`../events/bca_mix_zones_controller.txt`](../events/bca_mix_zones_controller.txt)
- Zone selector effects: [`../common/scripted_effects/bca_planet_setting_zones_0_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_0_effect.txt)
- Designation sync and layout sync: [`../common/scripted_effects/bca_planet_setting_zones_1_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_1_effect.txt)
- District plan math: [`../common/scripted_effects/bca_planet_district_setting_effect.txt`](../common/scripted_effects/bca_planet_district_setting_effect.txt)
- Resource-world district planner: [`../common/scripted_effects/bca_resource_planet_controller.txt`](../common/scripted_effects/bca_resource_planet_controller.txt)
- Build gating triggers: [`../common/scripted_triggers/bt_st_tool.txt`](../common/scripted_triggers/bt_st_tool.txt)
- Main GUI: [`../interface/bca_district_gui.gui`](../interface/bca_district_gui.gui)
- Generator entrypoint: [`../mod_builder/generate.py`](../mod_builder/generate.py)
- Generated-config copy step: [`../mod_builder/parse/copy_configs.py`](../mod_builder/parse/copy_configs.py)
- Generated-config extraction: [`../mod_builder/parse/zone_condition_gen.py`](../mod_builder/parse/zone_condition_gen.py), [`../mod_builder/parse/building_condition.py`](../mod_builder/parse/building_condition.py)
- Paradox script parser/toolchain: [`../mod_builder/synthetipy/`](../mod_builder/synthetipy/)

## Practical Rule

Before changing behavior:

- Identify whether the target file is handwritten or generated.
- If generated, find the template and config that produced it.
- Check whether the same concept also has handwritten logic elsewhere.

The rest of this doc set is organized to make that trace easier.
