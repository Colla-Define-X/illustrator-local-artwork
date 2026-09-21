#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image


VALID_JOB_STATES = {"draft", "candidate_ready", "selected", "placed", "verified", "failed"}
VALID_CANDIDATE_STATES = {"generated", "selected", "rejected"}
VALID_TONE_MODES = {"match_source", "user_override"}


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


def inside(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--stage", required=True, choices=("candidate", "place"))
    args = parser.parse_args()
    job = json.loads(Path(args.job).resolve().read_text(encoding="utf-8"))
    errors, warnings, checks = [], [], []

    if job.get("schema_version") != 3:
        errors.append("schema_version_must_be_3")
    if job.get("status") not in VALID_JOB_STATES:
        errors.append("invalid_job_status")

    attempt = job.get("generation_attempt")
    if not isinstance(attempt, int) or attempt not in {1, 2}:
        errors.append("generation_attempt_must_be_1_or_2")

    source = Path(job.get("source_ai", ""))
    if not source.is_absolute() or not source.is_file() or source.suffix.lower() != ".ai":
        errors.append("source_ai_must_be_existing_absolute_ai")

    work_dir = Path(job.get("work_dir", ""))
    if not work_dir.is_absolute() or ".aicreate" not in {part.lower() for part in work_dir.parts}:
        errors.append("work_dir_must_be_absolute_aicreate_directory")

    tone_policy = job.get("tone_policy", {})
    tone_mode = tone_policy.get("mode")
    if tone_mode not in VALID_TONE_MODES:
        errors.append("invalid_tone_policy_mode")
    elif tone_mode == "match_source":
        reference = Path(tone_policy.get("reference_path", ""))
        if not reference.is_absolute() or not reference.is_file():
            errors.append("match_source_requires_existing_reference")
    elif not str(tone_policy.get("target_tone", "")).strip():
        errors.append("user_override_requires_target_tone")

    target = job.get("target", {})
    if not isinstance(target.get("layer"), str) or not target.get("layer", "").strip():
        errors.append("target_layer_required")
    if target.get("placement_layer_scope") != "sibling_of_source_layer":
        errors.append("placement_layer_scope_must_be_sibling_of_source_layer")
    scope_id = target.get("scope_id")
    if not isinstance(scope_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}", scope_id):
        errors.append("target_scope_id_must_be_safe_identifier")
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

    candidate = job.get("candidate")
    if not isinstance(candidate, dict):
        errors.append("single_candidate_required")
        candidate = {}
    state = candidate.get("status")
    if state not in VALID_CANDIDATE_STATES:
        errors.append("candidate_invalid_status")
    candidate_path = Path(candidate.get("path", ""))
    if not candidate_path.is_absolute() or not candidate_path.is_file():
        errors.append("candidate_file_missing")
    elif not inside(candidate_path, work_dir):
        errors.append("candidate_must_be_inside_work_dir")
    elif candidate_path.suffix.lower() != ".png":
        errors.append("candidate_must_be_png")
    elif state != "rejected":
        try:
            info = inspect_png(candidate_path)
            checks.append(info)
            requirements = job.get("requirements", {})
            if not info["transparent_background"]:
                errors.append("candidate_transparent_background_failed")
            if not info["subject_alpha_sufficient"]:
                errors.append("candidate_subject_too_transparent")
            if info["width"] < int(requirements.get("min_width_px", 1)) or info["height"] < int(requirements.get("min_height_px", 1)):
                errors.append("candidate_resolution_below_minimum")
        except Exception as exc:
            errors.append(f"candidate_image_unreadable:{exc}")

    if args.stage == "place":
        if job.get("status") != "selected" or state != "selected":
            errors.append("placement_requires_selected_candidate")
        effective = Path(candidate.get("effective_asset_path", ""))
        if not effective.is_absolute() or not effective.is_file():
            errors.append("effective_asset_missing")
        elif not inside(effective, work_dir):
            errors.append("effective_asset_must_be_inside_work_dir")

    if errors and attempt == 1 and args.stage == "candidate":
        warnings.append("technical_failure_allows_one_more_generation_attempt")
    if errors and attempt == 2 and args.stage == "candidate":
        warnings.append("generation_retry_limit_reached")

    result = {"ok": not errors, "stage": args.stage, "errors": errors, "warnings": warnings, "candidate_checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
