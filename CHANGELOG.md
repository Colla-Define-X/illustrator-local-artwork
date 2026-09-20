# Changelog

All notable changes to this skill are documented here. Versions follow
[Semantic Versioning](https://semver.org/), and Git tags use the `vX.Y.Z` form.

## [Unreleased]

### Added

- Chinese README covering installation, usage, in-place layer behavior, deliverables, rollback, and validation.

## [0.2.0-rc.1] - 2026-09-20

### Changed

- Save the supplied Illustrator file in place instead of creating an output AI copy.
- Duplicate the mapped target layer, name it with the `aicreate-` prefix, replace artwork only in the duplicate, and hide the original layer for rollback.
- Automatically select the best technically valid, visually matched candidate instead of requiring an approval round trip.
- Replace full inventory auditing with in-script fast verification and a final preview export.
- Limit user-facing deliverables to the updated AI and final preview; keep jobs, candidates, JSX, and diagnostics internal.

## [0.1.0] - 2026-09-20

### Added

- Initial versioned release of the Illustrator local artwork workflow.
- Candidate validation, preview generation, approved placement, and post-placement audit scripts.
- Job manifest schema and Codex UI metadata.

[Unreleased]: https://github.com/Colla-Define-X/illustrator-local-artwork/compare/v0.2.0-rc.1...HEAD
[0.2.0-rc.1]: https://github.com/Colla-Define-X/illustrator-local-artwork/releases/tag/v0.2.0-rc.1
[0.1.0]: https://github.com/Colla-Define-X/illustrator-local-artwork/releases/tag/v0.1.0
