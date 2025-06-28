"""
Tests for uvmgr search operations
===============================

Comprehensive test suite for search operation implementations including
AST parsing, dependency analysis, file indexing, log aggregation, and
semantic search engines.
"""

import ast
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from uvmgr.ops.search import (
    SearchCache,
    CodeSearchEngine, 
    DependencyAnalyzer,
    FileSearchEngine,
    LogSearchEngine,
    SemanticSearchEngine,
    search_code,
    search_dependencies,
    search_files,
    search_logs,
    search_semantic,
    search_all,
)


class TestSearchCache:
    """Test suite for search caching functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.cache = SearchCache(self.cache_dir)
    
    def test_cache_initialization(self):
        """Test cache database initialization."""
        assert self.cache_dir.exists()
        assert (self.cache_dir / "search_cache.db").exists()
        
        # Check database schema
        with sqlite3.connect(self.cache.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert "cache_entries" in tables
            assert "file_indexes" in tables
    
    def test_cache_set_get(self):
        """Test basic cache set and get operations."""
        key = "test_key"
        value = {"result": "test_data", "count": 42}
        
        # Set value
        self.cache.set(key, value)
        
        # Get value
        retrieved = self.cache.get(key)
        assert retrieved == value
    
    def test_cache_file_tracking(self):
        """Test cache invalidation based on file changes."""
        # Create a test file
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('hello')")
        
        key = "file_test"
        value = {"parsed": True}
        
        # Set cache with file tracking
        self.cache.set(key, value, test_file)
        
        # Should retrieve cached value
        assert self.cache.get(key, test_file) == value
        
        # Modify file
        test_file.write_text("print('modified')")
        
        # Should return None due to file change
        assert self.cache.get(key, test_file) is None
    
    def test_cache_cleanup(self):
        """Test cache cleanup functionality."""
        old_key = "old_key"
        new_key = "new_key"
        
        # Set old entry (simulate old timestamp)
        self.cache.set(old_key, {"old": "data"})
        
        # Manually update timestamp to be old
        with sqlite3.connect(self.cache.db_path) as conn:
            old_date = datetime.now() - timedelta(days=35)
            conn.execute(
                "UPDATE cache_entries SET accessed_at = ? WHERE key = ?",
                (old_date, old_key)
            )
        
        # Set new entry
        self.cache.set(new_key, {"new": "data"})
        
        # Run cleanup
        self.cache.cleanup(max_age_days=30)
        
        # Old entry should be gone, new entry should remain
        assert self.cache.get(old_key) is None
        assert self.cache.get(new_key) is not None


class TestCodeSearchEngine:
    """Test suite for AST-based code search engine."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.engine = CodeSearchEngine()
    
    def test_python_ast_parsing(self):
        """Test Python AST parsing and search."""
        # Create test Python file
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
import requests
from typing import Optional

def fetch_data(url: str) -> Optional[dict]:
    '''Fetch data from URL with error handling.'''
    try:
        response = requests.get(url, timeout=30)
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data: {e}")
        return None

class DataProcessor:
    '''Process and validate data.'''
    
    def __init__(self, cache_size: int = 100):
        self.cache = {}
        self.cache_size = cache_size
    
    @property  
    def cache_count(self):
        return len(self.cache)
    
    async def process_async(self, data):
        # Complex processing logic
        for item in data:
            if self.validate(item):
                await self.store(item)
            else:
                self.reject(item)
        return True
""")
        
        config = {
            "pattern": "fetch_data",
            "path": self.temp_path,
            "files": "*.py",
            "search_type": "function",
            "include_tests": False,
            "include_docs": True,
            "case_sensitive": False,
            "exact_match": False,
            "context_lines": 3,
            "max_results": 100,
            "exclude_dirs": [],
            "complexity_range": (None, None),
            "lines_range": (None, None),
            "parallel": False,
            "cache": False,
        }
        
        results = self.engine.search(config)
        
        # Should find the fetch_data function
        assert len(results["matches"]) >= 1
        match = results["matches"][0]
        assert match["name"] == "fetch_data"
        assert match["type"] == "function"
        assert match["line"] == 5  # Function definition line
        assert "complexity" in match
    
    def test_class_search(self):
        """Test class definition search."""
        test_file = self.temp_path / "classes.py"
        test_file.write_text("""
class BaseProcessor:
    pass

class DataProcessor(BaseProcessor):
    def process(self):
        pass
        
class FileProcessor:
    def __init__(self):
        super().__init__()
