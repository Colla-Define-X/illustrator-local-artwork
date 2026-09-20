# Job schema

The job JSON is the single handoff between candidate generation, approval, placement, and audit.

```json
{
  "schema_version": 1,
  "job_id": "day-03-green-vessel",
  "status": "candidates_ready",
  "source_ai": "C:\\absolute\\source.ai",
  "source_sha256": "UPPERCASE_SHA256",
  "output_ai": "C:\\absolute\\output.ai",
  "target": {
    "layer": "印刷",
    "group_index": 17,
    "target_bounds": [-3295.25, 2103.56, -3126.53, 1939.16],
    "raster_indices": [0, 1],
    "primary_raster_index": 0,
    "fit": "contain",
    "allow_crop": false,
    "embed": true
  },
  "brief": {
    "subject": "green cloisonne lidded vessel",
    "style": "quiet hand-painted editorial illustration",
    "palette": ["jade", "celadon", "ivory", "muted gold"],
    "constraints": ["one object", "transparent background", "no text"],
    "avoid": ["watermark", "frame", "scenery"]
  },
  "references": [{"path": "C:\\absolute\\preview.png", "role": "layout_and_style"}],
  "candidates": [
    {"id": "A", "path": "C:\\absolute\\candidate-a.png", "status": "generated", "prompt_path": "C:\\absolute\\prompt-a.txt"}
  ],
  "approved_candidate_id": null,
  "protected_layers": ["说明", "刀线"],
  "requirements": {"document_color_space": "DocumentColorSpace.CMYK", "min_width_px": 1000, "min_height_px": 1000}
}
```

## States

- `draft`: target and brief are being prepared.
- `candidates_ready`: two or three candidates passed technical validation; no placement is allowed.
- `approved`: exactly one candidate has status `approved` and its ID equals `approved_candidate_id`.
- `placed`: Illustrator placement returned a definite success.
- `audited`: readback checks passed.
- `failed`: a terminal validation, placement, or audit failure was recorded.

Candidate status is `generated`, `approved`, or `rejected`. Rejection keeps a `reason` such as `opaque_background`, `insufficient_resolution`, `contains_text`, or `visual_mismatch`.

Approval is invalid when the selected file hash, source AI hash, target bounds, or creative brief changes.
