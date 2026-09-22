---
name: illustrator-local-artwork
description: Generate one reference-matched transparent artwork at a time, locate the exact Illustrator object and its containing layer, place the replacement on a page- or target-scoped sibling aicreate layer without copying the source layer, hide only the replaced object and same-scope older generated layers, save in place, and return only the AI and final preview. Use for local motif, ornament, object, or illustration replacement; do not use for text/date updates or full-layout generation.
metadata:
  version: "0.2.0-rc.5"
---

# Illustrator Local Artwork

Use the built-in image generator for one raster candidate per attempt and the configured Illustrator MCP for inspection, placement, saving, and preview export. Modify the supplied AI in place only when authorized. Preserve rollback through hidden version layers.

## Instruction priority

Apply requirements in this order:

1. Explicit user requirements.
2. Tone consistency with the replaced artwork.
3. Variation in silhouette, motif, pose, or composition.
4. Skill defaults.

If the user asks to preserve shape, motif, composition, or another element, treat it as a hard generation constraint. If the user explicitly requests a new tone, use `tone_policy.mode: user_override` and do not rematch the source tone.

## Workflow

Before first use or after moving this skill, read [references/setup.md](references/setup.md).
Run all Python commands with this skill's `.venv/Scripts/python.exe` (Windows)
or `.venv/bin/python` (macOS), using absolute script paths when outside the skill directory.
Run `scripts/doctor.py` with that interpreter. A runtime-ready result does not verify
the MCP connection or image-generation tool; confirm those in the current host separately.
Use absolute native filesystem paths in jobs and `target_path`, not URL-encoded paths.
The placement builder handles URI encoding internally. On macOS a path mismatch must
be inspected, never worked around by lowercasing the path.
Source AI paths containing literal percent escapes such as `%20` are rejected
before placement because Illustrator can misreport their identity; see setup.md.

1. Confirm the source AI, internal work directory, target layer/group, target bounds, stable target `scope_id`, and creative brief. Use a page identifier such as `p19` when the document is page-based. The source AI is also the final AI.
2. Inspect the target once and export the original target region as the tone reference. For an ambiguous target, stop after mapping suggestions instead of guessing.
3. Create a schema-v3 job using [references/schema.md](references/schema.md). Keep the job, prompt, generated asset, tone-matched asset, JSX, and diagnostics under `.aicreate/<job-id>/`.
4. Run `scripts/build_generation_prompt.py`, then generate one transparent candidate. Vary form only where the user allows it. Require one isolated subject, no text or watermark, true alpha transparency, and adequate resolution.
5. Run `scripts/validate_job.py --stage candidate`. If it fails, use the reported errors to identify the cause. Correct path, configuration, or tool-call problems and retry the affected step without consuming a generation attempt. For a defective generated asset, a low-cost, deterministic repair is optional when it preserves user requirements and the subject's visual appearance, and repair plus verification costs less than regeneration. Preserve the original, save the repaired copy in the work directory, and rerun the existing validation before continuing; do not build a dedicated repair workflow for an isolated incident. If repair is unsuitable or unsuccessful, regenerate once with `generation_attempt: 2`. If no valid candidate remains after that attempt and any suitable repair, stop without modifying Illustrator. Do not regenerate automatically for aesthetic dissatisfaction.
6. For `match_source`, run `scripts/match_tone.py`. It preserves alpha and structure, protects bright low-saturation material, and uses the adjusted image only when similarity improves. For `user_override`, keep the user-directed candidate unchanged.
7. Set the candidate and job to `selected`, record `effective_asset_path`, and run `validate_job.py --stage place` followed by `build_placement_jsx.py`.
8. Open the source AI itself and call Illustrator MCP `run` with that exact absolute path as `target_path`. The JSX locates the mapped objects in their existing layer, creates the next sibling `aicreate-*` layer, places only the replacement there, hides only the mapped old objects and older generated layers, saves in place, and exports the final preview.
9. Return only the updated AI and final preview PNG. If the user dislikes the result, create one new candidate in a new job and preserve the earlier generated layer as hidden.

## Layer and placement rules

- First version: `aicreate-<original-layer-name>-<scope_id>`; later versions in that same scope append `-02`, `-03`, and so on.
- Treat each page or independent replacement region as a separate scope. Hide only older layers in the exact same scope; never hide generated layers for another page or target. Legacy unscoped `aicreate-<original-layer-name>` layers remain untouched.
- Never duplicate the source layer or its unrelated contents. Create an empty sibling layer at the same layer hierarchy level and place only the replacement asset in it.
- Keep the source layer visible. Hide only the explicitly mapped old objects and earlier `aicreate-*` layers in the same scope; never delete them.
- Default to `contain`; permit `cover` only with an existing clipping group and `allow_crop: true`.
- Preserve mapped old raster items in their source layer with `hidden: true`, and embed the effective asset unless the user requests linking.
- Do not alter text, dates, artboard geometry, or unrelated layers.

## Fast verification and recovery

- Success requires an exact document-path match, a visible source layer, one visible newest `aicreate-*` sibling layer, hidden mapped old objects and older generated layers, valid placement, successful save, and a readable final preview.
- Do not build full inventories or expose jobs, intermediate images, tone profiles, scores, JSX, logs, or diagnostics to the user.
- On `outcome_unknown`, do not retry. Inspect Illustrator state first to avoid duplicate version layers.

## Commands

```powershell
python scripts/build_generation_prompt.py --job job.json
python scripts/validate_job.py --job job.json --stage candidate
python scripts/match_tone.py --job job.json --output candidate-tone-matched.png
python scripts/validate_job.py --job job.json --stage place
python scripts/build_placement_jsx.py --job job.json --preview-png final-preview.png --output place-selected.jsx
```
