"""
uvmgr.ops.indexes
-----------------
Persist extra index URLs in ~/.config/uvmgr/indexes.txt
"""

from __future__ import annotations

from pathlib import Path

from uvmgr.core.paths import CONFIG_DIR
from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span

_FILE: Path = CONFIG_DIR / "indexes.txt"


@timed
def add(url: str) -> None:
    with span("index.add", url=url):
        lines = {_FILE.read_text().splitlines(), url} if _FILE.exists() else {url}
        _FILE.write_text("\n".join(sorted(lines)) + "\n")


def list_indexes() -> list[str]:
    return _FILE.read_text().splitlines() if _FILE.exists() else []
