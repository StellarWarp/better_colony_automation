# DSL Style Guide

See also:

- [Development Setup](setup.md)
- [Maintenance Playbook](playbook.md)
- [Generation Pipeline](../architecture/generation-pipeline.md)
- [State Model](../architecture/state-model.md)

## Purpose

This guide records project-level rules for writing Paradox/Stellaris DSL,
custom GUI, and Jinja templates.

The goal is not to teach the whole language. The goal is to reduce errors from
scope confusion, weak runtime checks, generated-file ownership, GUI engine
limits, and template complexity.

## Topic Guides

Read the specific topic before editing that layer:

- [DSL Core Rules](dsl-style-guide/dsl-core.md): reference sources, scope,
  carrier flags, scripted values, and general DSL positioning.
- [GUI And Tooltip Rules](dsl-style-guide/gui.md): custom event GUI, scripted
  loc, effect buttons, tooltip limits, text icons, and external-panel layout.
- [Localisation Rules](dsl-style-guide/localisation.md): language coverage,
  UTF-8 BOM, scripted loc keys, and public-facing text consistency.
- [Template And Generation Rules](dsl-style-guide/templates.md): Jinja style,
  generated output ownership, generated-config exceptions, and submod variants.

## Useful Rule For AI Agents

AI agents usually have some prior knowledge of Paradox DSL because it is
publicly discussed and widely modded. That prior knowledge is useful, but it is
not enough for project correctness. Version-specific API behavior, scope
semantics, GUI behavior, and this repository's generation pipeline must be
checked locally.

Useful rule:

- AI may have language prior knowledge.
- AI does not have project semantic prior knowledge unless the project
  documents it.
