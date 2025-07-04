"""
uvmgr.runtime.guides - Guide Runtime Implementation
=================================================

Runtime implementation for agent guide catalog operations including
fetching, caching, version management, and validation.

This module handles the actual file system operations, network requests,
and cache management for the agent-guides ecosystem.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

from uvmgr.core.process import run
from uvmgr.core.telemetry import span, record_exception
from uvmgr.core.instrumentation import add_span_attributes, add_span_event


def get_guide_catalog(
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "popularity",
    limit: int = 20,
) -> Dict[str, Any]:
    """Get available guides from remote catalog."""
    with span("guides.runtime.get_catalog") as s:
        try:
            # For now, use a static catalog. In production, this would fetch from
            # a remote API or repository index
            catalog_data = _fetch_remote_catalog()
            
            guides = catalog_data.get("guides", [])
            
            # Apply filters
            if search:
                search_lower = search.lower()
                guides = [
                    g for g in guides
                    if search_lower in g["name"].lower()
                    or search_lower in g.get("description", "").lower()
                    or any(search_lower in tag for tag in g.get("tags", []))
                ]
            
            if category:
                guides = [g for g in guides if g.get("category") == category]
            
            # Sort guides
            if sort_by == "popularity":
                guides.sort(key=lambda x: x.get("downloads", 0), reverse=True)
            elif sort_by == "updated":
                guides.sort(key=lambda x: x.get("updated", ""), reverse=True)
            elif sort_by == "name":
                guides.sort(key=lambda x: x["name"])
            
            # Apply limit
            guides = guides[:limit]
            
            # Get categories with counts
            all_categories = {}
            for guide in catalog_data.get("guides", []):
                cat = guide.get("category", "general")
                all_categories[cat] = all_categories.get(cat, 0) + 1
            
            categories = [
                {"name": name, "count": count}
                for name, count in all_categories.items()
            ]
            categories.sort(key=lambda x: x["count"], reverse=True)
            
            return {
                "guides": guides,
                "categories": categories,
                "total": len(catalog_data.get("guides", [])),
                "filtered": len(guides),
            }
            
        except Exception as e:
            record_exception(e)
            raise


def fetch_guide(
    name: str,
    version: Optional[str] = None,
    force: bool = False,
    verify: bool = True,
) -> Dict[str, Any]:
    """Fetch a guide from repository."""
    with span("guides.runtime.fetch") as s:
        try:
            cache_dir = _get_cache_dir()
            version = version or "latest"
            
            # Check cache first
            cached_guide = _get_cached_guide(name, version)
            if cached_guide and not force:
                add_span_event("guides.loaded_from_cache", {"name": name})
                return {
                    "name": name,
                    "version": cached_guide["version"],
                    "path": str(cached_guide["path"]),
                    "from_cache": True,
                    "size": cached_guide["size"],
                    "dependencies": cached_guide.get("dependencies", []),
                }
            
            # Fetch from remote
            guide_info = _fetch_guide_info(name, version)
            if not guide_info:
                raise ValueError(f"Guide '{name}' not found in catalog")
            
            # Download guide
            guide_path = _download_guide(guide_info, cache_dir, verify)
            
            # Extract metadata
            metadata = _extract_guide_metadata(guide_path)
            
            # Cache metadata
            _cache_guide_metadata(name, guide_info["version"], guide_path, metadata)
            
            return {
                "name": name,
                "version": guide_info["version"],
                "path": str(guide_path),
                "from_cache": False,
                "size": _calculate_dir_size(guide_path),
                "dependencies": metadata.get("dependencies", []),
            }
            
        except Exception as e:
            record_exception(e)
            raise


def list_cached_guides(
    category: Optional[str] = None,
    outdated_only: bool = False,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """List locally cached guides."""
    with span("guides.runtime.list_cached") as s:
        try:
            cache_dir = _get_cache_dir()
            cache_index = _load_cache_index()
            
            guides = []
            for name, versions in cache_index.items():
                for version, info in versions.items():
                    guide_path = Path(info["path"])
                    if not guide_path.exists():
                        continue
                    
                    # Load metadata
                    metadata = info.get("metadata", {})
                    
                    # Apply filters
                    if category and metadata.get("category") != category:
                        continue
                    
                    # Check if outdated
                    is_outdated = False
                    if outdated_only:
                        latest_version = _get_latest_version(name)
                        is_outdated = latest_version and latest_version != version
                        if not is_outdated:
                            continue
                    
                    guide_info = {
                        "name": name,
                        "version": version,
                        "category": metadata.get("category", "general"),
                        "size": info.get("size", 0),
                        "size_human": _format_size(info.get("size", 0)),
                        "cached_date": info.get("cached_date", "unknown"),
                        "outdated": is_outdated,
                    }
                    
                    if verbose:
                        guide_info.update({
                            "path": str(guide_path),
                            "description": metadata.get("description", ""),
                            "tags": metadata.get("tags", []),
                        })
                    
                    guides.append(guide_info)
            
            # Sort by name
            guides.sort(key=lambda x: x["name"])
            
            return guides
            
        except Exception as e:
            record_exception(e)
            raise


def update_guides(
    name: Optional[str] = None,
    update_all: bool = False,
    check_only: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """Update guides to latest versions."""
    with span("guides.runtime.update") as s:
        try:
            cache_index = _load_cache_index()
            
            # Determine which guides to check
            if name:
                guides_to_check = [name] if name in cache_index else []
            elif update_all:
                guides_to_check = list(cache_index.keys())
            else:
                guides_to_check = []
            
            checked = []
            available_updates = []
            updated = []
            failed = []
            
            for guide_name in guides_to_check:
                try:
                    # Get current version
                    current_versions = cache_index.get(guide_name, {})
                    if not current_versions:
                        continue
                    
                    current_version = max(current_versions.keys())
                    checked.append(guide_name)
                    
                    # Get latest version
                    latest_version = _get_latest_version(guide_name)
                    if not latest_version:
                        continue
                    
                    # Check if update available
                    if current_version != latest_version or force:
                        update_info = {
                            "name": guide_name,
                            "current": current_version,
                            "latest": latest_version,
                        }
                        available_updates.append(update_info)
                        
                        if not check_only:
                            # Perform update
                            result = fetch_guide(
                                guide_name,
                                latest_version,
                                force=True,
                                verify=True,
                            )
                            updated.append({
                                "name": guide_name,
                                "version": latest_version,
                                "path": result["path"],
                            })
                
                except Exception as e:
                    failed.append({
                        "name": guide_name,
                        "error": str(e),
                    })
            
            return {
                "checked": checked,
                "available_updates": available_updates,
                "updated": updated,
                "failed": failed,
            }
            
        except Exception as e:
            record_exception(e)
            raise


def validate_guides(
    name: Optional[str] = None,
    validate_all: bool = False,
    strict: bool = False,
) -> Dict[str, Any]:
    """Validate guide structure and compatibility."""
    with span("guides.runtime.validate") as s:
        try:
            cache_index = _load_cache_index()
            
            # Determine which guides to validate
            if name:
                guides_to_validate = [name] if name in cache_index else []
            elif validate_all:
                guides_to_validate = list(cache_index.keys())
            else:
                guides_to_validate = []
            
            validated = []
            passed = []
            failed = []
            
            for guide_name in guides_to_validate:
                versions = cache_index.get(guide_name, {})
                for version, info in versions.items():
                    guide_path = Path(info["path"])
                    if not guide_path.exists():
                        continue
                    
                    validated.append(f"{guide_name}:{version}")
                    
                    # Perform validation
                    is_valid, errors = _validate_guide_structure(guide_path, strict)
                    
                    if is_valid:
                        passed.append({
                            "name": guide_name,
                            "version": version,
                        })
                    else:
                        failed.append({
                            "name": guide_name,
                            "version": version,
                            "reason": f"{len(errors)} validation errors",
                            "errors": errors,
                        })
            
            return {
                "validated": validated,
                "passed": passed,
                "failed": failed,
            }
            
        except Exception as e:
            record_exception(e)
            raise


def pin_guide_version(
    name: str,
    version: str,
    project_only: bool = False,
) -> Dict[str, Any]:
    """Pin a guide to specific version."""
    with span("guides.runtime.pin") as s:
        try:
            # Load pin configuration
            pin_config = _load_pin_config(project_only)
            
            # Verify guide exists in cache
            cache_index = _load_cache_index()
            if name not in cache_index or version not in cache_index[name]:
                # Try to fetch it first
                fetch_guide(name, version)
            
            # Update pin configuration
            pin_config["pinned_versions"][name] = version
            
            # Save configuration
            _save_pin_config(pin_config, project_only)
            
            result = {
                "name": name,
                "version": version,
                "scope": "project" if project_only else "global",
            }
            
            if project_only:
                result["project_path"] = str(Path.cwd())
            
            # Check if this is the latest version
            latest = _get_latest_version(name)
            if latest and latest != version:
                result["warning"] = f"Pinned to {version} but latest is {latest}"
            
            return result
            
        except Exception as e:
            record_exception(e)
            raise


def get_cache_status() -> Dict[str, Any]:
    """Get guide cache status."""
    with span("guides.runtime.cache_status") as s:
        try:
            cache_dir = _get_cache_dir()
            cache_index = _load_cache_index()
            
            # Calculate total size
            total_size = 0
            guide_count = 0
            oldest_date = None
            
            for name, versions in cache_index.items():
                for version, info in versions.items():
                    guide_path = Path(info["path"])
                    if guide_path.exists():
                        guide_count += 1
                        total_size += info.get("size", 0)
                        
                        cached_date = info.get("cached_date")
                        if cached_date:
                            if not oldest_date or cached_date < oldest_date:
                                oldest_date = cached_date
            
            # Load cache settings
            config = _load_guide_config()
            cache_settings = config.get("cache_settings", {})
            
            return {
                "path": str(cache_dir),
                "size": total_size,
                "size_human": _format_size(total_size),
                "guide_count": guide_count,
                "oldest_date": oldest_date,
                "max_age_days": cache_settings.get("max_age_days"),
                "max_size_mb": cache_settings.get("max_size_mb"),
            }
            
        except Exception as e:
            record_exception(e)
            raise


def clean_cache(
    max_age_days: Optional[int] = None,
    max_size_mb: Optional[int] = None,
    clear_all: bool = False,
) -> Dict[str, Any]:
    """Clean guide cache."""
    with span("guides.runtime.clean_cache") as s:
        try:
            cache_dir = _get_cache_dir()
            cache_index = _load_cache_index()
            
            removed_count = 0
            freed_size = 0
            
            if clear_all:
                # Remove everything
                for name, versions in cache_index.items():
                    for version, info in versions.items():
                        guide_path = Path(info["path"])
                        if guide_path.exists():
                            shutil.rmtree(guide_path)
                            removed_count += 1
                            freed_size += info.get("size", 0)
                
                # Clear index
                _save_cache_index({})
                
            else:
                # Selective cleaning
                now = datetime.now()
                guides_by_age = []
                
                # Collect guides with age info
                for name, versions in cache_index.items():
                    for version, info in versions.items():
                        guide_path = Path(info["path"])
                        if not guide_path.exists():
                            continue
                        
                        cached_date = info.get("cached_date")
                        if cached_date:
                            age_days = (now - datetime.fromisoformat(cached_date)).days
                            guides_by_age.append({
                                "name": name,
                                "version": version,
                                "path": guide_path,
                                "size": info.get("size", 0),
                                "age_days": age_days,
                            })
                
                # Sort by age (oldest first)
                guides_by_age.sort(key=lambda x: x["age_days"], reverse=True)
                
                # Remove based on age
                if max_age_days:
                    for guide in guides_by_age:
                        if guide["age_days"] > max_age_days:
                            shutil.rmtree(guide["path"])
                            removed_count += 1
                            freed_size += guide["size"]
                            del cache_index[guide["name"]][guide["version"]]
                
                # Remove based on size
                if max_size_mb:
                    max_size_bytes = max_size_mb * 1024 * 1024
                    current_size = sum(g["size"] for g in guides_by_age)
                    
                    for guide in guides_by_age:
                        if current_size <= max_size_bytes:
                            break
                        
                        if guide["path"].exists():
                            shutil.rmtree(guide["path"])
                            removed_count += 1
                            freed_size += guide["size"]
                            current_size -= guide["size"]
                            del cache_index[guide["name"]][guide["version"]]
                
                # Save updated index
                _save_cache_index(cache_index)
            
            return {
                "removed_count": removed_count,
                "freed_size": freed_size,
                "freed_size_human": _format_size(freed_size),
            }
            
        except Exception as e:
            record_exception(e)
            raise


def configure_cache(
    max_age_days: Optional[int] = None,
    max_size_mb: Optional[int] = None,
) -> Dict[str, Any]:
    """Configure cache settings."""
    with span("guides.runtime.configure_cache") as s:
        try:
            config = _load_guide_config()
            
            if max_age_days is not None:
                config["cache_settings"]["max_age_days"] = max_age_days
            
            if max_size_mb is not None:
                config["cache_settings"]["max_size_mb"] = max_size_mb
            
            _save_guide_config(config)
            
            return config["cache_settings"]
            
        except Exception as e:
            record_exception(e)
            raise


# Helper functions

def _get_cache_dir() -> Path:
    """Get guide cache directory."""
    cache_dir = Path.home() / ".uvmgr" / "guides"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_config_dir() -> Path:
    """Get configuration directory."""
    config_dir = Path.home() / ".uvmgr" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _load_cache_index() -> Dict[str, Dict[str, Any]]:
    """Load cache index file."""
    index_file = _get_cache_dir() / "index.json"
    if not index_file.exists():
        return {}
    
    with open(index_file, 'r') as f:
        return json.load(f)


def _save_cache_index(index: Dict[str, Dict[str, Any]]) -> None:
    """Save cache index file."""
    index_file = _get_cache_dir() / "index.json"
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)


def _load_guide_config() -> Dict[str, Any]:
    """Load guide configuration."""
    config_file = _get_config_dir() / "guides.json"
    if not config_file.exists():
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
    
    with open(config_file, 'r') as f:
        return json.load(f)


def _save_guide_config(config: Dict[str, Any]) -> None:
    """Save guide configuration."""
    config_file = _get_config_dir() / "guides.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def _load_pin_config(project_only: bool) -> Dict[str, Any]:
    """Load pin configuration."""
    if project_only:
        config_file = Path.cwd() / ".uvmgr" / "guides.json"
    else:
        config_file = _get_config_dir() / "pins.json"
    
    if not config_file.exists():
        return {"pinned_versions": {}}
    
    with open(config_file, 'r') as f:
        return json.load(f)


def _save_pin_config(config: Dict[str, Any], project_only: bool) -> None:
    """Save pin configuration."""
    if project_only:
        config_dir = Path.cwd() / ".uvmgr"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "guides.json"
    else:
        config_file = _get_config_dir() / "pins.json"
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def _fetch_remote_catalog() -> Dict[str, Any]:
    """Fetch catalog from remote source."""
    # In production, this would make an API call or fetch from a git repo
    # For now, return a mock catalog
    return {
        "guides": [
            {
                "name": "claude-commands",
                "category": "commands",
                "version": "1.0.0",
                "description": "Essential Claude command shortcuts and templates",
                "downloads": 1523,
                "updated": "2024-01-15",
                "tags": ["claude", "commands", "productivity"],
                "url": "https://github.com/tokenbender/agent-guides/tree/main/claude-commands",
            },
            {
                "name": "python-patterns",
                "category": "patterns",
                "version": "2.1.0",
                "description": "Python design patterns and best practices",
                "downloads": 892,
                "updated": "2024-01-10",
                "tags": ["python", "patterns", "best-practices"],
                "url": "https://github.com/tokenbender/agent-guides/tree/main/python-patterns",
            },
            {
                "name": "weaver-templates",
                "category": "templates",
                "version": "1.5.2",
                "description": "Weaver Forge semantic convention templates",
                "downloads": 567,
                "updated": "2024-01-08",
                "tags": ["weaver", "otel", "templates"],
                "url": "https://github.com/tokenbender/agent-guides/tree/main/weaver-templates",
            },
            {
                "name": "react-components",
                "category": "components",
                "version": "3.0.1",
                "description": "Reusable React component library",
                "downloads": 2341,
                "updated": "2024-01-12",
                "tags": ["react", "components", "ui"],
                "url": "https://github.com/tokenbender/agent-guides/tree/main/react-components",
            },
            {
                "name": "testing-strategies",
                "category": "testing",
                "version": "1.2.0",
                "description": "Comprehensive testing strategies and examples",
                "downloads": 423,
                "updated": "2024-01-05",
                "tags": ["testing", "qa", "automation"],
                "url": "https://github.com/tokenbender/agent-guides/tree/main/testing-strategies",
            },
        ],
    }


def _get_cached_guide(name: str, version: str) -> Optional[Dict[str, Any]]:
    """Get cached guide info."""
    cache_index = _load_cache_index()
    
    if name in cache_index and version in cache_index[name]:
        info = cache_index[name][version]
        guide_path = Path(info["path"])
        
        if guide_path.exists():
            return {
                "version": version,
                "path": guide_path,
                "size": info.get("size", 0),
                "dependencies": info.get("metadata", {}).get("dependencies", []),
            }
    
    return None


def _fetch_guide_info(name: str, version: str) -> Optional[Dict[str, Any]]:
    """Fetch guide information from catalog."""
    catalog = _fetch_remote_catalog()
    
    for guide in catalog["guides"]:
        if guide["name"] == name:
            # In production, would resolve "latest" to actual version
            if version == "latest":
                version = guide["version"]
            
            return {
                "name": name,
                "version": version,
                "url": guide["url"],
                "category": guide.get("category", "general"),
            }
    
    return None


def _download_guide(guide_info: Dict[str, Any], cache_dir: Path, verify: bool) -> Path:
    """Download guide from remote repository."""
    guide_dir = cache_dir / guide_info["name"] / guide_info["version"]
    guide_dir.mkdir(parents=True, exist_ok=True)
    
    # In production, this would:
    # 1. Clone or download from the URL
    # 2. Verify checksums if enabled
    # 3. Extract to the guide directory
    
    # For now, create a mock guide structure
    readme_content = f"""# {guide_info['name']}

