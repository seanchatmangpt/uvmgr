"""
uvmgr.runtime.cache
------------------
Runtime layer for cache management operations.

This module provides the runtime implementation for cache management operations,
including cleaning, sizing, and directory operations for uv cache and uvmgr's
internal cache systems.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import CacheAttributes, CacheOperations
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import span


def clear_cache(cache_type: str = "all") -> Dict[str, Any]:
    """
    Clear cache based on type.
    
    Args:
        cache_type: Type of cache to clear ("uv", "uvmgr", or "all")
        
    Returns:
        Dictionary with operation results
    """
    with span("cache.clear", cache_type=cache_type):
        add_span_attributes(**{
            CacheAttributes.OPERATION: CacheOperations.CLEAR,
            CacheAttributes.TYPE: cache_type,
        })
        add_span_event("cache.clear.started", {"type": cache_type})
        
        results = {"cleared": [], "errors": [], "sizes_freed": 0}
        
        try:
            if cache_type in ("uv", "all"):
                # Clear uv cache
                result = subprocess.run(
                    ["uv", "cache", "clean"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                results["cleared"].append("uv_cache")
                add_span_event("cache.uv.cleared", {"success": True})
                colour("✅ UV cache cleared", "green")
            
            if cache_type in ("uvmgr", "all"):
                # Clear uvmgr cache
                uvmgr_cache = Path.home() / ".uvmgr_cache"
                if uvmgr_cache.exists():
                    size_before = sum(f.stat().st_size for f in uvmgr_cache.rglob('*') if f.is_file())
                    shutil.rmtree(uvmgr_cache)
                    uvmgr_cache.mkdir(exist_ok=True)
                    results["cleared"].append("uvmgr_cache")
                    results["sizes_freed"] += size_before
                    add_span_event("cache.uvmgr.cleared", {"size_freed": size_before})
                    colour("✅ uvmgr cache cleared", "green")
                
            add_span_attributes(**{
                CacheAttributes.SIZE: results["sizes_freed"],
                "cache.cleared_count": len(results["cleared"]),
            })
            add_span_event("cache.clear.completed", {"success": True})
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to clear {cache_type} cache: {e.stderr}"
            results["errors"].append(error_msg)
            add_span_event("cache.clear.failed", {"error": error_msg})
            colour(f"❌ {error_msg}", "red")
        except Exception as e:
            error_msg = f"Error clearing cache: {str(e)}"
            results["errors"].append(error_msg)
            add_span_event("cache.clear.error", {"error": error_msg})
            colour(f"❌ {error_msg}", "red")
        
        return results


def get_cache_size(cache_type: str = "all") -> Dict[str, Any]:
    """
    Get cache size information.
    
    Args:
        cache_type: Type of cache to check ("uv", "uvmgr", or "all")
        
    Returns:
        Dictionary with cache size information
    """
    with span("cache.size", cache_type=cache_type):
        add_span_attributes(**{
            CacheAttributes.OPERATION: CacheOperations.SIZE,
            CacheAttributes.TYPE: cache_type,
        })
        add_span_event("cache.size.started", {"type": cache_type})
        
        sizes = {"uv_cache": 0, "uvmgr_cache": 0, "total": 0, "errors": []}
        
        try:
            if cache_type in ("uv", "all"):
                # Get uv cache info
                result = subprocess.run(
                    ["uv", "cache", "dir"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                uv_cache_dir = Path(result.stdout.strip())
                if uv_cache_dir.exists():
                    sizes["uv_cache"] = sum(
                        f.stat().st_size for f in uv_cache_dir.rglob('*') if f.is_file()
                    )
                add_span_event("cache.uv.size_checked", {"size": sizes["uv_cache"]})
            
            if cache_type in ("uvmgr", "all"):
                # Get uvmgr cache size
                uvmgr_cache = Path.home() / ".uvmgr_cache"
                if uvmgr_cache.exists():
                    sizes["uvmgr_cache"] = sum(
                        f.stat().st_size for f in uvmgr_cache.rglob('*') if f.is_file()
                    )
                add_span_event("cache.uvmgr.size_checked", {"size": sizes["uvmgr_cache"]})
            
            sizes["total"] = sizes["uv_cache"] + sizes["uvmgr_cache"]
            
            add_span_attributes(**{
                CacheAttributes.SIZE: sizes["total"],
                "cache.uv_size": sizes["uv_cache"],
                "cache.uvmgr_size": sizes["uvmgr_cache"],
            })
            add_span_event("cache.size.completed", {"total_size": sizes["total"]})
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to get cache size: {e.stderr}"
            sizes["errors"].append(error_msg)
            add_span_event("cache.size.failed", {"error": error_msg})
        except Exception as e:
            error_msg = f"Error getting cache size: {str(e)}"
            sizes["errors"].append(error_msg)
            add_span_event("cache.size.error", {"error": error_msg})
        
        return sizes


def get_cache_dir(cache_type: str = "uv") -> Optional[str]:
    """
    Get cache directory path.
    
    Args:
        cache_type: Type of cache ("uv" or "uvmgr")
        
    Returns:
        Cache directory path or None if not found
    """
    with span("cache.dir", cache_type=cache_type):
        add_span_attributes(**{
            CacheAttributes.OPERATION: CacheOperations.DIR,
            CacheAttributes.TYPE: cache_type,
        })
        add_span_event("cache.dir.started", {"type": cache_type})
        
        try:
            if cache_type == "uv":
                result = subprocess.run(
                    ["uv", "cache", "dir"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                cache_dir = result.stdout.strip()
                add_span_attributes(**{CacheAttributes.PATH: cache_dir})
                add_span_event("cache.dir.found", {"path": cache_dir})
                return cache_dir
            
            elif cache_type == "uvmgr":
                cache_dir = str(Path.home() / ".uvmgr_cache")
                add_span_attributes(**{CacheAttributes.PATH: cache_dir})
                add_span_event("cache.dir.found", {"path": cache_dir})
                return cache_dir
            
            else:
                add_span_event("cache.dir.invalid_type", {"type": cache_type})
                return None
                
        except subprocess.CalledProcessError as e:
            add_span_event("cache.dir.failed", {"error": e.stderr})
            return None
        except Exception as e:
            add_span_event("cache.dir.error", {"error": str(e)})
            return None


def get_cache_stats() -> Dict[str, Any]:
    """
    Get comprehensive cache statistics.
    
    Returns:
        Dictionary with detailed cache statistics
    """
    with span("cache.stats"):
        add_span_attributes(**{
            CacheAttributes.OPERATION: "stats",
        })
        add_span_event("cache.stats.started", {})
        
        stats = {
            "uv_cache": {"size": 0, "path": "", "exists": False, "item_count": 0},
            "uvmgr_cache": {"size": 0, "path": "", "exists": False, "item_count": 0},
            "total_size": 0,
            "total_items": 0,
        }
        
        try:
            # UV cache stats
            uv_dir = get_cache_dir("uv")
            if uv_dir:
                uv_path = Path(uv_dir)
                stats["uv_cache"]["path"] = str(uv_path)
                stats["uv_cache"]["exists"] = uv_path.exists()
                if uv_path.exists():
                    files = list(uv_path.rglob('*'))
                    file_files = [f for f in files if f.is_file()]
                    stats["uv_cache"]["size"] = sum(f.stat().st_size for f in file_files)
                    stats["uv_cache"]["item_count"] = len(file_files)
            
            # uvmgr cache stats
            uvmgr_dir = get_cache_dir("uvmgr")
            if uvmgr_dir:
                uvmgr_path = Path(uvmgr_dir)
                stats["uvmgr_cache"]["path"] = str(uvmgr_path)
                stats["uvmgr_cache"]["exists"] = uvmgr_path.exists()
                if uvmgr_path.exists():
                    files = list(uvmgr_path.rglob('*'))
                    file_files = [f for f in files if f.is_file()]
                    stats["uvmgr_cache"]["size"] = sum(f.stat().st_size for f in file_files)
                    stats["uvmgr_cache"]["item_count"] = len(file_files)
            
            # Totals
            stats["total_size"] = stats["uv_cache"]["size"] + stats["uvmgr_cache"]["size"]
            stats["total_items"] = stats["uv_cache"]["item_count"] + stats["uvmgr_cache"]["item_count"]
            
            add_span_attributes(**{
                CacheAttributes.SIZE: stats["total_size"],
                CacheAttributes.ITEM_COUNT: stats["total_items"],
            })
            add_span_event("cache.stats.completed", {"total_size": stats["total_size"]})
            
        except Exception as e:
            add_span_event("cache.stats.error", {"error": str(e)})
            stats["error"] = str(e)
        
        return stats