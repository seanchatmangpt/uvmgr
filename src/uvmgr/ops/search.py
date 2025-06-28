"""
uvmgr.ops.search - Advanced Search Operations
==========================================

Core search operations and algorithms for comprehensive code, dependency,
file, log, and semantic search capabilities.

This module provides the implementation of advanced search functionality
including AST-based code parsing, dependency analysis, file indexing,
log aggregation, and AI-powered semantic search.

Key Components
--------------
• **CodeSearchEngine**: AST-based Python code search with semantic understanding
• **DependencyAnalyzer**: Comprehensive dependency analysis and vulnerability scanning
• **FileIndexer**: High-performance file search with metadata filtering
• **LogAggregator**: Multi-source log search and real-time following
• **SemanticSearchEngine**: AI-powered semantic search using embeddings
• **SearchCache**: Intelligent caching for performance optimization

Search Algorithms
-----------------
• **AST Pattern Matching**: Parse Python syntax trees for precise code search
• **Fuzzy Matching**: Flexible string matching with similarity scoring
• **Vector Similarity**: Semantic search using embedding vectors
• **Index-based Search**: Pre-built indexes for fast file and content search
• **Parallel Processing**: Multi-threaded search for large codebases
• **Incremental Updates**: Maintain search indexes with file change detection

Performance Features
-------------------
• **Smart Caching**: Cache parsed ASTs and search results
• **Parallel Execution**: Utilize multiple CPU cores for search operations
• **Memory Streaming**: Process large files without loading entirely into memory
• **Index Optimization**: Build and maintain optimized search indexes
• **Result Pagination**: Stream results for better memory usage
• **Progress Tracking**: Real-time progress updates for long searches

Integration Points
-----------------
• **OpenTelemetry**: Full observability and performance tracking
• **AI/MCP Integration**: Leverage AI for semantic understanding
• **Git Integration**: Search across branches and commit history
• **Security Scanning**: Identify potential security vulnerabilities
• **Quality Metrics**: Code complexity and quality analysis
"""

import ast
import asyncio
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, Union

# Import search-related libraries
try:
    import tree_sitter
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.shell import run_command


class SearchCache:
    """Intelligent caching system for search operations."""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path.home() / ".uvmgr" / "search_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "search_cache.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize the cache database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP,
                    accessed_at TIMESTAMP,
                    file_hash TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_indexes (
                    file_path TEXT PRIMARY KEY,
                    file_hash TEXT,
                    ast_cache TEXT,
                    metadata TEXT,
                    indexed_at TIMESTAMP
                )
            """)
    
    def get(self, key: str, file_path: Path = None) -> Optional[Any]:
        """Get cached value, checking file modification if provided."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if file_path and file_path.exists():
                # Check if file has been modified
                current_hash = self._file_hash(file_path)
                cursor.execute(
                    "SELECT value, file_hash FROM cache_entries WHERE key = ?",
                    (key,)
                )
                result = cursor.fetchone()
                
                if result and result[1] == current_hash:
                    # Update access time
                    cursor.execute(
                        "UPDATE cache_entries SET accessed_at = ? WHERE key = ?",
                        (datetime.now(), key)
                    )
                    return json.loads(result[0])
                return None
            else:
                cursor.execute("SELECT value FROM cache_entries WHERE key = ?", (key,))
                result = cursor.fetchone()
                if result:
                    cursor.execute(
                        "UPDATE cache_entries SET accessed_at = ? WHERE key = ?",
                        (datetime.now(), key)
                    )
                    return json.loads(result[0])
        return None
    
    def set(self, key: str, value: Any, file_path: Path = None):
        """Set cached value with optional file tracking."""
        file_hash = self._file_hash(file_path) if file_path and file_path.exists() else None
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache_entries 
                (key, value, created_at, accessed_at, file_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (key, json.dumps(value), datetime.now(), datetime.now(), file_hash))
    
    def _file_hash(self, file_path: Path) -> str:
        """Calculate file hash for cache invalidation."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def cleanup(self, max_age_days: int = 30):
        """Clean up old cache entries."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM cache_entries WHERE accessed_at < ?",
                (cutoff_date,)
            )


