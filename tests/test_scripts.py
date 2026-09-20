from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class ScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.work = self.root / ".aicreate" / "job-1"
        self.work.mkdir(parents=True)
        self.source = self.root / "source.ai"
        self.source.write_bytes(b"illustrator-test-placeholder")
        self.candidates = []
        for candidate_id in ("A", "B", "C"):
            path = self.work / f"candidate-{candidate_id.lower()}.png"
            image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            for x in range(8, 56):
                for y in range(8, 56):
                    image.putpixel((x, y), (20, 120, 80, 255))
            image.save(path)
            self.candidates.append({"id": candidate_id, "path": str(path), "status": "generated"})
        self.job = {
            "schema_version": 2,
            "job_id": "job-1",
            "status": "candidates_ready",
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
            "candidates": self.candidates,
            "selected_candidate_id": None,
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

    def test_candidate_validation_and_selection(self) -> None:
        result = self.run_script("validate_job.py", "--job", str(self.job_path), "--stage", "candidates")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.job["status"] = "selected"
        self.job["selected_candidate_id"] = "B"
        self.job["candidates"][1]["status"] = "selected"
        self.write_job()
        result = self.run_script("validate_job.py", "--job", str(self.job_path), "--stage", "place")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_placement_builder_targets_source_and_reversible_layers(self) -> None:
        self.job["status"] = "selected"
        self.job["selected_candidate_id"] = "A"
        self.job["candidates"][0]["status"] = "selected"
        self.write_job()
        jsx = self.work / "place.jsx"
        preview = self.root / "final-preview.png"
        result = self.run_script(
            "build_placement_jsx.py",
            "--job",
            str(self.job_path),
            "--preview-png",
            str(preview),
            "--output",
            str(jsx),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        code = jsx.read_text(encoding="utf-8-sig")
        self.assertIn("aicreate-", code)
        self.assertIn("sourceLayer.visible=false", code)
        self.assertIn("doc.save()", code)
        self.assertNotIn("output_ai", code)


if __name__ == "__main__":
    unittest.main()