Version: {guide_info['version']}
Category: {guide_info['category']}

This is a mock guide for demonstration purposes.
"""
    
    (guide_dir / "README.md").write_text(readme_content)
    
    # Create guide.json
    guide_json = {
        "name": guide_info["name"],
        "version": guide_info["version"],
        "description": f"Mock guide for {guide_info['name']}",
        "category": guide_info["category"],
        "dependencies": [],
    }
    
    with open(guide_dir / "guide.json", 'w') as f:
        json.dump(guide_json, f, indent=2)
    
    # Create example content based on category
    if guide_info["category"] == "commands":
        commands_dir = guide_dir / "commands"
        commands_dir.mkdir(exist_ok=True)
        (commands_dir / "example.md").write_text("# Example Command\n\nCommand content here.")
    
    return guide_dir


def _extract_guide_metadata(guide_path: Path) -> Dict[str, Any]:
    """Extract metadata from guide."""
    metadata_file = guide_path / "guide.json"
    
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    
    # Fallback to basic metadata
    return {
        "name": guide_path.name,
        "version": "unknown",
        "category": "general",
        "dependencies": [],
    }


def _cache_guide_metadata(name: str, version: str, path: Path, metadata: Dict[str, Any]) -> None:
    """Cache guide metadata."""
    cache_index = _load_cache_index()
    
    if name not in cache_index:
        cache_index[name] = {}
    
    cache_index[name][version] = {
        "path": str(path),
        "size": _calculate_dir_size(path),
        "cached_date": datetime.now().isoformat(),
        "metadata": metadata,
    }
    
    _save_cache_index(cache_index)


def _get_latest_version(name: str) -> Optional[str]:
    """Get latest version of a guide."""
    guide_info = _fetch_guide_info(name, "latest")
    return guide_info["version"] if guide_info else None


def _validate_guide_structure(guide_path: Path, strict: bool) -> Tuple[bool, List[str]]:
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
    if "command" in guide_path.name:
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


def _calculate_dir_size(path: Path) -> int:
    """Calculate total size of directory."""
    total_size = 0
    for file_path in path.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    return total_size


def _format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"