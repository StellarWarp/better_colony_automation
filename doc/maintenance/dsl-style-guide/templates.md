# Template And Generation Rules

See also:

- [DSL Style Guide](../dsl-style-guide.md)
- [Generation Pipeline](../../architecture/generation-pipeline.md)
- [Maintenance Playbook](../playbook.md)

## Jinja Template Style

Templates are code. Optimize them for safe maintenance, not only for output.
Generated PDX-like output is formatted by the renderer, so template authors
should prioritize template readability, ownership clarity, and maintainable
Jinja structure over matching final output indentation exactly.

Rules:

- Prefer explicit macro parameters.
- Put each macro argument on its own line for non-trivial calls.
- Extract repeated coordinates, sizes, gaps, and row heights into variables.
- Use arithmetic for layout relationships instead of duplicating magic numbers.
- Keep shell macros and business component macros separate.
- Keep generated output readable enough for review, but rely on output
  formatting for routine PDX indentation cleanup.
- Do not put generated-config business data directly into templates if it
  belongs in `configs/` or parser output.

For large mechanical template changes such as broad indentation cleanup, use
the explicit template formatter:

```powershell
conda run -n better_colony_automation python mod_builder/format_templates.py
```

This formatter targets PDX-like Jinja templates under `mod_builder/templates/`.
It intentionally skips localisation and generated-config templates where
indentation or quoted strings may carry different meaning.

## Generated Output Rules

When editing runtime files:

- first check whether a same-named `.txt.j2` template exists under
  `mod_builder/templates/`; if it does, the runtime `.txt` is generated output
  and should not be read or edited directly
- normal `rg` searches skip generated runtime files through repository and
  directory `.rgignore` files; use source templates/config/parser files for
  routine search and avoid bypassing `.rgignore` unless proving a renderer
  defect or a narrow source-to-output mismatch
- if no matching template is found and a runtime `.txt` must be inspected, read
  only the first five lines first to check for ownership metadata
- generated warning header answers "can I edit this file directly?"
- if the answer is no, go to the template, handwritten config, or
  parser/extraction tool
- do not patch generated runtime output as the only fix
- do not hand-edit `mod_builder/templates/generated_configs/` unless the file
  is explicitly documented as a handwritten exception

When changing templates:

- let the file watcher or generator update runtime outputs
- let `mod_builder/generate.py` maintain generated-output blocks in `.rgignore`
  files; do not hand-maintain those blocks
- treat a successful generator run as sufficient generated-output validation
  for normal maintenance
- do not review generated output bodies unless a renderer defect is suspected
  or a narrow source-to-output mismatch must be proven
- test in game after re-entering, because Stellaris logic does not hot reload

## Generated-Config Exceptions

`mod_builder/templates/generated_configs/` is primarily generated input for the
Jinja renderer. Most files there must be changed through `mod_builder/configs/`,
`mod_builder/parse/`, or `mod_builder/synthetipy/`.

Current explicit handwritten exception:

- `mod_builder/templates/generated_configs/support_layout.yaml`

That file stores support-panel build/layout values shared by GUI rendering and
DDS generation. If more handwritten build config is needed, prefer moving it to
`mod_builder/configs/` rather than adding more exceptions under
`templates/generated_configs/`.

## Shared Economic Row Config

The economic-management rows are maintained in
`mod_builder/configs/global_settings_economic_rows.yaml`. Each row owns its
identity, runtime variable, localization keys, effect names, and adjustment
steps. The GUI, button effects, scripted localization, and shared numeric
localization are generated from this file.

When several rows use the same steps, define the YAML anchor on the first
representative row and reference it from later rows. For example, `energy`
defines `&standard_steps`, and `minerals` references it with
`steps: *standard_steps`. This keeps the configuration order aligned with the
reader's first encounter with the shared profile.

Use an explicit `steps` list when a row needs independent increments. Each step
must provide an `id`, localization key (`text`), display string (`label`), and
numeric delta (`value`). The sign of `value` determines whether the generated
button is placed in the decrease or increase group. Keep the generated copy in
`templates/generated_configs/` out of manual edits; rerun the config builder and
generator after changing the handwritten source.

## Submod GUI Variants

GUI files are whole-file definitions, not incremental patches. A submod GUI
variant should be produced through template compile variants instead of a
handwritten fork.

Rules:

- Put submod ownership and compile-variant metadata on the source template, not
  on generated runtime output.
- Use `# compile_variants main <submod>` when the main mod and submod both need
  IDE-visible generated GUI files.
- Use the generated `file_name` metadata so publication can rename the submod
  variant back to the override filename.
