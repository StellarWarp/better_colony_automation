# Generation Pipeline

See also:

- [Source Of Truth Map](source-of-truth.md)
- [Maintenance Playbook](maintenance-playbook.md)

## Overview

The runtime generator renders Jinja templates into Stellaris files, but that is only the last stage.

In practice, the pipeline is:

1. maintain handwritten config under `mod_builder/configs/`
2. generate `mod_builder/templates/generated_configs/` from config copy steps and parser scripts
3. load the generated-config layer into Jinja
4. render runtime files into `common/`, `events/`, `interface/`, and `localisation/`

Entrypoints:

- [`../mod_builder/generate.py`](../mod_builder/generate.py)
- [`../mod_builder/build_all.py`](../mod_builder/build_all.py)
- [`../mod_builder/parse/copy_configs.py`](../mod_builder/parse/copy_configs.py)
- [`../mod_builder/parse/zone_condition_gen.py`](../mod_builder/parse/zone_condition_gen.py)
- [`../mod_builder/parse/building_condition.py`](../mod_builder/parse/building_condition.py)

## Inputs

There are four main input classes.

### 1. Handwritten templates

Location:

- [`../mod_builder/templates/`](../mod_builder/templates/)

Important subfolders:

- `common/`
- `events/`
- `interface/`
- `component/`
- `localisation/`

### 2. Handwritten config YAML

Location:

- [`../mod_builder/configs/`](../mod_builder/configs/)

This is the human-maintained source data layer.

Examples:

- [`../mod_builder/configs/zone_type_fitness.yaml`](../mod_builder/configs/zone_type_fitness.yaml)
- [`../mod_builder/configs/mix_zone_buildings_config.yaml`](../mod_builder/configs/mix_zone_buildings_config.yaml)
- [`../mod_builder/configs/job_config.yaml`](../mod_builder/configs/job_config.yaml)

### 3. Copied/generated config YAML

Location:

- [`../mod_builder/templates/generated_configs/`](../mod_builder/templates/generated_configs/)

This directory is generated and not editable by hand.

It is a generated input layer used by `generate.py`, and its contents come from program steps only:

- copy from handwritten `configs/` via generator scripts
- generated extraction output from parser scripts

Direct copy entrypoint:

- [`../mod_builder/parse/copy_configs.py`](../mod_builder/parse/copy_configs.py)

Examples of copied files:

- `all_designations.yaml`
- `job_config.yaml`
- `mix_zone_buildings_config.yaml`

Examples of generated files:

- `primary_districts_for_zone.yaml`
- `secondary_districts_for_zone.yaml`
- `building_conditions.yaml`
- `zone_config.yaml`

### 4. Parser/extraction tooling

Locations:

- [`../mod_builder/parse/`](../mod_builder/parse/)
- [`../mod_builder/synthetipy/`](../mod_builder/synthetipy/)

This layer parses Paradox/Stellaris script definitions, builds ASTs, resolves inline script expansion, and emits YAML consumed by templates.

Important examples:

- [`../mod_builder/parse/zone_condition_gen.py`](../mod_builder/parse/zone_condition_gen.py)
- [`../mod_builder/parse/building_condition.py`](../mod_builder/parse/building_condition.py)
- [`../mod_builder/synthetipy/ast_loadder.py`](../mod_builder/synthetipy/ast_loadder.py)
- [`../mod_builder/synthetipy/parser.py`](../mod_builder/synthetipy/parser.py)
- [`../mod_builder/synthetipy/compiler.py`](../mod_builder/synthetipy/compiler.py)

## Rendering Model

`generate.py` does the following:

1. Load every YAML file in `templates/generated_configs/`.
2. Merge them into one Jinja context dictionary.
3. Render all `.gui.j2` templates into `interface/`.
4. Render all `.txt.j2` templates under `templates/common/` into `common/`.
5. Render all `.txt.j2` templates under `templates/events/` into `events/`.
6. Render all `.yml.j2` localisation templates into `localisation/`.
7. Prepend a generated-file warning header to every rendered output.

This means:

- output file paths are determined by template locations
- some runtime directories contain both generated and handwritten files
- generated runtime files are expected to warn maintainers not to edit them directly

## Component Macros

The `component/` templates act like an internal meta-API.

Important files:

- [`../mod_builder/templates/component/planet_flag_ps.j2`](../mod_builder/templates/component/planet_flag_ps.j2)
- [`../mod_builder/templates/component/planet_variable.j2`](../mod_builder/templates/component/planet_variable.j2)
- [`../mod_builder/templates/component/zone_setting_option_operation.j2`](../mod_builder/templates/component/zone_setting_option_operation.j2)
- [`../mod_builder/templates/component/conditions.j2`](../mod_builder/templates/component/conditions.j2)

If a behavior seems to repeat in many templates, check here first.

## Data Extraction Pipeline

Not all YAML is handwritten. `templates/generated_configs/` is generated output only.

Important parser:

- [`../mod_builder/parse/zone_condition_gen.py`](../mod_builder/parse/zone_condition_gen.py)
- [`../mod_builder/parse/building_condition.py`](../mod_builder/parse/building_condition.py)
- [`../mod_builder/synthetipy/`](../mod_builder/synthetipy/)

What it derives:

- zone-to-district mappings
- primary vs secondary district capability
- icon groupings and zone type grouping
- overlapping zone relationships

It also consumes:

- [`../mod_builder/configs/blacklisted_secondary_districts.yaml`](../mod_builder/configs/blacklisted_secondary_districts.yaml)
- [`../mod_builder/configs/zone_type_fitness.yaml`](../mod_builder/configs/zone_type_fitness.yaml)

## Generated File Warning

`generate.py` prepends a warning header to rendered runtime files.

Purpose:

- make generated ownership obvious during manual inspection
- reduce accidental edits to checked-in generated output
- point maintainers back to the source template

If that header disappears or becomes inaccurate, fix the renderer rather than editing many generated files by hand.

## Important Current Reality

The current repository contains generated runtime outputs checked in.

That is convenient for the game, but it creates a maintenance hazard:

- Changing only the generated output may be overwritten later.
- Changing only the template may leave committed runtime files stale until regeneration.

Always decide whether the intended change belongs in:

- handwritten runtime files
- templates
- handwritten config inputs
- copied/generated config inputs
- parser/extraction tooling

## Safe Workflow For Generator-Backed Changes

1. Locate the generated runtime file.
2. Find the matching template.
3. Check whether the template input comes from handwritten `configs/`, copied config files, or parser-generated YAML.
4. If the value is parser-derived, identify the relevant script in `parse/` or `synthetipy/`.
5. Edit the highest-leverage source.
6. Regenerate outputs.
7. Spot-check both the generated runtime file and the UI/runtime behavior assumptions.
