# Building Strategy Model

This document records the current working design for migrating building
automation authoring toward a building-centered extension model while keeping
runtime generation aligned with Stellaris automation behavior.

This is an active implementation proposal, not a long-term speculative
roadmap.

## Goals

- Make mod compatibility easier by letting extension authors describe behavior
  from the perspective of a building.
- Keep vanilla/core authoring readable when many buildings share the same
  context and ordering rules.
- Avoid exposing raw Stellaris trigger logic to normal extension authors.
- Generate designation-based construction config, zone-based construction
  config, and building demolition config from one strategy source.
- Preserve priority semantics that already matter in the handwritten
  automation files.

## Design Summary

The model has three layers:

1. Building-centered authoring for player and mod-extension input.
2. Row-centered normalized compiler processing.
3. Strategy-driven template behavior.

The key boundary is:

- The compiler owns structure: normalization, projection, grouping, ordering,
  category inference, and validation.
- Templates own runtime DSL behavior for construction strategies.
- Demolition uses explicit custom triggers instead of construction-style
  strategies.

## Authoring Forms

### Building-Centered Overlay

This is the preferred shape for external mod compatibility data and future web
tool output.

```yaml
buildings:
  building_my_mod_factory:
    construction:
      - projection: designation
        context: factory
        strategy: job_only
        priority:
          after: building_factory_1

      - projection: zone
        context:
          - factory
          - industrial
        strategy: job_only

    destruction:
      - triggers:
          - bca_can_remove_building_factory
      - triggers:
          - bca_advanced_factory_building_replace
        remove_series: true
```

Construction entries describe where a building participates in automation.

`context` accepts either one string or a non-empty list of unique strings. A
list is authoring sugar for otherwise identical construction entries and is
expanded into normalized rows before duplicate validation:

```yaml
- projection: zone
  context: [food, agrarian]
  strategy: efficiency
```

Designation construction entries may participate in explicitly declared
mutually exclusive subcases and override their strategy per branch:

```yaml
buildings:
  building_food_processing_facility:
    construction:
      - projection: designation
        context: farming
        strategy: efficiency
        subcases:
          - trigger: bca_is_farming_habitat
          - trigger: bca_other_farming_case
            strategy_override: job_only
```

The base `strategy` applies to the default branch. A listed subcase inherits it
unless `strategy_override` is present. Buildings participate only in the
subcases they explicitly list, so adding a new context subcase does not change
existing building behavior.

A building that belongs only to subcases uses `include_default: false`:

```yaml
buildings:
  building_betharian_power_plant:
    construction:
      - projection: designation
        context: generator
        strategy: job_only
        include_default: false
        subcases:
          - trigger: bca_is_generator_betharian
```

`include_default` defaults to true. Setting it to false requires at least one
subcase.

Each building may have at most one source construction entry for the same
`projection + context`, regardless of strategy or subcase. Different
projections and different contexts remain independent.

Destruction entries describe which custom demolition triggers apply to a
building. These triggers are already project-level semantic APIs, so wrapping
them in another strategy layer would add indirection without reducing
complexity.

### Grouped Context Authoring

Grouped context remains useful for project-owned vanilla/core data because
many buildings share the same context and strategy order.

```yaml
- designations:
    - industrial
    - factory
  zone_types:
    - industrial
    - factory
  groups:
    - strategy: efficiency
      buildings:
        - building_factory_efficiency_1
        - building_affluence_emporium
    - strategy: job_only
      buildings:
        - building_factory_1
```

Grouped context is authoring sugar. The compiler must normalize it into the
same internal row model as building-centered overlays.

### Designation Context Metadata

Designation scheduling metadata is configured separately from buildings:

```yaml
designation_contexts:
  generator:
    job_provider_districts:
      - district_generator
    subcases:
      bca_is_generator_betharian: {}

  mining:
    job_provider_districts:
      - district_mining
      - district_melting
```

`job_provider_districts` identifies districts that compete with job-providing
buildings. Its rules are:

- omitted or `any`: use `free_district_slots = 0`;
- one district: use one `num_free_districts` condition;
- multiple districts: combine their `num_free_districts` conditions with
  `OR`, because these district types normally represent mutually exclusive
  alternatives.

Subcase keys are scripted trigger names. A subcase inherits its parent
designation context metadata and may override `job_provider_districts`:

```yaml
designation_contexts:
  generator:
    job_provider_districts:
      - district_generator
    subcases:
      bca_is_generator_betharian:
        job_provider_districts: any
```

Designation conditions themselves are derived from the context and are not
authored as `designation_trigger` configuration.

Subcases are ordered mutually exclusive branches. For subcases `A` and `B`,
the compiler generates:

```text
A branch: A
B branch: B AND NOT A
default: NOT A AND NOT B
```

Templates consume these already-expanded branches and do not calculate
subcase precedence themselves.

## Normalized Internal Model

The serialized intermediate model may be grouped by building for readability:

```yaml
buildings:
  building_factory_1:
    construction:
      - projection: designation
        context: factory
        strategy: job_only
        source_order: 120
      - projection: zone
        context: factory
        strategy: job_only
        source_order: 121
    destruction:
      - triggers:
          - bca_can_remove_building_factory
      - triggers:
          - bca_advanced_factory_building_replace
        remove_series: true
```

The compiler should process this as rows:

```text
ConstructionRow(
    building,
    projection,
    context,
    strategy,
    include_default,
    subcases,
    priority,
    source_order,
)
ConstructionSubcase(trigger, strategy_override)
DestructionRow(building, triggers, remove_series, source_order)
```

This keeps projection generation straightforward while still allowing readable
debug output.

## Construction Strategy Semantics

`strategy` is a template API.

Configuration declares the strategy name. Templates define the actual
Stellaris DSL generated for each strategy. Normal extension authors should not
write raw `build_triggers`, `build_and_upgrade_triggers`, or building settings.

Examples of construction strategies:

- `efficiency`
- `always`
- `job_only`
- project-owned special strategies for handwritten exception behavior such as
  staged limits, upgrade-only passes, or other cases found under
  `common/colony_automation_exceptions/`

The currently aligned general strategies are:

| Strategy | Building-entry behavior | Designation priority band |
| --- | --- | --- |
| `district_capacity` | relevant job-provider districts are exhausted | high |
| `efficiency` | jobs are not urgently required, or relevant districts are exhausted | main |
| `always` | no additional building-entry condition | main |
| `job_only` | more jobs are required and relevant districts are exhausted | main |
| `job_bookend` | `job_only`, repeated at the start and end with `planet_limit = 1` on the first entry | main |
| `job_low_priority` | more jobs are required and relevant districts are exhausted | low |

The historical `bca_pf_advance_controller_order` planet-flag condition is not
part of any strategy contract and should not be generated.

The compiler should validate that a strategy is known and supported for the
requested projection, but it should not try to encode the full runtime DSL
meaning of that strategy in YAML.

Strategies are expected to grow beyond the current `efficiency`, `always`, and
`job_only` buckets. Many existing handwritten construction exceptions carry
special scheduling or availability semantics. Those should be represented as
named construction strategies instead of raw triggers in normal authoring data.

### Strategy Rendering Boundary

A strategy bucket is not automatically an automation block.

For the general designation renderer, the block grouping key is:

```text
context + subcase branch + template-defined priority band
```

It is explicitly not:

```text
context + subcase branch + strategy
```

Several strategy buckets can therefore be rendered into one block. Strategy
conditions are emitted on each building entry. Handwritten files may hoist a
condition shared by every building into `block.available`, but generated files
do not need to reproduce that deduplication because the runtime semantics are
the same.

Projection templates decide how strategy buckets are rendered into Stellaris
automation blocks. A template may:

- render several strategy buckets into one automation block;
- render a high-priority strategy bucket before the main block;
- render a low-priority strategy bucket after the main block;
- ignore a strategy that is meaningful only for another projection;
- inject strategy-specific conditions at the block level;
- inject strategy-specific conditions or settings at the building-entry level.

For example, a designation template may render the `district_capacity`
strategy as its own high-priority block before the
ordinary farming building block, matching the existing
`automate_farming_planet_building_district` behavior. The same strategy may be
ignored by a mixed-zone template if district capacity is not meaningful there.

Conversely, ordinary strategies such as `efficiency` and `job_only` can be
rendered into the same automation block when that matches the handwritten
runtime behavior.

The data model should therefore preserve `projection + context + strategy`
buckets, but should not pre-split final automation blocks. Block layout is part
of the projection template.

There is no separate strategy metadata/configuration layer planned. The
cross-strategy scheduling semantics are expressed directly by template order:
strategies rendered earlier by a template are higher priority, and strategies
rendered later are lower priority.

## Priority Semantics

Strategy is higher than priority.

Priority only has meaning inside the same:

```text
projection + context + strategy
```

For example:

```yaml
priority:
  after: building_factory_1
```

means:

```text
place this building after building_factory_1 inside the same projection,
context, and strategy bucket
```

It does not mean the building can move across strategy buckets.

Sorting rules:

1. Group construction rows by `projection + context`.
2. Group each context by strategy bucket.
3. Apply `priority.before` and `priority.after` only within one bucket.
4. Use source order for rows without explicit priority.
5. Pass ordered strategy buckets to the consuming template.
6. Let the template define cross-strategy ordering and automation block layout.
7. Treat cross-strategy priority references as invalid for core data. Player
   overlays may choose warning-plus-fallback behavior if compatibility data can
   be partially missing.

The compiler must not interpret a strategy bucket as a final priority band or
as a final automation block. Those decisions belong to the template.

Template authors should keep high-priority strategy rendering earlier in the
file and low-priority strategy rendering later in the file. This keeps
cross-strategy priority visible in the generated DSL instead of hiding it in a
second strategy registry.

The initial generic designation bands are defined directly by template order:

