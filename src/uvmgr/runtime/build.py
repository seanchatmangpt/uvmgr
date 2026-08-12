from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from uvmgr.core.command_registry import admitted_command_names as resolve_admitted_commands
from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span

_LOGGER = logging.getLogger(__name__)

_BASE_HIDDEN_IMPORTS = (
    "uvmgr.commands",
    "uvmgr.ops",
    "uvmgr.runtime",
    "uvmgr.core",
    "uvmgr.core.cache",
    "uvmgr.core.clipboard",
    "uvmgr.core.concurrency",
    "uvmgr.core.config",
    "uvmgr.core.fs",
    "uvmgr.core.history",
    "uvmgr.core.instrumentation",
    "uvmgr.core.lint",
    "uvmgr.core.metrics",
    "uvmgr.core.paths",
    "uvmgr.core.process",
    "uvmgr.core.semconv",
    "uvmgr.core.shell",
    "uvmgr.core.telemetry",
    "uvmgr.core.venv",
    "uvmgr.core.workspace",
    "typer",
    "rich",
    "fastapi",
    "apscheduler",
)


def _discover_command_sources() -> set[str]:
    """Discover physical command modules without importing the command layer."""
    command_dir = Path(__file__).parent.parent / "commands"
    return {
        path.stem
        for path in command_dir.glob("*.py")
        if path.stem != "__init__"
        and not path.stem.startswith("_")
        and not path.stem.endswith("_backup")
    }


def _admitted_command_names() -> tuple[str, ...]:
    """Resolve the command ontology against the current source projection."""
    return resolve_admitted_commands(_discover_command_sources())


def _admitted_layer_imports() -> tuple[str, ...]:
    """Project admitted commands into frozen Command/Ops/Runtime module closure."""
    source_root = Path(__file__).parent.parent
    modules: list[str] = []
    for name in _admitted_command_names():
        for package in ("commands", "ops", "runtime"):
            if (source_root / package / f"{name}.py").is_file():
                modules.append(f"uvmgr.{package}.{name}")
    return tuple(modules)


def _default_hidden_imports() -> tuple[str, ...]:
    """Return deterministic PyInstaller closure for every admitted command."""
    return tuple(dict.fromkeys((*_BASE_HIDDEN_IMPORTS, *_admitted_layer_imports())))


def dist(outdir: Path | None = None) -> None:
    """Build wheel and source distributions."""
    args = ["python", "-m", "build"]
    if outdir:
        args += ["--outdir", str(outdir)]
    with span("build.dist"):
        run_logged(args)


def upload(dist_dir: Path = Path("dist")) -> None:
    """Upload manufactured distributions with Twine."""
    with span("build.upload"):
        run_logged(["twine", "upload", str(dist_dir / "*")])


def exe(  # noqa: PLR0913
    outdir: Path | None = None,
    name: str = "uvmgr",
    onefile: bool = True,
    clean: bool = True,
    spec_file: Path | None = None,
    icon: Path | None = None,
    hidden_imports: list[str] | None = None,
    exclude_modules: list[str] | None = None,
    debug: bool = False,
) -> Path:
    """Build executable using PyInstaller."""
    hidden_imports = hidden_imports or []
    exclude_modules = exclude_modules or []
    with span("build.exe"):
        args = ["pyinstaller"]

        if spec_file:
            args.append(str(spec_file))
        else:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("""#!/usr/bin/env python
import sys
from uvmgr.cli import app

if __name__ == "__main__":
    app()
""")
                entry_script = f.name
                os.chmod(entry_script, 0o600)

            args.append(entry_script)
            args.extend(["--name", name])

            if onefile:
                args.append("--onefile")

            if clean:
                args.append("--clean")

            if icon:
                args.extend(["--icon", str(icon)])

            for imp in hidden_imports:
                args.extend(["--hidden-import", imp])

            for mod in exclude_modules:
                args.extend(["--exclude-module", mod])

            for imp in _default_hidden_imports():
                if imp not in hidden_imports:
                    args.extend(["--hidden-import", imp])

        if outdir:
            args.extend(["--distpath", str(outdir)])
        else:
            outdir = Path("dist")

        if debug:
            args.append("--debug=all")

        try:
            run_logged(args)
        finally:
            if not spec_file and "entry_script" in locals():
                try:
                    os.unlink(entry_script)
                except OSError as exc:
                    _LOGGER.warning(
                        "Failed to clean up temporary entry script %s: %s",
                        entry_script,
                        exc,
                    )

        if onefile:
            if sys.platform == "win32":
                return outdir / f"{name}.exe"
            return outdir / name
        if sys.platform == "win32":
            return outdir / name / f"{name}.exe"
        return outdir / name / name


def generate_spec(  # noqa: PLR0913
    outfile: Path,
    name: str = "uvmgr",
    onefile: bool = True,
    icon: Path | None = None,
    hidden_imports: list[str] | None = None,
    exclude_modules: list[str] | None = None,
) -> Path:
    """Generate PyInstaller spec file."""
    hidden_imports = hidden_imports or []
    exclude_modules = exclude_modules or []
    with span("build.generate_spec"):
        all_hidden_imports = list(
            dict.fromkeys((*_default_hidden_imports(), *hidden_imports))
        )

        entry_script_content = """#!/usr/bin/env python
import sys
from uvmgr.cli import app

if __name__ == "__main__":
    app()
"""

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Generated by uvmgr for PyInstaller

# Entry script content
entry_script = """{entry_script_content}"""

# Write entry script
import tempfile
import os
entry_file = tempfile.mktemp(suffix='.py')
with open(entry_file, 'w') as f:
    f.write(entry_script)

block_cipher = None

a = Analysis(
    [entry_file],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports={all_hidden_imports!r},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={exclude_modules!r},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

'''

        if onefile:
            spec_content += f"""exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
"""
            if icon:
                spec_content += f"    icon='{icon}',\n"
            spec_content += ")\n"
        else:
            spec_content += f"""exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
"""
            if icon:
                spec_content += f"    icon='{icon}',\n"
            spec_content += f""")

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{name}',
)

# Cleanup entry file after build
os.unlink(entry_file)
"""

        outfile.write_text(spec_content)
        return outfile


def test_executable(exe_path: Path) -> dict:
    """Verify the frozen executable and every command admitted by its source registry."""
    incomplete_markers = ("BUILD_BROKEN:", "UNSUPPORTED:")

    def probe(arguments: list[str], label: str) -> dict | None:
        result = subprocess.run(
            [str(exe_path), *arguments],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"{label} failed with exit {result.returncode}: {output.strip()}",
            }
        marker = next((item for item in incomplete_markers if item in output), None)
        if marker is not None:
            return {
                "success": False,
                "error": f"{label} exposed incomplete standing {marker}: {output.strip()}",
            }
        return None

    with span("build.test_executable"):
        try:
            failure = probe(["--version"], "Version check")
            if failure is not None:
                return failure

            failure = probe(["--help"], "Help check")
            if failure is not None:
                return failure

            commands_tested: list[str] = []
            for command in _admitted_command_names():
                failure = probe([command, "--help"], f"Admitted command {command!r}")
                if failure is not None:
                    return failure
                commands_tested.append(command)

            failure = probe(["capabilities", "verify"], "Frozen capability verification")
            if failure is not None:
                return failure

            return {
                "success": True,
                "tests_passed": [
                    "version",
                    "help",
                    "admitted_commands",
                    "capabilities_verify",
                ],
                "commands_tested": commands_tested,
                "command_count": len(commands_tested),
                "executable": str(exe_path),
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Executable probe timed out"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
