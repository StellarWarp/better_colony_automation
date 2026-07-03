# Building Automation Pipeline

See also:

- [Architecture Overview](overview.md)
- [Generation Pipeline](generation-pipeline.md)
- [Building Strategy Model](../proposal/building-strategy-model.md)
- [Change Entrypoints](../maintenance/change-entrypoints.md)

## Scope

Building construction for normal designation and zone scenarios, plus most
building demolition lists, is generated from a shared strategy model.

The model deliberately does not describe every building behavior. Housing,
pop management, rare-resource deficit handling, capital automation, and other
scenario-specific flows may remain handwritten.

## Source Layers

### Building strategy config

The main source directory is
[`../../mod_builder/configs/buildings/`](../../mod_builder/configs/buildings/).

Two authoring forms are supported:

- building-centered entries, preferred for new content and mod extensions;
- grouped context entries, retained as concise syntax when many buildings
  share identical behavior.

Both forms normalize into rows keyed by building, projection, and context.
Duplicate rows are rejected.

`designation_contexts.yaml` defines context-level metadata such as
`job_provider_districts` and mutually exclusive subcases. Construction config
can opt into a subcase and override its strategy without embedding raw trigger
blocks.

### Manual demolition config

[`../../mod_builder/configs/manual_building_destruction.yaml`](../../mod_builder/configs/manual_building_destruction.yaml)
contains demolition rules for buildings whose construction is owned by a
handwritten scenario.

This keeps special construction behavior out of the shared strategy model
while still allowing one demolition compiler to infer categories, expand
upgrade chains, deduplicate entries, and merge trigger groups.

### Parsed game metadata

[`../../mod_builder/parse/building_condition.py`](../../mod_builder/parse/building_condition.py)
extracts building category, building sets, and upgrade-chain metadata.

[`../../mod_builder/parse/zone_condition_gen.py`](../../mod_builder/parse/zone_condition_gen.py)
extracts zone types, district/zone-slot relationships, explicit building
allowlists and denylists, and building-set compatibility. Inline scripts are
expanded by `ASTLoader` before icon and building-set data are read.

The generated `zone_building_mapping.yaml` records both zone ids and zone
types for each building set.

Important distinction:

- building-set compatibility answers where a building is allowed;
- a strategy context answers when that building is useful.

Do not copy every compatible zone type into building automation config. A
building should participate only in contexts whose production or behavior it
actually improves.

## Compiler

[`../../mod_builder/parse/building_strategy_compile.py`](../../mod_builder/parse/building_strategy_compile.py)
performs normalization, validation, priority sorting, projection, demolition
expansion, and grouping.

Primary outputs under `templates/generated_configs/` are:

- `designation_building_strategies.yaml`
- `zone_building_strategies.yaml`
- `destruction_building_strategies.yaml`
- `normalized_building_strategy_model.yaml`
- `building_strategy_compile_warnings.yaml`, when warnings exist

`copy_configs.py` invokes this compiler after copying the small set of direct
config inputs used elsewhere by the template system.

## Construction Strategies

Strategies define template behavior and scheduling bands. They are not
user-configurable trigger bundles.

| Strategy | Meaning |
| --- | --- |
| `district_capacity` | Build after relevant job-provider districts are exhausted. |
| `efficiency` | Build when jobs are not urgent or relevant districts are exhausted. |
| `always` | No job-demand condition; used for required or job-providing support buildings. |
| `job_only` | Build when more jobs are required and relevant districts are exhausted. |
| `job_low_priority` | Same demand condition as `job_only`, rendered in a later block. |
| `job_bookend` | Render one limited entry first and the same building last around normal choices. |

Strategy order is above per-building priority. `priority.before` and
`priority.after` only order buildings within the same strategy bucket.

`job_bookend` is used by Wilderness construction in both designation and zone
projections. A projection context may contain at most one bookend building.

## Runtime Templates

Designation construction:

- template: `31_bca_designation_buildings.txt.j2`
- runtime: `common/colony_automation_exceptions/31_bca_designation_buildings.txt`

Zone construction:

- template: `500_bca_mixd_zones_building.txt.j2`
- runtime: `common/colony_automation_exceptions/500_bca_mixd_zones_building.txt`

Building demolition:

- template: `common/scripted_effects/bca_building_destruction.txt.j2`
- runtime: `common/scripted_effects/bca_building_destruction.txt`

Templates own the Stellaris DSL emitted for each strategy. Config should not
duplicate template conditions.

## Special-Case Boundary

Keep a building outside shared construction config when its behavior is owned
by a different automation category or requires scenario state beyond the
strategy vocabulary.

Examples include:

- Passenger Dorms in handwritten housing automation;
- pop assembly buildings in dedicated pop-management automation;
- rare-resource buildings in deficit-management automation;
- capital, resort, slave, and Biotrophy scenes.

If such a building still needs automatic demolition, add it to the manual
demolition source rather than inventing a fake construction context.

## Adding Game Or Mod Content

1. Parse or inspect the building, district, zone, and designation definitions.
2. Separate physical compatibility from automation demand.
3. Add missing zone fitness data and manual district-slot classification.
4. Choose building-centered strategy config for normal construction behavior.
5. Keep special construction in its owning handwritten automation category.
6. Add demolition beside normal config or in the manual demolition source.
7. Let the file watcher regenerate outputs and inspect generated YAML and
   runtime blocks.

New game versions can also rename or remove script APIs. Consult the Stellaris
user document `logs/script_documentation` as the source of truth when a version
change invalidates otherwise correct templates. If the document does not make
the concrete call shape clear, check `.config/stellaris/`, then matching usage
in project or game scripts.
