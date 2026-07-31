# Maintenance Playbook

See also:

- [Development Setup](setup.md)
- [DSL Style Guide](dsl-style-guide.md)
- [GUI And Tooltip Rules](dsl-style-guide/gui.md)
- [Localisation Rules](dsl-style-guide/localisation.md)
- [Template And Generation Rules](dsl-style-guide/templates.md)
- [Change Entrypoints](change-entrypoints.md)
- [Generation Pipeline](../architecture/generation-pipeline.md)
- [Runtime Flow](../architecture/runtime-flow.md)

## Goal

This document is written for future AI agents and contributors making changes under time pressure.

Development reality:

- Stellaris mod logic does not hot reload.
- Every logic change must be validated by re-entering the game.
- Event-window tests are the fastest feedback loop for scripted logic.
- Use IntelliJ IDEA if possible, and pair it with a file watcher that re-renders templates on save.

## Before You Edit Anything

1. Complete [Development Setup](setup.md), including the
   `.config/stellaris` link used for local DSL reference and validation.
2. Classify the change by layer: config/frontend, template, game logic, presentation, or documentation.
3. Check whether the file is generated. Generated warning headers are the first edit-site signal.
4. If generated, go back to the template, handwritten config, or parser/extraction tool.
5. Check whether the same behavior also has handwritten siblings.
6. If DSL syntax, scope, GUI behavior, or API usage is uncertain, check
   [DSL Style Guide](dsl-style-guide.md): use the Stellaris user document
   `logs/script_documentation` first, then `.config/stellaris/` when the
   official document is unclear, then matching usage in project or game
   scripts.

When inspecting `.txt` runtime DSL files, first check whether a same-named
`.txt.j2` file exists under `mod_builder/templates/`. If it exists, the `.txt`
file is generated output; do not read or edit the runtime `.txt` body, and use
the template as the edit site.

Normal `rg` searches intentionally skip generated runtime `.txt` and `.yml` files because
`mod_builder/generate.py` maintains those paths in the repository `.rgignore`.
This keeps routine searches focused on source files and handwritten runtime
hotspots. Do not bypass `.rgignore` during normal development. Generated-output
inspection is an exception only for suspected renderer defects or narrow
source-to-output mismatch investigations; return to the source template, config,
or parser before editing. If generation fails, inspect the traceback, template,
config, or parser source rather than the stale generated output.

If no matching template is found and a `.txt` file must be inspected, read only
the first five lines first. Generated files should identify their source
template near the top; use that source as the edit site.

After template changes, a successful generation run is sufficient generated
output validation for normal maintenance. Do not spend time reviewing large
generated `.txt` or `.yml` bodies unless a renderer defect is suspected or a narrow
source-to-output mismatch must be proven.

Useful starting questions:

- "Am I changing runtime execution, state naming, UI behavior, ranking data, or automation categories?"
- "Am I looking at handwritten config in `configs/`, generated config in `templates/generated_configs/`, a template, or runtime output?"

## Change Recipes

### Change default zone preference

Start with:

1. [`../../mod_builder/configs/zone_type_fitness.yaml`](../../mod_builder/configs/zone_type_fitness.yaml)
2. [`../../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2`](../../mod_builder/templates/common/script_values/bca_planet_setting_zone_ranking.txt.j2)
3. [`../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_0_effect.txt.j2)
4. [`../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_planet_setting_zones_1_effect.txt.j2)

Why:

- ranking affects default option ordering
- selector generation and current-layout sync must agree on the same type universe

### Change district ratio or manual district plan behavior

Start with:

