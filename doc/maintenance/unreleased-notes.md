# Unreleased Notes

This file is a temporary holding area for changes that should be reviewed when
preparing the next public release.

It is not the public changelog. Before release, fold the relevant items into
the player-facing surfaces listed in [Maintenance Playbook](playbook.md):
intro/update messages, `README.md`, descriptors, and Workshop descriptions.

## Pending Release Items

- Job regulation localisation: replaced Unicode bullet indicators in resource
  change tooltips with existing dot text icons, avoiding `?` glyphs in English
  font sets while preserving colored status markers.
- District construction planning: restored the single-build-plan guard by
  setting `bca_pf_has_district_build_plan` when a district build plan is chosen
  and clearing it during the monthly plan-flag reset.
- Zone auto-demolition disable sync: replaced per-`d1`/`d2`/`d3` secondary
  free-zone checks with a single aggregate secondary capacity check, avoiding
  accidental binding between mod district-slot semantics and the game's
  unstable numeric district indexes.
