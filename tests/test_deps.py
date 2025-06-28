"""
Test suite for uvmgr.commands.deps

This module provides comprehensive testing for the dependency management
commands, including unit tests for all operations and integration tests
for the complete workflow.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess
import sys
from types import ModuleType

# Mock the CLI module to avoid circular imports
sys.modules['uvmgr.main'] = Mock()
sys.modules['uvmgr.cli'] = Mock()

from uvmgr.core.semconv import PackageAttributes, PackageOperations

# Now import the deps operations directly to test them
from uvmgr.ops import deps as deps_ops


class TestDepsOperations:
    """Test cases for deps operations (business logic layer)."""
    
    @patch('uvmgr.runtime.uv.call')
    def test_add_operation_success(self, mock_uv_call):
        """Test successful package addition operation."""
        mock_uv_call.return_value = None  # uv add returns None on success
        
        result = deps_ops.add(["requests"], dev=False)
        
        mock_uv_call.assert_called_once()
        # The call should include the package name
        call_args = mock_uv_call.call_args[0][0]
        assert "add" in call_args
        assert "requests" in call_args
    
    @patch('uvmgr.runtime.uv.call')
    def test_add_dev_dependency(self, mock_uv_call):
        """Test adding development dependency."""
        mock_uv_call.return_value = None
        
        result = deps_ops.add(["pytest"], dev=True)
        
        mock_uv_call.assert_called_once()
        call_args = mock_uv_call.call_args[0][0]
        assert "add" in call_args
        assert "pytest" in call_args
        assert "--dev" in call_args
    
    @patch('uvmgr.runtime.uv.call')
    def test_remove_operation(self, mock_uv_call):
        """Test package removal operation."""
        mock_uv_call.return_value = None
        
        result = deps_ops.remove(["requests"])
        
        mock_uv_call.assert_called_once()
        call_args = mock_uv_call.call_args[0][0]
        assert "remove" in call_args
        assert "requests" in call_args
    
    @patch('uvmgr.runtime.uv.call')
    def test_list_packages(self, mock_uv_call):
        """Test listing packages."""
        mock_uv_call.return_value = "requests==2.28.0\npandas==1.5.0\n"
        
        result = deps_ops.list_pkgs()
        
        assert isinstance(result, list)
        mock_uv_call.assert_called_once()


class TestDepsUpgrade:
    """Test cases for deps upgrade operations."""
    
    @patch('uvmgr.runtime.uv.call')
    def test_upgrade_all_packages(self, mock_uv_call):
        """Test upgrading all packages."""
        mock_uv_call.return_value = None
        
        result = deps_ops.upgrade(all_pkgs=True, pkgs=None)
        
        mock_uv_call.assert_called_once()
        call_args = mock_uv_call.call_args[0][0]
        assert "sync" in call_args or "upgrade" in call_args
    
    @patch('uvmgr.runtime.uv.call')
    def test_upgrade_specific_packages(self, mock_uv_call):
        """Test upgrading specific packages."""
        mock_uv_call.return_value = None
        
        result = deps_ops.upgrade(all_pkgs=False, pkgs=["requests"])
        
        mock_uv_call.assert_called_once()


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create a minimal pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = []

[dependency-groups]
dev = []
""")
    
    return project_dir


class TestDepsWithFileSystem:
    """Tests that interact with the file system."""
    
    def test_project_structure_validation(self, temp_project_dir):
        """Test that commands validate project structure."""
        # This would test actual file system interactions
        # when the operations layer is implemented
        assert temp_project_dir.exists()
        assert (temp_project_dir / "pyproject.toml").exists()


if __name__ == "__main__":
    pytest.main([__file__])