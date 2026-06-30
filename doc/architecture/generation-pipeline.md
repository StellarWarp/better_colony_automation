# Generation Pipeline

See also:

- [Architecture Overview](overview.md)
- [DSL Style Guide](../maintenance/dsl-style-guide.md)
- [Maintenance Playbook](../maintenance/playbook.md)

## Overview

The runtime generator renders Jinja templates into Stellaris files, but rendering is only the last stage.

The full pipeline is:

1. Maintain handwritten config under `mod_builder/configs/`.
2. Parse or copy data into `mod_builder/templates/generated_configs/`.
3. Load the generated-config layer into Jinja.
4. Render runtime files into `common/`, `events/`, `interface/`, and `localisation/`.
5. Prepend generated-file warning headers to rendered outputs.

Entrypoints:

- [`../../mod_builder/generate.py`](../../mod_builder/generate.py)
- [`../../mod_builder/build_all.py`](../../mod_builder/build_all.py)
- [`../../mod_builder/parse/build_generated_configs.py`](../../mod_builder/parse/build_generated_configs.py)
- [`../../mod_builder/parse/copy_configs.py`](../../mod_builder/parse/copy_configs.py)
- [`../../mod_builder/parse/zone_condition_gen.py`](../../mod_builder/parse/zone_condition_gen.py)
- [`../../mod_builder/parse/building_condition.py`](../../mod_builder/parse/building_condition.py)
- [`../../mod_builder/parse/building_strategy_compile.py`](../../mod_builder/parse/building_strategy_compile.py)

## Input Classes

### Handwritten templates

Location:

- [`../../mod_builder/templates/`](../../mod_builder/templates/)

Important subfolders:

- `common/`
- `events/`
- `interface/`
- `component/`
- `localisation/`

### Handwritten config YAML

Location:

- [`../../mod_builder/configs/`](../../mod_builder/configs/)

This is the human-maintained source data layer.

Examples:

- [`../../mod_builder/configs/zone_type_fitness.yaml`](../../mod_builder/configs/zone_type_fitness.yaml)
- [`../../mod_builder/configs/buildings/`](../../mod_builder/configs/buildings/)
- [`../../mod_builder/configs/manual_building_destruction.yaml`](../../mod_builder/configs/manual_building_destruction.yaml)
- [`../../mod_builder/configs/job_config.yaml`](../../mod_builder/configs/job_config.yaml)

### Copied/generated config YAML

Location:

- [`../../mod_builder/templates/generated_configs/`](../../mod_builder/templates/generated_configs/)

This directory is generated and not editable by hand.

Its contents come from:

- copy steps from handwritten `configs/`
- parser/extraction output from Stellaris definitions
- normalized building strategy projections

Important building-related generated inputs include:

- `building_conditions.yaml`: category, building-set, and upgrade metadata
- `zone_building_mapping.yaml`: zone allow/deny data and building-set mappings
- `designation_building_strategies.yaml`: designation construction projection
- `zone_building_strategies.yaml`: zone construction projection
- `destruction_building_strategies.yaml`: merged demolition projection
- `normalized_building_strategy_model.yaml`: compiler inspection output

### Parser/extraction tooling

Locations:

- [`../../mod_builder/parse/`](../../mod_builder/parse/)
- [`../../mod_builder/synthetipy/`](../../mod_builder/synthetipy/)

This layer acts like a small compiler frontend for Paradox DSL:

- lex and parse upstream script definitions
- build AST-like structures
- resolve inline script expansion where needed
- emit YAML consumed by templates

This exists because the official runtime DSL API is not rich enough for all
automation decisions. Some information must be extracted before runtime.

For Stellaris DSL syntax reference (effects, triggers, scopes, modifiers,
enums), consult `.config/stellaris/` as the primary source and the Stellaris
user document `logs/script_documentation` as the secondary reference. See the
[DSL Style Guide](../maintenance/dsl-style-guide.md) for the full reference
priority.

The parser side is being consolidated around a shared framework:

