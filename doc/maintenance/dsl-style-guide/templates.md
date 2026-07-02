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

- generated warning header answers "can I edit this file directly?"
- if the answer is no, go to the template, handwritten config, or
  parser/extraction tool
- do not patch generated runtime output as the only fix
- do not hand-edit `mod_builder/templates/generated_configs/` unless the file
  is explicitly documented as a handwritten exception

When changing templates:

- let the file watcher or generator update runtime outputs
- spot-check both the template and generated file
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
