# Releasing

This repository uses Semantic Versioning, including `-rc.N` prereleases for
Illustrator integration testing. Keep the version in `VERSION` and `SKILL.md`
(`metadata.version`) identical.

1. Move the intended entries from `CHANGELOG.md` under `[Unreleased]` into a
   new `X.Y.Z` section dated `YYYY-MM-DD`.
2. Update `VERSION` and `SKILL.md` to `X.Y.Z`.
3. Run the skill validator and the script smoke checks.
4. Commit with `Release X.Y.Z`.
5. Create an annotated tag such as `vX.Y.Z` or `vX.Y.Z-rc.N`.
6. Push the branch and tag, then create the GitHub release from that tag.

Version increments:

- PATCH: compatible fixes or instruction clarifications.
- MINOR: compatible new workflows, scripts, or schema capabilities.
- MAJOR: incompatible manifest, command, or workflow changes.