""")
        
        config = {
            "pattern": ".*Processor",
            "path": self.temp_path,
            "files": "*.py",
            "search_type": "class",
            "include_tests": False,
            "include_docs": False,
            "case_sensitive": False,
            "exact_match": False,
            "context_lines": 2,
            "max_results": 100,
            "exclude_dirs": [],
            "complexity_range": (None, None),
            "lines_range": (None, None),
            "parallel": False,
            "cache": False,
        }
        
        results = self.engine.search(config)
        
        # Should find all three Processor classes
        assert len(results["matches"]) == 3
        class_names = [match["name"] for match in results["matches"]]
        assert "BaseProcessor" in class_names
        assert "DataProcessor" in class_names
        assert "FileProcessor" in class_names
    
    def test_import_search(self):
        """Test import statement search."""
        test_file = self.temp_path / "imports.py"
        test_file.write_text("""
import os
import sys
import requests
from pathlib import Path
from typing import Dict, List, Optional
from uvmgr.core import instrumentation
""")
        
        config = {
            "pattern": "requests",
            "path": self.temp_path,
            "files": "*.py",
            "search_type": "import",
            "include_tests": False,
            "include_docs": False,
            "case_sensitive": False,
            "exact_match": True,
            "context_lines": 1,
            "max_results": 100,
            "exclude_dirs": [],
            "complexity_range": (None, None),
            "lines_range": (None, None),
            "parallel": False,
            "cache": False,
        }
        
        results = self.engine.search(config)
        
        # Should find the requests import
        assert len(results["matches"]) == 1
        match = results["matches"][0]
        assert match["name"] == "requests"
        assert match["type"] == "import"
        assert match["line"] == 4
    
    def test_complexity_filtering(self):
        """Test complexity-based filtering."""
        test_file = self.temp_path / "complex.py"
        test_file.write_text("""
def simple_function():
    return True

def complex_function(data):
    for item in data:
        if item.valid:
            try:
                if item.process():
                    while item.has_more():
                        if item.next():
                            continue
                        else:
                            break
                    else:
                        return False
                else:
                    raise ValueError("Processing failed")
            except Exception as e:
                if isinstance(e, ValueError):
                    return None
                else:
                    raise
        else:
            continue
    return True
""")
        
        config = {
            "pattern": ".*function",
            "path": self.temp_path,
            "files": "*.py",
            "search_type": "function",
            "include_tests": False,
            "include_docs": False,
            "case_sensitive": False,
            "exact_match": False,
            "context_lines": 1,
            "max_results": 100,
            "exclude_dirs": [],
            "complexity_range": (5, None),  # Only complex functions
            "lines_range": (None, None),
            "parallel": False,
            "cache": False,
        }
        
        results = self.engine.search(config)
        
        # Should only find the complex function
        assert len(results["matches"]) == 1
        match = results["matches"][0]
        assert match["name"] == "complex_function"
        assert match["complexity"] >= 5
    
    def test_parallel_search(self):
        """Test parallel processing functionality."""
        # Create multiple test files
        for i in range(5):
            test_file = self.temp_path / f"file_{i}.py"
            test_file.write_text(f"""
def function_{i}():
    return {i}

class Class_{i}:
    def method_{i}(self):
        pass
""")
        
        config = {
            "pattern": "function_.*",
            "path": self.temp_path,
            "files": "*.py",
            "search_type": "function",
            "include_tests": False,
            "include_docs": False,
            "case_sensitive": False,
            "exact_match": False,
            "context_lines": 1,
            "max_results": 100,
            "exclude_dirs": [],
            "complexity_range": (None, None),
            "lines_range": (None, None),
            "parallel": True,
            "cache": False,
        }
        
        results = self.engine.search(config)
        
        # Should find all 5 functions
        assert len(results["matches"]) == 5
        function_names = [match["name"] for match in results["matches"]]
        for i in range(5):
            assert f"function_{i}" in function_names
    
    def test_text_fallback(self):
        """Test fallback to text search for non-Python files."""
        test_file = self.temp_path / "config.toml"
        test_file.write_text("""
[project]
name = "test-project"
version = "1.0.0"

