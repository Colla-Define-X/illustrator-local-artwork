"""Read-only runtime and MCP configuration checks. Never launch Illustrator."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import sys

from runtime_support import utf8_output


def check_pillow() -> dict:
    try:
        from PIL import Image, __version__
        Image.new("RGBA", (1, 1)).close()
        supported = 10 <= int(__version__.split(".")[0]) < 13
        return {"status": "ok" if supported else "unsupported", "version": __version__}
    except (ImportError, OSError, ValueError) as exc:
        return {"status": "missing_or_broken", "error_type": type(exc).__name__}


def check_mcp(config: Path, server_name: str) -> dict:
    if not config.is_file():
        return {"status": "not_configured"}
    try:
        import tomllib
        data = tomllib.loads(config.read_text(encoding="utf-8-sig"))
        server = data.get("mcp_servers", {}).get(server_name)
        if not isinstance(server, dict):
            return {"status": "not_configured"}
        if server.get("enabled", True) is False:
            return {"status": "disabled"}
        if server.get("url"):
            return {"status": "configured_remote_unverified"}
        command = server.get("command")
        if not isinstance(command, str) or not command:
            return {"status": "invalid_command"}
        path = Path(command)
        available = path.is_file() if path.is_absolute() else bool(shutil.which(command))
        # Do not print arguments/env: they can contain credentials. Presence is not connectivity.
        return {"status": "configured_unverified" if available else "command_not_found"}
    except (ValueError, OSError, ImportError, TypeError, AttributeError):
        return {"status": "config_unreadable_or_invalid"}


def report(config: Path, server_name: str) -> dict:
    system = platform.system()
    python_ok = sys.version_info >= (3, 12)
    pillow = check_pillow()
    return {
        "os": system, "architecture": platform.machine(),
        "python": {"version": platform.python_version(), "executable": sys.executable,
                   "status": "ok" if python_ok else "unsupported"},
        "pillow": pillow,
        "runtime_ready": python_ok and pillow["status"] == "ok" and system in ("Windows", "Darwin"),
        "mcp_config": check_mcp(config, server_name),
        "illustrator_connection": "unverified",
        "image_generation": "unverified",
        "integration_ready": False,
    }


def main() -> None:
    utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--config", type=Path, default=home / "config.toml")
    parser.add_argument("--server-name", default="illustrator")
    args = parser.parse_args()
    result = report(args.config.expanduser(), args.server_name)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["runtime_ready"] else 1)


if __name__ == "__main__":
    main()
