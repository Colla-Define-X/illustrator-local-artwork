"""Small shared helpers; no Adobe or host configuration side effects."""
from __future__ import annotations

import sys
import re


def source_path_is_unambiguous(path: str) -> bool:
    # Illustrator 28.6 can report literal %20 as a space in Document.fullName
    # even though the file on disk still contains %20. Never weaken identity checks.
    return re.search(r"%[0-9a-fA-F]{2}", path) is None


def utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


# Kept separately so the actual ExtendScript comparison can be executed in tests.
# macOS paths may contain a literal backslash. Only Windows treats it as a separator.
PATH_GUARD_JS = r"""
function normPath(v,isWindows){
 var value=String(v);
 return isWindows?value.replace(/\\/g,'/').toLowerCase():value;
}
function sameDocumentPath(actual,expected,isWindows){
 return normPath(actual,isWindows)===normPath(expected,isWindows);
}
"""
