# DSL Core Rules

See also:

- [DSL Style Guide](../dsl-style-guide.md)
- [Development Setup](../setup.md)
- [State Model](../../architecture/state-model.md)

## Reference Sources

Use these references in this order:

1. **`.config/stellaris/` rule files** are the primary source for Stellaris DSL
   syntax, effects, triggers, scopes, modifiers, and enums. These `.cwt` files
   define the authoritative API surface for the targeted game version. Follow
   [Development Setup](../setup.md) to link this path to the external
   `cwtools-stellaris-config` checkout.
2. The **Stellaris user document** under the Stellaris user data directory at
   `logs/script_documentation` is the secondary reference for API details and
   version-specific behavior. On Windows, the usual user data relative path is
   `Documents/Paradox Interactive/Stellaris/logs/script_documentation/`.
3. Existing game scripts are the gold sample for Paradox DSL style and
   engine-supported patterns.
4. Existing verified project code is the gold sample for project conventions.
5. Trusted mods can be used as examples for custom GUI and unusual script
   patterns.

Do not hardcode machine-specific absolute paths to `script_documentation` in
docs or comments. Describe it by location relative to the Stellaris user data
directory or use the Windows user-data relative path above. Paths to
`.config/stellaris/` should be relative to the workspace root.

## Official DSL Positioning

Paradox DSL is a content configuration layer, not a general-purpose programming
language.

For official development, complex abstractions live mostly in the C++ engine.
The script layer describes content, conditions, effects, weights, and UI
bindings inside the engine's exposed API.

Consequences:

- weak abstraction is expected
- runtime query APIs are limited
- complex behavior often needs precomputed data
- large generated enumerations can be appropriate

In this project, many large generated branches are intentional. The aim is not
to avoid enumeration entirely; the aim is to avoid handwritten enumeration.

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
- `event_target:*` when a custom GUI or scripted loc needs a stable scope
  reference

Carrier-flag rule:

- treat `carrier_flag` as the authoritative colony-local flag API
- do not document or reason about new logic as if it were using plain planet
  flags
- colony scope does not itself persist flags; the implementation mirrors the
  flag onto carrier and planet so lookups remain stable across colony-oriented
  code paths

Rules:

- Do not assume a GUI keeps the scope you expect; bind stable global event
  targets when needed.
- Prefer explicit `owner = { ... }` or `event_target:* = { ... }` blocks over
  relying on implicit scope transitions.
- If a button effect can be clicked from a planet panel but mutates country
  settings, make the planet-to-owner transition explicit.
- If a value displays in custom GUI and scope can drift, use a saved event
  target rather than `This` or broad `Owner` assumptions.

## Scripted Values And Variables

Do not confuse scripted values and variables.

Rules:

- `value:some_script_value` is for calling a scripted value.
- Plain variables should be referenced by their variable name, not through
  `value:`.
- If a variable display fails in scripted loc, first confirm whether the
  localisation scope is correct.

This bug class is easy to miss because syntax may parse while the displayed
value remains wrong.
