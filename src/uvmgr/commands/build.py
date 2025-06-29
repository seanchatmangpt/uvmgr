"""
uvmgr.commands.build - Package and Executable Building
====================================================

Build wheel, source distributions, and standalone executables.

This module provides CLI commands for building Python packages and standalone
executables using various build tools including uv, PyInstaller, and other
packaging utilities.

Key Features
-----------
• **Package Building**: Wheel and source distribution creation
• **Executable Building**: Standalone executables with PyInstaller
• **Spec Generation**: Customizable PyInstaller spec files
• **Self-Building**: Dogfood builds for uvmgr itself
• **Telemetry Integration**: Full OpenTelemetry instrumentation

Available Commands
-----------------
- **dist**: Build Python wheel and source distribution
- **exe**: Build standalone executable using PyInstaller
- **spec**: Generate PyInstaller spec file for customization
- **dogfood**: Build uvmgr executable (self-build demonstration)

Build Types
----------
- **Wheel/SDist**: Standard Python package distributions
- **Executable**: Standalone executables for distribution
- **Spec Files**: Customizable build configurations
- **Self-Build**: Recursive builds for uvmgr itself

Examples
--------
    >>> # Build package distribution
    >>> uvmgr build dist --upload
    >>> 
    >>> # Build standalone executable
    >>> uvmgr build exe --name my-app --onefile
    >>> 
    >>> # Generate spec file
    >>> uvmgr build spec --outfile custom.spec
    >>> 
    >>> # Self-build uvmgr
    >>> uvmgr build dogfood --version --test

See Also
--------
- :mod:`uvmgr.ops.build` : Build operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

import pathlib

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import BuildAttributes
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import build as build_ops

app = typer.Typer(help="Build wheel + sdist")


@app.callback()
def build_callback(ctx: typer.Context):
    """Build callback - default to dist if no subcommand provided."""
    if ctx.invoked_subcommand is None:
        # Default to dist command
        dist(ctx)


@app.command()
@instrument_command("build_dist", track_args=True)
def dist(
    ctx: typer.Context,
    outdir: pathlib.Path = typer.Option(None, "--outdir", "-o", file_okay=False),
    upload: bool = typer.Option(False, "--upload", help="Twine upload after build"),
):
    """Build Python wheel and source distribution."""
    # Track build operation
    add_span_attributes(
        **{
            BuildAttributes.OPERATION: "dist",
            BuildAttributes.TYPE: "wheel_sdist",
            "build.upload": upload,
        }
    )
    add_span_event("build.dist.started", {"upload": upload})
    payload = build_ops.dist(outdir)
    if upload:
        build_ops.upload(outdir or pathlib.Path("dist"))
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour("✔ build completed", "green")


@app.command("wheel")
@instrument_command("build_wheel", track_args=True)
def wheel(
    ctx: typer.Context,
    outdir: pathlib.Path = typer.Option(None, "--outdir", "-o", file_okay=False),
    upload: bool = typer.Option(False, "--upload", help="Twine upload after build"),
):
    """Build Python wheel (alias for dist command)."""
    # Track build operation with wheel alias
    add_span_attributes(
        **{
            BuildAttributes.OPERATION: "wheel",
            BuildAttributes.TYPE: "wheel_sdist",
            "build.upload": upload,
            "build.alias_for": "dist",
        }
    )
    add_span_event("build.wheel.started", {"upload": upload, "alias_for": "dist"})
    payload = build_ops.dist(outdir)
    if upload:
        build_ops.upload(outdir or pathlib.Path("dist"))
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour("✔ wheel build completed", "green")


@app.command("sdist")
@instrument_command("build_sdist", track_args=True)
def sdist(
    ctx: typer.Context,
    outdir: pathlib.Path = typer.Option(None, "--outdir", "-o", file_okay=False),
    upload: bool = typer.Option(False, "--upload", help="Twine upload after build"),
):
    """Build Python source distribution."""
    # Track build operation with sdist
    add_span_attributes(
        **{
            BuildAttributes.OPERATION: "sdist",
            BuildAttributes.TYPE: "sdist",
            "build.upload": upload,
        }
    )
    add_span_event("build.sdist.started", {"upload": upload})
    payload = build_ops.dist(outdir)
    if upload:
        build_ops.upload(outdir or pathlib.Path("dist"))
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour("✔ sdist build completed", "green")


@app.command()
@instrument_command("build_exe", track_args=True)
def exe(
    ctx: typer.Context,
    outdir: pathlib.Path = typer.Option(None, "--outdir", "-o", file_okay=False),
    name: str = typer.Option("uvmgr", "--name", "-n", help="Executable name"),
    onefile: bool = typer.Option(True, "--onefile/--onedir", help="Build single file"),
    clean: bool = typer.Option(True, "--clean/--no-clean", help="Clean build dirs"),
    spec_file: pathlib.Path | None = typer.Option(
        None, "--spec", "-s", help="Use existing spec file"
    ),
    icon: pathlib.Path | None = typer.Option(None, "--icon", "-i", help="Icon file"),
    hidden_imports: list[str] | None = typer.Option(
        None, "--hidden-import", "-H", help="Hidden imports"
    ),
    exclude_modules: list[str] | None = typer.Option(
        None, "--exclude", "-X", help="Exclude modules"
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Debug build process"),
):
    """Build standalone executable using PyInstaller."""
    # Track exe build
    add_span_attributes(
        **{
            BuildAttributes.OPERATION: "exe",
            BuildAttributes.TYPE: "executable",
            "build.onefile": onefile,
            "build.debug": debug,
        }
    )
    add_span_event("build.exe.started", {"name": name, "onefile": onefile})
    payload = build_ops.exe(
        outdir=outdir,
        name=name,
        onefile=onefile,
        clean=clean,
        spec_file=spec_file,
        icon=icon,
        hidden_imports=hidden_imports or [],
        exclude_modules=exclude_modules or [],
        debug=debug,
    )
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour(f"✔ executable built: {payload['output_file']}", "green")


@app.command()
@instrument_command("build_spec", track_args=True)
def spec(
    ctx: typer.Context,
    outfile: pathlib.Path = typer.Option("uvmgr.spec", "--outfile", "-o", help="Output spec file"),
    name: str = typer.Option("uvmgr", "--name", "-n", help="Executable name"),
    onefile: bool = typer.Option(True, "--onefile/--onedir", help="Build single file"),
    icon: pathlib.Path | None = typer.Option(None, "--icon", "-i", help="Icon file"),
    hidden_imports: list[str] | None = typer.Option(
        None, "--hidden-import", "-H", help="Hidden imports"
    ),
    exclude_modules: list[str] | None = typer.Option(
        None, "--exclude", "-X", help="Exclude modules"
    ),
):
    """Generate PyInstaller spec file for customization."""
    # Track spec generation
    add_span_attributes(
        **{
            BuildAttributes.OPERATION: "spec",
            BuildAttributes.TYPE: "spec_file",
        }
    )
    add_span_event("build.spec.started", {"outfile": str(outfile)})
    payload = build_ops.generate_spec(
        outfile=outfile,
        name=name,
        onefile=onefile,
        icon=icon,
        hidden_imports=hidden_imports or [],
        exclude_modules=exclude_modules or [],
    )
    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour(f"✔ spec file generated: {payload['spec_file']}", "green")


@app.command()
@instrument_command("build_dogfood", track_args=True)
def dogfood(
    ctx: typer.Context,
    outdir: pathlib.Path = typer.Option(None, "--outdir", "-o", file_okay=False),
    version: bool = typer.Option(False, "--version", "-v", help="Include version in name"),
    platform_suffix: bool = typer.Option(
        True, "--platform/--no-platform", help="Add platform suffix"
    ),
    test: bool = typer.Option(True, "--test/--no-test", help="Test built executable"),
):
    """Build uvmgr executable (eat own dog food).

    This command builds uvmgr as a standalone executable using PyInstaller,
    demonstrating that uvmgr can package itself.
    """
    # Track dogfood build (self-build)
    add_span_attributes(
        **{
            BuildAttributes.TYPE: "exe",
            "build.operation": "dogfood",
            "build.self_build": True,
            "build.include_version": version,
            "build.test": test,
        }
    )
    add_span_event("build.dogfood.started", {"recursive": True})
    import platform

    # Build executable name
    name = "uvmgr"
    if version:
        # Get version from pyproject.toml or default
        try:
            import tomllib

            with open("pyproject.toml", "rb") as f:
                pyproject = tomllib.load(f)
                pkg_version = pyproject.get("project", {}).get("version", "0.0.0")
        except:
            pkg_version = "0.0.0"
        name += f"-{pkg_version}"
    if platform_suffix:
        system = platform.system().lower()
        machine = platform.machine().lower()
        name += f"-{system}-{machine}"

    # Build the executable
    payload = build_ops.exe(
        outdir=outdir,
        name=name,
        onefile=True,
        clean=True,
        hidden_imports=[
            "uvmgr.commands.agent",
            "uvmgr.commands.ai",
            "uvmgr.commands.ap_scheduler",
            "uvmgr.commands.build",
            "uvmgr.commands.cache",
            "uvmgr.commands.deps",
            "uvmgr.commands.exec",
            "uvmgr.commands.index",
            "uvmgr.commands.lint",
            "uvmgr.commands.project",
            "uvmgr.commands.release",
            "uvmgr.commands.remote",
            "uvmgr.commands.serve",
            "uvmgr.commands.shell",
            "uvmgr.commands.tests",
            "uvmgr.commands.tool",
        ],
        exclude_modules=[
            "matplotlib",
            "numpy",
            "pandas",
            "scipy",
            "PIL",
            "tkinter",
        ],
    )

    if test:
        # Test the built executable
        test_result = build_ops.test_executable(pathlib.Path(payload["output_file"]))
        payload["test_result"] = test_result

    if ctx.meta.get("json"):
        dump_json(payload)
    else:
        colour(f"✔ uvmgr executable built: {payload['output_file']}", "green")
        if test:
            if payload["test_result"]["success"]:
                colour("✔ executable test passed", "green")
            else:
                colour(f"✗ executable test failed: {payload['test_result']['error']}", "red")
