"""
uvmgr.ops.weaver - Weaver Operations
===================================

Operations layer for OpenTelemetry Weaver semantic convention management.

This module provides the business logic for Weaver operations, including
installation, validation, code generation, and registry management.
"""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from typing import Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.process import run_logged
from uvmgr.core.telemetry import metric_counter, metric_histogram, span


# Paths
WEAVER_PATH = Path(__file__).parent.parent.parent.parent / "tools" / "weaver"
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "weaver-forge" / "registry"
WEAVER_URL = "https://github.com/open-telemetry/weaver/releases/latest"


def get_weaver_version() -> Optional[str]:
    """Get the current Weaver version."""
    if not WEAVER_PATH.exists():
        return None
    
    try:
        result = run_logged([str(WEAVER_PATH), "--version"], capture=True)
        return result.strip() if result else None
    except Exception:
        return None


def detect_platform() -> tuple[str, str, str]:
    """Detect platform and return system, machine, and artifact name."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":
        if machine == "arm64":
            artifact = "weaver-aarch64-apple-darwin"
        else:
            artifact = "weaver-x86_64-apple-darwin"
    elif system == "linux":
        if machine == "aarch64":
            artifact = "weaver-aarch64-unknown-linux-gnu"
        else:
            artifact = "weaver-x86_64-unknown-linux-gnu"
    elif system == "windows":
        artifact = "weaver-x86_64-pc-windows-msvc"
    else:
        raise ValueError(f"Unsupported platform: {system}/{machine}")
    
    return system, machine, artifact


def get_latest_version() -> str:
    """Get the latest Weaver version from GitHub API."""
    api_url = "https://api.github.com/repos/open-telemetry/weaver/releases/latest"
    
    try:
        result = run_logged(["curl", "-s", api_url], capture=True)
        if result:
            release_data = json.loads(result)
            return release_data["tag_name"]
    except Exception:
        pass
    
    return "latest"


def install_weaver(version: str = "latest", force: bool = False) -> dict:
    """Install or update OpenTelemetry Weaver."""
    with span("weaver.install", version=version, force=force):
        add_span_attributes(**{
            "weaver.operation": "install",
            "weaver.version": version,
            "weaver.force": force,
        })
        add_span_event("weaver.install.started", {"version": version})
        
        start_time = time.time()
        
        try:
            # Check if already installed
            if WEAVER_PATH.exists() and not force:
                current_version = get_weaver_version()
                if current_version:
                    add_span_event("weaver.install.already_installed", {"version": current_version})
                    return {
                        "status": "already_installed",
                        "version": current_version,
                        "message": f"Weaver already installed: {current_version}"
                    }
            
            # Detect platform
            system, machine, artifact = detect_platform()
            
            # Get version
            if version == "latest":
                version = get_latest_version()
            
            download_url = f"https://github.com/open-telemetry/weaver/releases/download/{version}/{artifact}.tar.xz"
            
            # Create tools directory
            tools_dir = WEAVER_PATH.parent
            tools_dir.mkdir(exist_ok=True)
            
            # Download and extract
            add_span_event("weaver.install.downloading", {"url": download_url})
            run_logged(["curl", "-L", "-o", "weaver.tar.xz", download_url], cwd=tools_dir)
            
            add_span_event("weaver.install.extracting")
            run_logged(["tar", "-xf", "weaver.tar.xz"], cwd=tools_dir)
            (tools_dir / "weaver.tar.xz").unlink()
            
            # Make executable and create symlink
            weaver_bin = tools_dir / artifact / "weaver"
            if weaver_bin.exists():
                weaver_bin.chmod(0o755)
                if WEAVER_PATH.exists():
                    WEAVER_PATH.unlink()
                WEAVER_PATH.symlink_to(f"{artifact}/weaver")
            
            # Verify installation
            installed_version = get_weaver_version()
            duration = time.time() - start_time
            
            if installed_version:
                add_span_event("weaver.install.success", {
                    "version": installed_version,
                    "duration": duration
                })
                metric_counter("weaver.install.success")(1)
                metric_histogram("weaver.install.duration")(duration)
                
                return {
                    "status": "success",
                    "version": installed_version,
                    "duration": duration,
                    "message": f"Weaver {installed_version} installed successfully!"
                }
            else:
                add_span_event("weaver.install.failed", {"duration": duration})
                metric_counter("weaver.install.failed")(1)
                raise RuntimeError("Installation verification failed")
                
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.install.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.install.failed")(1)
            raise


def check_registry(registry: Path, future: bool = True, policy: Optional[Path] = None) -> dict:
    """Validate semantic convention registry."""
    with span("weaver.check_registry", registry=str(registry), future=future):
        add_span_attributes(**{
            "weaver.operation": "check_registry",
            "weaver.registry_path": str(registry),
            "weaver.future": future,
            "weaver.policy": str(policy) if policy else None,
        })
        add_span_event("weaver.check_registry.started", {"registry": str(registry)})
        
        if not WEAVER_PATH.exists():
            raise FileNotFoundError("Weaver not installed. Run: uvmgr weaver install")
        
        start_time = time.time()
        
        try:
            cmd = [str(WEAVER_PATH), "registry", "check", "-r", str(registry)]
            if future:
                cmd.append("--future")
            if policy:
                cmd.extend(["-p", str(policy)])
            
            result = run_logged(cmd, capture=True)
            duration = time.time() - start_time
            
            add_span_event("weaver.check_registry.success", {
                "duration": duration,
                "output_length": len(result) if result else 0
            })
            metric_counter("weaver.check_registry.success")(1)
            metric_histogram("weaver.check_registry.duration")(duration)
            
            return {
                "status": "success",
                "duration": duration,
                "output": result,
                "message": "Registry validation passed!"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.check_registry.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.check_registry.failed")(1)
            raise


def generate_code(template: str, output: Path, registry: Path, config: Optional[Path] = None) -> dict:
    """Generate code from semantic conventions."""
    with span("weaver.generate", template=template, output=str(output), registry=str(registry)):
        add_span_attributes(**{
            "weaver.operation": "generate",
            "weaver.template": template,
            "weaver.output_path": str(output),
            "weaver.registry_path": str(registry),
            "weaver.config": str(config) if config else None,
        })
        add_span_event("weaver.generate.started", {
            "template": template,
            "registry": str(registry)
        })
        
        if not WEAVER_PATH.exists():
            raise FileNotFoundError("Weaver not installed. Run: uvmgr weaver install")
        
        start_time = time.time()
        
        try:
            # For Python template, use our custom generator
            if template == "python":
                from weaver_forge.validate_semconv import generate_python_constants
                generate_python_constants()
                
                duration = time.time() - start_time
                add_span_event("weaver.generate.python_success", {"duration": duration})
                metric_counter("weaver.generate.python.success")(1)
                
                return {
                    "status": "success",
                    "template": template,
                    "duration": duration,
                    "message": "Python constants generated!"
                }
            
            # For other templates, use Weaver's built-in generators
            cmd = [
                str(WEAVER_PATH), "registry", "generate",
                "-r", str(registry),
                "-t", template,
                str(output)
            ]
            
            if config:
                cmd.extend(["-c", str(config)])
            
            result = run_logged(cmd, capture=True)
            duration = time.time() - start_time
            
            add_span_event("weaver.generate.success", {
                "template": template,
                "duration": duration,
                "output_length": len(result) if result else 0
            })
            metric_counter("weaver.generate.success")(1)
            metric_histogram("weaver.generate.duration")(duration)
            
            return {
                "status": "success",
                "template": template,
                "duration": duration,
                "output": result,
                "message": f"Generated {template} in {output}"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.generate.failed", {
                "template": template,
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.generate.failed")(1)
            raise


def resolve_registry(registry: Path, output: Optional[Path] = None, format: str = "json") -> dict:
    """Resolve semantic convention references and inheritance."""
    with span("weaver.resolve", registry=str(registry), format=format):
        add_span_attributes(**{
            "weaver.operation": "resolve",
            "weaver.registry_path": str(registry),
            "weaver.format": format,
            "weaver.output": str(output) if output else None,
        })
        add_span_event("weaver.resolve.started", {"registry": str(registry)})
        
        if not WEAVER_PATH.exists():
            raise FileNotFoundError("Weaver not installed. Run: uvmgr weaver install")
        
        start_time = time.time()
        
        try:
            cmd = [str(WEAVER_PATH), "registry", "resolve", "-r", str(registry), "-f", format]
            
            if output:
                cmd.extend(["-o", str(output)])
            
            result = run_logged(cmd, capture=True)
            duration = time.time() - start_time
            
            add_span_event("weaver.resolve.success", {
                "duration": duration,
                "output_length": len(result) if result else 0
            })
            metric_counter("weaver.resolve.success")(1)
            metric_histogram("weaver.resolve.duration")(duration)
            
            return {
                "status": "success",
                "format": format,
                "duration": duration,
                "output": result,
                "message": f"Registry resolved in {format} format"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.resolve.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.resolve.failed")(1)
            raise


def search_registry(query: str, registry: Path, type: Optional[str] = None) -> dict:
    """Search for semantic conventions in registry."""
    with span("weaver.search", query=query, registry=str(registry), type=type):
        add_span_attributes(**{
            "weaver.operation": "search",
            "weaver.query": query,
            "weaver.registry_path": str(registry),
            "weaver.search_type": type,
        })
        add_span_event("weaver.search.started", {"query": query})
        
        if not WEAVER_PATH.exists():
            raise FileNotFoundError("Weaver not installed. Run: uvmgr weaver install")
        
        start_time = time.time()
        
        try:
            cmd = [str(WEAVER_PATH), "registry", "search", "-r", str(registry), query]
            
            if type:
                cmd.extend(["-t", type])
            
            result = run_logged(cmd, capture=True)
            duration = time.time() - start_time
            
            add_span_event("weaver.search.success", {
                "duration": duration,
                "results_count": len(result.splitlines()) if result else 0
            })
            metric_counter("weaver.search.success")(1)
            metric_histogram("weaver.search.duration")(duration)
            
            return {
                "status": "success",
                "query": query,
                "duration": duration,
                "results": result,
                "message": f"Found results for '{query}'"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.search.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.search.failed")(1)
            raise


def get_registry_stats(registry: Path) -> dict:
    """Get statistics about the registry."""
    with span("weaver.stats", registry=str(registry)):
        add_span_attributes(**{
            "weaver.operation": "stats",
            "weaver.registry_path": str(registry),
        })
        add_span_event("weaver.stats.started", {"registry": str(registry)})
        
        if not WEAVER_PATH.exists():
            raise FileNotFoundError("Weaver not installed. Run: uvmgr weaver install")
        
        start_time = time.time()
        
        try:
            cmd = [str(WEAVER_PATH), "registry", "stats", "-r", str(registry)]
            result = run_logged(cmd, capture=True)
            duration = time.time() - start_time
            
            add_span_event("weaver.stats.success", {"duration": duration})
            metric_counter("weaver.stats.success")(1)
            metric_histogram("weaver.stats.duration")(duration)
            
            return {
                "status": "success",
                "duration": duration,
                "stats": result,
                "message": "Registry statistics retrieved"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.stats.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.stats.failed")(1)
            raise


def diff_registries(registry1: Path, registry2: Path, output: Optional[Path] = None) -> dict:
    """Compare two registries and show differences."""
    with span("weaver.diff", registry1=str(registry1), registry2=str(registry2)):
        add_span_attributes(**{
            "weaver.operation": "diff",
            "weaver.registry1": str(registry1),
            "weaver.registry2": str(registry2),
            "weaver.output": str(output) if output else None,
        })
        add_span_event("weaver.diff.started", {
            "registry1": str(registry1),
            "registry2": str(registry2)
        })
        
        if not WEAVER_PATH.exists():
            raise FileNotFoundError("Weaver not installed. Run: uvmgr weaver install")
        
        start_time = time.time()
        
        try:
            cmd = [str(WEAVER_PATH), "registry", "diff", str(registry1), str(registry2)]
            
            if output:
                cmd.extend(["-o", str(output)])
            
            result = run_logged(cmd, capture=True)
            duration = time.time() - start_time
            
            add_span_event("weaver.diff.success", {
                "duration": duration,
                "diff_length": len(result) if result else 0
            })
            metric_counter("weaver.diff.success")(1)
            metric_histogram("weaver.diff.duration")(duration)
            
            return {
                "status": "success",
                "duration": duration,
                "diff": result,
                "message": f"Registry diff generated"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.diff.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.diff.failed")(1)
            raise


def init_registry(name: str, path: Path, force: bool = False) -> dict:
    """Initialize a new semantic convention registry."""
    with span("weaver.init", name=name, path=str(path), force=force):
        add_span_attributes(**{
            "weaver.operation": "init",
            "weaver.name": name,
            "weaver.path": str(path),
            "weaver.force": force,
        })
        add_span_event("weaver.init.started", {"name": name, "path": str(path)})
        
        if not WEAVER_PATH.exists():
            raise FileNotFoundError("Weaver not installed. Run: uvmgr weaver install")
        
        start_time = time.time()
        
        try:
            if path.exists() and not force:
                raise FileExistsError(f"Registry already exists at {path}. Use --force to overwrite.")
            
            cmd = [str(WEAVER_PATH), "registry", "init", "-n", name, str(path)]
            result = run_logged(cmd, capture=True)
            duration = time.time() - start_time
            
            add_span_event("weaver.init.success", {"duration": duration})
            metric_counter("weaver.init.success")(1)
            metric_histogram("weaver.init.duration")(duration)
            
            return {
                "status": "success",
                "name": name,
                "path": str(path),
                "duration": duration,
                "output": result,
                "message": f"Registry '{name}' initialized at {path}"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.init.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.init.failed")(1)
            raise


def generate_docs(registry: Path, output: Path, format: str = "markdown") -> dict:
    """Generate documentation from semantic conventions."""
    with span("weaver.docs", registry=str(registry), output=str(output), format=format):
        add_span_attributes(**{
            "weaver.operation": "docs",
            "weaver.registry_path": str(registry),
            "weaver.output_path": str(output),
            "weaver.format": format,
        })
        add_span_event("weaver.docs.started", {
            "registry": str(registry),
            "format": format
        })
        
        if not WEAVER_PATH.exists():
            raise FileNotFoundError("Weaver not installed. Run: uvmgr weaver install")
        
        start_time = time.time()
        
        try:
            cmd = [
                str(WEAVER_PATH), "registry", "docs",
                "-r", str(registry),
                "-o", str(output),
                "-f", format
            ]
            
            result = run_logged(cmd, capture=True)
            duration = time.time() - start_time
            
            add_span_event("weaver.docs.success", {"duration": duration})
            metric_counter("weaver.docs.success")(1)
            metric_histogram("weaver.docs.duration")(duration)
            
            return {
                "status": "success",
                "format": format,
                "duration": duration,
                "output": result,
                "message": f"Documentation generated in {format} format"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("weaver.docs.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("weaver.docs.failed")(1)
            raise 