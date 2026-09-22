"""Install skill files and a local Python environment, never edit Codex config."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import venv

from delivery_files import delivery_files
from runtime_support import utf8_output

ROOT = Path(__file__).resolve().parents[1]


def copy_skill(source: Path, destination: Path) -> None:
    source, destination = source.resolve(), destination.resolve()
    if source == destination:
        return
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("Source and destination must not contain one another.")
    files = delivery_files(source)
    # Preflight every collision before writing anything. Never overwrite a user's edits.
    for path in files:
        target = destination / path.relative_to(source)
        if target.is_symlink() or target.resolve() != target.absolute():
            raise ValueError(f"Refusing symlink destination: {target}")
        if target.exists() and (not target.is_file() or target.read_bytes() != path.read_bytes()):
            raise ValueError(f"Existing different file: {target}. Choose a new directory or update in place.")
    for path in files:
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def install(destination: Path) -> Path:
    if sys.version_info < (3, 12):
        raise ValueError("Python 3.12 or newer is required.")
    if platform.system() not in ("Windows", "Darwin"):
        raise ValueError("This installer supports Windows and macOS only.")
    copy_skill(ROOT, destination)
    env = destination / ".venv"
    if env.is_symlink():
        raise ValueError("Refusing a symlink .venv; select a fresh install directory.")
    venv.EnvBuilder(with_pip=True).create(env)
    python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    child_env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(destination / "requirements.txt")], check=True, env=child_env)
    subprocess.run([str(python), str(destination / "scripts" / "doctor.py")], check=True, env=child_env)
    return python


def main() -> None:
    utf8_output()
    default_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=default_home / "skills" / "illustrator-local-artwork")
    args = parser.parse_args()
    try:
        python = install(args.destination.expanduser().resolve())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Installation failed: {exc}")
    print(f"Skill runtime installed. Use this Python for ALL skill commands: {python}")
    print("Next: references/setup.md. MCP connection and image generation remain unverified.")


if __name__ == "__main__":
    main()
