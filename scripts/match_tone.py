#!/usr/bin/env python3
from __future__ import annotations

import argparse
import colorsys
import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def circular_delta(target: float, source: float) -> float:
    return (target - source + 0.5) % 1.0 - 0.5


def rgb_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a[index] - b[index]) ** 2 for index in range(3)))


def subject_pixels(image: Image.Image) -> list[tuple[int, int, int]]:
    rgba = image.convert("RGBA")
    rgba.thumbnail((320, 320))
    width, height = rgba.size
    corners = [rgba.getpixel((0, 0))[:3], rgba.getpixel((width - 1, 0))[:3], rgba.getpixel((0, height - 1))[:3], rgba.getpixel((width - 1, height - 1))[:3]]
    opaque = [(r, g, b) for r, g, b, a in rgba.getdata() if a > 12]
    filtered = [pixel for pixel in opaque if min(rgb_distance(pixel, corner) for corner in corners) >= 22]
    return filtered if len(filtered) >= max(32, len(opaque) // 20) else opaque


def profile(image: Image.Image) -> dict:
    pixels = subject_pixels(image)
    if not pixels:
        raise ValueError("no_subject_pixels")
    hsv = [colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0) for r, g, b in pixels]
    saturation = sum(item[1] for item in hsv) / len(hsv)
    value = sum(item[2] for item in hsv) / len(hsv)
    hue_weights = [max(item[1], 0.01) for item in hsv]
    x = sum(math.cos(2 * math.pi * item[0]) * weight for item, weight in zip(hsv, hue_weights))
    y = sum(math.sin(2 * math.pi * item[0]) * weight for item, weight in zip(hsv, hue_weights))
    hue = (math.atan2(y, x) / (2 * math.pi)) % 1.0
    mean_rgb = [round(sum(pixel[index] for pixel in pixels) / len(pixels)) for index in range(3)]
    buckets = Counter(tuple(min(255, (channel // 32) * 32 + 16) for channel in pixel) for pixel in pixels)
    dominant = ["#%02X%02X%02X" % color for color, _ in buckets.most_common(5)]
    return {"hue": hue, "saturation": saturation, "value": value, "mean_rgb": mean_rgb, "dominant_colors": dominant, "pixel_count": len(pixels)}


def similarity(reference: dict, candidate: dict) -> float:
    hue_distance = abs(circular_delta(reference["hue"], candidate["hue"])) / 0.5
    chroma_weight = clamp(max(reference["saturation"], candidate["saturation"]) / 0.25, 0.15, 1.0)
    saturation_distance = min(1.0, abs(reference["saturation"] - candidate["saturation"]) / 0.5)
    value_distance = min(1.0, abs(reference["value"] - candidate["value"]) / 0.5)
    penalty = 0.45 * chroma_weight * hue_distance + 0.30 * saturation_distance + 0.25 * value_distance
    return round(clamp(100.0 * (1.0 - penalty), 0.0, 100.0), 2)


def transfer_tone(image: Image.Image, reference: dict, candidate: dict) -> Image.Image:
    rgba = image.convert("RGBA")
    hue_shift = clamp(circular_delta(reference["hue"], candidate["hue"]), -1 / 12, 1 / 12)
    saturation_ratio = clamp(reference["saturation"] / max(candidate["saturation"], 0.01), 0.65, 1.6)
    value_shift = clamp(reference["value"] - candidate["value"], -0.12, 0.12)
    output = []
    for r, g, b, alpha in rgba.getdata():
        if alpha == 0:
            output.append((r, g, b, alpha))
            continue
        hue, saturation, value = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        if saturation < 0.18 and value > 0.72:
            adjusted_hue = hue
            adjusted_saturation = saturation
            adjusted_value = clamp(value + value_shift * 0.25, 0.0, 1.0)
        else:
            adjusted_hue = (hue + hue_shift) % 1.0 if saturation > 0.05 else hue
            adjusted_saturation = clamp(saturation * saturation_ratio, 0.0, 1.0)
            adjusted_value = clamp(value + value_shift, 0.0, 1.0)
        nr, ng, nb = colorsys.hsv_to_rgb(adjusted_hue, adjusted_saturation, adjusted_value)
        output.append((round(nr * 255), round(ng * 255), round(nb * 255), alpha))
    adjusted = Image.new("RGBA", rgba.size)
    adjusted.putdata(output)
    return adjusted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    job = json.loads(Path(args.job).resolve().read_text(encoding="utf-8"))
    if job.get("schema_version") != 3:
        raise SystemExit("schema_version_must_be_3")
    candidate_path = Path(job["candidate"]["path"]).resolve()
    if not candidate_path.is_file():
        raise SystemExit("candidate_missing")
    mode = job.get("tone_policy", {}).get("mode")
    if mode == "user_override":
        print(json.dumps({"mode": mode, "adjusted": False, "effective_asset_path": str(candidate_path), "reason": "user_tone_override"}, ensure_ascii=False))
        return
    if mode != "match_source":
        raise SystemExit("invalid_tone_policy_mode")
    reference_path = Path(job["tone_policy"]["reference_path"]).resolve()
    if not reference_path.is_file():
        raise SystemExit("tone_reference_missing")
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(reference_path) as reference_image, Image.open(candidate_path) as candidate_image:
        original_alpha = candidate_image.convert("RGBA").getchannel("A").tobytes()
        reference_profile = profile(reference_image)
        candidate_profile = profile(candidate_image)
        before = similarity(reference_profile, candidate_profile)
        adjusted_image = transfer_tone(candidate_image, reference_profile, candidate_profile)
        after_profile = profile(adjusted_image)
        after = similarity(reference_profile, after_profile)
        if adjusted_image.getchannel("A").tobytes() != original_alpha:
            raise SystemExit("alpha_channel_changed")
        adjusted_image.save(output_path)

    use_adjusted = after > before + 0.5
    result = {
        "mode": mode,
        "adjusted": use_adjusted,
        "score_before": before,
        "score_after": after,
        "reference_profile": reference_profile,
        "candidate_profile": candidate_profile,
        "adjusted_profile": after_profile,
        "effective_asset_path": str(output_path if use_adjusted else candidate_path),
        "warning": None if use_adjusted or before >= 75 else "tone_match_did_not_improve",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
