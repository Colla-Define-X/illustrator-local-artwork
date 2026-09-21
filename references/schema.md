# Job schema v3

Schema v3 represents one generation attempt and one candidate. Schema-v2 jobs must not be resumed.

```json
{
  "schema_version": 3,
  "job_id": "day-03-green-vessel-attempt-1",
  "status": "candidate_ready",
  "generation_attempt": 1,
  "source_ai": "C:\\absolute\\source.ai",
  "work_dir": "C:\\project\\.aicreate\\day-03-green-vessel-attempt-1",
  "target": {
    "layer": "印刷",
    "placement_layer_scope": "sibling_of_source_layer",
    "group_index": 17,
    "target_bounds": [-3295.25, 2103.56, -3126.53, 1939.16],
    "raster_indices": [0, 1],
    "primary_raster_index": 0,
    "fit": "contain",
    "allow_crop": false,
    "embed": true
  },
  "brief": {
    "subject": "decorated porcelain vessel",
    "style": "quiet hand-painted editorial illustration",
    "constraints": ["one object", "transparent background", "no text"],
    "preserve": [],
    "variation": ["silhouette", "motif arrangement"]
  },
  "tone_policy": {
    "mode": "match_source",
    "reference_path": "C:\\project\\.aicreate\\day-03-green-vessel-attempt-1\\tone-reference.png",
    "target_tone": null
  },
  "candidate": {
    "id": "candidate",
    "path": "C:\\project\\.aicreate\\day-03-green-vessel-attempt-1\\candidate.png",
    "status": "generated",
    "tone_score_before": null,
    "tone_score_after": null,
    "effective_asset_path": null
  },
  "requirements": {"min_width_px": 1000, "min_height_px": 1000}
}
```

For a user-requested tone change, use `tone_policy.mode: user_override`, set `target_tone`, and omit `reference_path`. User-preserved elements belong in `brief.preserve` and override default variation.

## States and retry limit

- `draft`: target and brief are being prepared.
- `candidate_ready`: the single generated candidate is ready for technical validation.
- `selected`: the candidate is technically valid and has an effective asset path.
- `placed`: Illustrator returned a definite placement and save success.
- `verified`: fast checks and final preview export passed.
- `failed`: generation attempt 2 or a later placement step failed.

`generation_attempt` is `1` or `2`. Attempt 2 is allowed only after a technical failure. Aesthetic dissatisfaction starts a new job and a new `aicreate-*` layer version rather than incrementing this retry counter.

`target.layer` names the layer containing the original mapped objects. Placement creates an empty sibling layer named with the `aicreate-` prefix; it must not copy the source layer. `raster_indices` identifies only the original objects to hide after successful placement.
