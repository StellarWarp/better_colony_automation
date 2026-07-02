# Localisation Rules

See also:

- [DSL Style Guide](../dsl-style-guide.md)
- [GUI And Tooltip Rules](gui.md)
- [Maintenance Playbook](../playbook.md)

## Language Coverage

Player-facing text changes should update every supported localisation file in
the same pass.

Current required languages:

- `english`
- `simp_chinese`
- `japanese`
- `russian`

Do not leave new keys defined only in the language used during development.
Missing keys are easy to miss when the local test language is not changed.

## Encoding

Stellaris localisation files should be UTF-8 with BOM.

Rules:

- Use UTF-8 BOM for files under `localisation/`.
- `mod_builder/generate.py` normalizes localisation encoding at the end of a
  full generation run.
- If localisation files are edited by hand and generation is not run, normalize
  the touched files before testing in game.

## Scripted Loc Keys

Scripted loc should be hidden behind stable localisation keys.

Rules:

- GUI-facing keys may call scripted loc, for example
  `"[From.bca_support_display_image]"`.
- For dynamic tooltip text, use one effect-side `custom_tooltip` key that calls
  scripted loc. Do not rely on GUI `tooltipText` to evaluate scripted loc.
- Provide an explicit empty fallback key when a dynamic scripted-loc tooltip
  should display nothing.

## Template Placement

Generated localisation templates should keep language-specific content in the
matching language directory under `mod_builder/templates/localisation/`.

Rules:

- Put shared, language-neutral generated structure in common localisation
  templates only when it contains no translated text.
- Put translated keys, comments, and language-specific phrasing in
  `mod_builder/templates/localisation/<language>/`.
- Do not add Chinese or other language-specific text to a template that is used
  to generate every supported language.

## Public Text Style

Keep public-facing text consistent with the surface:

- in-game control labels should stay short
- tooltips can be playful but must explain the immediate interaction
- Workshop text should be clearer and less dense than internal documentation
- support/donation text should not imply gameplay features are paywalled
