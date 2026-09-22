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
    "scope_id": "p03",
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

`generation_attempt` is `1` or `2` and counts actual image-generation calls only. Attempt 2 is allowed only for a technically defective generated asset when a reasonable repair is unsuitable or unsuccessful; path, configuration, and tool-call corrections do not consume a generation attempt. Follow the repair criteria in the skill's workflow. For a repair, preserve the original file in the work directory, point `candidate.path` to the separate repaired copy, and rerun candidate validation before selection and tone matching. Repairs do not increment `generation_attempt` or require additional schema fields. Aesthetic dissatisfaction starts a new job and a new `aicreate-*` layer version rather than incrementing this retry counter.

`target.layer` names the layer containing the original mapped objects. `target.scope_id` is a required stable ASCII identifier for the page or replacement region, such as `p03`; it may contain letters, digits, underscores, and hyphens, up to 32 characters. Placement creates an empty sibling layer named `aicreate-<source-layer>-<scope_id>` and increments only that scope with `-02`, `-03`, and so on. It must not copy the source layer. `raster_indices` identifies only the original objects to hide after successful placement.

## Cross-platform paths

The example above uses Windows paths. On macOS use native absolute paths such as
`/Users/alex/项目/source.ai` and `/Users/alex/项目/.aicreate/job-1/candidate.png`.
Do not reuse another machine's job without updating every path. Preserve macOS
filename case and pass literal filenames (including percent signs), not URI-encoded
strings. JSON can be UTF-8 with or without BOM. The placement builder handles
File URI encoding internally; schema v3 and the command arguments are unchanged.
Source AI paths containing `%` followed by two hexadecimal digits are rejected
before placement (`source_path_contains_percent_escape`); Illustrator can report
their document identity incorrectly. This restriction does not apply to PNG assets.
