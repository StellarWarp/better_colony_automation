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
- Copy entrypoint: [`../../mod_builder/parse/copy_configs.py`](../../mod_builder/parse/copy_configs.py)
- Extraction scripts: [`../../mod_builder/parse/zone_condition_gen.py`](../../mod_builder/parse/zone_condition_gen.py), [`../../mod_builder/parse/building_condition.py`](../../mod_builder/parse/building_condition.py)
- Parser/toolchain: [`../../mod_builder/synthetipy/`](../../mod_builder/synthetipy/)

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
- Ownership: handwritten runtime

### Intro/update messages and release metadata

- Runtime files: [`../../events/bca_intro_event.txt`](../../events/bca_intro_event.txt), [`../../events/bca_update_event.txt`](../../events/bca_update_event.txt)
- Localisation: [`../../localisation/`](../../localisation/)
- Mod descriptor: [`../../descriptor.mod`](../../descriptor.mod)
- Public changelog: [`../../README.md`](../../README.md)

## Mixed Cases

Changing a default zone choice usually touches ranking config, generated config, selector templates, and current-layout sync.

Changing when construction happens usually touches gating triggers, monthly orchestration, and building exception files.

Changing demolition behavior can mean zone demolition, district demolition, building demolition, default country settings, planet flags, or global bulk actions. Do not assume these share one implementation path.
