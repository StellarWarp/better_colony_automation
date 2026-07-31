# Parallel Construction Patch Development

## Layout

- `src/`: feature scanner, patch transaction logic, reviewed helper source,
  payload, and current-version manifest.
- `tests/`: synthetic PE, helper, ASLR, apply, restore, and path-prompt tests.
- `build_release.py`: reproducible PyInstaller one-file build.
- `dist/`: generated standalone executable; not committed.
- `descriptor.mod`, `workshop_en.txt`, and `workshop_cn.txt`: Workshop metadata.
- `assets/construction_queue.png` and `build_thumbnail.py`: deterministic
  thumbnail source and builder; no `thumbnail_0.png` intermediary.
- `Install Patch.bat` and `Restore Original.bat`: double-click user entry
  points.

Crash dumps, local application receipts, and other machine-specific evidence
remain under `tools/patches/` and are not included in the Workshop package.

## Build

```powershell
conda run -n better_colony_automation python -m pip install `
  -r submods/colony_automation_parallelize_patch/requirements-build.txt

conda run -n better_colony_automation python `
  submods/colony_automation_parallelize_patch/build_release.py
```

The build runs the submod tests and verifies that the generated EXE can start.

Build the Workshop thumbnail directly:

```powershell
conda run -n better_colony_automation python `
  submods/colony_automation_parallelize_patch/build_thumbnail.py
```

## Local Package Publication

Preview:

```powershell
conda run -n better_colony_automation python scripts/publish_mod.py `
  --dry-run --package colony_automation_parallelize_patch
```

Publish to the local Stellaris Mod directory:

```powershell
conda run -n better_colony_automation python scripts/publish_mod.py `
  --package colony_automation_parallelize_patch
```

The publisher copies only the declared release files and synchronizes the
external launcher `.mod` descriptor. User-generated patch receipts are not
deleted.

## Workshop Description

Preview:

```powershell
conda run -n better_colony_automation python scripts/update_steam_workshop.py `
  --package colony_automation_parallelize_patch --preview
```

Submit:

```powershell
conda run -n better_colony_automation python scripts/update_steam_workshop.py `
  --package colony_automation_parallelize_patch --submit --headless
```

Content upload remains a manual Paradox Launcher operation.