1. [`../../common/button_effects/bca_planet_setting_zones_buttons_aux.txt`](../../common/button_effects/bca_planet_setting_zones_buttons_aux.txt)
2. [`../../mod_builder/templates/common/scripted_effects/bca_planet_district_setting_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_planet_district_setting_effect.txt.j2)
3. [`../../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2`](../../mod_builder/templates/common/script_values/bca_planet_setting_values.txt.j2)

### Change when construction starts

Start with:

1. [`../../common/scripted_triggers/bt_st_tool.txt`](../../common/scripted_triggers/bt_st_tool.txt)
2. [`../../events/bca_planet_monthly_iteration_entry.txt`](../../events/bca_planet_monthly_iteration_entry.txt)
3. relevant files under [`../../common/colony_automation_exceptions/`](../../common/colony_automation_exceptions/)

### Change zone replacement or removal behavior

Start with:

1. [`../../mod_builder/templates/events/bca_mix_zones_controller.txt.j2`](../../mod_builder/templates/events/bca_mix_zones_controller.txt.j2)
2. [`../../mod_builder/templates/common/scripted_effects/bca_controller_effect.txt.j2`](../../mod_builder/templates/common/scripted_effects/bca_controller_effect.txt.j2)
3. [`../../common/colony_automation/500_bca_mixed_zones.txt`](../../common/colony_automation/500_bca_mixed_zones.txt)

### Change building demolition

Start with:

- [`../../common/scripted_effects/bca_building_destruction.txt`](../../common/scripted_effects/bca_building_destruction.txt)

Do not start in templates unless you confirm the target building logic is generated elsewhere.

### Change default auto-demolition behavior

Start with:

1. [`../../common/button_effects/bca_global_settings_panel.txt`](../../common/button_effects/bca_global_settings_panel.txt)
2. [`../../mod_builder/templates/events/bca_update_default_selection.txt.j2`](../../mod_builder/templates/events/bca_update_default_selection.txt.j2)
3. [`../../events/bca_auto_destruction_global_events.txt`](../../events/bca_auto_destruction_global_events.txt)
4. related files under [`../../localisation/`](../../localisation/)

Important distinction:

- the global settings panel writes country flags for default behavior
- the same panel triggers bulk country-level application flows for
  already-owned colonies, which then fan out into per-colony `carrier_event`
  work

### Change empire settings center GUI

Start with:

1. [`../../mod_builder/templates/component/event_gui_shell.j2`](../../mod_builder/templates/component/event_gui_shell.j2)
2. [`../../mod_builder/templates/component/global_settings_components.j2`](../../mod_builder/templates/component/global_settings_components.j2)
3. [`../../mod_builder/templates/interface/bca_global_setting_panel.gui.j2`](../../mod_builder/templates/interface/bca_global_setting_panel.gui.j2)
4. [`../../events/bca_global_settings_events.txt`](../../events/bca_global_settings_events.txt)

Rules:

- shell macro owns required hidden/displaced event-window fields
- content macro owns visible business controls
- dynamic GUI tooltips should use one button-effect `custom_tooltip` that calls
  scripted loc through localisation; GUI `tooltipText` is not reliable for
  scripted loc
- auto-demolition now has one public entry point: the global settings panel
- GUI display text must use `BCA_GLOBAL_SETTINGS_*` localisation keys
- custom GUI must not reuse legacy `policy_*` public-entry text

## Common Hazards

### Editing generated output only

Risk:

- future regeneration silently discards the fix
- normal `rg` searches may not show generated `.txt` or `.yml` output, so a missing
  result is not evidence that no generated runtime block exists

Mitigation:

- read the generated warning header
- find the matching template or generator input
- update the source layer, then regenerate
- treat a successful generation run as the generated-output check unless the
  failure is specifically about renderer output shape

### Editing generated-config YAML directly

Risk:

- later copy/generation steps overwrite the change

Mitigation:

- edit `mod_builder/configs/` for handwritten config changes
- edit `mod_builder/parse/` or `mod_builder/synthetipy/` for extracted config logic
- never hand-edit `mod_builder/templates/generated_configs/` unless the file is
  explicitly documented as a handwritten exception

### Breaking custom event GUI shell invariants

Risk:

- event window opens blank
- close behavior breaks
- hidden vanilla event controls bleed into view

Mitigation:

- keep hidden/displaced required event fields centralized in `event_gui_shell.j2`
- update shell first when event GUI structure breaks
- keep business controls isolated from shell-only compatibility fields

### State sync bugs

Typical trigger points:

- colonization
- planet transfer
- planet class change
- building/zone/district completion

When debugging plan-related behavior, inspect synchronization hooks before changing planner math.

## Suggested Debugging Order

1. Confirm the event/effect is reached.
2. Confirm gating triggers pass.
3. Confirm internal plan flags/variables are set as expected.
4. Confirm automation categories consume those flags.
5. Confirm cleanup does not immediately erase state.
6. If generated-config values look wrong, confirm whether the issue starts in `configs/`, `parse/`, or `synthetipy/`.

## Testing Workflow

For scripted logic, prefer a dedicated test event such as [`../../events/test_event.txt`](../../events/test_event.txt) and trigger it manually from the in-game event window.

For template changes, rely on a file watcher to regenerate outputs before re-entering the game.

For auto-demolition changes, test both paths:

- global-settings defaults on a newly initialized or reset planet
- global-settings bulk application on already initialized planets

## Local Generation And Publication

Before running build commands, check the available Conda environments and use
the project environment described in [Development Setup](setup.md).

`mod_builder/generate.py` renders runtime files, normalizes localisation
encoding, and then publishes using `scripts/publish_mod.py` with quiet output.
Do not run it casually if the configured Stellaris mod target directories
should not be touched.

```powershell
conda run -n better_colony_automation python mod_builder/generate.py
```

To inspect publication behavior without copying files, run the publisher
directly with `--dry-run`:

```powershell
conda run -n better_colony_automation python scripts/publish_mod.py --dry-run
```

Targets and per-package root files are configured in
[`../../scripts/publish_mod.yaml`](../../scripts/publish_mod.yaml).

With no package argument, `publish_mod.py` publishes every configured package.
Use `--package` to limit which package is copied.

Publication cleans only configured generated/runtime paths in each target
directory before copying the current package. The default clean set is:

- `common`
- `events`
- `gfx`
- `interface`
- `descriptor.mod`
- `license`
- `thumbnail.png`

Useful package-specific checks:

```powershell
conda run -n better_colony_automation python scripts/publish_mod.py --dry-run --package main
conda run -n better_colony_automation python scripts/publish_mod.py --dry-run --package job_regulation
conda run -n better_colony_automation python scripts/publish_mod.py --dry-run --package colony_automation_parallelize_patch
```

Packages may declare `launcher_descriptor` in `publish_mod.yaml`. The
publisher then derives the external launcher `.mod` file from the package's
published `descriptor.mod` and appends the resolved target `path`. This keeps
launcher metadata synchronized without treating the external descriptor as a
second hand-maintained source.

Publication ownership comes from the first line of source templates, not from
manual edits to generated runtime files.

## Release Workflow

When preparing a public release, update these in one pass:

1. Review [`unreleased-notes.md`](unreleased-notes.md) and decide which items
   should become public release notes.
2. Bump the version flag in [`../../events/bca_intro_event.txt`](../../events/bca_intro_event.txt).
3. Update `MESSAGE_BCA_UPDATE_desc_verson` and prepend the latest `MESSAGE_BCA_STARTUP_desc_log_v*` entry in relevant files under [`../../localisation/`](../../localisation/).
4. Bump the version string in [`../../descriptor.mod`](../../descriptor.mod).
5. Update the public-facing changelog in [`../../README.md`](../../README.md).
6. Update and review the bilingual Workshop descriptions in the selected package directory. The main package uses the repository root; submods use `submods/<package>/`.

Release note rule:

- keep the intro popup short and player-facing
- keep `README.md` slightly more descriptive
- keep each package's `workshop_en.txt` and `workshop_cn.txt` focused on current features rather than detailed version history
- clear or roll forward `unreleased-notes.md` after the release notes have been
  folded into public surfaces
- if a release changes global settings behavior, mention both the new default behavior and the primary entry point

## Documentation Maintenance Rule

When changing behavior, update whichever docs become stale:

- runtime order changes -> [`../architecture/runtime-flow.md`](../architecture/runtime-flow.md)
- state semantics changes -> [`../architecture/state-model.md`](../architecture/state-model.md)
- generator inputs/outputs change -> [`../architecture/generation-pipeline.md`](../architecture/generation-pipeline.md)
- DSL conventions change -> [`dsl-style-guide/dsl-core.md`](dsl-style-guide/dsl-core.md)
- GUI or tooltip conventions change -> [`dsl-style-guide/gui.md`](dsl-style-guide/gui.md)
- localisation conventions change -> [`dsl-style-guide/localisation.md`](dsl-style-guide/localisation.md)
- Jinja or generated-output conventions change -> [`dsl-style-guide/templates.md`](dsl-style-guide/templates.md)
- development prerequisites or external tool setup change -> [`setup.md`](setup.md)
- common change entrypoints change -> [`change-entrypoints.md`](change-entrypoints.md)
