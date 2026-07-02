# Architecture Overview

See also:

- [Generation Pipeline](generation-pipeline.md)
- [Building Automation Pipeline](building-automation-pipeline.md)
- [Runtime Flow](runtime-flow.md)
- [State Model](state-model.md)
- [Maintenance Playbook](../maintenance/playbook.md)

## Mental Model

This mod is best understood as a four-layer system:

1. Config and compiler-frontend layer
2. Template generation layer
3. Game logic layer
4. Presentation and interaction layer

The layers are not just folders. They represent where information is created, transformed, executed, and shown to players.

## 1. Config And Compiler-Frontend Layer

This is the bottom layer.

It contains handwritten source data and tools that extract missing information from Stellaris definitions:

- Handwritten config: [`../../mod_builder/configs/`](../../mod_builder/configs/)
- Parser/extraction scripts: [`../../mod_builder/parse/`](../../mod_builder/parse/)
- Paradox script parser/toolchain: [`../../mod_builder/synthetipy/`](../../mod_builder/synthetipy/)
- Generated config output: [`../../mod_builder/templates/generated_configs/`](../../mod_builder/templates/generated_configs/)

Within `parse/`, the intended flow is:

- shared parse framework and derived relation graph
- generated-config builders
- then template rendering

Why it exists:

- Paradox DSL is a content configuration layer, not a full programming platform.
- Many facts needed by automation logic are not conveniently available through runtime script APIs.
- The project therefore parses upstream Stellaris definitions before rendering runtime scripts.

`mod_builder/templates/generated_configs/` is primarily a generated input
layer. Do not edit files there by hand unless a file is explicitly documented
as a handwritten exception in
[Template And Generation Rules](../maintenance/dsl-style-guide/templates.md).

## 2. Template Generation Layer

This layer converts config and parser output into Stellaris runtime files.

Main locations:

- Templates: [`../../mod_builder/templates/`](../../mod_builder/templates/)
- Component macros: [`../../mod_builder/templates/component/`](../../mod_builder/templates/component/)
- Generator entrypoint: [`../../mod_builder/generate.py`](../../mod_builder/generate.py)

The template layer handles repetition that would be unmaintainable in raw DSL. In a normal programming language, thousands of repeated branches may look like a failure of abstraction. In this DSL, pre-expanded enumeration is often necessary; the maintainable version is generated enumeration, not handwritten enumeration.

Generated runtime files should include a warning header that points back to the template.

## 3. Game Logic Layer

This is the runtime logic executed by Stellaris.

Main locations:

- [`../../common/`](../../common/)
- [`../../events/`](../../events/)

This layer contains:

- event orchestration
- button effects
- scripted effects
- scripted triggers
- scripted values
- carrier flags and colony/carrier-scope variables
- automation categories and exceptions

Some files here are handwritten, some are generated, and some features are split across both. Check the file header and [Change Entrypoints](../maintenance/change-entrypoints.md) before editing.

## 4. Presentation And Interaction Layer

This is the player-facing layer.

Main locations:

- GUI: [`../../interface/`](../../interface/)
- Localisation: [`../../localisation/`](../../localisation/)

This layer contains:

- planet setting UI
- global settings event GUI
- button text
- tooltips
- scripted loc display text
- update and intro messages

GUI changes usually cross layers. A visible button can require edits to templates, button effects, events, scripted loc, and localisation.

## Important Consequence

This project is not a pile of script files. It is a pipeline:

```text
handwritten config + parsed Stellaris definitions
        -> normalized strategy and generated config inputs
        -> Jinja templates
        -> common/events runtime logic
        -> interface/localisation player experience
```

When debugging or changing behavior, identify the layer first. Editing the wrong layer is usually more dangerous than writing one wrong condition.
