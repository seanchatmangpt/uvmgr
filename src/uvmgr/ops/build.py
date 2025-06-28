from __future__ import annotations

from pathlib import Path
import time

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span
from uvmgr.core.metrics import build_metrics, OperationResult
from uvmgr.core.semconv import BuildAttributes
from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.runtime import build as _rt


@timed
def dist(outdir: Path | None = None) -> dict:
    start_time = time.time()
    
    with span("ops.build.dist", outdir=str(outdir) if outdir else "dist"):
        add_span_attributes(**{
            BuildAttributes.TYPE: "wheel_sdist",
            BuildAttributes.OUTPUT_PATH: str(outdir or "dist/"),
        })
        add_span_event("build.dist.started", {"output_dir": str(outdir or "dist/")})
        
        try:
            _rt.dist(outdir)
            
            # Calculate size of built artifacts
            dist_path = outdir or Path("dist")
            artifacts_size = 0
            if dist_path.exists():
                for artifact in dist_path.glob("*"):
                    artifacts_size += artifact.stat().st_size
            
            # Record successful build metrics
            duration = time.time() - start_time
            result = OperationResult(success=True, duration=duration, metadata={
                "artifact_type": "wheel_sdist",
                "artifact_size": artifacts_size,
                "output_path": str(outdir or "dist/"),
            })
            build_metrics.record_wheel(artifacts_size, str(outdir or "dist/"), result)
            
            add_span_attributes(**{"build.artifacts_size": artifacts_size})
            add_span_event("build.dist.completed", {
                "output_dir": str(outdir or "dist/"),
                "artifacts_size": artifacts_size,
                "success": True
            })
            
            return {"built": str(outdir or "dist/")}
            
        except Exception as e:
            # Record failed build metrics
            duration = time.time() - start_time
            result = OperationResult(success=False, duration=duration, error=e)
            build_metrics.record_wheel(0, str(outdir or "dist/"), result)
            
            add_span_event("build.dist.failed", {"error": str(e)})
            raise


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
    start_time = time.time()
    
    with span("ops.build.exe", exe_name=name, onefile=onefile):
        add_span_attributes(**{
            BuildAttributes.TYPE: "exe",
            "build.name": name,
            "build.onefile": onefile,
            "build.clean": clean,
            "build.debug": debug,
            "build.hidden_imports_count": len(hidden_imports),
            "build.exclude_modules_count": len(exclude_modules),
        })
        add_span_event("build.exe.started", {
            "name": name,
            "type": "onefile" if onefile else "onedir",
            "hidden_imports": hidden_imports[:5],  # First 5 imports
            "exclude_modules": exclude_modules[:5],  # First 5 modules
        })
        
        try:
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
            
            # Calculate executable size
            exe_size = 0
            if output_file.exists():
                exe_size = output_file.stat().st_size
            
            # Record successful build metrics
            duration = time.time() - start_time
            result = OperationResult(success=True, duration=duration, metadata={
                "artifact_type": "exe",
                "artifact_size": exe_size,
                "platform": "current",
            })
            build_metrics.record_exe(exe_size, "current", result)
            
            add_span_attributes(**{
                "build.executable_size": exe_size,
                BuildAttributes.SIZE: exe_size,
            })
            add_span_event("build.exe.completed", {
                "output_file": str(output_file),
                "size": exe_size,
                "success": True
            })
            
            return {
                "output_file": str(output_file),
                "name": name,
                "type": "onefile" if onefile else "onedir",
                "size": exe_size,
            }
            
        except Exception as e:
            # Record failed build metrics
            duration = time.time() - start_time
            result = OperationResult(success=False, duration=duration, error=e)
            build_metrics.record_exe(0, "current", result)
            
            add_span_event("build.exe.failed", {"error": str(e), "name": name})
            raise


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
    with span("ops.build.test_executable", exe_path=str(exe_path)):
        add_span_attributes(**{
            "build.test_target": str(exe_path),
            "build.test_type": "executable",
        })
        add_span_event("build.test.started", {"executable": str(exe_path)})
        
        try:
            result = _rt.test_executable(exe_path)
            
            success = result.get("success", False)
            add_span_attributes(**{"build.test_success": success})
            add_span_event("build.test.completed", {
                "executable": str(exe_path),
                "success": success,
                "result": result
            })
            
            return result
            
        except Exception as e:
            add_span_event("build.test.failed", {
                "error": str(e),
                "executable": str(exe_path)
            })
            raise