[dependencies]
requests = ">=2.0.0"
""")
        
        config = {
            "pattern": "requests",
            "path": self.temp_path,
            "files": "*.toml",
            "search_type": "all",
            "include_tests": False,
            "include_docs": False,
            "case_sensitive": False,
            "exact_match": False,
            "context_lines": 2,
            "max_results": 100,
            "exclude_dirs": [],
            "complexity_range": (None, None),
            "lines_range": (None, None),
            "parallel": False,
            "cache": False,
        }
        
        results = self.engine.search(config)
        
        # Should find text match
        assert len(results["matches"]) == 1
        match = results["matches"][0]
        assert match["type"] == "text"
        assert "requests" in match["content"]


class TestDependencyAnalyzer:
    """Test suite for dependency analysis and search."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.analyzer = DependencyAnalyzer()
    
    @patch('uvmgr.core.shell.run_command')
    def test_installed_packages_search(self, mock_run):
        """Test searching installed packages."""
        # Mock pip list output
        mock_run.return_value = Mock(
            stdout=json.dumps([
                {"name": "requests", "version": "2.28.0"},
                {"name": "urllib3", "version": "1.26.0"},
                {"name": "pytest", "version": "7.0.0"},
            ])
        )
        
        config = {
            "pattern": "requests",
            "path": self.temp_path,
            "search_type": "installed",
            "show_usage": False,
            "show_versions": True,
            "show_vulnerabilities": False,
            "include_dev": True,
            "include_transitive": False,
            "outdated_only": False,
            "unused_only": False,
            "max_results": 50,
        }
        
        results = self.analyzer.search(config)
        
        # Should find requests package
        assert len(results["matches"]) == 1
        match = results["matches"][0]
        assert match["name"] == "requests"
        assert match["version"] == "2.28.0"
        assert match["type"] == "installed"
    
    def test_import_usage_search(self):
        """Test searching import usage in code."""
        # Create test Python files
        (self.temp_path / "main.py").write_text("""
import requests
import json
from pathlib import Path
from typing import Optional, Dict

def fetch_data():
    response = requests.get("http://example.com")
    return response.json()
""")
        
        (self.temp_path / "utils.py").write_text("""
import requests
from requests.exceptions import RequestException

def safe_request(url):
    try:
        return requests.get(url)
    except RequestException:
        return None
""")
        
        config = {
            "pattern": "requests",
            "path": self.temp_path,
            "search_type": "imports",
            "show_usage": True,
            "show_versions": False,
            "show_vulnerabilities": False,
            "include_dev": True,
            "include_transitive": False,
            "outdated_only": False,
            "unused_only": False,
            "max_results": 50,
        }
        
        results = self.analyzer.search(config)
        
        # Should find requests imports in both files
        assert len(results["matches"]) >= 2
        
        requests_matches = [m for m in results["matches"] if m["name"] == "requests"]
        assert len(requests_matches) >= 2
        
        # Check that usage information is included
        for match in requests_matches:
            assert "usage" in match
            assert len(match["usage"]) > 0
    
    def test_requirements_file_search(self):
        """Test searching requirements files."""
        # Create requirements.txt
        (self.temp_path / "requirements.txt").write_text("""
requests>=2.25.0
numpy==1.21.0
pandas>=1.3.0
pytest>=6.0.0  # dev dependency
""")
        
        # Create requirements-dev.txt
        (self.temp_path / "requirements-dev.txt").write_text("""
black==21.12b0
mypy>=0.910
pytest-cov>=3.0.0
""")
        
        config = {
            "pattern": "pytest",
            "path": self.temp_path,
            "search_type": "requirements",
            "show_usage": False,
            "show_versions": True,
            "show_vulnerabilities": False,
            "include_dev": True,
            "include_transitive": False,
            "outdated_only": False,
            "unused_only": False,
            "max_results": 50,
        }
        
        results = self.analyzer.search(config)
        
        # Should find pytest entries
        pytest_matches = [m for m in results["matches"] if "pytest" in m["name"]]
        assert len(pytest_matches) >= 2  # pytest and pytest-cov
    
    def test_pyproject_toml_search(self):
        """Test searching pyproject.toml dependencies."""
        # Create pyproject.toml
        (self.temp_path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-project"
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0",
    "rich>=10.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0.0",
    "black>=21.0.0",
    "mypy>=0.910"
]
test = [
    "pytest-cov>=3.0.0",
    "pytest-mock>=3.6.0"
]
""")
        
        config = {
            "pattern": "pytest",
            "path": self.temp_path,
            "search_type": "pyproject",
            "show_usage": False,
            "show_versions": True,
            "show_vulnerabilities": False,
            "include_dev": True,
            "include_transitive": False,
            "outdated_only": False,
            "unused_only": False,
            "max_results": 50,
        }
        
        results = self.analyzer.search(config)
        
        # Should find pytest dependencies
        pytest_matches = [m for m in results["matches"] if "pytest" in m["name"]]
        assert len(pytest_matches) >= 3  # pytest, pytest-cov, pytest-mock
        
        # Check that section information is included
        for match in pytest_matches:
            assert "section" in match


class TestFileSearchEngine:
    """Test suite for file search engine."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.engine = FileSearchEngine()
    
    def test_basic_file_search(self):
        """Test basic file content search."""
        # Create test files
        (self.temp_path / "file1.txt").write_text("""
This is a test file.
It contains some TODO items.
Please implement the feature soon.
""")
        
        (self.temp_path / "file2.py").write_text("""
def function():
    # TODO: Add error handling
    pass
""")
        
        config = {
            "pattern": "TODO",
            "path": self.temp_path,
            "files": "*",
            "name_pattern": None,
            "file_types": "all",
            "case_sensitive": False,
            "whole_words": False,
            "context_lines": 2,
            "max_results": 100,
            "max_file_size": "10MB",
            "modified_since": None,
            "created_since": None,
            "exclude_dirs": [],
            "include_hidden": False,
            "parallel": False,
        }
        
        results = self.engine.search(config)
        
        # Should find TODO in both files
        assert len(results["matches"]) == 2
        
        # Check that context is included
        for match in results["matches"]:
            assert "context" in match
            assert len(match["context"]) > 0
            assert "TODO" in match["content"]
    
    def test_file_type_filtering(self):
        """Test file type filtering."""
        # Create files of different types
        (self.temp_path / "script.py").write_text("print('test')")
        (self.temp_path / "config.toml").write_text("[project]\nname = 'test'")
        (self.temp_path / "readme.md").write_text("# Test\nThis is a test.")
        (self.temp_path / "data.json").write_text('{"key": "value"}')
        
        config = {
            "pattern": "test",
            "path": self.temp_path,
            "files": "*",
            "name_pattern": None,
            "file_types": "source",  # Only source files
            "case_sensitive": False,
            "whole_words": False,
            "context_lines": 1,
            "max_results": 100,
            "max_file_size": "10MB",
            "modified_since": None,
            "created_since": None,
            "exclude_dirs": [],
            "include_hidden": False,
            "parallel": False,
        }
        
        results = self.engine.search(config)
        
        # Should only find matches in source files (.py)
        assert len(results["matches"]) == 1
        assert results["matches"][0]["file"].endswith(".py")
    
    def test_file_size_filtering(self):
        """Test file size filtering."""
        # Create small and large files
        (self.temp_path / "small.txt").write_text("small content")
        (self.temp_path / "large.txt").write_text("x" * 1000000)  # 1MB file
        
        config = {
            "pattern": "content|x",
            "path": self.temp_path,
            "files": "*.txt",
            "name_pattern": None,
            "file_types": "all",
            "case_sensitive": False,
            "whole_words": False,
            "context_lines": 1,
            "max_results": 100,
            "max_file_size": "500KB",  # Exclude large files
            "modified_since": None,
            "created_since": None,
            "exclude_dirs": [],
            "include_hidden": False,
            "parallel": False,
        }
        
        results = self.engine.search(config)
        
        # Should only find matches in small file
        assert len(results["matches"]) == 1
        assert results["matches"][0]["file"].endswith("small.txt")
    
    def test_parallel_file_search(self):
        """Test parallel file search."""
        # Create multiple files
        for i in range(10):
            (self.temp_path / f"file_{i}.txt").write_text(f"content_{i} with pattern")
        
        config = {
            "pattern": "pattern",
            "path": self.temp_path,
            "files": "*.txt",
            "name_pattern": None,
            "file_types": "all",
            "case_sensitive": False,
            "whole_words": False,
            "context_lines": 1,
            "max_results": 100,
            "max_file_size": "10MB",
            "modified_since": None,
            "created_since": None,
            "exclude_dirs": [],
            "include_hidden": False,
            "parallel": True,
        }
        
        results = self.engine.search(config)
        
        # Should find pattern in all files
        assert len(results["matches"]) == 10