```text
high: district_capacity
main: efficiency, always, job_only, job_bookend
low: job_low_priority
```

`job_bookend` is a generic structural strategy rather than a wilderness
special case. The designation renderer emits its building before the ordinary
main-band entries with `planet_limit = 1`, then emits it again after those
entries without the limit. A designation context/subcase branch may contain at
most one `job_bookend` building.

Subcases such as habitat and Betharian do not receive dedicated templates or
strategies when their remaining building behavior is already represented by a
general strategy. Their scripted triggers only select mutually exclusive
branches.

Context compatibility that belongs to an existing semantic designation
trigger should be implemented in that trigger rather than in building config.
The project overrides vanilla `has_trade_designation` to add `col_hive` while
preserving every vanilla designation, including `col_nexus`. The historical
mining fallback based on `zone_betharian` is intentionally not preserved.

## Generated Projections

The exact generated projection shape can be chosen during implementation based
on template readability and migration cost.

Acceptable shapes include:

```yaml
zone_building_contexts:
  - context: factory
    entries:
      - building: building_factory_efficiency_1
        strategy: efficiency
      - building: building_factory_1
        strategy: job_only
```

or:

```yaml
zone_building_contexts:
  - context: factory
    strategy_buckets:
      - strategy: efficiency
        buildings:
          - building_factory_efficiency_1
      - strategy: job_only
        buildings:
          - building_factory_1
```

During migration, the compiler may also emit legacy bucket fields such as
`efficiency`, `always`, and `job_only` if that makes template conversion safer.

The required constraints are:

- Generated projection data must preserve strategy.
- Generated projection data must preserve within-strategy ordering.
- Generated projection data must not imply that every strategy bucket becomes
  its own automation block.
- Construction strategy DSL details should remain in templates, not in user
  config.
- Cross-strategy automation order should be readable in template order.
- The final shape should make the templates easier to read, not merely more
  abstract.

Designation projections additionally expose context metadata and expanded
branches:

```yaml
- context: generator
  job_provider_districts: [district_generator]
  branches:
    - name: default
      trigger: null
      exclude_triggers: [bca_is_generator_betharian]
      job_provider_districts: [district_generator]
      strategy_buckets: []
    - name: bca_is_generator_betharian
      trigger: bca_is_generator_betharian
      exclude_triggers: []
      job_provider_districts: [district_generator]
      strategy_buckets: []
```

The designation template can therefore use generic macros for designation
conditions, branch conditions, district exhaustion, and building entries. It
should branch only on strategies whose runtime block structure is genuinely
different. It should not branch on resource context names such as `farming`,
`generator`, or `mining`.

The generic designation renderer is now the formal source at
`mod_builder/templates/common/colony_automation_exceptions/31_bca_designation_buildings.txt.j2`.
It generates
`common/colony_automation_exceptions/31_bca_designation_buildings.txt` and
replaces the former resource, industry, trade, research, unity, fortress, and
wilderness handwritten designation files. Capital, resort, slave, monument,
and other independent automation categories remain handwritten.

## Demolition Projection

Demolition authoring uses explicit trigger lists:

```yaml
destruction:
  - triggers:
      - bca_can_remove_building_factory
  - triggers:
      - bca_advanced_factory_building_replace
    remove_series: true
```

The `triggers` list is an authoring convenience for alternative demolition
conditions. During compilation, each trigger becomes its own template-facing
condition group. It is not emitted as one combined AND condition.

`remove_series` is also an authoring-only directive. It tells the compiler to
expand the building through its parsed `upgrades` chain. After expansion, the
generated demolition projection should list the concrete building ids and
should not keep a `remove_series` marker.

`remove_series` defaults to `true`. Authors only need to write it when a
destruction rule must target the configured building alone:

```yaml
destruction:
  - triggers:
      - bca_can_remove_only_this_building
    remove_series: false
```

The compiler should:

- split alternative triggers into independent condition groups;
- group buildings by trigger and compatible category filter;
- infer category filters from parsed vanilla or mod building definitions;
- allow explicit category override when automatic inference is ambiguous;
- apply structural directives such as `remove_series` before projection;
- generate the template-facing demolition config.

Category inference is an optimization and safety filter, not a source-level
authoring burden for normal extension authors.

## Implementation Plan

1. Continue auditing special cases under
   `common/colony_automation_exceptions/` and define
   the additional project-owned strategies needed to represent their scheduling,
   availability, limit, and upgrade semantics.
2. Migrate designation templates context group by context group, stopping to
   model genuinely different runtime behavior before replacing handwritten
   files.
3. Keep old generated outputs temporarily where useful for diff-based parity
   checks.
4. Use the building-centered overlay format as the future website export
   format.

## Open Design Points

- How strict player overlay validation should be when a priority target is
  absent in the current mod set.
- Which category inference failures should be hard errors and which should be
  warnings.
- Whether project-owned core configs need an internal escape hatch for rare
  construction behavior that should not be exposed to normal extension authors.
