from __future__ import annotations

from pathlib import Path

from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span


def dist(outdir: Path | None = None) -> None:
    args = ["python", "-m", "build"]
    if outdir:
        args += ["--outdir", str(outdir)]
    with span("build.dist"):
        run_logged(args)


def upload(dist_dir: Path = Path("dist")) -> None:
    with span("build.upload"):
        run_logged(["twine", "upload", str(dist_dir / "*")])
