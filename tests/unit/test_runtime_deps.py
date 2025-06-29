"""
Unit tests for uvmgr.runtime.deps module.

Tests dependency management runtime functionality including
package addition, removal, upgrading, and listing operations.
"""

import pytest
import json
import subprocess
import tempfile
from unittest.mock import Mock, patch, mock_open, call
from pathlib import Path

from uvmgr.runtime.deps import (
    add_packages, remove_packages, upgrade_packages, list_packages,
    lock_dependencies, sync_dependencies, _list_from_pyproject
)


class TestAddPackages:
    """Test package addition functionality."""
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_add_basic_packages(self, mock_span, mock_run_logged):
        """Test adding basic packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = add_packages(["fastapi", "uvicorn"])
        
        mock_run_logged.assert_called_once_with(["uv", "add", "fastapi", "uvicorn"])
        assert result["success"] is True
        assert result["packages"] == ["fastapi", "uvicorn"]
        assert result["dev"] is False
        assert "Successfully added" in result["message"]
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_add_dev_packages(self, mock_span, mock_run_logged):
        """Test adding development packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = add_packages(["pytest", "ruff"], dev=True)
        
        mock_run_logged.assert_called_once_with(["uv", "add", "--dev", "pytest", "ruff"])
        assert result["success"] is True
        assert result["dev"] is True
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_add_packages_with_extras(self, mock_span, mock_run_logged):
        """Test adding packages with extras."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = add_packages(["fastapi"], extras=["dev", "test"])
        
        expected_cmd = ["uv", "add", "fastapi", "--extra", "dev", "--extra", "test"]
        mock_run_logged.assert_called_once_with(expected_cmd)
        assert result["success"] is True
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_add_packages_failure(self, mock_span, mock_run_logged):
        """Test package addition failure."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        error = subprocess.CalledProcessError(1, "uv", "Package not found")
        error.output = "Error: Package 'nonexistent' not found"
        mock_run_logged.side_effect = error
        
        result = add_packages(["nonexistent"])
        
        assert result["success"] is False
        assert "nonexistent" in result["packages"]
        assert result["error"] == str(error)
        assert result["output"] == "Error: Package 'nonexistent' not found"
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_add_dev_packages_with_extras(self, mock_span, mock_run_logged):
        """Test adding dev packages with extras."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = add_packages(["django"], dev=True, extras=["async"])
        
        expected_cmd = ["uv", "add", "--dev", "django", "--extra", "async"]
        mock_run_logged.assert_called_once_with(expected_cmd)


class TestRemovePackages:
    """Test package removal functionality."""
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_remove_packages(self, mock_span, mock_run_logged):
        """Test removing packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = remove_packages(["old-package", "unused-lib"])
        
        mock_run_logged.assert_called_once_with(["uv", "remove", "old-package", "unused-lib"])
        assert result["success"] is True
        assert result["packages"] == ["old-package", "unused-lib"]
        assert "Successfully removed" in result["message"]
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_remove_packages_failure(self, mock_span, mock_run_logged):
        """Test package removal failure."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        error = subprocess.CalledProcessError(1, "uv", "Package not installed")
        error.output = "Error: Package 'not-installed' is not installed"
        mock_run_logged.side_effect = error
        
        result = remove_packages(["not-installed"])
        
        assert result["success"] is False
        assert result["packages"] == ["not-installed"]
        assert result["error"] == str(error)


class TestUpgradePackages:
    """Test package upgrade functionality."""
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_upgrade_all_packages(self, mock_span, mock_run_logged):
        """Test upgrading all packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = upgrade_packages(all_packages=True)
        
        mock_run_logged.assert_called_once_with(["uv", "sync", "--upgrade"])
        assert result["success"] is True
        assert result["all_packages"] is True
        assert "Successfully upgraded" in result["message"]
    
    @patch('uvmgr.runtime.deps.remove_packages')
    @patch('uvmgr.runtime.deps.add_packages')
    @patch('uvmgr.runtime.deps.span')
    def test_upgrade_specific_packages(self, mock_span, mock_add, mock_remove):
        """Test upgrading specific packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock successful remove and add operations
        mock_remove.return_value = {"success": True}
        mock_add.return_value = {"success": True}
        
        result = upgrade_packages(packages=["fastapi", "uvicorn"])
        
        # Should remove and re-add each package
        mock_remove.assert_any_call(["fastapi"])
        mock_remove.assert_any_call(["uvicorn"])
        mock_add.assert_any_call(["fastapi"])
        mock_add.assert_any_call(["uvicorn"])
        
        assert result["success"] is True
        assert result["packages"] == ["fastapi", "uvicorn"]
        assert len(result["results"]) == 2
    
    @patch('uvmgr.runtime.deps.remove_packages')
    @patch('uvmgr.runtime.deps.add_packages')
    @patch('uvmgr.runtime.deps.span')
    def test_upgrade_specific_packages_failure(self, mock_span, mock_add, mock_remove):
        """Test upgrading specific packages with failure."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock failed remove operation
        mock_remove.return_value = {"success": False}
        
        result = upgrade_packages(packages=["nonexistent"])
        
        assert result["success"] is False
        assert "Some upgrades failed" in result["message"]
        assert result["results"][0]["success"] is False
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_upgrade_no_args(self, mock_span, mock_run_logged):
        """Test upgrade with no arguments (just sync)."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = upgrade_packages()
        
        mock_run_logged.assert_called_once_with(["uv", "sync"])
        assert result["success"] is True


class TestListPackages:
    """Test package listing functionality."""
    
    @patch('subprocess.run')
    @patch('uvmgr.runtime.deps.span')
    def test_list_packages_json_format(self, mock_span, mock_subprocess):
        """Test listing packages using JSON format."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.stdout = json.dumps([
            {"name": "fastapi", "version": "0.104.1"},
            {"name": "uvicorn", "version": "0.24.0"}
        ])
        mock_subprocess.return_value = mock_result
        
        result = list_packages()
        
        mock_subprocess.assert_called_once_with(
            ["uv", "pip", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        expected = ["fastapi==0.104.1", "uvicorn==0.24.0"]
        assert result == expected
    
    @patch('uvmgr.runtime.deps._list_from_pyproject')
    @patch('subprocess.run')
    @patch('uvmgr.runtime.deps.span')
    def test_list_packages_fallback_to_pyproject(self, mock_span, mock_subprocess, mock_fallback):
        """Test fallback to pyproject.toml when pip list fails."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock subprocess failure
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "uv")
        mock_fallback.return_value = ["requests>=2.28.0", "click>=8.0.0"]
        
        result = list_packages()
        
        assert result == ["requests>=2.28.0", "click>=8.0.0"]
        mock_fallback.assert_called_once()
    
    @patch('uvmgr.runtime.deps._list_from_pyproject')
    @patch('subprocess.run')
    @patch('uvmgr.runtime.deps.span')
    def test_list_packages_json_decode_error(self, mock_span, mock_subprocess, mock_fallback):
        """Test fallback when JSON decoding fails."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock invalid JSON response
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_subprocess.return_value = mock_result
        mock_fallback.return_value = ["fallback-package"]
        
        result = list_packages()
        
        assert result == ["fallback-package"]
        mock_fallback.assert_called_once()


class TestListFromPyproject:
    """Test pyproject.toml dependency extraction."""
    
    @patch("builtins.open", new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_list_from_pyproject_basic(self, mock_exists, mock_file):
        """Test basic dependency extraction from pyproject.toml."""
        mock_exists.return_value = True
        
        # Mock pyproject.toml content
        toml_content = b"""
[project]
name = "test-project"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.24.0"
]
"""
        
        with patch('tomllib.load') as mock_tomllib:
            mock_tomllib.return_value = {
                "project": {
                    "dependencies": [
                        "fastapi>=0.100.0",
                        "uvicorn[standard]>=0.24.0"
                    ]
                }
            }
            
            result = _list_from_pyproject()
            
            expected = ["fastapi>=0.100.0", "uvicorn[standard]>=0.24.0"]
            assert result == expected
    
    @patch("builtins.open", new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_list_from_pyproject_with_dev_groups(self, mock_exists, mock_file):
        """Test dependency extraction including dev groups."""
        mock_exists.return_value = True
        
        with patch('tomllib.load') as mock_tomllib:
            mock_tomllib.return_value = {
                "project": {
                    "dependencies": ["fastapi>=0.100.0"]
                },
                "dependency-groups": {
                    "dev": ["pytest>=7.0.0", "ruff>=0.1.0"],
                    "test": ["coverage>=7.0.0"]
                }
            }
            
            result = _list_from_pyproject()
            
            assert "fastapi>=0.100.0" in result
            assert "pytest>=7.0.0 (group: dev)" in result
            assert "ruff>=0.1.0 (group: dev)" in result
            assert "coverage>=7.0.0 (group: test)" in result
    
    @patch('pathlib.Path.exists')
    def test_list_from_pyproject_no_file(self, mock_exists):
        """Test behavior when pyproject.toml doesn't exist."""
        mock_exists.return_value = False
        
        result = _list_from_pyproject()
        
        assert result == []
    
    @patch("builtins.open", new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_list_from_pyproject_malformed(self, mock_exists, mock_file):
        """Test behavior with malformed pyproject.toml."""
        mock_exists.return_value = True
        
        with patch('tomllib.load') as mock_tomllib:
            mock_tomllib.side_effect = Exception("Invalid TOML")
            
            result = _list_from_pyproject()
            
            assert result == []


class TestLockDependencies:
    """Test dependency locking functionality."""
    
    @patch('subprocess.run')
    @patch('uvmgr.runtime.deps.span')
    def test_lock_dependencies_basic(self, mock_span, mock_subprocess):
        """Test basic dependency locking."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_result = Mock()
        mock_result.stdout = "Dependencies locked successfully"
        mock_subprocess.return_value = mock_result
        
        result = lock_dependencies()
        
        mock_subprocess.assert_called_once_with(
            ["uv", "lock"],
            capture_output=True,
            text=True,
            check=True
        )
        
        assert result["success"] is True
        assert "Dependencies locked successfully" in result["message"]
        assert result["output"] is None  # Not verbose
    
    @patch('subprocess.run')
    @patch('uvmgr.runtime.deps.span')
    def test_lock_dependencies_verbose(self, mock_span, mock_subprocess):
        """Test dependency locking with verbose output."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_result = Mock()
        mock_result.stdout = "Detailed lock output..."
        mock_subprocess.return_value = mock_result
        
        result = lock_dependencies(verbose=True)
        
        mock_subprocess.assert_called_once_with(
            ["uv", "lock", "--verbose"],
            capture_output=True,
            text=True,
            check=True
        )
        
        assert result["success"] is True
        assert result["output"] == "Detailed lock output..."
    
    @patch('subprocess.run')
    @patch('uvmgr.runtime.deps.span')
    def test_lock_dependencies_failure(self, mock_span, mock_subprocess):
        """Test dependency locking failure."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        error = subprocess.CalledProcessError(1, "uv", "Lock failed")
        error.stderr = "Dependency conflict detected"
        mock_subprocess.side_effect = error
        
        result = lock_dependencies()
        
        assert result["success"] is False
        assert result["error"] == str(error)
        assert result["output"] == "Dependency conflict detected"


class TestSyncDependencies:
    """Test dependency synchronization functionality."""
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_sync_dependencies_basic(self, mock_span, mock_run_logged):
        """Test basic dependency synchronization."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = sync_dependencies()
        
        mock_run_logged.assert_called_once_with(["uv", "sync"])
        assert result["success"] is True
        assert "Dependencies synced successfully" in result["message"]
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_sync_dependencies_frozen(self, mock_span, mock_run_logged):
        """Test dependency synchronization with frozen versions."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        result = sync_dependencies(frozen=True)
        
        mock_run_logged.assert_called_once_with(["uv", "sync", "--frozen"])
        assert result["success"] is True
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('uvmgr.runtime.deps.span')
    def test_sync_dependencies_failure(self, mock_span, mock_run_logged):
        """Test dependency synchronization failure."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        error = subprocess.CalledProcessError(1, "uv", "Sync failed")
        error.output = "Missing lock file"
        mock_run_logged.side_effect = error
        
        result = sync_dependencies()
        
        assert result["success"] is False
        assert result["error"] == str(error)
        assert result["output"] == "Missing lock file"


class TestIntegration:
    """Integration tests for dependency management."""
    
    @patch('uvmgr.runtime.deps.run_logged')
    @patch('subprocess.run')
    def test_complete_dependency_workflow(self, mock_subprocess, mock_run_logged):
        """Test a complete dependency management workflow."""
        with patch('uvmgr.runtime.deps.span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()
            
            # 1. Add packages
            result1 = add_packages(["fastapi", "uvicorn"])
            assert result1["success"] is True
            
            # 2. List packages
            mock_subprocess.return_value.stdout = json.dumps([
                {"name": "fastapi", "version": "0.104.1"},
                {"name": "uvicorn", "version": "0.24.0"}
            ])
            result2 = list_packages()
            assert "fastapi==0.104.1" in result2
            
            # 3. Lock dependencies
            mock_subprocess.return_value = Mock(stdout="Lock successful")
            result3 = lock_dependencies()
            assert result3["success"] is True
            
            # 4. Sync dependencies
            result4 = sync_dependencies()
            assert result4["success"] is True
            
            # Verify all operations were called
            assert mock_run_logged.call_count >= 2  # add, sync calls