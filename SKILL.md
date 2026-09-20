---
name: illustrator-local-artwork
description: Generate reference-matched transparent artwork candidates for a mapped region in an Adobe Illustrator document, preview them, place only an explicitly approved candidate into a saved copy, and audit that unrelated content stayed unchanged. Use for local motif, ornament, object, or illustration replacement; do not use for text/date updates or full-layout generation.
metadata:
  version: "0.1.0"
---

# Illustrator Local Artwork

Use the built-in image generation tool for new raster candidates and the configured Illustrator MCP for document inspection, placement, previews, and readback. Keep generation, approval, placement, and audit as separate states.

## Workflow

1. Confirm the source AI, output directory, target region, and creative brief. Never overwrite the source AI.
2. Record the source SHA-256, byte length, modification time, document color space, target layer/group, target bounds, existing artwork indices, and protected-layer inventory.
3. Export or capture a local preview of the target page. Treat it as a style/layout reference, not an edit target.
4. Create a job manifest using [references/schema.md](references/schema.md). For a new template or ambiguous target, stop after mapping suggestions; do not modify Illustrator.
5. Generate three candidates by default. Require one isolated subject, no text, no watermark, and true alpha transparency. Save every kept candidate outside the image generator's default directory.
6. Run `scripts/validate_job.py --stage candidates`. Judge transparency from the PNG alpha channel, not the previewer's black/gray transparency canvas. Alpha maximum `254` is valid for watercolor-like semi-transparent edges; require transparent corners and sufficient subject opacity instead of requiring a `255` pixel. A genuinely failed alpha check may be repaired once with a dedicated background-removal tool. If it still fails, mark the candidate `rejected`.
7. Build target-area mockups with `scripts/build_preview_jsx.py` against a disposable AI copy. Export the preview, close that copy without saving, and present the valid candidates. Stop before final Illustrator mutation until the user explicitly selects one candidate.
8. Set only the selected candidate to `approved`, set `approved_candidate_id`, and run `validate_job.py --stage place`. The placement builder must refuse any unapproved job.
9. Copy the source to `output_ai`, open the saved copy, generate trusted JSX with `scripts/build_placement_jsx.py`, and call Illustrator MCP `run` with the absolute `target_path`.
10. Read back the document inventory, run `scripts/audit_artwork.py`, export an after-preview, and recompute the source hash.

## Placement rules

- Default to `contain`; preserve aspect ratio and center the asset inside the mapped bounds.
- Permit `cover` only when the target parent is an existing clipping group and `allow_crop` is true.
- Insert next to the primary artwork item so the original container and stacking context are preserved. Remove the mapped old raster items only after the new file has been placed successfully.
- Embed the approved asset unless the user explicitly requests a linked file.
- Do not alter text, dates, artboard geometry, or unrelated groups.

## Safety and recovery

- Treat configured protected layers such as `说明` and `刀线` as immutable. Any fingerprint difference fails the run.
- Always pass the open saved copy's absolute path as MCP `run.target_path`.
- On `outcome_unknown`, do not retry. Call `get_state`, inspect the document, record the partial result, then use `recover_connection(acknowledge=true)` only after verification.
- Approval applies to one candidate in one job. A prompt change, regenerated asset, changed target, or changed source hash invalidates that approval.
- Keep rejected candidates and the reason for rejection in the test log; do not present them as valid choices.

## Commands

```powershell
python scripts/validate_job.py --job job.json --stage candidates
python scripts/build_preview_jsx.py --job job.json --candidate-id A --preview-ai preview-working.ai --preview-png preview-a.png --output preview-a.jsx
python scripts/validate_job.py --job job.json --stage place
python scripts/build_placement_jsx.py --job job.json --output place-approved.jsx
python scripts/audit_artwork.py --job job.json --baseline baseline-inventory.json --actual actual-inventory.json --report audit-report.json
```
