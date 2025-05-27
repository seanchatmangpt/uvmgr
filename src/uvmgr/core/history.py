"""
uvmgr.core.history – recent artefact tracker (≤100 entries).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List

from .paths import CONFIG_DIR
from .shell import rich_table

HIST: Path = CONFIG_DIR / "history.json"


def _load() -> list[dict]:
    return json.loads(HIST.read_text()) if HIST.exists() else []


def log_output(p: Path) -> None:
    recs = _load()
    recs.append({"ts": datetime.now().isoformat(), "file": str(p)})
    HIST.write_text(json.dumps(recs[-100:]))


def last_files(n: int = 5) -> list[Path]:
    return [Path(r["file"]) for r in _load()[-n:]]


def history_menu(n: int = 10) -> None:
    files = last_files(n)
    rich_table(["#", "file"], [(i + 1, f) for i, f in enumerate(files)])
    try:
        sel = int(input("Open which? ")) - 1
        os.system(f"${{EDITOR:-nano}} '{files[sel]}'")
    except (ValueError, IndexError):
        print("cancelled")
