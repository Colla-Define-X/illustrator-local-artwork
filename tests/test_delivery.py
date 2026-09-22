from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_delivery
import doctor
import install
from runtime_support import PATH_GUARD_JS


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_actual_javascript_path_comparison(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js required for JS behavior test")
        cases = [
            [r"C:\中文 空格\Art%20.ai", "c:/中文 空格/art%20.ai", True, True],
            [r"\\server\Share\Art.ai", "//SERVER/share/art.ai", True, True],
            ["/Users/test/Art.ai", "/Users/test/art.ai", False, False],
            ["/Users/中文 空格/(a) %20 # '.ai", "/Users/中文 空格/(a) %20 # '.ai", False, True],
            ["/Users/test/a%20b.ai", "/Users/test/a b.ai", False, False],
            [r"/Users/test/a\b.ai", "/Users/test/a/b.ai", False, False],
            ["/Users/test/one.ai", "/Users/test/two.ai", False, False],
        ]
        code = PATH_GUARD_JS + "\nconst cases=" + json.dumps(cases) + ";\n"
        code += "for(const [a,b,w,expected] of cases){if(sameDocumentPath(a,b,w)!==expected)throw Error(JSON.stringify([a,b]));}"
        result = subprocess.run([node], input=code, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_doctor_never_claims_integration_ready(self):
        report = doctor.report(self.root / "missing.toml", "illustrator")
        self.assertEqual(report["mcp_config"]["status"], "not_configured")
        self.assertFalse(report["integration_ready"])
        self.assertEqual(report["illustrator_connection"], "unverified")
        self.assertEqual(report["image_generation"], "unverified")

    def test_doctor_missing_pillow_without_site_packages(self):
        result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/doctor.py"),
                                 "--config", str(self.root / "missing.toml")],
                                text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["runtime_ready"])
        self.assertEqual(report["pillow"]["status"], "missing_or_broken")

    def test_mcp_config_status_and_secret_redaction(self):
        config = self.root / "config.toml"
        command = json.dumps(sys.executable)
        config.write_text('[mcp_servers.custom]\ncommand = ' + command +
                          '\nargs = ["PRIVATE_SENTINEL"]\n[mcp_servers.custom.env]\nTOKEN = "PRIVATE_SENTINEL"\n', encoding="utf-8-sig")
        report = doctor.report(config, "custom")
        self.assertEqual(report["mcp_config"]["status"], "configured_unverified")
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(report))
        config.write_text('[mcp_servers.custom]\nenabled = false\ncommand = "missing"', encoding="utf-8")
        self.assertEqual(doctor.check_mcp(config, "custom")["status"], "disabled")
        config.write_text('[mcp_servers.custom]\ncommand = "no-such-command-abcxyz"', encoding="utf-8")
        self.assertEqual(doctor.check_mcp(config, "custom")["status"], "command_not_found")
        config.write_text("not TOML", encoding="utf-8")
        self.assertEqual(doctor.check_mcp(config, "custom")["status"], "config_unreadable_or_invalid")

    def test_copy_relocation_and_collision_preserves_existing_files(self):
        first = self.root / "安装 中文 (1)"
        second = self.root / "迁移 中文 (2)"
        install.copy_skill(ROOT, first)
        (first / ".venv").mkdir()
        (first / ".venv" / "private.txt").write_text("secret")
        install.copy_skill(first, second)
        self.assertFalse((second / ".venv").exists())
        install.copy_skill(first, second)  # Repeat is safe.
        (second / "README.md").write_text("user changes", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Existing different file"):
            install.copy_skill(first, second)
        self.assertEqual((second / "README.md").read_text(), "user changes")

    def test_install_dependency_failure_propagates(self):
        with patch.object(install, "copy_skill"), patch.object(install.platform, "system", return_value="Windows"), \
             patch.object(install.venv, "EnvBuilder"), \
             patch.object(install.subprocess, "run", side_effect=subprocess.CalledProcessError(1, ["pip"])):
            with self.assertRaises(subprocess.CalledProcessError):
                install.install(self.root / "install")

    def test_zip_allowlist_and_hashes(self):
        source = self.root / "source"
        install.copy_skill(ROOT, source)
        (source / "personal-config.toml").write_text("private")
        (source / "private.ai").write_text("private")
        output = self.root / "delivery.zip"
        report = build_delivery.build(source, output)
        self.assertEqual(report["sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
        with zipfile.ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertFalse(any("private" in name or "personal-config" in name or ".venv" in name for name in names))
            manifest = json.loads(archive.read("illustrator-local-artwork/MANIFEST.json"))
            for relative, digest in manifest["files_sha256"].items():
                self.assertEqual(hashlib.sha256(archive.read("illustrator-local-artwork/" + relative)).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