class TestLogSearchEngine:
    """Test suite for log search engine."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.engine = LogSearchEngine()
    
    def test_log_file_parsing(self):
        """Test log file parsing and search."""
        # Create mock log directory
        log_dir = self.temp_path / ".uvmgr" / "logs"
        log_dir.mkdir(parents=True)
        
        # Create test log file
        log_file = log_dir / "uvmgr.log"
        log_file.write_text("""
2023-06-01T10:00:00 INFO uvmgr Starting search operation
2023-06-01T10:00:01 DEBUG uvmgr Parsing configuration
2023-06-01T10:00:02 ERROR uvmgr Search failed: timeout occurred
2023-06-01T10:00:03 WARNING uvmgr Retrying search operation
2023-06-01T10:00:04 INFO uvmgr Search completed successfully
""")
        
        with patch.object(Path, 'home', return_value=self.temp_path):
            config = {
                "pattern": "search",
                "log_sources": ["uvmgr"],
                "level": "all",
                "since": None,
                "until": None,
                "service": None,
                "trace_id": None,
                "span_id": None,
                "max_results": 100,
                "follow": False,
                "case_sensitive": False,
            }
            
            results = self.engine.search(config)
            
            # Should find multiple log entries with "search"
            assert len(results["matches"]) >= 3
            
            # Check that log entries are parsed correctly
            for match in results["matches"]:
                assert "timestamp" in match
                assert "level" in match
                assert "message" in match
                assert "search" in match["message"].lower()
    
    def test_log_level_filtering(self):
        """Test log level filtering."""
        log_dir = self.temp_path / ".uvmgr" / "logs"
        log_dir.mkdir(parents=True)
        
        log_file = log_dir / "test.log"
        log_file.write_text("""
