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

For a delivery build, create the release tag only after all intended entries are versioned. Build the lightweight
archive with `python scripts/build_delivery.py --output dist/illustrator-local-artwork.zip`.
It contains an allowlisted skill payload and a SHA-256 manifest, excluding environments,
personal settings and artwork. Keep TESTING.md accurate about local, CI and real-Adobe
checks separately. Rebuild the ZIP after updating documentation or code.

- PATCH: compatible fixes or instruction clarifications.
- MINOR: compatible new workflows, scripts, or schema capabilities.
- MAJOR: incompatible manifest, command, or workflow changes.
