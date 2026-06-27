# DSL Style Guide

See also:

- [Maintenance Playbook](playbook.md)
- [Generation Pipeline](../architecture/generation-pipeline.md)
- [State Model](../architecture/state-model.md)

## Purpose

This guide records project-level rules for writing Paradox/Stellaris DSL and Jinja templates.

The goal is not to teach the whole language. The goal is to reduce errors from scope confusion, weak runtime checks, generated-file ownership, and template complexity.

## Reference Sources

Use these references in this order:

1. **`.config/stellaris/` rule files** are the primary source for Stellaris DSL
   syntax, effects, triggers, scopes, modifiers, and enums. These `.cwt` files
   define the authoritative API surface for the targeted game version.
2. The **Stellaris user document** (`%USERPROFILE%\Documents\Paradox
   Interactive\Stellaris\logs\script_documentation` on Windows) is the
   secondary reference for API details and version-specific behavior.
3. Existing game scripts are the gold sample for Paradox DSL style and
   engine-supported patterns.
4. Existing verified project code is the gold sample for project conventions.
5. Trusted mods can be used as examples for custom GUI and unusual script
   patterns.

Do not hardcode machine-specific absolute paths to `script_documentation` in
docs or comments. Describe it by location relative to the Stellaris user
document/logs directory. Paths to `.config/stellaris/` should be relative to
the workspace root.

AI agents usually have some prior knowledge of Paradox DSL because it is publicly discussed and widely modded. That prior knowledge is useful, but it is not enough for project correctness. Version-specific API behavior, scope semantics, and this repository's generation pipeline must be checked locally.

Useful rule:

- AI may have language prior knowledge.
- AI does not have project semantic prior knowledge unless the project documents it.

## Official DSL Positioning

Paradox DSL is a content configuration layer, not a general-purpose programming language.

For official development, complex abstractions live mostly in the C++ engine. The script layer describes content, conditions, effects, weights, and UI bindings inside the engine's exposed API.

Consequences:

- weak abstraction is expected
- runtime query APIs are limited
- complex behavior often needs precomputed data
- large generated enumerations can be appropriate

In this project, many large generated branches are intentional. The aim is not to avoid enumeration entirely; the aim is to avoid handwritten enumeration.

## Scope Rules

Scope is the main correctness risk.

Always identify the current scope before writing a trigger or effect:

- `carrier` or colony-oriented execution paths for colony-local automation
  state, especially `carrier_flag`
- `planet` scope for planet data such as districts, zones, buildings, and any
  logic that still truly depends on planet-native APIs
- `country` scope for empire flags, global settings variables, edicts, and
  country events
- `owner` when starting from a colony/planet and needing country state
- `event_target:*` when a custom GUI or scripted loc needs a stable scope reference

Carrier-flag rule:

- treat `carrier_flag` as the authoritative colony-local flag API
- do not document or reason about new logic as if it were using plain planet
  flags
- colony scope does not itself persist flags; the implementation mirrors the
  flag onto carrier and planet so lookups remain stable across colony-oriented
  code paths

Rules:

- Do not assume a GUI keeps the scope you expect; bind stable global event targets when needed.
- Prefer explicit `owner = { ... }` or `event_target:* = { ... }` blocks over relying on implicit scope transitions.
- If a button effect can be clicked from a planet panel but mutates country settings, make the planet-to-owner transition explicit.
- If a value displays in custom GUI and scope can drift, use a saved event target rather than `This` or broad `Owner` assumptions.

## Scripted Values And Variables

Do not confuse scripted values and variables.

Rules:

- `value:some_script_value` is for calling a scripted value.
- Plain variables should be referenced by their variable name, not through `value:`.
- If a variable display fails in scripted loc, first confirm whether the localisation scope is correct.

This bug class is easy to miss because syntax may parse while the displayed value remains wrong.

## Scripted Loc And GUI Text

Scripted loc is useful for displaying computed state, but GUI text controls do not all behave the same.

Project conventions:

- Use scripted loc for compact state display such as enabled/disabled planet counts.
- When plain text controls fail to resolve variables reliably, use the verified `effectButtonType` display pattern.
- Display-only `effectButtonType` controls should visually behave like text and should not perform business effects.
- Keep value display localisation in GUI-specific keys, usually under `BCA_GLOBAL_SETTINGS_*`.

## Tooltips And Hidden Effects

Player-facing button effects should not expose raw implementation details.

Rules:

- Use `custom_tooltip` for the text players should see.
- Put implementation effects inside `hidden_effect` when raw effect output should not be shown.
- For one-shot bulk actions, do not style buttons as persistent state toggles.
- For selected/default state buttons, make the highlighted state match the text shown on the button.

## Event GUI Rules

Custom event GUI is fragile because the engine expects several vanilla event-window fields.

Rules:

- Keep required shell fields centralized in `mod_builder/templates/component/event_gui_shell.j2`.
- Keep business controls in content/component templates.
- Do not copy hidden/displaced vanilla event fields into business GUI templates.
- If an event GUI opens blank, loses close behavior, or crashes surrounding UI, inspect the shell first.
- Event GUI scope should be stabilized with event targets when controls read country-level state.

## Jinja Template Style

Templates are code. Optimize them for safe maintenance, not only for output.

Rules:

- Prefer explicit macro parameters.
- Put each macro argument on its own line for non-trivial calls.
- Extract repeated coordinates, sizes, gaps, and row heights into variables.
- Use arithmetic for layout relationships instead of duplicating magic numbers.
- Keep shell macros and business component macros separate.
- Keep generated output readable enough for review.
- Do not put generated-config business data directly into templates if it belongs in `configs/` or parser output.

## Generated Output Rules

When editing runtime files:

- generated warning header answers "can I edit this file directly?"
- if the answer is no, go to the template, handwritten config, or parser/extraction tool
- do not patch generated runtime output as the only fix
- do not hand-edit `mod_builder/templates/generated_configs/`

When changing templates:

- let the file watcher or generator update runtime outputs
- spot-check both the template and generated file
- test in game after re-entering, because Stellaris logic does not hot reload
