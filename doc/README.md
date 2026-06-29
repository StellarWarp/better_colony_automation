# Better Colony Automation Maintainer Docs

This folder documents how the mod is built, how it runs, and how humans or AI agents should safely change it.

The docs have two reading paths:

1. Understand the project architecture.
2. Maintain the project safely, including DSL and AI coding practices.

Design records and active proposals live under `proposal/`. The
[Building Strategy Model](proposal/building-strategy-model.md) records the
design that led to the current building automation compiler.

## Architecture Path

Read these when you need to understand how the mod is organized and executed:

1. [Architecture Overview](architecture/overview.md)
2. [Generation Pipeline](architecture/generation-pipeline.md)
3. [Building Automation Pipeline](architecture/building-automation-pipeline.md)
4. [Runtime Flow](architecture/runtime-flow.md)
5. [State Model](architecture/state-model.md)

## Maintenance And AI Coding Path

Read these when you are about to change behavior, templates, GUI, localisation, or release metadata:

1. [Development Setup](maintenance/setup.md)
2. [Maintenance Playbook](maintenance/playbook.md)
3. [DSL Style Guide](maintenance/dsl-style-guide.md)
4. [Change Entrypoints](maintenance/change-entrypoints.md)
5. [Handwritten Hotspots](maintenance/handwritten-hotspots.md)

## Project Ownership Model

The project mixes handwritten runtime code, generated runtime code, templates, generated config inputs, and parser output.

Important rules:

- `mod_builder/configs/` contains handwritten config source.
- `mod_builder/templates/` contains Jinja templates and template components.
- `mod_builder/templates/generated_configs/` is fully program-generated and must not be edited by hand.
- `mod_builder/parse/` and `mod_builder/synthetipy/` form a parser/extraction frontend for Stellaris script definitions.
- Generated runtime files should contain a warning header pointing back to the source template.

Do not assume that a long file under `common/`, `events/`, `interface/`, or `localisation/` is handwritten. Many runtime files are generated outputs.

## Development Constraints

- Clone the CWTools Stellaris configuration repository and link its `config/`
  directory to `.config/stellaris` as described in
  [Development Setup](maintenance/setup.md).
- Stellaris mod logic does not support hot reload; after logic edits, re-enter the game to test.
- Event-window tests are the fastest practical feedback loop for scripted logic.
- Use a dedicated test event such as [`../events/test_event.txt`](../events/test_event.txt) for manual in-game testing.
- IntelliJ IDEA is recommended because its Paradox/Stellaris syntax support is useful.
- A file watcher should render templates after template edits.

## Practical Rule

Before changing behavior:

1. Identify which layer owns the change.
2. If a runtime file has a generated warning header, go back to the template or generator input.
3. If DSL syntax or API usage is uncertain, check [DSL Style Guide](maintenance/dsl-style-guide.md) and the Stellaris user document `logs/script_documentation`.
4. If the change affects release metadata, follow the release workflow in [Maintenance Playbook](maintenance/playbook.md).