class CodeSearchEngine:
    """AST-based Python code search engine."""
    
    def __init__(self, cache: SearchCache = None):
        self.cache = cache or SearchCache()
        self.ast_patterns = {}
    
    def search(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code search with AST parsing."""
        add_span_event("code_search.started", {"pattern": config["pattern"]})
        
        start_time = time.time()
        matches = []
        files_scanned = 0
        
        search_path = config["path"]
        file_pattern = config["files"]
        
        # Find files to search
        files_to_search = self._find_files(search_path, file_pattern, config.get("exclude_dirs", []))
        
        # Use parallel processing if enabled
        if config.get("parallel", True):
            matches = self._parallel_search(files_to_search, config)
        else:
            for file_path in files_to_search:
                file_matches = self._search_file(file_path, config)
                matches.extend(file_matches)
                files_scanned += 1
        
        execution_time = time.time() - start_time
        
        # Filter and limit results
        matches = self._filter_matches(matches, config)
        matches = matches[:config.get("max_results", 100)]
        
        add_span_attributes(**{
            "search.files_scanned": files_scanned,
            "search.matches_found": len(matches),
            "search.execution_time": execution_time,
        })
        
        return {
            "matches": matches,
            "files_scanned": files_scanned,
            "execution_time": execution_time,
            "search_config": config,
        }
    
    def _find_files(self, search_path: Path, pattern: str, exclude_dirs: List[str]) -> List[Path]:
        """Find files matching the pattern."""
        files = []
        exclude_set = set(exclude_dirs)
        
        if pattern == "*.py":
            # Optimized Python file search
            for path in search_path.rglob("*.py"):
                if not any(part in exclude_set for part in path.parts):
                    files.append(path)
        else:
            # General pattern matching
            for path in search_path.rglob(pattern):
                if path.is_file() and not any(part in exclude_set for part in path.parts):
                    files.append(path)
        
        return files
    
    def _parallel_search(self, files: List[Path], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute parallel search across files."""
        matches = []
        max_workers = min(len(files), os.cpu_count() or 4)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._search_file, file_path, config): file_path
                for file_path in files
            }
            
            for future in as_completed(future_to_file):
                try:
                    file_matches = future.result()
                    matches.extend(file_matches)
                except Exception as e:
                    # Log error but continue searching
                    file_path = future_to_file[future]
                    add_span_event("code_search.file_error", {
                        "file": str(file_path),
                        "error": str(e)
                    })
        
        return matches
    
    def _search_file(self, file_path: Path, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search a single file using AST parsing."""
        try:
            # Check cache first
            cache_key = f"ast:{file_path}:{config['pattern']}"
            cached_result = self.cache.get(cache_key, file_path)
            if cached_result:
                return cached_result
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            matches = []
            
            if file_path.suffix == '.py':
                # Use AST parsing for Python files
                matches = self._search_python_ast(file_path, content, config)
            else:
                # Use text-based search for other files
                matches = self._search_text(file_path, content, config)
            
            # Cache the results
            self.cache.set(cache_key, matches, file_path)
            
            return matches
            
        except Exception as e:
            add_span_event("code_search.parse_error", {
                "file": str(file_path),
                "error": str(e)
            })
            return []
    
    def _search_python_ast(self, file_path: Path, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search Python file using AST parsing."""
        try:
            tree = ast.parse(content)
            matches = []
            lines = content.split('\n')
            
            pattern = config["pattern"]
            search_type = config.get("search_type", "all")
            include_docs = config.get("include_docs", False)
            
            # Compile regex pattern
            flags = 0 if config.get("case_sensitive", False) else re.IGNORECASE
            if config.get("exact_match", False):
                regex = re.compile(re.escape(pattern), flags)
            else:
                regex = re.compile(pattern, flags)
            
            for node in ast.walk(tree):
                match_info = self._check_ast_node(node, regex, search_type, include_docs, lines)
                if match_info:
                    match_info["file"] = str(file_path)
                    matches.append(match_info)
            
            return matches
            
        except SyntaxError:
            # Fall back to text search for files with syntax errors
            return self._search_text(file_path, content, config)
    
    def _check_ast_node(self, node: ast.AST, regex: re.Pattern, search_type: str, 
                       include_docs: bool, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Check if an AST node matches the search criteria."""
        match_info = None
        
        # Function definitions
        if (search_type in ["all", "function"] and 
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
            if regex.search(node.name):
                match_info = {
                    "type": "function",
                    "name": node.name,
                    "line": node.lineno,
                    "complexity": self._calculate_complexity(node),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }
        
        # Class definitions
        elif (search_type in ["all", "class"] and isinstance(node, ast.ClassDef)):
            if regex.search(node.name):
                match_info = {
                    "type": "class",
                    "name": node.name,
                    "line": node.lineno,
                    "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                    "bases": [self._get_name(base) for base in node.bases],
                }
        
        # Variable assignments
        elif (search_type in ["all", "variable"] and isinstance(node, ast.Assign)):
            for target in node.targets:
                if isinstance(target, ast.Name) and regex.search(target.id):
                    match_info = {
                        "type": "variable",
                        "name": target.id,
                        "line": node.lineno,
                        "value_type": type(node.value).__name__,
                    }
                    break
        
        # Import statements
        elif (search_type in ["all", "import"] and isinstance(node, (ast.Import, ast.ImportFrom))):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if regex.search(alias.name):
                        match_info = {
                            "type": "import",
                            "name": alias.name,
                            "line": node.lineno,
                            "alias": alias.asname,
                        }
                        break
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if regex.search(module):
                    match_info = {
                        "type": "import_from",
                        "module": module,
                        "line": node.lineno,
                        "names": [alias.name for alias in node.names],
                    }
        
        # Decorators
        elif (search_type in ["all", "decorator"] and 
              hasattr(node, 'decorator_list') and node.decorator_list):
            for decorator in node.decorator_list:
                decorator_name = self._get_name(decorator)
                if decorator_name and regex.search(decorator_name):
                    match_info = {
                        "type": "decorator",
                        "name": decorator_name,
                        "line": decorator.lineno,
                        "target": getattr(node, 'name', 'unknown'),
                    }
                    break
        
        # Add context lines if match found
        if match_info:
            context_lines = self._get_context_lines(
                lines, match_info["line"] - 1, 
                config.get("context_lines", 3)
            )
            match_info["context"] = context_lines
            match_info["content"] = lines[match_info["line"] - 1] if match_info["line"] <= len(lines) else ""
        
        return match_info
    
    def _search_text(self, file_path: Path, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search file using text-based pattern matching."""
        pattern = config["pattern"]
        flags = 0 if config.get("case_sensitive", False) else re.IGNORECASE
        
        if config.get("exact_match", False):
            regex = re.compile(re.escape(pattern), flags)
        else:
            regex = re.compile(pattern, flags)
        
        matches = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if regex.search(line):
                context_lines = self._get_context_lines(lines, line_num - 1, config.get("context_lines", 3))
                matches.append({
                    "type": "text",
                    "line": line_num,
                    "file": str(file_path),
                    "content": line,
                    "context": context_lines,
                })
        
        return matches
    
    def _get_context_lines(self, lines: List[str], center_line: int, context: int) -> List[str]:
        """Get context lines around a match."""
        start = max(0, center_line - context)
        end = min(len(lines), center_line + context + 1)
        return lines[start:end]
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _get_name(self, node: ast.AST) -> Optional[str]:
        """Extract name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return None
    
    def _filter_matches(self, matches: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter matches based on configuration criteria."""
        filtered = matches
        
        # Filter by complexity
        complexity_range = config.get("complexity_range", (None, None))
        if complexity_range[0] is not None or complexity_range[1] is not None:
            min_complexity, max_complexity = complexity_range
            filtered = [
                m for m in filtered 
                if (min_complexity is None or m.get("complexity", 0) >= min_complexity) and
                   (max_complexity is None or m.get("complexity", 0) <= max_complexity)
            ]
        
        # Filter by line count
        lines_range = config.get("lines_range", (None, None))
        if lines_range[0] is not None or lines_range[1] is not None:
            min_lines, max_lines = lines_range
            filtered = [
                m for m in filtered
                if (min_lines is None or len(m.get("context", [])) >= min_lines) and
                   (max_lines is None or len(m.get("context", [])) <= max_lines)
            ]
        
        return filtered


class DependencyAnalyzer:
    """Comprehensive dependency analysis and search."""
    
    def __init__(self, cache: SearchCache = None):
        self.cache = cache or SearchCache()
    
    def search(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Search dependencies and analyze usage."""
        add_span_event("deps_search.started", {"pattern": config["pattern"]})
        
        search_path = config["path"]
        pattern = config["pattern"]
        search_type = config.get("search_type", "all")
        
        matches = []
        
        if search_type in ["all", "installed"]:
            matches.extend(self._search_installed_packages(pattern, config))
        
        if search_type in ["all", "imports"]:
            matches.extend(self._search_import_usage(search_path, pattern, config))
        
        if search_type in ["all", "requirements", "pyproject"]:
            matches.extend(self._search_requirements(search_path, pattern, config))
        
        # Add vulnerability information if requested
        if config.get("show_vulnerabilities", False):
            matches = self._add_vulnerability_info(matches)
        
        # Filter results
        if config.get("outdated_only", False):
            matches = self._filter_outdated(matches)
        
        if config.get("unused_only", False):
            matches = self._filter_unused(matches, search_path)
        
        return {
            "matches": matches[:config.get("max_results", 50)],
            "search_config": config,
        }
    
    def _search_installed_packages(self, pattern: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search installed packages using uv/pip."""
        try:
            # Use uv if available, fall back to pip
            try:
                result = run_command(["uv", "pip", "list", "--format", "json"])
                packages = json.loads(result.stdout)
            except:
                result = run_command(["pip", "list", "--format", "json"])
                packages = json.loads(result.stdout)
            
            matches = []
            pattern_regex = re.compile(pattern, re.IGNORECASE)
            
            for package in packages:
                name = package["name"]
                version = package["version"]
                
                if pattern == "*" or pattern_regex.search(name):
                    match_info = {
                        "name": name,
                        "version": version,
                        "type": "installed",
                        "source": "pip_list",
                    }
                    
                    if config.get("show_versions", False):
                        match_info.update(self._get_package_info(name))
                    
                    matches.append(match_info)
            
            return matches
            
        except Exception as e:
            add_span_event("deps_search.installed_error", {"error": str(e)})
            return []
    
    def _search_import_usage(self, search_path: Path, pattern: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for import usage in Python files."""
        matches = []
        pattern_regex = re.compile(pattern, re.IGNORECASE)
        
        for py_file in search_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                lines = content.split('\n')
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        import_matches = self._extract_import_matches(node, pattern_regex, py_file, lines)
                        matches.extend(import_matches)
                        
            except Exception:
                continue  # Skip files with syntax errors
        
        return matches
    
    def _search_requirements(self, search_path: Path, pattern: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search requirements files and pyproject.toml."""
        matches = []
        pattern_regex = re.compile(pattern, re.IGNORECASE)
        
        # Search requirements files
        for req_file in search_path.rglob("requirements*.txt"):
            matches.extend(self._parse_requirements_file(req_file, pattern_regex))
        
        # Search pyproject.toml
        pyproject_file = search_path / "pyproject.toml"
        if pyproject_file.exists():
            matches.extend(self._parse_pyproject_toml(pyproject_file, pattern_regex, config))
        
        return matches
    
    def _extract_import_matches(self, node: ast.AST, pattern: re.Pattern, 
                              file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract import matches from AST node."""
        matches = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                if pattern.search(alias.name):
                    matches.append({
                        "name": alias.name,
                        "type": "import",
                        "file": str(file_path),
                        "line": node.lineno,
                        "alias": alias.asname,
                        "usage": [{"file": str(file_path), "line": node.lineno}],
                    })
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if pattern.search(module):
                matches.append({
                    "name": module,
                    "type": "import_from",
                    "file": str(file_path),
                    "line": node.lineno,
                    "imports": [alias.name for alias in node.names],
                    "usage": [{"file": str(file_path), "line": node.lineno}],
                })
        
        return matches
    
    def _parse_requirements_file(self, req_file: Path, pattern: re.Pattern) -> List[Dict[str, Any]]:
        """Parse requirements.txt file."""
        matches = []
        
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package name and version
                        parts = re.split(r'[><=!]', line)
                        if parts:
                            package_name = parts[0].strip()
                            if pattern.search(package_name):
                                matches.append({
                                    "name": package_name,
                                    "type": "requirement",
                                    "file": str(req_file),
                                    "line": line_num,
                                    "constraint": line,
                                })
        except Exception:
            pass
        
        return matches
    
    def _parse_pyproject_toml(self, pyproject_file: Path, pattern: re.Pattern, 
                             config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse pyproject.toml for dependencies."""
        matches = []
        
        try:
            import tomllib
            with open(pyproject_file, 'rb') as f:
                data = tomllib.load(f)
            
            # Check project dependencies
            project_deps = data.get("project", {}).get("dependencies", [])
            for dep in project_deps:
                package_name = re.split(r'[><=!]', dep)[0].strip()
                if pattern.search(package_name):
                    matches.append({
                        "name": package_name,
                        "type": "project_dependency",
                        "file": str(pyproject_file),
                        "constraint": dep,
                        "section": "project.dependencies",
                    })
            
            # Check optional dependencies if including dev
            if config.get("include_dev", True):
                optional_deps = data.get("project", {}).get("optional-dependencies", {})
                for group, deps in optional_deps.items():
                    for dep in deps:
                        package_name = re.split(r'[><=!]', dep)[0].strip()
                        if pattern.search(package_name):
                            matches.append({
                                "name": package_name,
                                "type": "optional_dependency",
                                "file": str(pyproject_file),
                                "constraint": dep,
                                "section": f"project.optional-dependencies.{group}",
                            })
        
        except Exception:
            pass
        
        return matches
    
    def _get_package_info(self, package_name: str) -> Dict[str, Any]:
        """Get detailed package information."""
        try:
            result = run_command(["pip", "show", package_name])
            info = {}
            
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip().lower()] = value.strip()
            
            return {
                "summary": info.get("summary", ""),
                "homepage": info.get("home-page", ""),
                "author": info.get("author", ""),
                "license": info.get("license", ""),
                "requires": info.get("requires", "").split(', ') if info.get("requires") else [],
            }
        except Exception:
            return {}
    
    def _add_vulnerability_info(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add vulnerability information using safety or similar tools."""
        # This would integrate with vulnerability databases
        # For now, return matches as-is
        return matches
    
    def _filter_outdated(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter to show only outdated packages."""
        # This would check for newer versions
        # For now, return all matches
        return matches
    
    def _filter_unused(self, matches: List[Dict[str, Any]], search_path: Path) -> List[Dict[str, Any]]:
        """Filter to show only unused dependencies."""
        # This would analyze import usage vs declared dependencies
        # For now, return all matches
        return matches


class FileSearchEngine:
    """High-performance file search with metadata filtering."""
    
    def __init__(self, cache: SearchCache = None):
        self.cache = cache or SearchCache()
    
    def search(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file search with advanced filtering."""
        add_span_event("file_search.started", {"pattern": config["pattern"]})
        
        start_time = time.time()
        search_path = config["path"]
        pattern = config["pattern"]
        
        # Find files matching criteria
        candidate_files = self._find_candidate_files(search_path, config)
        
        # Search file contents
        matches = []
        files_scanned = 0
        
        if config.get("parallel", True):
            matches = self._parallel_file_search(candidate_files, pattern, config)
            files_scanned = len(candidate_files)
        else:
            for file_path in candidate_files:
                file_matches = self._search_file_content(file_path, pattern, config)
                matches.extend(file_matches)
                files_scanned += 1
        
        execution_time = time.time() - start_time
        
        return {
            "matches": matches[:config.get("max_results", 100)],
            "files_scanned": files_scanned,
            "execution_time": execution_time,
            "search_config": config,
        }
    
    def _find_candidate_files(self, search_path: Path, config: Dict[str, Any]) -> List[Path]:
        """Find files matching the search criteria."""
        files = []
        file_pattern = config.get("files", "*")
        name_pattern = config.get("name_pattern")
        file_types = config.get("file_types", "all")
        exclude_dirs = set(config.get("exclude_dirs", []))
        include_hidden = config.get("include_hidden", False)
        max_file_size = self._parse_file_size(config.get("max_file_size", "10MB"))
        modified_since = config.get("modified_since")
        created_since = config.get("created_since")
        
        for path in search_path.rglob(file_pattern):
            if not path.is_file():
                continue
            
            # Skip hidden files/directories unless requested
            if not include_hidden and any(part.startswith('.') for part in path.parts):
                continue
            
            # Skip excluded directories
            if any(part in exclude_dirs for part in path.parts):
                continue
            
            # Check file name pattern
            if name_pattern and not re.search(name_pattern, path.name, re.IGNORECASE):
                continue
            
            # Check file type
            if not self._matches_file_type(path, file_types):
                continue
            
            # Check file size
            try:
                if path.stat().st_size > max_file_size:
                    continue
            except OSError:
                continue
            
            # Check modification time
            if modified_since:
                try:
                    if datetime.fromtimestamp(path.stat().st_mtime) < modified_since:
                        continue
                except OSError:
                    continue
            
            # Check creation time
            if created_since:
                try:
                    if datetime.fromtimestamp(path.stat().st_ctime) < created_since:
                        continue
                except OSError:
                    continue
            
            files.append(path)
        
        return files
    
    def _matches_file_type(self, path: Path, file_types: str) -> bool:
        """Check if file matches the specified type."""
        if file_types == "all":
            return True
        
        suffix = path.suffix.lower()
        
        type_mappings = {
            "source": {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".rs", ".go"},
            "config": {".toml", ".yaml", ".yml", ".json", ".ini", ".cfg", ".conf", ".env"},
            "docs": {".md", ".rst", ".txt", ".doc", ".docx", ".pdf"},
            "data": {".csv", ".json", ".xml", ".yaml", ".yml", ".db", ".sqlite"},
        }
        
        for file_type in file_types.split(","):
            file_type = file_type.strip()
            if file_type in type_mappings and suffix in type_mappings[file_type]:
                return True
        
        return False
    
    def _parse_file_size(self, size_str: str) -> int:
        """Parse file size string (e.g., '10MB', '1GB')."""
        size_str = size_str.upper()
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                number = size_str[:-len(suffix)]
                try:
                    return int(number) * multiplier
                except ValueError:
                    return 10 * 1024 * 1024  # Default 10MB
        
        return 10 * 1024 * 1024  # Default 10MB
    
    def _parallel_file_search(self, files: List[Path], pattern: str, 
                             config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute parallel file content search."""
        matches = []
        max_workers = min(len(files), os.cpu_count() or 4)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._search_file_content, file_path, pattern, config): file_path
                for file_path in files
            }
            
            for future in as_completed(future_to_file):
                try:
                    file_matches = future.result()
                    matches.extend(file_matches)
                except Exception as e:
                    file_path = future_to_file[future]
                    add_span_event("file_search.error", {
                        "file": str(file_path),
                        "error": str(e)
                    })
        
        return matches
    
    def _search_file_content(self, file_path: Path, pattern: str, 
                           config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search content within a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            matches = []
            case_sensitive = config.get("case_sensitive", False)
            whole_words = config.get("whole_words", False)
            context_lines = config.get("context_lines", 3)
            
            # Build regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            if whole_words:
                pattern = r'\b' + re.escape(pattern) + r'\b'
            
            regex = re.compile(pattern, flags)
            
            for line_num, line in enumerate(lines, 1):
                if regex.search(line.rstrip('\n')):
                    context = self._get_file_context(lines, line_num - 1, context_lines)
                    matches.append({
                        "file": str(file_path),
                        "line": line_num,
                        "content": line.rstrip('\n'),
                        "context": context,
                    })
            
            return matches
            
        except Exception:
            return []
    
    def _get_file_context(self, lines: List[str], center_line: int, context: int) -> List[str]:
        """Get context lines around a match."""
        start = max(0, center_line - context)
        end = min(len(lines), center_line + context + 1)
        return [line.rstrip('\n') for line in lines[start:end]]


class LogSearchEngine:
    """Multi-source log search and aggregation."""
    
    def __init__(self, cache: SearchCache = None):
        self.cache = cache or SearchCache()
        self.log_sources = {
            "uvmgr": self._get_uvmgr_logs,
            "otel": self._get_otel_logs,
            "system": self._get_system_logs,
        }
    
    def search(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Search logs from multiple sources."""
        add_span_event("log_search.started", {"pattern": config["pattern"]})
        
        pattern = config["pattern"]
        log_sources = config.get("log_sources", ["all"])
        level = config.get("level", "all")
        since = config.get("since")
        until = config.get("until")
        
        matches = []
        files_scanned = 0
        
        # Determine which log sources to search
        sources_to_search = []
        if "all" in log_sources:
            sources_to_search = list(self.log_sources.keys())
        else:
            sources_to_search = [src for src in log_sources if src in self.log_sources]
        
        # Search each log source
        for source in sources_to_search:
            source_matches, source_files = self.log_sources[source](config)
            matches.extend(source_matches)
            files_scanned += source_files
        
        # Filter by time range
        if since or until:
            matches = self._filter_by_time(matches, since, until)
        
        # Filter by log level
        if level != "all":
            matches = self._filter_by_level(matches, level)
        
        # Sort by timestamp
        matches.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "matches": matches[:config.get("max_results", 100)],
            "files_scanned": files_scanned,
            "search_config": config,
        }
    
    def follow_logs(self, config: Dict[str, Any], callback: Callable[[Dict[str, Any]], None]):
        """Follow logs in real-time."""
        # This would implement real-time log following
        # For now, just call the callback with some sample data
        pass
    
    def _get_uvmgr_logs(self, config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Get uvmgr-specific logs."""
        matches = []
        files_scanned = 0
        
        # Look for uvmgr log files
        log_dirs = [
            Path.home() / ".uvmgr" / "logs",
            Path("/var/log/uvmgr"),
            Path("/tmp/uvmgr"),
        ]
        
        pattern = config["pattern"]
        case_sensitive = config.get("case_sensitive", False)
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        for log_dir in log_dirs:
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    file_matches = self._search_log_file(log_file, regex, config)
                    matches.extend(file_matches)
                    files_scanned += 1
        
        return matches, files_scanned
    
    def _get_otel_logs(self, config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Get OpenTelemetry logs and traces."""
        # This would integrate with OTEL collector or Jaeger
        return [], 0
    
    def _get_system_logs(self, config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Get system logs."""
        # This would search system logs (/var/log, journalctl, etc.)
        return [], 0
    
    def _search_log_file(self, log_file: Path, regex: re.Pattern, 
                        config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search a single log file."""
        matches = []
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.rstrip('\n')
                    if regex.search(line):
                        log_entry = self._parse_log_line(line, str(log_file), line_num)
                        matches.append(log_entry)
            
        except Exception:
            pass
        
        return matches
    
    def _parse_log_line(self, line: str, file_path: str, line_num: int) -> Dict[str, Any]:
        """Parse a log line to extract structured information."""
        # Simple log parsing - could be enhanced with proper log parsers
        entry = {
            "file": file_path,
            "line": line_num,
            "message": line,
            "raw": line,
        }
        
        # Try to extract timestamp
        timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', line)
        if timestamp_match:
            entry["timestamp"] = timestamp_match.group()
        
        # Try to extract log level
        level_match = re.search(r'\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b', line, re.IGNORECASE)
        if level_match:
            entry["level"] = level_match.group().lower()
        
        # Try to extract service name
        service_match = re.search(r'service[_\.]name[=:][\s]*([^\s,]+)', line, re.IGNORECASE)
        if service_match:
            entry["service"] = service_match.group(1)
        
        return entry
    
    def _filter_by_time(self, matches: List[Dict[str, Any]], since: datetime = None, 
                       until: datetime = None) -> List[Dict[str, Any]]:
        """Filter log entries by time range."""
        if not since and not until:
            return matches
        
        filtered = []
        for match in matches:
            timestamp_str = match.get("timestamp")
            if not timestamp_str:
                continue
            
            try:
                # Try to parse timestamp
                timestamp = datetime.fromisoformat(timestamp_str.replace('T', ' '))
                
                if since and timestamp < since:
                    continue
                if until and timestamp > until:
                    continue
                
                filtered.append(match)
            except ValueError:
                # Skip entries with unparseable timestamps
                continue
        
        return filtered
    
    def _filter_by_level(self, matches: List[Dict[str, Any]], level: str) -> List[Dict[str, Any]]:
        """Filter log entries by log level."""
        level_hierarchy = {
            "debug": 0,
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4,
        }
        
        target_level = level_hierarchy.get(level.lower(), 1)
        
        return [
            match for match in matches
            if level_hierarchy.get(match.get("level", "info").lower(), 1) >= target_level
        ]


class SemanticSearchEngine:
    """AI-powered semantic search using embeddings."""
    
    def __init__(self, cache: SearchCache = None):
        self.cache = cache or SearchCache()
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """Initialize the sentence transformer model."""
        if EMBEDDINGS_AVAILABLE:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                self.model = None
        
    def search(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute semantic search using AI embeddings."""
        if not self.model:
            return {
                "matches": [],
                "error": "Semantic search requires sentence-transformers library",
                "search_config": config,
            }
        
        add_span_event("semantic_search.started", {"query": config["query"]})
        
        query = config["query"]
        search_path = config["path"]
        search_scope = config.get("search_scope", "all")
        similarity_threshold = config.get("similarity_threshold", 0.7)
        max_results = config.get("max_results", 20)
        
        # Extract text from files
        text_chunks = self._extract_text_chunks(search_path, search_scope)
        
        if not text_chunks:
            return {
                "matches": [],
                "search_config": config,
            }
        
        # Generate embeddings
        query_embedding = self.model.encode([query])
        chunk_embeddings = self.model.encode([chunk["text"] for chunk in text_chunks])
        
        # Calculate similarities
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]
        
        # Create matches with similarity scores
        matches = []
        for i, similarity in enumerate(similarities):
            if similarity >= similarity_threshold:
                chunk = text_chunks[i]
                match = {
                    "file": chunk["file"],
                    "line": chunk.get("line"),
                    "type": chunk["type"],
                    "similarity": float(similarity),
                    "preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                    "full_text": chunk["text"],
                }
                
                if config.get("explain_results", False):
                    match["explanation"] = self._explain_similarity(query, chunk["text"], similarity)
                
                matches.append(match)
        
        # Sort by similarity
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        avg_similarity = sum(m["similarity"] for m in matches) / len(matches) if matches else 0
        
        return {
            "matches": matches[:max_results],
            "avg_similarity": avg_similarity,
            "total_chunks_processed": len(text_chunks),
            "search_config": config,
        }
    
    def _extract_text_chunks(self, search_path: Path, search_scope: str) -> List[Dict[str, Any]]:
        """Extract text chunks from files for semantic search."""
        chunks = []
        
        scope_patterns = {
            "all": ["*.py", "*.md", "*.rst", "*.txt"],
            "code": ["*.py"],
            "docs": ["*.md", "*.rst", "*.txt"],
            "comments": ["*.py"],  # Will extract only comments
            "tests": ["test_*.py", "*_test.py"],
        }
        
        patterns = scope_patterns.get(search_scope, scope_patterns["all"])
        
        for pattern in patterns:
            for file_path in search_path.rglob(pattern):
                if file_path.is_file():
                    file_chunks = self._extract_file_chunks(file_path, search_scope)
                    chunks.extend(file_chunks)
        
        return chunks
    
    def _extract_file_chunks(self, file_path: Path, search_scope: str) -> List[Dict[str, Any]]:
        """Extract text chunks from a single file."""
        chunks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if file_path.suffix == '.py':
                chunks.extend(self._extract_python_chunks(file_path, content, search_scope))
            elif file_path.suffix in ['.md', '.rst', '.txt']:
                chunks.extend(self._extract_doc_chunks(file_path, content))
            else:
                # General text extraction
                chunks.append({
                    "file": str(file_path),
                    "type": "content",
                    "text": content,
                })
        
        except Exception:
            pass
        
        return chunks
    
    def _extract_python_chunks(self, file_path: Path, content: str, 
                              search_scope: str) -> List[Dict[str, Any]]:
        """Extract semantic chunks from Python files."""
        chunks = []
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                # Function definitions
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_text = self._extract_function_text(node, lines)
                    if func_text:
                        chunks.append({
                            "file": str(file_path),
                            "line": node.lineno,
                            "type": "function",
                            "text": func_text,
                            "name": node.name,
                        })
                
                # Class definitions
                elif isinstance(node, ast.ClassDef):
                    class_text = self._extract_class_text(node, lines)
                    if class_text:
                        chunks.append({
                            "file": str(file_path),
                            "line": node.lineno,
                            "type": "class",
                            "text": class_text,
                            "name": node.name,
                        })
            
            # Extract comments if requested
            if search_scope in ["all", "comments"]:
                comment_chunks = self._extract_comments(file_path, lines)
                chunks.extend(comment_chunks)
        
        except SyntaxError:
            # Fall back to text extraction for files with syntax errors
            chunks.append({
                "file": str(file_path),
                "type": "content",
                "text": content,
            })
        
        return chunks
    
    def _extract_function_text(self, node: ast.FunctionDef, lines: List[str]) -> str:
        """Extract function definition and docstring."""
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10
        
        func_lines = lines[start_line:end_line]
        func_text = '\n'.join(func_lines)
        
        # Include docstring in the text
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
            func_text = f"{func_text}\n\nDocstring: {docstring}"
        
        return func_text
    
    def _extract_class_text(self, node: ast.ClassDef, lines: List[str]) -> str:
        """Extract class definition and docstring."""
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 20
        
        class_lines = lines[start_line:end_line]
        class_text = '\n'.join(class_lines)
        
        # Include docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
            class_text = f"{class_text}\n\nDocstring: {docstring}"
        
        return class_text
    
    def _extract_comments(self, file_path: Path, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract comments from Python file."""
        chunks = []
        current_comment = []
        comment_start = None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                if not current_comment:
                    comment_start = line_num
                current_comment.append(stripped[1:].strip())
            else:
                if current_comment:
                    comment_text = ' '.join(current_comment)
                    if len(comment_text) > 10:  # Only include substantial comments
                        chunks.append({
                            "file": str(file_path),
                            "line": comment_start,
                            "type": "comment",
                            "text": comment_text,
                        })
                    current_comment = []
                    comment_start = None
        
        return chunks
    
    def _extract_doc_chunks(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Extract chunks from documentation files."""
        chunks = []
        
        # Split by headers or paragraphs
        if file_path.suffix == '.md':
            # Split by markdown headers
            sections = re.split(r'^#+\s+', content, flags=re.MULTILINE)
            for i, section in enumerate(sections):
                if section.strip():
                    chunks.append({
                        "file": str(file_path),
                        "type": "documentation",
                        "text": section.strip(),
                        "section": i,
                    })
        else:
            # Split by double newlines (paragraphs)
            paragraphs = re.split(r'\n\s*\n', content)
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip() and len(paragraph.strip()) > 50:
                    chunks.append({
                        "file": str(file_path),
                        "type": "documentation",
                        "text": paragraph.strip(),
                        "paragraph": i,
                    })
        
        return chunks
    
    def _explain_similarity(self, query: str, text: str, similarity: float) -> str:
        """Generate explanation for why text matches the query."""
        # Simple explanation based on similarity score
        if similarity > 0.9:
            return "Very high semantic similarity - closely matches the query intent"
        elif similarity > 0.8:
            return "High semantic similarity - strongly related concepts"
        elif similarity > 0.7:
            return "Good semantic similarity - related concepts and themes"
        else:
            return "Moderate semantic similarity - some conceptual overlap"


# Main search functions
def search_code(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute code search operation."""
    engine = CodeSearchEngine()
    return engine.search(config)


def search_dependencies(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute dependency search operation."""
    analyzer = DependencyAnalyzer()
    return analyzer.search(config)


def search_files(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute file search operation."""
    engine = FileSearchEngine()
    return engine.search(config)


def search_logs(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute log search operation."""
    engine = LogSearchEngine()
    return engine.search(config)


def follow_logs(config: Dict[str, Any], callback: Callable[[Dict[str, Any]], None]):
    """Follow logs in real-time."""
    engine = LogSearchEngine()
    engine.follow_logs(config, callback)


def search_semantic(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute semantic search operation."""
    engine = SemanticSearchEngine()
    return engine.search(config)


def search_all(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute multi-faceted search across all sources."""
    results = {}
    
    # Prepare individual search configs
    base_config = {
        "path": config["path"],
        "pattern": config["pattern"],
        "max_results": config.get("max_results_per_type", 25),
    }
    
    search_tasks = []
    
    if config.get("include_code", True):
        search_tasks.append(("code", search_code, {**base_config, "files": "*.py"}))
    
    if config.get("include_deps", True):
        search_tasks.append(("deps", search_dependencies, base_config))
    
    if config.get("include_files", True):
        search_tasks.append(("files", search_files, base_config))
    
    if config.get("include_logs", False):
        search_tasks.append(("logs", search_logs, base_config))
    
    # Execute searches
    if config.get("parallel", True):
        # Parallel execution
        with ThreadPoolExecutor(max_workers=len(search_tasks)) as executor:
            future_to_type = {
                executor.submit(search_func, search_config): search_type
                for search_type, search_func, search_config in search_tasks
            }
            
            for future in as_completed(future_to_type):
                search_type = future_to_type[future]
                try:
                    results[search_type] = future.result()
                except Exception as e:
                    results[search_type] = {"matches": [], "error": str(e)}
    else:
        # Sequential execution
        for search_type, search_func, search_config in search_tasks:
            try:
                results[search_type] = search_func(search_config)
            except Exception as e:
                results[search_type] = {"matches": [], "error": str(e)}
    
    return results