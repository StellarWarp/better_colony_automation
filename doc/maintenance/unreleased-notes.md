# Unreleased Notes

This file is a temporary holding area for changes that should be reviewed when
preparing the next public release.

It is not the public changelog. Before release, fold the relevant items into
the player-facing surfaces listed in [Maintenance Playbook](playbook.md):
intro/update messages, `README.md`, descriptors, and Workshop descriptions.

## Unreleased

- Fixed missing localisation.
- Fixed Global Settings layout issues.
- Fixed an automated workforce statistics bug.
- Fixed secondary district planning controls when specialization demolition is disabled.

## Released In v2.1.0 (2026-07-31)

- Reworked economic-management rows into a shared configuration that generates
  the GUI, effects, scripted localisation, and shared numeric labels.
- Added live economic stockpile and income values plus a persistent main-screen
  entry for BCA Global Settings.
- Changed construction planning to use every free native construction slot;
  job regulation remains independent of construction queue availability.
- Added the optional `Colony Automation: Parallel Construction Patch` Windows
  utility for Stellaris 4.4.6, with explicit in-game installation and recovery
  guidance.
- Fixed Nomad Arkship secondary-district ordering and fortress-building support
  for its combat specializations.
- Fixed secondary-district plan synchronization after construction and made the
  designation reset explicitly enable district-specialization demolition before
  rebuilding its plan.
