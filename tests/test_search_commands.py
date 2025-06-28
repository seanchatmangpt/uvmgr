"""
Tests for uvmgr search commands
==============================

Comprehensive test suite for advanced search functionality including
code search, dependency search, file search, log search, and semantic search.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest
from typer.testing import CliRunner

from uvmgr.commands.search import search_app


class TestSearchCommands:
    """Test suite for search commands."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def test_code_search_basic(self):
        """Test basic code search functionality."""
        # Create a test Python file
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
def hello_world():
    '''A simple greeting function.'''
    return "Hello, World!"

class TestClass:
    def method(self):
        pass
""")
        
        with patch('uvmgr.ops.search.search_code') as mock_search:
            mock_search.return_value = {
                "matches": [
                    {
                        "file": str(test_file),
                        "line": 2,
                        "type": "function",
                        "name": "hello_world",
                        "content": "def hello_world():",
                        "context": ["", "def hello_world():", "    '''A simple greeting function.'''"]
                    }
                ],
                "files_scanned": 1,
                "execution_time": 0.1
            }
            
            result = self.runner.invoke(search_app, [
                "code", "hello_world", "--path", str(self.temp_path)
            ])
            
            assert result.exit_code == 0
            assert "hello_world" in result.stdout
            mock_search.assert_called_once()
    
    def test_code_search_with_filters(self):
        """Test code search with complexity and type filters."""
        with patch('uvmgr.ops.search.search_code') as mock_search:
            mock_search.return_value = {
                "matches": [],
                "files_scanned": 0,
                "execution_time": 0.05
            }
            
            result = self.runner.invoke(search_app, [
                "code", "async.*def", 
                "--type", "function",
                "--complexity-min", "3",
                "--complexity-max", "10",
                "--include-docs",
                "--parallel"
            ])
            
            assert result.exit_code == 0
            mock_search.assert_called_once()
            
            # Check that configuration was passed correctly
            call_args = mock_search.call_args[0][0]
            assert call_args["search_type"] == "function"
            assert call_args["complexity_range"] == (3, 10)
            assert call_args["include_docs"] is True
            assert call_args["parallel"] is True
    
    def test_deps_search_basic(self):
        """Test basic dependency search."""
        with patch('uvmgr.ops.search.search_dependencies') as mock_search:
            mock_search.return_value = {
                "matches": [
                    {
                        "name": "requests",
                        "version": "2.28.0",
                        "type": "installed",
                        "usage": [{"file": "/app/main.py", "line": 1}]
                    }
                ],
                "search_config": {}
            }
            
            result = self.runner.invoke(search_app, [
                "deps", "requests",
                "--show-usage",
                "--show-versions",
                "--include-dev"
            ])
            
            assert result.exit_code == 0
            assert "requests" in result.stdout
            mock_search.assert_called_once()
    
    def test_deps_search_vulnerabilities(self):
        """Test dependency search with vulnerability checking."""
        with patch('uvmgr.ops.search.search_dependencies') as mock_search:
            mock_search.return_value = {
                "matches": [
                    {
                        "name": "vulnerable-package",
                        "version": "1.0.0",
                        "type": "installed",
                        "vulnerabilities": [
                            {
                                "id": "CVE-2023-12345",
                                "description": "Remote code execution vulnerability",
                                "severity": "high"
                            }
                        ]
                    }
                ],
                "search_config": {}
            }
            
            result = self.runner.invoke(search_app, [
                "deps", "*",
                "--show-vulnerabilities",
                "--format", "json"
            ])
            
            assert result.exit_code == 0
            mock_search.assert_called_once()
    
    def test_files_search_basic(self):
        """Test basic file search functionality."""
        with patch('uvmgr.ops.search.search_files') as mock_search:
            mock_search.return_value = {
                "matches": [
                    {
                        "file": "/app/config.py",
                        "line": 15,
                        "content": "TODO: Implement caching",
                        "context": ["# Configuration", "TODO: Implement caching", "pass"]
                    }
                ],
                "files_scanned": 10,
                "execution_time": 0.2
            }
            
            result = self.runner.invoke(search_app, [
                "files", "TODO",
                "--modified-since", "1 week ago",
                "--exclude", "__pycache__,node_modules"
            ])
            
            assert result.exit_code == 0
            assert "TODO" in result.stdout
            mock_search.assert_called_once()
    
    def test_files_search_with_filters(self):
        """Test file search with advanced filters."""
        with patch('uvmgr.ops.search.search_files') as mock_search:
            mock_search.return_value = {
                "matches": [],
                "files_scanned": 5,
                "execution_time": 0.1
            }
            
            result = self.runner.invoke(search_app, [
                "files", "api_key",
                "--types", "config",
                "--name", "*.env*",
                "--max-size", "1MB",
                "--include-hidden",
                "--case-sensitive"
            ])
            
            assert result.exit_code == 0
            mock_search.assert_called_once()
            
            call_args = mock_search.call_args[0][0]
            assert call_args["file_types"] == "config"
            assert call_args["name_pattern"] == "*.env*"
            assert call_args["case_sensitive"] is True
            assert call_args["include_hidden"] is True
    
    def test_logs_search_basic(self):
        """Test basic log search functionality."""
        with patch('uvmgr.ops.search.search_logs') as mock_search:
            mock_search.return_value = {
                "matches": [
                    {
                        "timestamp": "2023-06-01T12:00:00",
                        "level": "error",
                        "service": "uvmgr-search",
                        "message": "Search operation failed: timeout",
                        "trace_id": "abc123"
                    }
                ],
                "files_scanned": 3
            }
            
            result = self.runner.invoke(search_app, [
                "logs", "error",
                "--level", "error",
                "--since", "24h",
                "--format", "json"
            ])
            
            assert result.exit_code == 0
            mock_search.assert_called_once()
    
    def test_logs_search_follow(self):
        """Test real-time log following."""
        with patch('uvmgr.ops.search.follow_logs') as mock_follow:
            result = self.runner.invoke(search_app, [
                "logs", "info",
                "--follow",
                "--service", "uvmgr"
            ])
            
            # Note: This might exit quickly in test environment
            mock_follow.assert_called_once()
    
    def test_semantic_search_basic(self):
        """Test basic semantic search functionality."""
        with patch('uvmgr.ops.search.search_semantic') as mock_search:
            mock_search.return_value = {
                "matches": [
                    {
                        "file": "/app/auth.py",
                        "type": "function",
                        "similarity": 0.85,
                        "preview": "def authenticate_user(username, password)...",
                        "explanation": "High semantic similarity - closely matches authentication concepts"
                    }
                ],
                "avg_similarity": 0.85,
                "total_chunks_processed": 50
            }
            
            result = self.runner.invoke(search_app, [
                "semantic", "user authentication and login",
                "--threshold", "0.7",
                "--explain"
            ])
            
            assert result.exit_code == 0
            assert "authenticate_user" in result.stdout
            mock_search.assert_called_once()
    
    def test_semantic_search_with_scope(self):
        """Test semantic search with specific scope."""
        with patch('uvmgr.ops.search.search_semantic') as mock_search:
            mock_search.return_value = {
                "matches": [],
                "avg_similarity": 0.0,
                "total_chunks_processed": 0
            }
            
            result = self.runner.invoke(search_app, [
                "semantic", "database optimization patterns",
                "--scope", "code",
                "--model", "custom-model",
                "--format", "markdown"
            ])
            
            assert result.exit_code == 0
            mock_search.assert_called_once()
            
            call_args = mock_search.call_args[0][0]
            assert call_args["search_scope"] == "code"
            assert call_args["model"] == "custom-model"
    
    def test_search_all_basic(self):
        """Test multi-faceted search functionality."""
        with patch('uvmgr.ops.search.search_all') as mock_search:
            mock_search.return_value = {
                "code": {
                    "matches": [
                        {"file": "/app/main.py", "line": 10, "type": "function"}
                    ]
                },
                "deps": {
                    "matches": [
                        {"name": "requests", "version": "2.28.0"}
                    ]
                },
                "files": {
                    "matches": [
                        {"file": "/app/config.txt", "line": 5}
                    ]
                },
                "logs": {
                    "matches": []
                }
            }
            
            result = self.runner.invoke(search_app, [
                "all", "database",
                "--include-logs",
                "--max-per-type", "10"
            ])
            
            assert result.exit_code == 0
            assert "CODE SEARCH" in result.stdout
            assert "requests" in result.stdout
            mock_search.assert_called_once()
    
    def test_search_all_selective(self):
        """Test multi-faceted search with selective inclusion."""
        with patch('uvmgr.ops.search.search_all') as mock_search:
            mock_search.return_value = {
                "code": {"matches": []},
                "files": {"matches": []}
            }
            
            result = self.runner.invoke(search_app, [
                "all", "test_pattern",
                "--no-deps",
                "--no-code",
                "--format", "json"
            ])
            
            assert result.exit_code == 0
            mock_search.assert_called_once()
            
            call_args = mock_search.call_args[0][0]
            assert call_args["include_deps"] is False
            assert call_args["include_code"] is False
            assert call_args["include_files"] is True  # Default
    
    def test_output_formats(self):
        """Test different output formats."""
        with patch('uvmgr.ops.search.search_code') as mock_search:
            mock_search.return_value = {
                "matches": [
                    {
                        "file": "/app/test.py",
                        "line": 1,
                        "type": "function",
                        "name": "test_func",
                        "content": "def test_func():"
                    }
                ],
                "files_scanned": 1,
                "execution_time": 0.1
            }
            
            # Test JSON format
            result = self.runner.invoke(search_app, [
                "code", "test_func", "--format", "json"
            ])
            assert result.exit_code == 0
            
            # Test CSV format
            result = self.runner.invoke(search_app, [
                "code", "test_func", "--format", "csv"
            ])
            assert result.exit_code == 0
            
            # Test LSP format
            result = self.runner.invoke(search_app, [
                "code", "test_func", "--format", "lsp"
            ])
            assert result.exit_code == 0
    
    def test_error_handling(self):
        """Test error handling in search commands."""
        with patch('uvmgr.ops.search.search_code') as mock_search:
            mock_search.side_effect = Exception("Search failed")
            
            result = self.runner.invoke(search_app, [
                "code", "pattern"
            ])
            
            assert result.exit_code == 1
            assert "Search failed" in result.stdout
    
    def test_time_delta_parsing(self):
        """Test time delta parsing functionality."""
        from uvmgr.commands.search import _parse_time_delta
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Test "ago" format
        result = _parse_time_delta("1 week ago")
        assert isinstance(result, datetime)
        assert result < now
        
        # Test hour format
        result = _parse_time_delta("24h")
        assert isinstance(result, datetime)
        assert result < now
        
        # Test day format
        result = _parse_time_delta("7d")
        assert isinstance(result, datetime)
        assert result < now
    
    def test_instrumentation_integration(self):
        """Test OpenTelemetry instrumentation integration."""
        with patch('uvmgr.ops.search.search_code') as mock_search:
            with patch('uvmgr.core.instrumentation.add_span_attributes') as mock_attrs:
                with patch('uvmgr.core.instrumentation.add_span_event') as mock_event:
                    mock_search.return_value = {
                        "matches": [],
                        "files_scanned": 0,
                        "execution_time": 0.1
                    }
                    
                    result = self.runner.invoke(search_app, [
                        "code", "test_pattern"
                    ])
                    
                    assert result.exit_code == 0
                    
                    # Verify instrumentation was called
                    mock_attrs.assert_called()
                    mock_event.assert_called()
    
    def test_cache_integration(self):
        """Test search cache integration."""
        # This would test the caching functionality
        # For now, we'll test that cache parameters are passed correctly
        with patch('uvmgr.ops.search.search_code') as mock_search:
            mock_search.return_value = {
                "matches": [],
                "files_scanned": 0,
                "execution_time": 0.1
            }
            
            result = self.runner.invoke(search_app, [
                "code", "pattern", "--no-cache"
            ])
            
            assert result.exit_code == 0
            
            call_args = mock_search.call_args[0][0]
            assert call_args["cache"] is False


class TestSearchIntegration:
    """Integration tests for search functionality."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create sample files for testing
        self._create_sample_project()
    
    def _create_sample_project(self):
        """Create a sample project structure for testing."""
        # Python files
        (self.temp_path / "main.py").write_text("""
import requests
from typing import Optional

def fetch_data(url: str) -> Optional[dict]:
    '''Fetch data from a URL.'''
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

class DataProcessor:
    def __init__(self):
        self.cache = {}
    
    def process(self, data):
        # TODO: Implement data processing
        pass
""")
        
        (self.temp_path / "utils.py").write_text("""
def helper_function():
    return "helper"

async def async_helper():
    await some_operation()
    return True
""")
        
        # Configuration files
        (self.temp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
dependencies = [
    "requests>=2.0.0",
    "typing-extensions"
]

[project.optional-dependencies]
dev = ["pytest", "black", "mypy"]
""")
        
        (self.temp_path / "requirements.txt").write_text("""
requests==2.28.0
numpy>=1.20.0
pandas
""")
        
        # Documentation
        (self.temp_path / "README.md").write_text("""
# Test Project

This is a test project for search functionality.

## Features

- Data fetching
- Processing pipeline
- Error handling
""")
        
        # Test files
        test_dir = self.temp_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_main.py").write_text("""
import pytest
from main import fetch_data

def test_fetch_data():
    result = fetch_data("http://example.com")
    assert result is not None
""")
    
    @pytest.mark.integration
    def test_real_code_search(self):
        """Test code search on real files."""
        with patch('uvmgr.ops.search.SearchCache'):
            from uvmgr.ops.search import search_code
            
            config = {
                "pattern": "fetch_data",
                "path": self.temp_path,
                "files": "*.py",
                "search_type": "function",
                "include_tests": True,
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
            
            results = search_code(config)
            
            # Should find the function definition and usage
            assert len(results["matches"]) >= 1
            assert any("fetch_data" in match["name"] for match in results["matches"])
    
    @pytest.mark.integration
    def test_real_file_search(self):
        """Test file search on real files."""
        with patch('uvmgr.ops.search.SearchCache'):
            from uvmgr.ops.search import search_files
            
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
            
            results = search_files(config)
            
            # Should find the TODO comment
            assert len(results["matches"]) >= 1
            assert any("TODO" in match["content"] for match in results["matches"])


class TestSearchHelperFunctions:
    """Test helper functions and utilities."""
    
    def test_display_functions(self):
        """Test result display functions."""
        from uvmgr.commands.search import (
            _display_code_search_results,
            _display_deps_search_results,
            _display_file_search_results,
            _display_log_search_results
        )
        
        # Test with empty results
        empty_results = {"matches": []}
        
        # These should not raise exceptions
        _display_code_search_results(empty_results, 3)
        _display_deps_search_results(empty_results)
        _display_file_search_results(empty_results, 3)
        _display_log_search_results(empty_results)
    
    def test_csv_output(self):
        """Test CSV output formatting."""
        from uvmgr.commands.search import _display_csv_results
        
        results = {
            "matches": [
                {
                    "file": "/test.py",
                    "line": 1,
                    "type": "function",
                    "content": "def test():",
                    "complexity": 1
                }
            ]
        }
        
        # Should not raise exceptions
        _display_csv_results(results, "code")
    
    def test_lsp_output(self):
        """Test LSP format output."""
        from uvmgr.commands.search import _display_lsp_results
        
        results = {
            "matches": [
                {
                    "file": "/test.py",
                    "line": 1,
                    "type": "function"
                }
            ]
        }
        
        # Should not raise exceptions
        _display_lsp_results(results)
    
    def test_markdown_output(self):
        """Test markdown format output."""
        from uvmgr.commands.search import (
            _display_semantic_results_markdown,
            _display_all_results_markdown
        )
        
        semantic_results = {
            "matches": [
                {
                    "file": "/test.py",
                    "similarity": 0.85,
                    "type": "function",
                    "preview": "Test function",
                    "explanation": "High similarity"
                }
            ]
        }
        
        all_results = {
            "code": {"matches": [{"file": "/test.py", "line": 1, "type": "function"}]},
            "deps": {"matches": [{"name": "requests", "version": "2.28.0"}]}
        }
        
        # Should not raise exceptions
        _display_semantic_results_markdown(semantic_results)
        _display_all_results_markdown(all_results)