"""Explicit allowlist shared by the installer and ZIP builder."""
from pathlib import Path

FILES = ("SKILL.md", "README.md", "RELEASING.md", "CHANGELOG.md", "VERSION",
         "requirements.txt", "install-windows.ps1", "install-macos.sh", "TESTING.md")
DIRECTORIES = ("scripts", "references", "agents", "tests")
SUFFIXES = {".py", ".md", ".yaml", ".json", ".js"}


def delivery_files(root: Path) -> list[Path]:
    result = [root / name for name in FILES]
    for name in DIRECTORIES:
        result.extend(path for path in (root / name).rglob("*")
                      if path.is_file() and path.suffix in SUFFIXES
                      and "__pycache__" not in path.parts)
    return sorted(result)
