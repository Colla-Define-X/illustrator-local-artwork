"""Build an allowlisted ZIP with per-file hashes; no local settings or assets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from delivery_files import delivery_files
from runtime_support import utf8_output

ROOT = Path(__file__).resolve().parents[1]


def build(root: Path, output: Path) -> dict:
    hashes = {}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in delivery_files(root):
            relative = path.relative_to(root).as_posix()
            content = path.read_bytes()
            hashes[relative] = hashlib.sha256(content).hexdigest()
            archive.writestr("illustrator-local-artwork/" + relative, content)
        archive.writestr("illustrator-local-artwork/MANIFEST.json", json.dumps({
            "version": (root / "VERSION").read_text().strip(), "files_sha256": hashes,
        }, indent=2))
    return {"file": str(output), "files": len(hashes), "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main() -> None:
    utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(ROOT, parser.parse_args().output.resolve()), ensure_ascii=False))


if __name__ == "__main__":
    main()
