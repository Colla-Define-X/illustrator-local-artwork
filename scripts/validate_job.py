#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


VALID_JOB_STATES = {"draft", "candidates_ready", "approved", "placed", "audited", "failed"}
VALID_CANDIDATE_STATES = {"generated", "approved", "rejected"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def inspect_png(path: Path) -> dict:
    with Image.open(path) as image:
        image.load()
        bands = image.getbands()
        alpha = image.getchannel("A") if "A" in bands else None
        extrema = alpha.getextrema() if alpha else None
        corners = []
        if alpha:
            w, h = image.size
            corners = [alpha.getpixel((0, 0)), alpha.getpixel((w - 1, 0)), alpha.getpixel((0, h - 1)), alpha.getpixel((w - 1, h - 1))]
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "alpha_extrema": list(extrema) if extrema else None,
            "corner_alpha": corners,
            "transparent_background": bool(extrema and extrema[0] == 0 and extrema[1] > 0 and all(value == 0 for value in corners)),
            "subject_alpha_sufficient": bool(extrema and extrema[1] >= 240),
            "has_fully_opaque_pixels": bool(extrema and extrema[1] == 255),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--stage", required=True, choices=("candidates", "place", "audit"))
    args = parser.parse_args()
    job_path = Path(args.job).resolve()
    job = json.loads(job_path.read_text(encoding="utf-8"))
    errors, warnings, checks = [], [], []

    if job.get("schema_version") != 1:
        errors.append("schema_version_must_be_1")
    if job.get("status") not in VALID_JOB_STATES:
        errors.append("invalid_job_status")

    source = Path(job.get("source_ai", ""))
    output = Path(job.get("output_ai", ""))
    if not source.is_absolute() or not source.is_file() or source.suffix.lower() != ".ai":
        errors.append("source_ai_must_be_existing_absolute_ai")
    elif job.get("source_sha256") and sha256(source) != str(job["source_sha256"]).upper():
        errors.append("source_sha256_mismatch")
    if args.stage in {"place", "audit"}:
        if not output.is_absolute() or output.suffix.lower() != ".ai":
            errors.append("output_ai_must_be_absolute_ai")
        elif source.resolve() == output.resolve():
            errors.append("output_ai_must_not_equal_source_ai")

    target = job.get("target", {})
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

    valid_candidates = []
    approved = []
    for item in candidates:
        state = item.get("status")
        if state not in VALID_CANDIDATE_STATES:
            errors.append(f"candidate_{item.get('id')}_invalid_status")
            continue
        if state == "rejected":
            if not item.get("reason"):
                warnings.append(f"candidate_{item.get('id')}_rejected_without_reason")
            continue
        path = Path(item.get("path", ""))
        if not path.is_absolute() or not path.is_file():
            errors.append(f"candidate_{item.get('id')}_file_missing")
            continue
        if path.suffix.lower() != ".png":
            errors.append(f"candidate_{item.get('id')}_must_be_png")
            continue
        try:
            info = inspect_png(path)
        except Exception as exc:
            errors.append(f"candidate_{item.get('id')}_image_unreadable:{exc}")
            continue
        info.update({"id": item.get("id"), "path": str(path), "sha256": sha256(path)})
        checks.append(info)
        if not info["transparent_background"]:
            errors.append(f"candidate_{item.get('id')}_transparent_background_failed")
        if not info["subject_alpha_sufficient"]:
            errors.append(f"candidate_{item.get('id')}_subject_too_transparent")
        if info["width"] < min_width or info["height"] < min_height:
            errors.append(f"candidate_{item.get('id')}_resolution_below_minimum")
        if info["transparent_background"] and info["subject_alpha_sufficient"] and info["width"] >= min_width and info["height"] >= min_height:
            valid_candidates.append(item)
        if state == "approved":
            approved.append(item)

    if args.stage == "candidates" and not 2 <= len(valid_candidates) <= 3:
        errors.append("candidates_stage_requires_two_or_three_valid_candidates")
    if args.stage in {"place", "audit"}:
        selected = job.get("approved_candidate_id")
        if job.get("status") not in {"approved", "placed", "audited"}:
            errors.append("placement_requires_approved_job_status")
        if len(approved) != 1 or not selected or str(approved[0].get("id")) != str(selected):
            errors.append("exactly_one_matching_approved_candidate_required")

    result = {"ok": not errors, "stage": args.stage, "errors": errors, "warnings": warnings, "candidate_checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
