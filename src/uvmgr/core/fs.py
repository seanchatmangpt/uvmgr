"""
uvmgr.core.fs – hashing, atomic writes, temp helpers.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from .paths import CACHE_DIR

__all__ = [
    "atomic_copy",
    "auto_name",
    "hash_bytes",
    "hash_file",
    "hash_str",
    "safe_write",
    "tempfile_in_cache",
]

_BLOCK = 1 << 20  # 1 MiB


def _digest(algo: str) -> hashlib._Hash:  # type: ignore[attr-defined]
    return hashlib.new(algo)


def hash_file(path: Path, *, algo: str = "sha1") -> str:
    h = _digest(algo)
    with path.open("rb") as fh:
        while chunk := fh.read(_BLOCK):
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes, *, algo: str = "sha1") -> str:
    return _digest(algo)(data).hexdigest()


def hash_str(text: str, *, algo: str = "sha1") -> str:
    return hash_bytes(text.encode(), algo=algo)


def safe_write(path: Path, data: str | bytes, *, mode: str | None = None) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    if isinstance(data, str):
        tmp.write_text(data, encoding="utf-8")
    else:
        tmp.write_bytes(data)
    if mode:
        tmp.chmod(int(mode, 8))
    tmp.replace(path)


def atomic_copy(src: Path, dst: Path) -> None:
    tmp = dst.with_suffix(".tmp")
    shutil.copy2(src, tmp)
    tmp.replace(dst)


def auto_name(prefix: str, ext: str = ".txt") -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(f"{prefix}_{ts}{ext}")


def tempfile_in_cache(*, suffix: str = "") -> Path:
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    fd, name = tempfile.mkstemp(dir=CACHE_DIR, suffix=suffix)
    os.close(fd)
    return Path(name)
