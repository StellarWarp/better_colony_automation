# Unreleased Notes

This file is a temporary holding area for changes that should be reviewed when
preparing the next public release.

It is not the public changelog. Before release, fold the relevant items into
the player-facing surfaces listed in [Maintenance Playbook](playbook.md):
intro/update messages, `README.md`, descriptors, and Workshop descriptions.

## Pending Release Items

- District planning UI: fixed detailed secondary district increment buttons so
  they are blocked when district auto-demolition is disabled and no secondary
  district quota is available.
- District auto-demolition disable behavior: disabling district demolition now
  clamps district plans to the current layout, clearing plan states that would
  otherwise imply district removal.
- Global settings panel: disabled event auto-selection so the custom settings
  event is not closed by the game's long-running event timeout.
- Early construction: added build-specific economic need triggers so planets
  with early construction enabled can prebuild planned districts, zones, and
  buildings even when the empire does not currently need that output, without
  changing job-regulation demand checks.
- District planning UI: fixed dynamic district and zone text lookups by using
  the colony scope in localisation, so primary/secondary district counts and
  zone icons no longer display stale or zero values from the wrong scope.
- District planning UI: updated the job regulation header icons and tooltips so
  automation rate uses the automated workforce icon, monthly job change uses the
  job icon, and transparent buttons still expose their tooltips.
- District planning UI: adjusted automation-rate value styling to use the muted
  grey display color in job regulation rows.
- Arcology candidate planning: aligned primary district counting with the
  arcology-candidate display scale while keeping existing build gates and
  secondary-district clearing behavior intact.