2023-06-01T10:00:00 DEBUG Application starting
2023-06-01T10:00:01 INFO Process initialized
2023-06-01T10:00:02 WARNING Configuration missing
2023-06-01T10:00:03 ERROR Failed to connect
2023-06-01T10:00:04 CRITICAL System failure
""")
        
        with patch.object(Path, 'home', return_value=self.temp_path):
            config = {
                "pattern": ".*",  # Match all
                "log_sources": ["uvmgr"],
                "level": "error",  # Only error and above
                "since": None,
                "until": None,
                "service": None,
                "trace_id": None,
                "span_id": None,
                "max_results": 100,
                "follow": False,
                "case_sensitive": False,
            }
            
            results = self.engine.search(config)
            
            # Should only find ERROR and CRITICAL entries
            assert len(results["matches"]) == 2
            
            levels = [match["level"] for match in results["matches"]]
            assert "error" in levels
            assert "critical" in levels


class TestSemanticSearchEngine:
    """Test suite for semantic search engine."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.engine = SemanticSearchEngine()
    
    @pytest.mark.skipif(not hasattr(SemanticSearchEngine, 'model') or 
                       SemanticSearchEngine(SearchCache()).model is None,
                       reason="Sentence transformers not available")
    def test_semantic_code_search(self):
        """Test semantic search on code."""
        # Create test Python file
        (self.temp_path / "auth.py").write_text("""
def authenticate_user(username, password):
    '''Verify user credentials and return authentication status.'''
    if not username or not password:
        return False
    
    user = find_user_by_username(username)
    if user and verify_password(password, user.password_hash):
        return True
    return False

def login_user(request):
    '''Handle user login process.'''
    username = request.form.get('username')
    password = request.form.get('password')
    
    if authenticate_user(username, password):
        create_user_session(username)
        return redirect_to_dashboard()
    else:
        return show_login_error()
""")
        
        config = {
            "query": "user authentication and login",
            "path": self.temp_path,
            "search_scope": "code",
            "include_external": False,
            "similarity_threshold": 0.3,  # Lower threshold for testing
            "max_results": 20,
            "model": "auto",
            "explain_results": True,
        }
        
        results = self.engine.search(config)
        
        if results.get("error"):
            pytest.skip(f"Semantic search not available: {results['error']}")
        
        # Should find authentication-related functions
        assert len(results["matches"]) >= 1
        
        # Check that similarity scores are included
        for match in results["matches"]:
            assert "similarity" in match
            assert match["similarity"] >= config["similarity_threshold"]
            assert "explanation" in match  # Since explain_results=True
    
    def test_semantic_search_unavailable(self):
        """Test semantic search when dependencies are unavailable."""
        # Force model to be None
        self.engine.model = None
        
        config = {
            "query": "test query",
            "path": self.temp_path,
            "search_scope": "all",
            "include_external": False,
            "similarity_threshold": 0.7,
            "max_results": 20,
            "model": "auto",
            "explain_results": False,
        }
        
        results = self.engine.search(config)
        
        # Should return error message
        assert "error" in results
        assert "sentence-transformers" in results["error"]
        assert len(results["matches"]) == 0


