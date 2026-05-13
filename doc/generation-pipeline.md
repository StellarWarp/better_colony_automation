# Generation Pipeline

See also:

- [Source Of Truth Map](source-of-truth.md)
- [Maintenance Playbook](maintenance-playbook.md)

## Overview

The generator renders Jinja templates into runtime Stellaris files.

Entrypoints:

- [`../mod_builder/generate.py`](../mod_builder/generate.py)
- [`../mod_builder/build_all.py`](../mod_builder/build_all.py)

## Inputs

There are three main input classes.

### 1. Handwritten templates

Location:

- [`../mod_builder/templates/`](../mod_builder/templates/)

Important subfolders:

- `common/`
- `events/`
- `interface/`
- `component/`
- `localisation/`

### 2. Generated config YAML

Location:

- [`../mod_builder/templates/generated_configs/`](../mod_builder/templates/generated_configs/)

This directory is merged by `generate.py` and made available as Jinja context.

Examples:

- `primary_districts_for_zone.yaml`
- `secondary_districts_for_zone.yaml`
- `all_designations.yaml`
- `job_config.yaml`

### 3. Handwritten config YAML

Location:

- [`../mod_builder/configs/`](../mod_builder/configs/)

Important examples:

- [`../mod_builder/configs/zone_type_fitness.yaml`](../mod_builder/configs/zone_type_fitness.yaml)
- [`../mod_builder/configs/mix_zone_buildings_config.yaml`](../mod_builder/configs/mix_zone_buildings_config.yaml)
- [`../mod_builder/configs/job_config.yaml`](../mod_builder/configs/job_config.yaml)

## Rendering Model

`generate.py` does the following:

1. Load every YAML file in `templates/generated_configs/`.
2. Merge them into one Jinja context dictionary.
3. Render all `.gui.j2` templates into `interface/`.
4. Render all `.txt.j2` templates under `templates/common/` into `common/`.
5. Render all `.txt.j2` templates under `templates/events/` into `events/`.
6. Render all `.yml.j2` localisation templates into `localisation/`.

This means:

- output file paths are determined by template locations
- some runtime directories contain both generated and handwritten files

## Component Macros

The `component/` templates act like an internal meta-API.

Important files:

- [`../mod_builder/templates/component/planet_flag_ps.j2`](../mod_builder/templates/component/planet_flag_ps.j2)
- [`../mod_builder/templates/component/planet_variable.j2`](../mod_builder/templates/component/planet_variable.j2)
- [`../mod_builder/templates/component/zone_setting_option_operation.j2`](../mod_builder/templates/component/zone_setting_option_operation.j2)
- [`../mod_builder/templates/component/conditions.j2`](../mod_builder/templates/component/conditions.j2)

If a behavior seems to repeat in many templates, check here first.

## Data Extraction Pipeline

Not all YAML is handwritten. Some is derived from Stellaris definitions.

Important parser:

- [`../mod_builder/parse/zone_condition_gen.py`](../mod_builder/parse/zone_condition_gen.py)

What it derives:

- zone-to-district mappings
- primary vs secondary district capability
- icon groupings and zone type grouping
- overlapping zone relationships

It also consumes:

- [`../mod_builder/configs/blacklisted_secondary_districts.yaml`](../mod_builder/configs/blacklisted_secondary_districts.yaml)
- [`../mod_builder/configs/zone_type_fitness.yaml`](../mod_builder/configs/zone_type_fitness.yaml)

## Important Current Reality

The current repository contains generated runtime outputs checked in.

That is convenient for the game, but it creates a maintenance hazard:

- Changing only the generated output may be overwritten later.
- Changing only the template may leave committed runtime files stale until regeneration.

Always decide whether the intended change belongs in:

- handwritten runtime files
- templates
- generated config inputs
- handwritten config inputs

## Safe Workflow For Generator-Backed Changes

1. Locate the generated runtime file.
2. Find the matching template.
3. Check whether the template depends on generated YAML or handwritten YAML.
4. Edit the highest-leverage source.
5. Regenerate outputs.
6. Spot-check both the generated runtime file and the UI/runtime behavior assumptions.
