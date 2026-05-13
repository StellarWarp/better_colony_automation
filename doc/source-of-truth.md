# Source Of Truth Map

See also:

- [Architecture Overview](architecture.md)
- [Generation Pipeline](generation-pipeline.md)
- [Maintenance Playbook](maintenance-playbook.md)

## Why This File Exists

This project is mixed-mode. A change request like "adjust default zone selection" or "fix district planning" is often impossible to implement safely unless you first identify the true source of truth.

## Rule Of Thumb

- If a runtime file has a matching `.j2` template under `mod_builder/templates/`, treat the template as the primary source.
- If there is no matching template, treat the runtime file as handwritten until proven otherwise.
- Some behavior is split: handwritten triggers call generated effects, or generated events emit flags consumed by handwritten automation exceptions.

## Source Map By Concern

### Monthly orchestration

- Runtime source: [`../events/bca_planet_monthly_iteration_entry.txt`](../events/bca_planet_monthly_iteration_entry.txt)
- Primary source: handwritten runtime file

### Initialization and reset

- Runtime source: [`../events/bca_update_default_selection.txt`](../events/bca_update_default_selection.txt)
- Template source: [`../mod_builder/templates/events/bca_update_default_selection.txt.j2`](../mod_builder/templates/events/bca_update_default_selection.txt.j2)

### District construction/removal events

- Runtime source: [`../events/bca_district_controller.txt`](../events/bca_district_controller.txt)
- Template source: [`../mod_builder/templates/events/bca_district_controller.txt.j2`](../mod_builder/templates/events/bca_district_controller.txt.j2)

### Mixed zone construction/removal events

- Runtime source: [`../events/bca_mix_zones_controller.txt`](../events/bca_mix_zones_controller.txt)
- Template source: [`../mod_builder/templates/events/bca_mix_zones_controller.txt.j2`](../mod_builder/templates/events/bca_mix_zones_controller.txt.j2)

### Zone selector effect system

- Runtime source: [`../common/scripted_effects/bca_planet_setting_zones_0_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_0_effect.txt)
- Template source: [`../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2)

### Designation sync and current-layout sync

- Runtime source: [`../common/scripted_effects/bca_planet_setting_zones_1_effect.txt`](../common/scripted_effects/bca_planet_setting_zones_1_effect.txt)
- Template source: [`../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2)

### District plan arithmetic

- Runtime source: [`../common/scripted_effects/bca_planet_district_setting_effect.txt`](../common/scripted_effects/bca_planet_district_setting_effect.txt)
- Template source: [`../mod_builder/templates/common/scripted_effects/bca_planet_district_setting_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_planet_district_setting_effect.txt.j2)

### Script values used by selectors and planning

- Runtime source: [`../common/script_values/bca_planet_setting_values.txt`](../common/script_values/bca_planet_setting_values.txt)
- Template source: [`../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2`](../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2)

### Zone ranking values

- Runtime source: [`../common/script_values/bca_planet_setting_zone_ranking.txt`](../common/script_values/bca_planet_setting_zone_ranking.txt)
- Template source: [`../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2`](../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2)
- Data source: [`../mod_builder/configs/zone_type_fitness.yaml`](../mod_builder/configs/zone_type_fitness.yaml)

### Trigger helpers

- Runtime source: [`../common/scripted_triggers/bt_st_tool.txt`](../common/scripted_triggers/bt_st_tool.txt)
- Primary source: handwritten runtime file

### Resource-world district planner

- Runtime source: [`../common/scripted_effects/bca_resource_planet_controller.txt`](../common/scripted_effects/bca_resource_planet_controller.txt)
- Template source: [`../mod_builder/templates/common/scripted_effects/bca_resource_planet_controller.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_resource_planet_controller.txt.j2)

### Zone build automation categories

- Runtime source: [`../common/colony_automation/500_bca_mixed_zones.txt`](../common/colony_automation/500_bca_mixed_zones.txt)
- Template source: [`../mod_builder/templates/common/colony_automation/500_bca_mixed_zones.txt.j2`](../mod_builder/templates/common/colony_automation/500_bca_mixed_zones.txt.j2)

### District automation categories

- Runtime source: [`../common/colony_automation_exceptions/500_bca_districts.txt`](../common/colony_automation_exceptions/500_bca_districts.txt)
- Template source: [`../mod_builder/templates/common/colony_automation_exceptions/500_bca_districts.txt.j2`](../mod_builder/templates/common/colony_automation_exceptions/500_bca_districts.txt.j2)

### Mixed-zone building exceptions

- Runtime source: [`../common/colony_automation_exceptions/500_bca_mixd_zones_building.txt`](../common/colony_automation_exceptions/500_bca_mixd_zones_building.txt)
- Template source: [`../mod_builder/templates/common/colony_automation_exceptions/500_bca_mixd_zones_building.txt.j2`](../mod_builder/templates/common/colony_automation_exceptions/500_bca_mixd_zones_building.txt.j2)

### Panel button effects

- Runtime source: [`../common/button_effects/bca_planet_setting_panel.txt`](../common/button_effects/bca_planet_setting_panel.txt)
- Primary source: handwritten runtime file

### Zone button effects

- Runtime source: [`../common/button_effects/bca_planet_setting_zones.txt`](../common/button_effects/bca_planet_setting_zones.txt)
- Template source: [`../mod_builder/templates/common/button_effects/bca_planet_setting_zones.txt.j2`](../mod_builder/templates/common/button_effects/bca_planet_setting_zones.txt.j2)

### Auxiliary district/slider button effects

- Runtime source: [`../common/button_effects/bca_planet_setting_zones_buttons_aux.txt`](../common/button_effects/bca_planet_setting_zones_buttons_aux.txt)
- Template source: [`../mod_builder/templates/common/button_effects/bca_planet_setting_zones_buttons_aux.txt.j2`](../mod_builder/templates/common/button_effects/bca_planet_setting_zones_buttons_aux.txt.j2)

### GUI

- Runtime source: [`../interface/bca_district_gui.gui`](../interface/bca_district_gui.gui)
- Template source: [`../mod_builder/templates/interface/bca_district_gui.gui.j2`](../mod_builder/templates/interface/bca_district_gui.gui.j2)

### Building demolition logic

- Runtime source: [`../common/scripted_effects/bca_building_destruction.txt`](../common/scripted_effects/bca_building_destruction.txt)
- Primary source: handwritten runtime file

### Intro/update messages

- Runtime source: [`../events/bca_intro_event.txt`](../events/bca_intro_event.txt), [`../events/bca_update_event.txt`](../events/bca_update_event.txt)
- Primary source: handwritten runtime files

## Mixed Cases Worth Remembering

### Changing a default zone choice

Usually touches:

- zone ranking data: [`../mod_builder/configs/zone_type_fitness.yaml`](../mod_builder/configs/zone_type_fitness.yaml)
- selector template: [`../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2)
- current-layout sync: [`../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2`](../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2)

### Changing when building happens

Usually touches:

- gating trigger: [`../common/scripted_triggers/bt_st_tool.txt`](../common/scripted_triggers/bt_st_tool.txt)
- monthly orchestration: [`../events/bca_planet_monthly_iteration_entry.txt`](../events/bca_planet_monthly_iteration_entry.txt)
- building exception files: `../common/colony_automation_exceptions/`

### Changing demolition behavior

Could mean:

- zone demolition in generated zone controller templates
- district demolition in generated district controller templates
- building demolition in handwritten [`../common/scripted_effects/bca_building_destruction.txt`](../common/scripted_effects/bca_building_destruction.txt)

Do not assume these share one implementation path.
