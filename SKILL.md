---
name: illustrator-local-artwork
description: Generate and automatically select reference-matched transparent artwork, replace a mapped Illustrator region on an aicreate-prefixed duplicate layer, hide the original layer, save the same AI file in place, and return only the AI and final preview. Use for local motif, ornament, object, or illustration replacement; do not use for text/date updates or full-layout generation.
metadata:
  version: "0.2.0-rc.1"
---

# Illustrator Local Artwork

Use the built-in image generator for raster candidates and the configured Illustrator MCP for inspection, placement, saving, and preview export. Modify the supplied AI in place only when the user has authorized that behavior. Preserve rollback inside the document by retaining the original layer as hidden.

## Workflow

1. Confirm the source AI, internal work directory, target layer/group, target bounds, and creative brief. The source AI is also the final AI.
2. Inspect the target once. For a new template or ambiguous target, stop after mapping suggestions instead of guessing.
3. Create an internal schema-v2 job using [references/schema.md](references/schema.md). Keep the job, prompts, candidates, JSX, and diagnostics under `.aicreate/<job-id>/`; do not present them as deliverables.
4. Generate three candidates by default. Require one isolated subject, no text or watermark, true alpha transparency, and adequate resolution.
5. Run `scripts/validate_job.py --stage candidates`. Reject technical failures, then visually rank the remaining candidates against the brief and reference. Set exactly one candidate to `selected`; do not ask the user to choose unless they explicitly request review.
6. Set the job status to `selected`, run `validate_job.py --stage place`, then generate trusted JSX with `scripts/build_placement_jsx.py`.
7. Open the source AI itself and call Illustrator MCP `run` with that exact absolute path as `target_path`. The JSX duplicates the target layer, gives the duplicate an `aicreate-` name, replaces artwork only inside the duplicate, hides the original layer, embeds the asset, saves in place, runs fast checks, and exports the final preview.
8. Return only the updated AI and final preview PNG. Do not attach or enumerate internal jobs, candidates, logs, JSX, or diagnostic files.

## Layer and placement rules

- Name the duplicate `aicreate-<original-layer-name>`; if occupied, append `-02`, `-03`, and so on.
- Keep the duplicate visible and unlocked. Hide the original layer only after the new artwork has been placed successfully.
- Default to `contain`; preserve aspect ratio and center the asset inside the mapped bounds.
- Permit `cover` only when the target parent is an existing clipping group and `allow_crop` is true.
- Place next to the mapped primary artwork, then remove only the mapped old raster items from the duplicate layer.
- Embed the selected asset unless the user explicitly requests a linked file.
- Do not alter text, dates, artboard geometry, or layers other than the original target layer and its duplicate.

## Fast verification and recovery

- Treat success as: exact document-path match, visible `aicreate-*` layer, hidden original layer, replacement inside the target for `contain`, embedded asset, successful in-place save, and readable final preview.
- Do not build full document inventories, hash the complete AI, fingerprint every protected layer, or produce an audit report unless the user explicitly requests strict auditing.
- On `outcome_unknown`, do not retry. Inspect Illustrator state first. If an `aicreate-*` layer already exists or the original layer is hidden, treat the operation as potentially applied and resolve from the actual document state.
- If all candidates fail or fast verification fails, keep internal diagnostics and report only a concise failure explanation.

## Commands

```powershell
python scripts/validate_job.py --job job.json --stage candidates
python scripts/validate_job.py --job job.json --stage place
python scripts/build_placement_jsx.py --job job.json --preview-png final-preview.png --output place-selected.jsx
```