- `build_generated_configs.py` is the unified entrypoint for generated config production
- `framework.py` owns shared AST loading, helpers, and derived relation graphs
- generator modules such as `zone_outputs.py` emit specific YAML artifacts from that shared graph

### Economic output extraction

[`../../mod_builder/parse/economic_outputs.py`](../../mod_builder/parse/economic_outputs.py)
extracts job, zone, and district economic output metadata.

Important generated artifacts:

- `job_resource_outputs.yaml` and `job_resource_conditions.yaml`: parsed job
  outputs and job-level resource conditions.
- `zone_resource_outputs.yaml` and `zone_resource_conditions.yaml`: zone
  outputs derived from jobs provided by zones.
- `district_resource_profiles.yaml`: inspection profile for each district,
  including parsed direct outputs and wrapper conditions around `job_<job>_add`
  entries.
- `economic_district_slot_groups.yaml`: slot-to-zone output groups consumed by
  district build gating.
- `economic_district_slot_direct_groups.yaml`: slot-to-district direct output
  groups from the explicit whitelist.
- `economic_district_slot_conditions.yaml`: conditions for the two group files.

`district_direct_outputs.yaml` is a whitelist, not a complete parser override.
Only listed districts may use direct district output as an automatic build
reason. Parsed direct outputs that are not whitelisted remain diagnostic data in
`district_resource_profiles.yaml`.

## Building Strategy Compilation

`build_generated_configs.py` is the preferred generated-config entrypoint.
`copy_configs.py` is now a compatibility wrapper around it.

The compiler combines:

- normal declarations under `configs/buildings/`;
- metadata from `configs/buildings/designation_contexts.yaml`;
- special demolition from `configs/manual_building_destruction.yaml`;
- category and upgrade metadata from `building_conditions.yaml`.

It validates construction uniqueness, expands context lists and upgrade
series, applies within-strategy priorities, and emits designation, zone, and
demolition projections. See
[Building Automation Pipeline](building-automation-pipeline.md).

## Rendering Model

`generate.py` does the following:

1. Load YAML files in `templates/generated_configs/`.
2. Merge them into one Jinja context dictionary.
3. Render `.gui.j2` templates into `interface/`.
4. Render `.txt.j2` templates under `templates/common/` into `common/`.
5. Render `.txt.j2` templates under `templates/events/` into `events/`.
6. Render `.yml.j2` localisation templates into `localisation/`.
7. Prepend a generated-file warning header to rendered output.

This means:

- output paths are determined by template locations
- runtime directories contain both generated and handwritten files
- warning headers are the first-line ownership signal during editing

## Component Macros

The `component/` templates act like an internal meta-API.

Important files:

- [`../../mod_builder/templates/component/planet_flag_ps.j2`](../../mod_builder/templates/component/planet_flag_ps.j2)
- [`../../mod_builder/templates/component/planet_variable.j2`](../../mod_builder/templates/component/planet_variable.j2)
- [`../../mod_builder/templates/component/zone_setting_option_operation.j2`](../../mod_builder/templates/component/zone_setting_option_operation.j2)
- [`../../mod_builder/templates/component/conditions.j2`](../../mod_builder/templates/component/conditions.j2)
- [`../../mod_builder/templates/component/event_gui_shell.j2`](../../mod_builder/templates/component/event_gui_shell.j2)
- [`../../mod_builder/templates/component/global_settings_components.j2`](../../mod_builder/templates/component/global_settings_components.j2)

If a behavior repeats across templates, check component macros before adding another local pattern.

## Generated File Warning

Generated runtime files should contain a warning header.

Purpose:

- make generated ownership visible at the edit site
- reduce accidental patches to generated output
- point maintainers back to the source template

If the header disappears or becomes inaccurate, fix the renderer instead of patching generated files one by one.

## Safe Workflow

1. Locate the runtime file involved in the bug or feature.
2. Check whether it has a generated warning header.
3. If generated, find the template named by the header.
4. Check whether template data comes from handwritten config or parser output.
5. Edit the highest-leverage source.
6. Regenerate outputs with the file watcher or generator.
7. Spot-check generated output and in-game behavior.
