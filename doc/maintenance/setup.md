# Development Setup

See also:

- [Maintenance Playbook](playbook.md)
- [DSL Style Guide](dsl-style-guide.md)

## Python Runtime Environment

The project build scripts should run inside the repository's Python environment.
Before assuming the environment name or creating a new one, inspect the local
Conda environments:

```powershell
conda env list
```

Look for a project-specific environment first. The current development
environment is commonly named:

```text
better_colony_automation
```

Use the environment's Python interpreter for build commands. If the active
shell does not expose `conda`, call the environment's `python.exe` directly
from the Conda installation. Do not commit machine-specific interpreter paths
to project files or documentation examples beyond illustrating the pattern.

## CWTools Stellaris Configuration

This project expects the Stellaris CWTools rule files to be available at:

```text
.config/stellaris/
```

The rule files are maintained in the
[DragonKnightOfBreeze/cwtools-stellaris-config](https://github.com/DragonKnightOfBreeze/cwtools-stellaris-config)
repository. Keep that repository as an external checkout and link its
`config/` directory into this project. Do not copy the rule files into the
project or commit the external repository.

### 1. Clone The Rule Repository

Choose a tools or source directory outside this project and run:

```powershell
$CwtoolsRepository = Join-Path `
  $HOME `
  "source\repos\cwtools-stellaris-config"

New-Item `
  -ItemType Directory `
  -Force `
  -Path (Split-Path $CwtoolsRepository)

git clone https://github.com/DragonKnightOfBreeze/cwtools-stellaris-config.git `
  $CwtoolsRepository
```

The path above is an example under the current user's home directory. A
different external checkout location may be assigned to
`$CwtoolsRepository`. Do not record its resolved machine-specific path in
project documentation or configuration committed to Git.

### 2. Create The Project Link On Windows

Run the following commands from the project root:

```powershell
$CwtoolsRepository = Join-Path `
  $HOME `
  "source\repos\cwtools-stellaris-config"

New-Item `
  -ItemType Directory `
  -Force `
  -Path .config

New-Item `
  -ItemType SymbolicLink `
  -Path .config\stellaris `
  -Target (Join-Path $CwtoolsRepository "config")
```

Creating a symbolic link may require Windows Developer Mode or an elevated
PowerShell session. If symbolic links are unavailable, a directory junction
can be used for a local checkout:

```powershell
New-Item `
  -ItemType Junction `
  -Path .config\stellaris `
  -Target (Join-Path $CwtoolsRepository "config")
```

The link command intentionally fails when `.config/stellaris` already exists.
Inspect the existing path and its target before replacing it.

### 3. Create The Project Link On Unix-Like Systems

Run the following commands from the project root:

```bash
CWTOOLS_REPOSITORY="$HOME/src/cwtools-stellaris-config"
git clone \
  https://github.com/DragonKnightOfBreeze/cwtools-stellaris-config.git \
  "$CWTOOLS_REPOSITORY"

mkdir -p .config
ln -s "$CWTOOLS_REPOSITORY/config" .config/stellaris
```

### 4. Verify The Setup

On Windows:

```powershell
Get-Item .config\stellaris |
  Format-List FullName,LinkType,Target

Get-ChildItem `
  -Path .config\stellaris `
  -Filter *.cwt `
  -Recurse |
  Select-Object -First 5
```

The first command should report a link whose target ends in
`cwtools-stellaris-config\config`. The second command should return CWTools
rule files.

## Updating The Rules

Update the external checkout independently from this project:

```powershell
$CwtoolsRepository = Join-Path `
  $HOME `
  "source\repos\cwtools-stellaris-config"

git -C $CwtoolsRepository pull --ff-only
```

Because `.config/stellaris` points to that checkout, the project immediately
uses the updated rule files. Review rule changes when the supported Stellaris
version changes, because updated validation rules may expose obsolete DSL APIs
or scope assumptions in existing scripts.

## Repository Ownership

- `.config/` is local development state and is ignored by this repository.
- `.config/stellaris` must point to the external repository's `config/`
  directory.
- Changes to this project's DSL belong in project source files, templates, or
  generators.
- Changes to CWTools rule definitions belong in the external rule repository
  and should follow its contribution process.
