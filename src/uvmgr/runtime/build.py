from __future__ import annotations

import sys
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

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write("""#!/usr/bin/env python
import sys
from uvmgr.cli import app

if __name__ == "__main__":
    app()
""")
                entry_script = f.name

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

            # Add common hidden imports for uvmgr
            default_hidden_imports = [
                "uvmgr.commands",
                "uvmgr.ops", 
                "uvmgr.runtime",
                "uvmgr.core",
                "uvmgr.mcp",
                # Explicit command modules for dynamic loading
                "uvmgr.commands.deps",
                "uvmgr.commands.tests", 
                "uvmgr.commands.build",
                "uvmgr.commands.tool",
                "uvmgr.commands.serve",
                "uvmgr.commands.lint",
                "uvmgr.commands.ai",
                "uvmgr.commands.cache", 
                "uvmgr.commands.exec",
                "uvmgr.commands.shell",
                "uvmgr.commands.index",
                "uvmgr.commands.release",
                "uvmgr.commands.remote",
                "uvmgr.commands.ap_scheduler",
                "uvmgr.commands.history",
                "uvmgr.commands.weaver",
                "uvmgr.commands.search",
                "uvmgr.commands.claude",
                "uvmgr.commands.forge",
                "uvmgr.commands.agent",
                "uvmgr.commands.otel",
                "uvmgr.commands.workflow",
                "uvmgr.commands.spiff_otel",
                "uvmgr.commands.project",
                # Core submodules for dynamic loading
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
                # External libraries
                "typer",
                "rich", 
                "fastapi",
                "dspy",
                "ember_ai",
                "spiffworkflow",
                "apscheduler",
            ]
            for imp in default_hidden_imports:
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
                except:
                    pass

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
        all_hidden_imports = [
            "uvmgr.commands",
            "uvmgr.ops",
            "uvmgr.runtime",
            "uvmgr.core",
            "uvmgr.mcp",
            "typer",
            "rich",
            "fastapi",
            "dspy",
            "ember_ai",
            "spiffworkflow",
            "apscheduler",
        ] + hidden_imports

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
    """Test the built executable by running basic commands."""
    import subprocess

    with span("build.test_executable"):
        try:
            # Test 1: Check version
            result = subprocess.run(
                [str(exe_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                return {"success": False, "error": f"Version check failed: {result.stderr}"}

            # Test 2: Check help
            result = subprocess.run(
                [str(exe_path), "--help"], capture_output=True, text=True, timeout=10, check=False
            )
            if result.returncode != 0:
                return {"success": False, "error": f"Help check failed: {result.stderr}"}

            # Test 3: List commands
            result = subprocess.run(
                [str(exe_path)], capture_output=True, text=True, timeout=10, check=False
            )
            if result.returncode != 0:
                return {"success": False, "error": f"Command listing failed: {result.stderr}"}

            return {
                "success": True,
                "tests_passed": ["version", "help", "commands"],
                "executable": str(exe_path),
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Executable timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
