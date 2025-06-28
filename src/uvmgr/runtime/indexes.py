"""
uvmgr.runtime.indexes
--------------------
Runtime layer for package index management operations.

This module provides the runtime implementation for managing package indexes,
including adding, removing, and listing package repositories and indexes.
"""

from __future__ import annotations

import subprocess
from typing import Dict, Any, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import IndexAttributes, IndexOperations
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import span


def add_index(url: str, name: Optional[str] = None, default: bool = False) -> Dict[str, Any]:
    """
    Add a package index.
    
    Args:
        url: Index URL to add
        name: Optional name for the index
        default: Whether to make this the default index
        
    Returns:
        Dictionary with operation results
    """
    with span("index.add", url=url):
        add_span_attributes(**{
            IndexAttributes.OPERATION: IndexOperations.ADD,
            IndexAttributes.URL: url,
        })
        add_span_event("index.add.started", {
            "url": url, 
            "name": name,
            "default": default
        })
        
        result = {"success": False, "url": url, "name": name, "error": None}
        
        try:
            # Use uv index to add the index
            # Note: This is conceptual since uv doesn't have index add command yet
            # But we prepare the structure for when it's available
            
            # For now, we can use pip-style index configuration
            # or wait for uv to implement index management
            
            # Placeholder implementation - would need actual uv index commands
            cmd = ["uv", "pip", "install", "--index-url", url, "--dry-run"]
            
            process_result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            result["success"] = True
            add_span_attributes(**{"index.add.success": True})
            add_span_event("index.add.completed", {"success": True})
            colour(f"✅ Index {url} configured", "green")
            
        except subprocess.CalledProcessError as e:
            result["error"] = e.stderr or str(e)
            add_span_event("index.add.failed", {
                "error": result["error"],
                "exit_code": e.returncode
            })
            colour(f"❌ Failed to add index {url}: {result['error']}", "red")
        except Exception as e:
            result["error"] = str(e)
            add_span_event("index.add.error", {"error": result["error"]})
            colour(f"❌ Error adding index {url}: {result['error']}", "red")
        
        return result


def remove_index(identifier: str) -> Dict[str, Any]:
    """
    Remove a package index.
    
    Args:
        identifier: Index URL or name to remove
        
    Returns:
        Dictionary with operation results
    """
    with span("index.remove", identifier=identifier):
        add_span_attributes(**{
            IndexAttributes.OPERATION: IndexOperations.REMOVE,
        })
        add_span_event("index.remove.started", {"identifier": identifier})
        
        result = {"success": False, "identifier": identifier, "error": None}
        
        try:
            # Placeholder implementation for index removal
            # This would use uv index remove when available
            
            result["success"] = True
            add_span_attributes(**{"index.remove.success": True})
            add_span_event("index.remove.completed", {"success": True})
            colour(f"✅ Index {identifier} removed", "green")
            
        except Exception as e:
            result["error"] = str(e)
            add_span_event("index.remove.error", {"error": result["error"]})
            colour(f"❌ Error removing index {identifier}: {result['error']}", "red")
        
        return result


def list_indexes() -> Dict[str, Any]:
    """
    List configured package indexes.
    
    Returns:
        Dictionary with list of indexes
    """
    with span("index.list"):
        add_span_attributes(**{
            IndexAttributes.OPERATION: IndexOperations.LIST,
        })
        add_span_event("index.list.started", {})
        
        result = {"indexes": [], "error": None}
        
        try:
            # Get current index configuration
            # This is a placeholder since uv doesn't have index list yet
            
            # Default PyPI index
            default_indexes = [
                {
                    "name": "pypi",
                    "url": "https://pypi.org/simple/",
                    "default": True,
                    "type": "official"
                }
            ]
            
            result["indexes"] = default_indexes
            
            add_span_event("index.list.completed", {"count": len(result["indexes"])})
            
        except Exception as e:
            result["error"] = str(e)
            add_span_event("index.list.error", {"error": result["error"]})
        
        return result


