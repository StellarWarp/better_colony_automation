# Change Entrypoints

See also:

- [Maintenance Playbook](playbook.md)
- [Handwritten Hotspots](handwritten-hotspots.md)
- [Generation Pipeline](../architecture/generation-pipeline.md)

## Why This File Exists

Generated warning headers answer "can I edit this file directly?"

This file answers the next question: "If not here, where should I start?"

It is an entrypoint index, not a complete source-of-truth map. Prefer warning headers, directory ownership, and the maintenance playbook when deciding how to edit.

## Rule Of Thumb

- If a runtime file has a generated warning header, follow it back to the template.
- If a template reads from `templates/generated_configs/`, trace the data to `configs/`, `parse/`, or `synthetipy/`.
- If there is no generated warning header and no matching template, treat the runtime file as handwritten until proven otherwise.
- If a change touches GUI, also check button effects, events, scripted loc, and localisation.
- If a change touches public-facing text, update all required localisation files.

## Entrypoints By Concern

### Monthly orchestration

- Runtime file: [`../../events/bca_planet_monthly_iteration_entry.txt`](../../events/bca_planet_monthly_iteration_entry.txt)
- Ownership: handwritten runtime

### Initialization and reset

- Runtime file: [`../../events/bca_update_default_selection.txt`](../../events/bca_update_default_selection.txt)
- Template: [`../../mod_builder/templates/events/bca_update_default_selection.txt.j2`](../../mod_builder/templates/events/bca_update_default_selection.txt.j2)

### District construction/removal

- Runtime file: [`../../events/bca_district_controller.txt`](../../events/bca_district_controller.txt)
- Template: [`../../mod_builder/templates/events/bca_district_controller.txt.j2`](../../mod_builder/templates/events/bca_district_controller.txt.j2)

### Mixed zone construction/removal

- Runtime file: [`../../events/bca_mix_zones_controller.txt`](../../events/bca_mix_zones_controller.txt)
- Template: [`../../mod_builder/templates/events/bca_mix_zones_controller.txt.j2`](../../mod_builder/templates/events/bca_mix_zones_controller.txt.j2)

### Zone selector effect system

- Runtime file: [`../../common/scripted_effects/bca_planet_setting_zones_0_effect.txt`](../../common/scripted_effects/bca_planet_setting_zones_0_effect.txt)
- Template: [`../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2)

### Designation and current-layout sync

- Runtime file: [`../../common/scripted_effects/bca_planet_setting_zones_1_effect.txt`](../../common/scripted_effects/bca_planet_setting_zones_1_effect.txt)
- Template: [`../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2)

### Zone ranking values

- Runtime file: [`../../common/script_values/bca_planet_setting_zone_ranking.txt`](../../common/script_values/bca_planet_setting_zone_ranking.txt)
- Template: [`../../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2`](../../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2)
- Data source: [`../../mod_builder/configs/zone_type_fitness.yaml`](../../mod_builder/configs/zone_type_fitness.yaml)

### Generated config copy and extraction

- Generated config directory: [`../../mod_builder/templates/generated_configs/`](../../mod_builder/templates/generated_configs/)
- Handwritten source config: [`../../mod_builder/configs/`](../../mod_builder/configs/)
- Unified parse entrypoint: [`../../mod_builder/parse/build_generated_configs.py`](../../mod_builder/parse/build_generated_configs.py)
- Compatibility wrapper: [`../../mod_builder/parse/copy_configs.py`](../../mod_builder/parse/copy_configs.py)
- Extraction scripts: [`../../mod_builder/parse/zone_condition_gen.py`](../../mod_builder/parse/zone_condition_gen.py), [`../../mod_builder/parse/building_condition.py`](../../mod_builder/parse/building_condition.py)
- Building strategy compiler: [`../../mod_builder/parse/building_strategy_compile.py`](../../mod_builder/parse/building_strategy_compile.py)
- Parser/toolchain: [`../../mod_builder/synthetipy/`](../../mod_builder/synthetipy/)

### Local Mod publication

- Publisher: [`../../scripts/publish_mod.py`](../../scripts/publish_mod.py)
- Target/package config: [`../../scripts/publish_mod.yaml`](../../scripts/publish_mod.yaml)
- Job-regulation descriptor and Workshop assets:
  [`../../submods/job_regulation/`](../../submods/job_regulation/)
- Template metadata implementation:
  [`../../mod_builder/generate.py`](../../mod_builder/generate.py)

Use template first-line metadata to change package ownership. Generated output
markers must not be edited directly.

### Building construction strategies

- Normal source config: [`../../mod_builder/configs/buildings/`](../../mod_builder/configs/buildings/)
- Designation template: [`../../mod_builder/templates/common/colony_automation_exceptions/31_bca_designation_buildings.txt.j2`](../../mod_builder/templates/common/colony_automation_exceptions/31_bca_designation_buildings.txt.j2)
- Zone template: [`../../mod_builder/templates/common/colony_automation_exceptions/500_bca_mixd_zones_building.txt.j2`](../../mod_builder/templates/common/colony_automation_exceptions/500_bca_mixd_zones_building.txt.j2)
- Architecture: [Building Automation Pipeline](../architecture/building-automation-pipeline.md)

Parsed building sets and zone mappings validate physical compatibility. They
do not by themselves define automation demand contexts.

### Trigger helpers

- Runtime file: [`../../common/scripted_triggers/bt_st_tool.txt`](../../common/scripted_triggers/bt_st_tool.txt)
- Ownership: handwritten runtime

### Resource-world district planner

