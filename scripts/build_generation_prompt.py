#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    job = json.loads(Path(args.job).resolve().read_text(encoding="utf-8"))
    if job.get("schema_version") != 3:
        raise SystemExit("schema_version_must_be_3")
    brief = job.get("brief", {})
    tone = job.get("tone_policy", {})
    preserve = [str(value).strip() for value in brief.get("preserve", []) if str(value).strip()]
    variation = [str(value).strip() for value in brief.get("variation", []) if str(value).strip() and str(value).strip() not in preserve]
    constraints = [str(value).strip() for value in brief.get("constraints", []) if str(value).strip()]
    parts = []
    if preserve:
        parts.append("HARD USER CONSTRAINTS — preserve exactly: " + "; ".join(preserve) + ".")
    parts.append("Create one isolated " + str(brief.get("subject", "artwork subject")) + ".")
    if brief.get("style"):
        parts.append("Rendering style: " + str(brief["style"]) + ".")
    if tone.get("mode") == "user_override":
        parts.append("HARD USER TONE REQUEST: " + str(tone.get("target_tone", "")).strip() + ". Do not rematch the source tone.")
    else:
        parts.append("Match the reference artwork's overall hue family, brightness, saturation, material feeling, and painting treatment.")
    if variation:
        parts.append("Variation is allowed only in: " + "; ".join(variation) + ".")
    if constraints:
        parts.append("Technical and content constraints: " + "; ".join(constraints) + ".")
    parts.append("Use a true transparent background. Do not add text, watermark, frame, or scenery.")
    print(" ".join(parts))


if __name__ == "__main__":
    main()
