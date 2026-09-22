# Changelog

All notable changes to this skill are documented here. Versions follow
[Semantic Versioning](https://semver.org/), and Git tags use the `vX.Y.Z` form.

## [Unreleased]

## [0.2.0-rc.5] - 2026-09-22

### Added

- Add Windows and macOS installation entrypoints with isolated Python environments.
- Add read-only runtime/MCP configuration diagnostics and portable setup instructions.
- Add allowlisted ZIP packaging with per-file SHA-256 verification.

### Changed

- Preserve macOS path case; use encoded File URIs for Unicode and literal percent asset filenames.
- Reject ambiguous percent-escape source AI paths before any document mutation.
- Read UTF-8 BOM jobs and emit UTF-8 CLI output on both platforms.
- Distinguish path, configuration, and tool-call corrections from image-generation attempts.
- Permit a low-cost deterministic repair before the single allowed regeneration when visual requirements remain unchanged.
- Keep schema v3 and existing artwork replacement/version-layer behavior.

## [0.2.0-rc.4] - 2026-09-21

### Fixed

- Scope generated layers by page or independent replacement region.
- Hide only older versions with the exact same `scope_id`; preserve other pages and legacy unscoped layers.
- Require and validate a safe stable target scope identifier in schema-v3 jobs.

## [0.2.0-rc.3] - 2026-09-21

### Fixed

- Create an empty `aicreate-*` sibling layer for the replacement instead of copying the complete source layer.
- Keep the source layer visible and hide only the mapped original artwork objects.
- Preserve earlier generated layers as hidden rollback versions.

## [0.2.0-rc.2] - 2026-09-21

### Added

- Single-candidate schema v3 with one technical retry at most.
- Deterministic generation-prompt priority for explicit user constraints.
- Lightweight source-tone profiling and restrained automatic tone matching with preserved alpha.
- Iterative layer versioning that hides older `aicreate-*` layers without deleting them.

### Changed

- Generate one result per user-visible iteration instead of three candidates.
- Let explicit user tone or preservation requirements override source-tone and variation defaults.

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

[Unreleased]: https://github.com/Colla-Define-X/illustrator-local-artwork/compare/v0.2.0-rc.5...HEAD
[0.2.0-rc.5]: https://github.com/Colla-Define-X/illustrator-local-artwork/releases/tag/v0.2.0-rc.5
[0.2.0-rc.4]: https://github.com/Colla-Define-X/illustrator-local-artwork/releases/tag/v0.2.0-rc.4
[0.2.0-rc.3]: https://github.com/Colla-Define-X/illustrator-local-artwork/releases/tag/v0.2.0-rc.3
[0.2.0-rc.2]: https://github.com/Colla-Define-X/illustrator-local-artwork/releases/tag/v0.2.0-rc.2
[0.2.0-rc.1]: https://github.com/Colla-Define-X/illustrator-local-artwork/releases/tag/v0.2.0-rc.1
[0.1.0]: https://github.com/Colla-Define-X/illustrator-local-artwork/releases/tag/v0.1.0
