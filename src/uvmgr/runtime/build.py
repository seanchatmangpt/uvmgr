from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import span


_BASE_HIDDEN_IMPORTS = (
    "uvmgr.commands",
    "uvmgr.ops",
    "uvmgr.runtime",
    "uvmgr.core",
    "uvmgr.mcp",
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


def _admitted_layer_imports() -> tuple[str, ...]:
    """Project the canonical command registry into frozen import closure."""
    import uvmgr.commands as commands_package

    modules: list[str] = []
    for name in commands_package.__all__:
        for package in ("uvmgr.commands", "uvmgr.ops", "uvmgr.runtime"):
            module = f"{package}.{name}"
            if importlib.util.find_spec(module) is not None:
                modules.append(module)
    return tuple(modules)


def _default_hidden_imports() -> tuple[str, ...]:
    """Return deterministic PyInstaller closure for every admitted command."""
    return tuple(dict.fromkeys((*_BASE_HIDDEN_IMPORTS, *_admitted_layer_imports())))


def dist(outdir: Path | None = None) -> None:
    args = ["python", "-m", "build"]
    if outdir:
        args += ["--outdir", str(outdir)]
    with span("build.dist"):
        run_logged(args)


def upload(dist_dir: Path = Path("dist")) -> None:
    with span("build.upload"):
        run_logged(["twine", "upload", str(dist_dir / "*")])


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
) -> Path:
    """Build executable using PyInstaller."""
    with span("build.exe"):
        args = ["pyinstaller"]

        # If spec file provided, use it
        if spec_file:
            args.append(str(spec_file))
        else:
            # Build from entry point - create a temporary entry script
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("""#!/usr/bin/env python
import sys
from uvmgr.cli import app

if __name__ == "__main__":
    app()
""")
                entry_script = f.name
                # Secure temp file permissions - readable/writable only by owner
                os.chmod(entry_script, 0o600)

            args.append(entry_script)
            args.extend(["--name", name])

            if onefile:
                args.append("--onefile")

            if clean:
                args.append("--clean")

            if icon:
                args.extend(["--icon", str(icon)])

            # Add hidden imports
            for imp in hidden_imports:
                args.extend(["--hidden-import", imp])

            # Add exclude modules
            for mod in exclude_modules:
                args.extend(["--exclude-module", mod])

            # Freeze the same command graph admitted by the runtime registry.
            for imp in _default_hidden_imports():
                if imp not in hidden_imports:
                    args.extend(["--hidden-import", imp])

        if outdir:
            args.extend(["--distpath", str(outdir)])
        else:
            outdir = Path("dist")

        if debug:
            args.append("--debug=all")

        # Add data files for MCP resources
        mcp_resources = Path(__file__).parent.parent / "mcp" / "resources.py"
        if mcp_resources.exists():
            args.extend(["--add-data", f"{mcp_resources}:uvmgr/mcp"])

        # Add litellm data files
        try:
            import litellm
            litellm_path = Path(litellm.__file__).parent
            for data_file in litellm_path.glob("*.json"):
                args.extend(["--add-data", f"{data_file}:litellm"])
        except ImportError:
            pass  # litellm not available

        try:
            run_logged(args)
        finally:
            # Clean up temporary entry script
            if not spec_file and "entry_script" in locals():
                import os

                try:
                    os.unlink(entry_script)
                except OSError as e:
                    # Log cleanup failure but don't block
                    _log.warning("Failed to clean up temporary entry script %s: %s", entry_script, e)

        # Return path to built executable
        if onefile:
            if sys.platform == "win32":
                return outdir / f"{name}.exe"
            return outdir / name
        if sys.platform == "win32":
            return outdir / name / f"{name}.exe"
        return outdir / name / name


def generate_spec(
    outfile: Path,
    name: str = "uvmgr",
    onefile: bool = True,
    icon: Path | None = None,
    hidden_imports: list[str] = [],
    exclude_modules: list[str] = [],
) -> Path:
    """Generate PyInstaller spec file."""
    with span("build.generate_spec"):
        # Build default hidden imports list
        all_hidden_imports = list(
            dict.fromkeys((*_default_hidden_imports(), *hidden_imports))
        )

        # Create entry script content
        entry_script_content = """#!/usr/bin/env python
import sys
from uvmgr.cli import app

if __name__ == "__main__":
    app()
"""

        # Generate spec file content
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
    datas=[
        ('src/uvmgr/mcp/resources.py', 'uvmgr/mcp'),
    ],
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

        # Write spec file
        outfile.write_text(spec_content)
        return outfile


def test_executable(exe_path: Path) -> dict:
    """Verify the frozen executable and every command admitted by its source registry."""
    import subprocess

    import uvmgr.commands as commands_package

    incomplete_markers = ("BUILD_BROKEN:", "UNSUPPORTED:", "REFUSED:")

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
            for command in commands_package.__all__:
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
        except Exception as e:
            return {"success": False, "error": str(e)}
