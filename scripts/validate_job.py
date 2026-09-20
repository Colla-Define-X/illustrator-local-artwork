#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


VALID_JOB_STATES = {"draft", "candidates_ready", "selected", "placed", "verified", "failed"}
VALID_CANDIDATE_STATES = {"generated", "selected", "rejected"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def inspect_png(path: Path) -> dict:
    with Image.open(path) as image:
        image.load()
        alpha = image.getchannel("A") if "A" in image.getbands() else None
        extrema = alpha.getextrema() if alpha else None
        corners = []
        if alpha:
            width, height = image.size
            corners = [
                alpha.getpixel((0, 0)),
                alpha.getpixel((width - 1, 0)),
                alpha.getpixel((0, height - 1)),
                alpha.getpixel((width - 1, height - 1)),
            ]
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "alpha_extrema": list(extrema) if extrema else None,
            "corner_alpha": corners,
            "transparent_background": bool(extrema and extrema[0] == 0 and extrema[1] > 0 and all(value == 0 for value in corners)),
            "subject_alpha_sufficient": bool(extrema and extrema[1] >= 240),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--stage", required=True, choices=("candidates", "place"))
    args = parser.parse_args()
    job = json.loads(Path(args.job).resolve().read_text(encoding="utf-8"))
    errors, warnings, checks = [], [], []

    if job.get("schema_version") != 2:
        errors.append("schema_version_must_be_2")
    if job.get("status") not in VALID_JOB_STATES:
        errors.append("invalid_job_status")

    source = Path(job.get("source_ai", ""))
    if not source.is_absolute() or not source.is_file() or source.suffix.lower() != ".ai":
        errors.append("source_ai_must_be_existing_absolute_ai")

    work_dir = Path(job.get("work_dir", ""))
    if not work_dir.is_absolute() or ".aicreate" not in {part.lower() for part in work_dir.parts}:
        errors.append("work_dir_must_be_absolute_aicreate_directory")

    target = job.get("target", {})
    if not isinstance(target.get("layer"), str) or not target.get("layer", "").strip():
        errors.append("target_layer_required")
    bounds = target.get("target_bounds")
    if not isinstance(bounds, list) or len(bounds) != 4 or not (bounds[2] > bounds[0] and bounds[1] > bounds[3]):
        errors.append("invalid_target_bounds")
    if not isinstance(target.get("group_index"), int) or target.get("group_index") < 0:
        errors.append("invalid_group_index")
    indices = target.get("raster_indices")
    if not isinstance(indices, list) or not indices or any(not isinstance(value, int) or value < 0 for value in indices):
        errors.append("invalid_raster_indices")
    if target.get("fit", "contain") not in {"contain", "cover"}:
        errors.append("invalid_fit")
    if target.get("fit") == "cover" and not target.get("allow_crop"):
        errors.append("cover_requires_allow_crop")

    requirements = job.get("requirements", {})
    min_width = int(requirements.get("min_width_px", 1))
    min_height = int(requirements.get("min_height_px", 1))
    candidates = job.get("candidates", [])
    ids = [str(item.get("id", "")) for item in candidates]
    if not ids or len(ids) != len(set(ids)) or any(not value for value in ids):
        errors.append("candidate_ids_must_be_unique_and_nonempty")

    valid_candidates, selected = [], []
    for item in candidates:
        state = item.get("status")
        candidate_id = item.get("id")
        if state not in VALID_CANDIDATE_STATES:
            errors.append(f"candidate_{candidate_id}_invalid_status")
            continue
        if state == "rejected":
            if not item.get("reason"):
                warnings.append(f"candidate_{candidate_id}_rejected_without_reason")
            continue
        path = Path(item.get("path", ""))
        if not path.is_absolute() or not path.is_file():
            errors.append(f"candidate_{candidate_id}_file_missing")
            continue
        if work_dir.is_absolute() and work_dir not in path.parents:
            errors.append(f"candidate_{candidate_id}_must_be_inside_work_dir")
        if path.suffix.lower() != ".png":
            errors.append(f"candidate_{candidate_id}_must_be_png")
            continue
        try:
            info = inspect_png(path)
        except Exception as exc:
            errors.append(f"candidate_{candidate_id}_image_unreadable:{exc}")
            continue
        info.update({"id": candidate_id, "path": str(path), "sha256": sha256(path)})
        checks.append(info)
        if not info["transparent_background"]:
            errors.append(f"candidate_{candidate_id}_transparent_background_failed")
        if not info["subject_alpha_sufficient"]:
            errors.append(f"candidate_{candidate_id}_subject_too_transparent")
        if info["width"] < min_width or info["height"] < min_height:
            errors.append(f"candidate_{candidate_id}_resolution_below_minimum")
        if info["transparent_background"] and info["subject_alpha_sufficient"] and info["width"] >= min_width and info["height"] >= min_height:
            valid_candidates.append(item)
        if state == "selected":
            selected.append(item)

    if args.stage == "candidates" and not 2 <= len(valid_candidates) <= 3:
        errors.append("candidates_stage_requires_two_or_three_valid_candidates")
    if args.stage == "place":
        selected_id = job.get("selected_candidate_id")
        if job.get("status") != "selected":
            errors.append("placement_requires_selected_job_status")
        if len(selected) != 1 or not selected_id or str(selected[0].get("id")) != str(selected_id):
            errors.append("exactly_one_matching_selected_candidate_required")

    result = {"ok": not errors, "stage": args.stage, "errors": errors, "warnings": warnings, "candidate_checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
