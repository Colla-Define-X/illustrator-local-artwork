#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def contains(outer: list[float], inner: list[float], tolerance: float = 0.75) -> bool:
    return inner[0] >= outer[0] - tolerance and inner[2] <= outer[2] + tolerance and inner[1] <= outer[1] + tolerance and inner[3] >= outer[3] - tolerance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    actual = json.loads(Path(args.actual).read_text(encoding="utf-8"))
    target = job["target"]
    approved = [item for item in job.get("candidates", []) if item.get("status") == "approved"]
    issues, checks = [], []
    if len(approved) != 1:
        issues.append({"severity": "error", "code": "approved_candidate_count_invalid"})
        asset = None
    else:
        asset = Path(approved[0]["path"])
    if asset and asset.is_file():
        with Image.open(asset) as image:
            alpha = image.getchannel("A") if "A" in image.getbands() else None
            extrema = alpha.getextrema() if alpha else None
            corners = []
            if alpha:
                w, h = image.size
                corners = [alpha.getpixel((0, 0)), alpha.getpixel((w - 1, 0)), alpha.getpixel((0, h - 1)), alpha.getpixel((w - 1, h - 1))]
            alpha_ok = bool(extrema and extrema[0] == 0 and extrema[1] >= 240 and all(value == 0 for value in corners))
            checks.append({"check": "approved_asset", "path": str(asset), "size": list(image.size), "mode": image.mode, "alpha_extrema": list(extrema) if extrema else None, "corner_alpha": corners, "alpha_ok": alpha_ok, "has_fully_opaque_pixels": bool(extrema and extrema[1] == 255)})
            if not alpha_ok:
                issues.append({"severity": "error", "code": "approved_asset_alpha_invalid"})
    else:
        issues.append({"severity": "error", "code": "approved_asset_missing"})

    source = Path(job["source_ai"])
    source_unchanged = source.is_file() and (not job.get("source_sha256") or sha256(source) == str(job["source_sha256"]).upper())
    if not source_unchanged:
        issues.append({"severity": "error", "code": "source_ai_changed"})

    base_groups = {int(group["index"]): group for group in baseline.get("groups", [])}
    actual_groups = {int(group["index"]): group for group in actual.get("groups", [])}
    group_index = int(target["group_index"])
    current = actual_groups.get(group_index)
    inside = [] if not current else [item for item in current.get("rasters", []) if contains(target["target_bounds"], item["bounds"])]
    placement_ok = bool(inside) if target.get("fit", "contain") == "contain" else bool(current and current.get("rasters"))
    checks.append({"check": "placement", "group_index": group_index, "fit": target.get("fit", "contain"), "raster_inside_target": len(inside), "ok": placement_ok})
    if not placement_ok:
        issues.append({"severity": "error", "code": "replacement_not_in_target"})

    unrelated = []
    for index, before in base_groups.items():
        if index == group_index:
            continue
        after = actual_groups.get(index)
        if not after or any(before.get(key) != after.get(key) for key in ("frames", "rasters", "types")):
            unrelated.append(index)
    if unrelated:
        issues.append({"severity": "error", "code": "unrelated_groups_changed", "group_indices": unrelated})

    protected_ok = baseline.get("protected_layers") == actual.get("protected_layers")
    if not protected_ok:
        issues.append({"severity": "error", "code": "protected_layer_changed"})
    required_space = job.get("requirements", {}).get("document_color_space")
    actual_space = actual.get("document", {}).get("colorSpace")
    if required_space and actual_space != required_space:
        issues.append({"severity": "error", "code": "document_color_space_mismatch", "expected": required_space, "actual": actual_space})
    if target.get("embed", True) and actual.get("document", {}).get("placedItems", 0) != 0:
        issues.append({"severity": "error", "code": "approved_asset_not_embedded"})

    report = {
        "summary": {"passed": not issues, "errors": len(issues), "source_unchanged": source_unchanged, "protected_layers_ok": protected_ok, "unrelated_groups_changed": len(unrelated)},
        "issues": issues,
        "checks": checks,
    }
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
