#!/bin/bash
set -euo pipefail
if [ "$(uname -s)" != "Darwin" ]; then
  echo 'Use install-windows.ps1 on Windows.' >&2
  exit 1
fi
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON_BIN:-python3}" "$SCRIPT_DIR/scripts/install.py" "$@"
