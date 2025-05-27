from __future__ import annotations

from pathlib import Path

from uvmgr.core.shell import timed
from uvmgr.runtime import build as _rt


@timed
def dist(outdir: Path | None = None) -> dict:
    _rt.dist(outdir)
    return {"built": str(outdir or "dist/")}


@timed
def upload(dist_dir: Path = Path("dist")) -> dict:
    _rt.upload(dist_dir)
    return {"uploaded": str(dist_dir)}
