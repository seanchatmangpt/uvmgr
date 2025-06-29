"""
uvmgr.ops.guides - Agent Guide Operations
=========================================

Business logic for agent guide catalog management, fetching, caching, and versioning.

This module provides the core operations for the agent-guides ecosystem,
enabling discovery, download, caching, and version management of agent guides.
"""

from __future__ import annotations

import json
import hashlib
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span, record_exception
from uvmgr.core.instrumentation import add_span_attributes, add_span_event


@timed
def get_guide_catalog(
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "popularity",
    limit: int = 20,
) -> Dict[str, Any]:
    """Get available guides from catalog."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.get_catalog", search=search or "", category=category or "all"):
        add_span_attributes(**{
            "guides.search": search or "",
            "guides.category": category or "all",
            "guides.sort_by": sort_by,
            "guides.limit": limit,
        })
        
        try:
            result = _rt.get_guide_catalog(
                search=search,
                category=category,
                sort_by=sort_by,
                limit=limit,
            )
            
            add_span_event("guides.catalog.retrieved", {
                "guide_count": len(result.get("guides", [])),
                "category_count": len(result.get("categories", [])),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def fetch_guide(
    name: str,
    version: Optional[str] = None,
    force: bool = False,
    verify: bool = True,
) -> Dict[str, Any]:
    """Fetch a guide from repository."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.fetch", guide_name=name, guide_version=version or "latest"):
        add_span_attributes(**{
            "guides.name": name,
            "guides.version": version or "latest",
            "guides.force": force,
            "guides.verify": verify,
        })
        
        try:
            result = _rt.fetch_guide(
                name=name,
                version=version,
                force=force,
                verify=verify,
            )
            
            add_span_event("guides.fetched", {
                "name": name,
                "version": result.get("version"),
                "size": result.get("size", 0),
                "from_cache": result.get("from_cache", False),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def list_cached_guides(
    category: Optional[str] = None,
    outdated_only: bool = False,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """List locally cached guides."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.list_cached"):
        add_span_attributes(**{
            "guides.category": category or "all",
            "guides.outdated_only": outdated_only,
            "guides.verbose": verbose,
        })
        
        try:
            guides = _rt.list_cached_guides(
                category=category,
                outdated_only=outdated_only,
                verbose=verbose,
            )
            
            add_span_attributes(**{"guides.count": len(guides)})
            
            return guides
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def update_guides(
    name: Optional[str] = None,
    update_all: bool = False,
    check_only: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Update guides to latest versions."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.update"):
        add_span_attributes(**{
            "guides.name": name or "all",
            "guides.update_all": update_all,
            "guides.check_only": check_only,
            "guides.force": force,
        })
        
        try:
            result = _rt.update_guides(
                name=name,
                update_all=update_all,
                check_only=check_only,
                force=force,
            )
            
            add_span_event("guides.update.completed", {
                "checked": len(result.get("checked", [])),
                "updated": len(result.get("updated", [])),
                "failed": len(result.get("failed", [])),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def validate_guides(
    name: Optional[str] = None,
    validate_all: bool = False,
    strict: bool = False,
) -> Dict[str, Any]:
    """Validate guide structure and compatibility."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.validate"):
        add_span_attributes(**{
            "guides.name": name or "all",
            "guides.validate_all": validate_all,
            "guides.strict": strict,
        })
        
        try:
            result = _rt.validate_guides(
                name=name,
                validate_all=validate_all,
                strict=strict,
            )
            
            add_span_event("guides.validation.completed", {
                "validated": len(result.get("validated", [])),
                "passed": len(result.get("passed", [])),
                "failed": len(result.get("failed", [])),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def pin_guide_version(
    name: str,
    version: str,
    project_only: bool = False,
) -> Dict[str, Any]:
    """Pin a guide to specific version."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.pin", guide_name=name, guide_version=version):
        add_span_attributes(**{
            "guides.name": name,
            "guides.version": version,
            "guides.project_only": project_only,
        })
        
        try:
            result = _rt.pin_guide_version(
                name=name,
                version=version,
                project_only=project_only,
            )
            
            add_span_event("guides.pinned", {
                "name": name,
                "version": version,
                "scope": "project" if project_only else "global",
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def get_cache_status() -> Dict[str, Any]:
    """Get guide cache status."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.cache.status"):
        try:
            result = _rt.get_cache_status()
            
            add_span_attributes(**{
                "cache.size": result.get("size", 0),
                "cache.guide_count": result.get("guide_count", 0),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def clean_cache(
    max_age_days: Optional[int] = None,
    max_size_mb: Optional[int] = None,
    clear_all: bool = False,
) -> Dict[str, Any]:
    """Clean guide cache."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.cache.clean"):
        add_span_attributes(**{
            "cache.max_age_days": max_age_days or 0,
            "cache.max_size_mb": max_size_mb or 0,
            "cache.clear_all": clear_all,
        })
        
        try:
            result = _rt.clean_cache(
                max_age_days=max_age_days,
                max_size_mb=max_size_mb,
                clear_all=clear_all,
            )
            
            add_span_event("guides.cache.cleaned", {
                "removed_count": result.get("removed_count", 0),
                "freed_size": result.get("freed_size", 0),
            })
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def configure_cache(
    max_age_days: Optional[int] = None,
    max_size_mb: Optional[int] = None,
) -> Dict[str, Any]:
    """Configure cache settings."""
    from uvmgr.runtime import guides as _rt
    
    with span("guides.cache.configure"):
        add_span_attributes(**{
            "cache.max_age_days": max_age_days or 0,
            "cache.max_size_mb": max_size_mb or 0,
        })
        
        try:
            result = _rt.configure_cache(
                max_age_days=max_age_days,
                max_size_mb=max_size_mb,
            )
            
            add_span_event("guides.cache.configured", result)
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


# Helper functions for guide management

def _get_guide_cache_dir() -> Path:
    """Get guide cache directory."""
    cache_dir = Path.home() / ".uvmgr" / "guides"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_guide_config_path() -> Path:
    """Get guide configuration file path."""
    config_dir = Path.home() / ".uvmgr" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "guides.json"


def _load_guide_config() -> Dict[str, Any]:
    """Load guide configuration."""
    config_path = _get_guide_config_path()
    if not config_path.exists():
        return {
            "pinned_versions": {},
            "cache_settings": {
                "max_age_days": None,
                "max_size_mb": None,
            },
            "repositories": [
                {
                    "name": "official",
                    "url": "https://github.com/tokenbender/agent-guides",
                    "enabled": True,
                },
            ],
        }
    
    with open(config_path, 'r') as f:
        return json.load(f)


def _save_guide_config(config: Dict[str, Any]) -> None:
    """Save guide configuration."""
    config_path = _get_guide_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def get_guide_hash(name: str, version: str) -> str:
    """Get unique hash for guide version."""
    return hashlib.sha256(f"{name}:{version}".encode()).hexdigest()[:16]


def get_guide_metadata(guide_path: Path) -> Dict[str, Any]:
    """Extract metadata from guide."""
    metadata_file = guide_path / "guide.json"
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    
    # Try to extract from README.md or other files
    readme_file = guide_path / "README.md"
    if readme_file.exists():
        content = readme_file.read_text()
        # Simple extraction logic
        return {
            "name": guide_path.name,
            "version": "unknown",
            "description": content.split('\n')[0].strip('# '),
            "category": "general",
        }
    
    return {
        "name": guide_path.name,
        "version": "unknown",
        "category": "general",
    }


def validate_guide_structure(guide_path: Path, strict: bool = False) -> tuple[bool, List[str]]:
    """Validate guide directory structure."""
    errors = []
    
    # Required files
    required_files = ["README.md"]
    if strict:
        required_files.extend(["guide.json", "LICENSE"])
    
    for req_file in required_files:
        if not (guide_path / req_file).exists():
            errors.append(f"Missing required file: {req_file}")
    
    # Check for commands directory if it's a command guide
    if "command" in str(guide_path).lower():
        if not (guide_path / "commands").is_dir():
            errors.append("Command guide missing 'commands' directory")
    
    # Validate guide.json if exists
    guide_json = guide_path / "guide.json"
    if guide_json.exists():
        try:
            with open(guide_json, 'r') as f:
                metadata = json.load(f)
                
            # Check required fields
            required_fields = ["name", "version", "description"]
            for field in required_fields:
                if field not in metadata:
                    errors.append(f"guide.json missing required field: {field}")
                    
        except json.JSONDecodeError as e:
            errors.append(f"Invalid guide.json: {e}")
    
    return len(errors) == 0, errors


def calculate_guide_size(guide_path: Path) -> int:
    """Calculate total size of guide directory."""
    total_size = 0
    for file_path in guide_path.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    return total_size


def format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"