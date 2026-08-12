"""Runtime manufacture and verification for distributions and executables."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from uvmgr.core.command_registry import admitted_command_names as resolve_admitted_commands
from uvmgr.core.command_repairs import repaired_command_module_names
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
    return tuple(
        f"uvmgr.{package}.{name}"
        for name in _admitted_command_names()
        for package in ("commands", "ops", "runtime")
        if (source_root / package / f"{name}.py").is_file()
    )


def _default_hidden_imports() -> tuple[str, ...]:
    """Return deterministic PyInstaller closure for every admitted command."""
    return tuple(dict.fromkeys((*_BASE_HIDDEN_IMPORTS, *_admitted_layer_imports())))


def _command_repair_data_files() -> tuple[tuple[Path, str], ...]:
    """Return source files required by the identity-checked command repair loader."""
    command_dir = Path(__file__).parent.parent / "commands"
    return tuple(
        (command_dir / f"{fullname.rpartition('.')[2]}.py", "uvmgr/commands")
        for fullname in repaired_command_module_names()
    )


def _create_entry_script() -> str:
    """Create the bounded PyInstaller entry script and return its path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as file_handle:
        file_handle.write("""#!/usr/bin/env python
from uvmgr.cli import app

if __name__ == "__main__":
    app()
""")
        entry_script = file_handle.name
    os.chmod(entry_script, 0o600)
    return entry_script


def _pyinstaller_args(  # noqa: PLR0913
    *,
    name: str,
    onefile: bool,
    clean: bool,
    spec_file: Path | None,
    icon: Path | None,
    hidden_imports: list[str],
    exclude_modules: list[str],
) -> tuple[list[str], str | None]:
    """Construct deterministic PyInstaller argv and optional temporary entry path."""
    if spec_file is not None:
        return ["pyinstaller", str(spec_file)], None

    entry_script = _create_entry_script()
    args = ["pyinstaller", entry_script, "--name", name]
    if onefile:
        args.append("--onefile")
    if clean:
        args.append("--clean")
    if icon:
        args.extend(["--icon", str(icon)])
    for imp in hidden_imports:
        args.extend(["--hidden-import", imp])
    for module in exclude_modules:
        args.extend(["--exclude-module", module])
    for imp in _default_hidden_imports():
        if imp not in hidden_imports:
            args.extend(["--hidden-import", imp])
    for source, destination in _command_repair_data_files():
        args.extend(["--add-data", f"{source}{os.pathsep}{destination}"])
    return args, entry_script


def _executable_output_path(outdir: Path, *, name: str, onefile: bool) -> Path:
    """Return the platform-specific path manufactured by PyInstaller."""
    suffix = ".exe" if sys.platform == "win32" else ""
    if onefile:
        return outdir / f"{name}{suffix}"
    return outdir / name / f"{name}{suffix}"


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
    output_directory = outdir or Path("dist")
    args, entry_script = _pyinstaller_args(
        name=name,
        onefile=onefile,
        clean=clean,
        spec_file=spec_file,
        icon=icon,
        hidden_imports=hidden_imports or [],
        exclude_modules=exclude_modules or [],
    )
    if outdir is not None:
        args.extend(["--distpath", str(outdir)])
    if debug:
        args.append("--debug=all")

    with span("build.exe"):
        try:
            run_logged(args)
        finally:
            if entry_script is not None:
                try:
                    os.unlink(entry_script)
                except OSError as exc:
                    _LOGGER.warning(
                        "Failed to clean up temporary entry script %s: %s",
                        entry_script,
                        exc,
                    )
    return _executable_output_path(output_directory, name=name, onefile=onefile)


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
        repair_datas = [
            (str(source), destination)
            for source, destination in _command_repair_data_files()
        ]

        entry_script_content = """#!/usr/bin/env python
from uvmgr.cli import app

if __name__ == "__main__":
    app()
"""

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Generated by uvmgr for PyInstaller

entry_script = """{entry_script_content}"""

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
    datas={repair_datas!r},
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

os.unlink(entry_file)
"""

        outfile.write_text(spec_content)
        return outfile


def _probe_executable(exe_path: Path, arguments: list[str], label: str) -> dict | None:
    """Execute one frozen-binary probe and classify structural failure."""
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
    incomplete_markers = ("BUILD_BROKEN:", "UNSUPPORTED:")
    marker = next((item for item in incomplete_markers if item in output), None)
    if marker is not None:
        return {
            "success": False,
            "error": f"{label} exposed incomplete standing {marker}: {output.strip()}",
        }
    return None


def test_executable(exe_path: Path) -> dict:
    """Verify the frozen executable and every command admitted by its source registry."""
    commands_tested = list(_admitted_command_names())
    probes = [
        (["--version"], "Version check"),
        (["--help"], "Help check"),
        *[([command, "--help"], f"Admitted command {command!r}") for command in commands_tested],
        (["capabilities", "verify"], "Frozen capability verification"),
    ]
    try:
        for arguments, label in probes:
            failure = _probe_executable(exe_path, arguments, label)
            if failure is not None:
                return failure
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Executable probe timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

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