- Runtime file: [`../../common/scripted_effects/bca_resource_planet_controller.txt`](../../common/scripted_effects/bca_resource_planet_controller.txt)
- Template: [`../../mod_builder/templates/common/scripted_effects/bca_resource_planet_controller.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_resource_planet_controller.txt.j2)

### Zone build automation categories

- Runtime file: [`../../common/colony_automation/500_bca_mixed_zones.txt`](../../common/colony_automation/500_bca_mixed_zones.txt)
- Template: [`../../mod_builder/templates/common/colony_automation/500_bca_mixed_zones.txt.j2`](../../mod_builder/templates/common/colony_automation/500_bca_mixed_zones.txt.j2)

### District automation categories

- Runtime file: [`../../common/colony_automation_exceptions/500_bca_districts.txt`](../../common/colony_automation_exceptions/500_bca_districts.txt)
- Template: [`../../mod_builder/templates/common/colony_automation_exceptions/500_bca_districts.txt.j2`](../../mod_builder/templates/common/colony_automation_exceptions/500_bca_districts.txt.j2)

### Economic district build gate

- Runtime file: [`../../common/scripted_effects/bca_district_build_effects.txt`](../../common/scripted_effects/bca_district_build_effects.txt)
- Template: [`../../mod_builder/templates/common/scripted_effects/bca_district_build_effects.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_district_build_effects.txt.j2)
- Parser: [`../../mod_builder/parse/economic_outputs.py`](../../mod_builder/parse/economic_outputs.py)
- Whitelist config: [`../../mod_builder/configs/district_direct_outputs.yaml`](../../mod_builder/configs/district_direct_outputs.yaml)
- Generated configs:
  [`../../mod_builder/templates/generated_configs/economic_district_slot_groups.yaml`](../../mod_builder/templates/generated_configs/economic_district_slot_groups.yaml),
  [`../../mod_builder/templates/generated_configs/economic_district_slot_direct_groups.yaml`](../../mod_builder/templates/generated_configs/economic_district_slot_direct_groups.yaml),
  [`../../mod_builder/templates/generated_configs/economic_district_slot_conditions.yaml`](../../mod_builder/templates/generated_configs/economic_district_slot_conditions.yaml)

### GUI

- Planet panel runtime GUI: [`../../interface/bca_district_gui.gui`](../../interface/bca_district_gui.gui)
- Planet panel template: [`../../mod_builder/templates/interface/bca_district_gui.gui.j2`](../../mod_builder/templates/interface/bca_district_gui.gui.j2)
- Global settings runtime GUI: [`../../interface/bca_global_setting_panel.gui`](../../interface/bca_global_setting_panel.gui)
- Global settings template: [`../../mod_builder/templates/interface/bca_global_setting_panel.gui.j2`](../../mod_builder/templates/interface/bca_global_setting_panel.gui.j2)
- Event GUI shell: [`../../mod_builder/templates/component/event_gui_shell.j2`](../../mod_builder/templates/component/event_gui_shell.j2)
- Global settings components: [`../../mod_builder/templates/component/global_settings_components.j2`](../../mod_builder/templates/component/global_settings_components.j2)

### Global settings behavior

- Event entrypoint: [`../../events/bca_global_settings_events.txt`](../../events/bca_global_settings_events.txt)
- Button effects: [`../../common/button_effects/bca_global_settings_panel.txt`](../../common/button_effects/bca_global_settings_panel.txt)
- Startup defaults: [`../../events/bca_global_settings_bootstrap.txt`](../../events/bca_global_settings_bootstrap.txt)
- Panel edict entry: [`../../common/edicts/bca_global_settings_panel.txt`](../../common/edicts/bca_global_settings_panel.txt)

### Building demolition logic

- Runtime file: [`../../common/scripted_effects/bca_building_destruction.txt`](../../common/scripted_effects/bca_building_destruction.txt)
- Template: [`../../mod_builder/templates/common/scripted_effects/bca_building_destruction.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_building_destruction.txt.j2)
- Normal source: demolition declarations under [`../../mod_builder/configs/buildings/`](../../mod_builder/configs/buildings/)
- Special source: [`../../mod_builder/configs/manual_building_destruction.yaml`](../../mod_builder/configs/manual_building_destruction.yaml)

### Stellaris API reference

- Primary syntax definitions: [`.config/stellaris/`](../../.config/stellaris/)
  (effects, triggers, scopes, modifiers, enums — `.cwt` rule files)
- Secondary reference: Stellaris user document
  `logs/script_documentation` (see DSL Style Guide for location)

Consult `.config/stellaris/` first when a game update renames or removes
script APIs. The `.cwt` files are the authoritative API surface for the
targeted game version.

### Intro/update messages and release metadata

- Runtime files: [`../../events/bca_intro_event.txt`](../../events/bca_intro_event.txt), [`../../events/bca_update_event.txt`](../../events/bca_update_event.txt)
- Localisation: [`../../localisation/`](../../localisation/)
- Mod descriptor: [`../../descriptor.mod`](../../descriptor.mod)
- Public changelog: [`../../README.md`](../../README.md)
- Main Workshop descriptions: [`../../workshop_en.txt`](../../workshop_en.txt), [`../../workshop_cn.txt`](../../workshop_cn.txt)
- Submod Workshop assets: [`../../submods/`](../../submods/)

## Mixed Cases

Changing a default zone choice usually touches ranking config, generated config, selector templates, and current-layout sync.

Changing when construction happens usually touches gating triggers, monthly orchestration, and building exception files.

Changing demolition behavior can mean zone demolition, district demolition,
building demolition, default country settings, carrier flags, or global bulk
actions. Do not assume these share one implementation path.
