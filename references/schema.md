# Job schema v2

The internal job coordinates candidate validation, automatic selection, and in-place placement. It is not a user-facing deliverable.

```json
{
  "schema_version": 2,
  "job_id": "day-03-green-vessel",
  "status": "candidates_ready",
  "source_ai": "C:\\absolute\\source.ai",
  "work_dir": "C:\\project\\.aicreate\\day-03-green-vessel",
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
  "references": [{"path": "C:\\absolute\\reference.png", "role": "layout_and_style"}],
  "candidates": [
    {"id": "A", "path": "C:\\project\\.aicreate\\day-03-green-vessel\\candidate-a.png", "status": "generated"}
  ],
  "selected_candidate_id": null,
  "requirements": {"min_width_px": 1000, "min_height_px": 1000}
}
```

## States

- `draft`: target and brief are being prepared.
- `candidates_ready`: two or three candidates passed technical validation.
- `selected`: exactly one candidate has status `selected` and matches `selected_candidate_id`.
- `placed`: Illustrator returned a definite placement and save success.
- `verified`: the in-script fast checks and final preview export passed.
- `failed`: candidate validation, placement, saving, or fast verification failed.

Candidate status is `generated`, `selected`, or `rejected`. Rejected candidates retain a short internal reason. Candidate choice is based on technical validity plus visual fit to the brief and reference.
