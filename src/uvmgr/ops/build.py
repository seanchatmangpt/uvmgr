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


@timed
def exe(
    outdir: Path | None = None,
    name: str = "uvmgr",
    onefile: bool = True,
    clean: bool = True,
    spec_file: Path | None = None,
    icon: Path | None = None,
    hidden_imports: list[str] = [],
    exclude_modules: list[str] = [],
    debug: bool = False,
) -> dict:
    """Build executable using PyInstaller."""
    output_file = _rt.exe(
        outdir=outdir,
        name=name,
        onefile=onefile,
        clean=clean,
        spec_file=spec_file,
        icon=icon,
        hidden_imports=hidden_imports,
        exclude_modules=exclude_modules,
        debug=debug,
    )
    return {
        "output_file": str(output_file),
        "name": name,
        "type": "onefile" if onefile else "onedir",
    }


@timed
def generate_spec(
    outfile: Path,
    name: str = "uvmgr",
    onefile: bool = True,
    icon: Path | None = None,
    hidden_imports: list[str] = [],
    exclude_modules: list[str] = [],
) -> dict:
    """Generate PyInstaller spec file."""
    spec_path = _rt.generate_spec(
        outfile=outfile,
        name=name,
        onefile=onefile,
        icon=icon,
        hidden_imports=hidden_imports,
        exclude_modules=exclude_modules,
    )
    return {"spec_file": str(spec_path)}


@timed
def test_executable(exe_path: Path) -> dict:
    """Test the built executable."""
    result = _rt.test_executable(exe_path)
    return result
