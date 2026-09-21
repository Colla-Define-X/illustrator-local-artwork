from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def make_subject(path: Path, color: tuple[int, int, int], neutral_center: bool = False) -> None:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(8, 56):
        for y in range(8, 56):
            pixel = (244, 244, 240, 255) if neutral_center and 20 <= x < 44 and 20 <= y < 44 else (*color, 255)
            image.putpixel((x, y), pixel)
    image.save(path)


class ScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.work = self.root / ".aicreate" / "job-1"
        self.work.mkdir(parents=True)
        self.source = self.root / "source.ai"
        self.source.write_bytes(b"illustrator-test-placeholder")
        self.reference = self.work / "tone-reference.png"
        self.candidate = self.work / "candidate.png"
        make_subject(self.reference, (92, 118, 205), neutral_center=True)
        make_subject(self.candidate, (205, 105, 58), neutral_center=True)
        self.job = {
            "schema_version": 3,
            "job_id": "job-1",
            "status": "candidate_ready",
            "generation_attempt": 1,
            "source_ai": str(self.source),
            "work_dir": str(self.work),
            "target": {
                "layer": "Print",
                "group_index": 0,
                "target_bounds": [0, 100, 100, 0],
                "raster_indices": [0],
                "primary_raster_index": 0,
                "fit": "contain",
                "allow_crop": False,
                "embed": True,
            },
            "brief": {
                "subject": "porcelain vessel",
                "style": "soft watercolor",
                "constraints": ["one object", "no text"],
                "preserve": [],
                "variation": ["silhouette", "motif arrangement"],
            },
            "tone_policy": {"mode": "match_source", "reference_path": str(self.reference), "target_tone": None},
            "candidate": {
                "id": "candidate",
                "path": str(self.candidate),
                "status": "generated",
                "effective_asset_path": None,
            },
            "requirements": {"min_width_px": 64, "min_height_px": 64},
        }
        self.job_path = self.work / "job.json"
        self.write_job()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_job(self) -> None:
        self.job_path.write_text(json.dumps(self.job), encoding="utf-8")

    def run_script(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_single_candidate_and_retry_limit(self) -> None:
        result = self.run_script("validate_job.py", "--job", str(self.job_path), "--stage", "candidate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.job["generation_attempt"] = 3
        self.write_job()
        result = self.run_script("validate_job.py", "--job", str(self.job_path), "--stage", "candidate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generation_attempt_must_be_1_or_2", result.stdout)

    def test_technical_failure_allows_only_one_retry(self) -> None:
        broken = Image.new("RGB", (64, 64), (255, 255, 255))
        broken.save(self.candidate)
        result = self.run_script("validate_job.py", "--job", str(self.job_path), "--stage", "candidate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("technical_failure_allows_one_more_generation_attempt", result.stdout)
        self.job["generation_attempt"] = 2
        self.write_job()
        result = self.run_script("validate_job.py", "--job", str(self.job_path), "--stage", "candidate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generation_retry_limit_reached", result.stdout)

    def test_tone_matching_improves_score_and_preserves_alpha(self) -> None:
        output = self.work / "candidate-tone-matched.png"
        original_alpha = Image.open(self.candidate).getchannel("A").tobytes()
        result = self.run_script("match_tone.py", "--job", str(self.job_path), "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertGreater(report["score_after"], report["score_before"])
        self.assertEqual(Image.open(output).getchannel("A").tobytes(), original_alpha)
        original_neutral = Image.open(self.candidate).getpixel((32, 32))[:3]
        adjusted_neutral = Image.open(output).getpixel((32, 32))[:3]
        self.assertLessEqual(max(abs(a - b) for a, b in zip(original_neutral, adjusted_neutral)), 8)

    def test_user_tone_override_skips_source_matching(self) -> None:
        self.job["tone_policy"] = {"mode": "user_override", "target_tone": "warm vermilion and gold"}
        self.write_job()
        output = self.work / "should-not-be-created.png"
        result = self.run_script("match_tone.py", "--job", str(self.job_path), "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["adjusted"])
        self.assertEqual(report["reason"], "user_tone_override")
        self.assertFalse(output.exists())

    def test_prompt_places_user_constraints_before_variation(self) -> None:
        self.job["brief"]["preserve"] = ["exact vessel silhouette", "existing crane motif"]
        self.job["brief"]["variation"] = ["exact vessel silhouette", "background ornament"]
        self.job["tone_policy"] = {"mode": "user_override", "target_tone": "celadon green"}
        self.write_job()
        result = self.run_script("build_generation_prompt.py", "--job", str(self.job_path))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertLess(result.stdout.index("HARD USER CONSTRAINTS"), result.stdout.index("HARD USER TONE REQUEST"))
        self.assertNotIn("Variation is allowed only in: exact vessel silhouette", result.stdout)
        self.assertIn("background ornament", result.stdout)

    def test_placement_uses_effective_asset_and_hides_older_versions(self) -> None:
        matched = self.work / "candidate-tone-matched.png"
        make_subject(matched, (100, 120, 200), neutral_center=True)
        self.job["status"] = "selected"
        self.job["candidate"]["status"] = "selected"
        self.job["candidate"]["effective_asset_path"] = str(matched)
        self.write_job()
        jsx = self.work / "place.jsx"
        preview = self.root / "final-preview.png"
        result = self.run_script(
            "build_placement_jsx.py",
            "--job", str(self.job_path),
            "--preview-png", str(preview),
            "--output", str(jsx),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        code = jsx.read_text(encoding="utf-8-sig")
        self.assertIn(str(matched).replace("\\", "\\\\"), code)
        self.assertIn("hideOlderVersions", code)
        self.assertIn("layer!==current", code)
        self.assertIn("sourceLayer.visible=false", code)
        self.assertIn("doc.save()", code)
        self.assertNotIn("output_ai", code)


if __name__ == "__main__":
    unittest.main()