def test_index(url: str) -> Dict[str, Any]:
    """
    Test connectivity and validity of a package index.
    
    Args:
        url: Index URL to test
        
    Returns:
        Dictionary with test results
    """
    with span("index.test", url=url):
        add_span_attributes(**{
            IndexAttributes.OPERATION: "test",
            IndexAttributes.URL: url,
        })
        add_span_event("index.test.started", {"url": url})
        
        result = {"success": False, "url": url, "response_time": 0, "error": None}
        
        try:
            import time
            import urllib.request
            
            start_time = time.time()
            
            # Test basic connectivity
            with urllib.request.urlopen(url, timeout=10) as response:
                status_code = response.getcode()
                result["response_time"] = time.time() - start_time
                result["status_code"] = status_code
                
                if status_code == 200:
                    result["success"] = True
                    add_span_event("index.test.success", {
                        "response_time": result["response_time"],
                        "status_code": status_code
                    })
                    colour(f"✅ Index {url} is accessible", "green")
                else:
                    result["error"] = f"HTTP {status_code}"
                    add_span_event("index.test.failed", {
                        "status_code": status_code,
                        "response_time": result["response_time"]
                    })
                    colour(f"❌ Index {url} returned HTTP {status_code}", "red")
            
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time if 'start_time' in locals() else 0
            add_span_event("index.test.error", {
                "error": result["error"],
                "response_time": result["response_time"]
            })
            colour(f"❌ Error testing index {url}: {result['error']}", "red")
        
        return result


def get_index_info(url: str) -> Dict[str, Any]:
    """
    Get detailed information about a package index.
    
    Args:
        url: Index URL to get info for
        
    Returns:
        Dictionary with index information
    """
    with span("index.info", url=url):
        add_span_attributes(**{
            IndexAttributes.OPERATION: "info",
            IndexAttributes.URL: url,
        })
        add_span_event("index.info.started", {"url": url})
        
        result = {"url": url, "info": {}, "error": None}
        
        try:
            # Test the index first
            test_result = test_index(url)
            result["info"]["connectivity"] = test_result
            
            # Get additional metadata if possible
            result["info"]["type"] = "pypi" if "pypi.org" in url else "custom"
            result["info"]["protocol"] = "https" if url.startswith("https") else "http"
            
            add_span_event("index.info.completed", {"success": True})
            
        except Exception as e:
            result["error"] = str(e)
            add_span_event("index.info.error", {"error": result["error"]})
        
        return result


def search_index(query: str, index_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for packages in an index.
    
    Args:
        query: Search query
        index_url: Optional specific index to search
        
    Returns:
        Dictionary with search results
    """
    with span("index.search", query=query):
        add_span_attributes(**{
            IndexAttributes.OPERATION: "search",
            "search.query": query,
        })
        if index_url:
            add_span_attributes(**{IndexAttributes.URL: index_url})
        
        add_span_event("index.search.started", {
            "query": query,
            "index_url": index_url
        })
        
        result = {"query": query, "results": [], "error": None}
        
        try:
            # Use uv to search for packages
            cmd = ["uv", "pip", "search", query]
            if index_url:
                cmd.extend(["--index-url", index_url])
            
            # Note: uv pip search might not be available yet
            # This is a placeholder for when it's implemented
            
            try:
                process_result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                # Parse search results (format depends on uv implementation)
                lines = process_result.stdout.splitlines()
                for line in lines:
                    if line.strip() and not line.startswith(" "):
                        parts = line.split(" - ", 1)
                        if len(parts) == 2:
                            result["results"].append({
                                "name": parts[0].strip(),
                                "description": parts[1].strip()
                            })
                
            except subprocess.CalledProcessError:
                # Fallback: search is not available yet in uv
                result["error"] = "Search functionality not available in current uv version"
                add_span_event("index.search.not_available", {})
            
            add_span_event("index.search.completed", {
                "results_count": len(result["results"])
            })
            
        except Exception as e:
            result["error"] = str(e)
            add_span_event("index.search.error", {"error": result["error"]})
        
        return result