"""
uvmgr.core.cache – SHA1 command-result cache.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .fs import hash_str
from .paths import CACHE_DIR

_RUNS = CACHE_DIR / "runs.jsonl"
_RUNS.touch(exist_ok=True)

__all__ = ["cache_hit", "hash_cmd", "store_result"]


def hash_cmd(cmd: str) -> str:
    return hash_str(cmd)


def cache_hit(cmd: str) -> bool:
    h = hash_cmd(cmd)
    return any(h in line for line in _RUNS.read_text().splitlines())


def store_result(cmd: str) -> None:
    _RUNS.write_text(json.dumps({"k": hash_cmd(cmd), "ts": time.time()}) + "\n", append=True)  # type: ignore[arg-type]