class TestSearchIntegration:
    """Integration tests for search operations."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self._create_test_project()
    
    def _create_test_project(self):
        """Create a realistic test project structure."""
        # Source files
        (self.temp_path / "main.py").write_text("""
import asyncio
import logging
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
logger = logging.getLogger(__name__)

class User(BaseModel):
    username: str
    email: str
    is_active: bool = True

@app.get("/users")
async def get_users() -> List[User]:
    '''Retrieve all active users.'''
    # TODO: Implement pagination
    users = await fetch_users_from_db()
    return [user for user in users if user.is_active]

@app.post("/users")
async def create_user(user: User) -> User:
    '''Create a new user account.'''
    try:
        return await save_user_to_db(user)
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="User creation failed")
""")
        
        (self.temp_path / "database.py").write_text("""
import asyncpg
from typing import List, Optional

class DatabaseManager:
    '''Manage database connections and operations.'''
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def connect(self):
        '''Establish database connection pool.'''
        self.pool = await asyncpg.create_pool(self.connection_string)
    
    async def fetch_users(self) -> List[dict]:
        '''Fetch all users from database.'''
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM users")
""")
        
        # Configuration files
        (self.temp_path / "pyproject.toml").write_text("""
[project]
name = "test-api"
version = "1.0.0"
dependencies = [
    "fastapi>=0.68.0",
    "uvicorn>=0.15.0", 
    "asyncpg>=0.24.0",
    "pydantic>=1.8.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0.0",
    "pytest-asyncio>=0.15.0",
    "black>=21.0.0",
    "mypy>=0.910"
]
""")
        
        # Documentation
        (self.temp_path / "README.md").write_text("""
# Test API

A FastAPI application for user management.

## Features

- User registration and authentication
- Database integration with PostgreSQL
- Async/await support for better performance
- Comprehensive error handling

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Start the development server:

```bash
uvicorn main:app --reload
```
""")
        
        # Test files
        test_dir = self.temp_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_users.py").write_text("""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_users():
    response = client.get("/users")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_user():
    user_data = {
        "username": "testuser",
        "email": "test@example.com"
    }
    response = client.post("/users", json=user_data)
    assert response.status_code == 200
""")
    
    def test_multi_search_integration(self):
        """Test multi-faceted search across the project."""
        config = {
            "pattern": "user",
            "path": self.temp_path,
            "include_code": True,
            "include_deps": True,
            "include_files": True,
            "include_logs": False,
            "include_docs": True,
            "max_results_per_type": 25,
            "parallel": True,
        }
        
        with patch('uvmgr.core.shell.run_command') as mock_run:
            # Mock pip list for dependency search
            mock_run.return_value = Mock(
                stdout=json.dumps([
                    {"name": "fastapi", "version": "0.68.0"},
                    {"name": "pydantic", "version": "1.8.0"},
                ])
            )
            
            results = search_all(config)
            
            # Should have results from multiple search types
            assert "code" in results
            assert "deps" in results  
            assert "files" in results
            
            # Code search should find User class and user-related functions
            code_matches = results["code"]["matches"]
            assert len(code_matches) > 0
            
            # File search should find "user" in documentation
            file_matches = results["files"]["matches"]
            assert len(file_matches) > 0
    
    def test_search_performance(self):
        """Test search performance with larger project."""
        # Create many files to test performance
        for i in range(50):
            file_path = self.temp_path / f"module_{i}.py"
            file_path.write_text(f"""
def function_{i}():
    '''Function number {i} for testing.'''
    return {i}

class Class_{i}:
    '''Class number {i} for testing.'''
    
    def method_{i}(self):
        return "method_{i}"
""")
        
        config = {
            "pattern": "function_.*",
            "path": self.temp_path,
            "files": "*.py",
            "search_type": "function",
            "include_tests": True,
            "include_docs": False,
            "case_sensitive": False,
            "exact_match": False,
            "context_lines": 1,
            "max_results": 100,
            "exclude_dirs": [],
            "complexity_range": (None, None),
            "lines_range": (None, None),
            "parallel": True,
            "cache": False,
        }
        
        import time
        start_time = time.time()
        results = search_code(config)
        execution_time = time.time() - start_time
        
        # Should find all 50 functions quickly
        assert len(results["matches"]) == 50
        assert execution_time < 5.0  # Should complete within 5 seconds
        
        # Verify parallel processing was effective
        assert results["execution_time"] < execution_time