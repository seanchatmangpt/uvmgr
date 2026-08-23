"""Build package distributions and standalone executables.

The build command surface delegates package and PyInstaller manufacture to the
Ops and Runtime layers while preserving CLI telemetry and typed exit behavior.
"""

import pathlib
import platform
import tomllib
from typing import Annotated, Final

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import BuildAttributes
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import build as build_ops

app = typer.Typer(help="Build wheel + sdist")
_DEFAULT_SPEC_FILE: Final = pathlib.Path("uvmgr.spec")


@app.command()
@instrument_command("build_dist", track_args=True)
def dist(
    ctx: typer.Context,
    outdir: Annotated[
        pathlib.Path | None,
        typer.Option("--outdir", "-o", file_okay=False),
    ] = None,
    upload: Annotated[
        bool,
        typer.Option("--upload", help="Twine upload after build"),
    ] = False,
):
    """Build Python wheel and source distribution."""
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
    outdir: Annotated[
        pathlib.Path | None,
        typer.Option("--outdir", "-o", file_okay=False),
    ] = None,
    upload: Annotated[
        bool,
        typer.Option("--upload", help="Twine upload after build"),
    ] = False,
):
    """Build Python wheel as an alias for the distribution command."""
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
    outdir: Annotated[
        pathlib.Path | None,
        typer.Option("--outdir", "-o", file_okay=False),
    ] = None,
    upload: Annotated[
        bool,
        typer.Option("--upload", help="Twine upload after build"),
    ] = False,
):
    """Build Python source distribution."""
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
def exe(  # noqa: PLR0913
    ctx: typer.Context,
    outdir: Annotated[
        pathlib.Path | None,
        typer.Option("--outdir", "-o", file_okay=False),
    ] = None,
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="Executable name"),
    ] = "uvmgr",
    onefile: Annotated[
        bool,
        typer.Option("--onefile/--onedir", help="Build single file"),
    ] = True,
    clean: Annotated[
        bool,
        typer.Option("--clean/--no-clean", help="Clean build dirs"),
    ] = True,
    spec_file: Annotated[
        pathlib.Path | None,
        typer.Option("--spec", "-s", help="Use existing spec file"),
    ] = None,
    icon: Annotated[
        pathlib.Path | None,
        typer.Option("--icon", "-i", help="Icon file"),
    ] = None,
    hidden_imports: Annotated[
        list[str] | None,
        typer.Option("--hidden-import", "-H", help="Hidden imports"),
    ] = None,
    exclude_modules: Annotated[
        list[str] | None,
        typer.Option("--exclude", "-X", help="Exclude modules"),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Debug build process"),
    ] = False,
):
    """Build standalone executable using PyInstaller."""
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
def spec(  # noqa: PLR0913
    ctx: typer.Context,
    outfile: Annotated[
        pathlib.Path,
        typer.Option("--outfile", "-o", help="Output spec file"),
    ] = _DEFAULT_SPEC_FILE,
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="Executable name"),
    ] = "uvmgr",
    onefile: Annotated[
        bool,
        typer.Option("--onefile/--onedir", help="Build single file"),
    ] = True,
    icon: Annotated[
        pathlib.Path | None,
        typer.Option("--icon", "-i", help="Icon file"),
    ] = None,
    hidden_imports: Annotated[
        list[str] | None,
        typer.Option("--hidden-import", "-H", help="Hidden imports"),
    ] = None,
    exclude_modules: Annotated[
        list[str] | None,
        typer.Option("--exclude", "-X", help="Exclude modules"),
    ] = None,
):
    """Generate PyInstaller spec file for customization."""
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
    outdir: Annotated[
        pathlib.Path | None,
        typer.Option("--outdir", "-o", file_okay=False),
    ] = None,
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Include version in name"),
    ] = False,
    platform_suffix: Annotated[
        bool,
        typer.Option("--platform/--no-platform", help="Add platform suffix"),
    ] = True,
    test: Annotated[
        bool,
        typer.Option("--test/--no-test", help="Test built executable"),
    ] = True,
):
    """Build and optionally verify a standalone uvmgr executable."""
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

    name = "uvmgr"
    if version:
        try:
            with open("pyproject.toml", "rb") as file_handle:
                pyproject = tomllib.load(file_handle)
                pkg_version = pyproject.get("project", {}).get("version", "0.0.0")
        except (OSError, tomllib.TOMLDecodeError, TypeError, AttributeError):
            pkg_version = "0.0.0"
        name += f"-{pkg_version}"
    if platform_suffix:
        system = platform.system().lower()
        machine = platform.machine().lower()
        name += f"-{system}-{machine}"

    payload = build_ops.exe(
        outdir=outdir,
        name=name,
        onefile=True,
        clean=True,
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
    if test and not payload["test_result"]["success"]:
        raise typer.Exit(1)
