"""
Unit tests for uvmgr.runtime.uv module.

Tests the UV package manager wrapper functionality including
command execution, telemetry integration, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, call
from pathlib import Path
import subprocess

from uvmgr.runtime.uv import call, add, remove, upgrade, list_pkgs, _extra_flags


class TestUvExtraFlags:
    """Test configuration flag handling."""
    
    def test_extra_flags_empty_by_default(self):
        """Test that no flags are set by default."""
        with patch('uvmgr.runtime.uv.env_or') as mock_env:
            mock_env.return_value = None
            flags = _extra_flags()
            assert flags == []
    
    def test_offline_flag_when_enabled(self):
        """Test offline flag is added when UV_OFFLINE=1."""
        with patch('uvmgr.runtime.uv.env_or') as mock_env:
            mock_env.side_effect = lambda key: "1" if key == "UV_OFFLINE" else None
            flags = _extra_flags()
            assert "--offline" in flags
    
    def test_extra_index_flag_when_set(self):
        """Test extra index URL flag when UV_EXTRA_INDEX is set."""
        with patch('uvmgr.runtime.uv.env_or') as mock_env:
            def env_side_effect(key):
                if key == "UV_OFFLINE":
                    return None
                elif key == "UV_EXTRA_INDEX":
                    return "https://test.pypi.org/simple/"
                return None
            mock_env.side_effect = env_side_effect
            
            flags = _extra_flags()
            assert "--extra-index-url" in flags
            assert "https://test.pypi.org/simple/" in flags


class TestUvCall:
    """Test the main UV command execution function."""
    
    @patch('uvmgr.runtime.uv.run_logged')
    @patch('uvmgr.runtime.uv._extra_flags')
    @patch('uvmgr.runtime.uv.span')
    def test_call_basic_command(self, mock_span, mock_extra_flags, mock_run_logged):
        """Test basic command execution."""
        mock_extra_flags.return_value = []
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        mock_run_logged.return_value = "success"
        
        result = call("add fastapi", capture=True)
        
        mock_run_logged.assert_called_once_with(
            ["uv", "add", "fastapi"], 
            capture=True, 
            cwd=None
        )
        assert result == "success"
    
    @patch('uvmgr.runtime.uv.run_logged')
    @patch('uvmgr.runtime.uv._extra_flags')
    @patch('uvmgr.runtime.uv.span')
    def test_call_with_extra_flags(self, mock_span, mock_extra_flags, mock_run_logged):
        """Test command execution with extra flags."""
        mock_extra_flags.return_value = ["--offline"]
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        call("pip list")
        
        mock_run_logged.assert_called_once_with(
            ["uv", "pip", "list", "--offline"], 
            capture=False, 
            cwd=None
        )
    
    @patch('uvmgr.runtime.uv.run_logged')
    @patch('uvmgr.runtime.uv._extra_flags')
    @patch('uvmgr.runtime.uv.span')
    def test_call_with_cwd(self, mock_span, mock_extra_flags, mock_run_logged):
        """Test command execution with custom working directory."""
        mock_extra_flags.return_value = []
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        cwd = Path("/test/project")
        call("init", cwd=cwd)
        
        mock_run_logged.assert_called_once_with(
            ["uv", "init"], 
            capture=False, 
            cwd=cwd
        )
    
    @patch('uvmgr.runtime.uv.run_logged')
    @patch('uvmgr.runtime.uv._extra_flags')
    def test_call_with_telemetry(self, mock_extra_flags, mock_run_logged):
        """Test that telemetry span is created."""
        mock_extra_flags.return_value = []
        
        with patch('uvmgr.runtime.uv.span') as mock_span:
            mock_context = Mock()
            mock_context.__enter__ = Mock()
            mock_context.__exit__ = Mock()
            mock_span.return_value = mock_context
            
            call("version")
            
            mock_span.assert_called_once_with("uv.call", cmd="uv version")
            mock_context.__enter__.assert_called_once()
            mock_context.__exit__.assert_called_once()


class TestUvAdd:
    """Test package addition functionality."""
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.package_metrics')
    @patch('uvmgr.runtime.uv.span')
    @patch('uvmgr.runtime.uv.add_span_attributes')
    @patch('uvmgr.runtime.uv.add_span_event')
    def test_add_single_package(self, mock_event, mock_attrs, mock_span, mock_metrics, mock_call):
        """Test adding a single package."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        add(["fastapi"])
        
        mock_call.assert_called_once_with("add  fastapi")
        mock_event.assert_any_call("uv.add.started", {"packages": ["fastapi"], "dev": False})
        mock_event.assert_any_call("uv.add.completed", {"packages": ["fastapi"], "success": True})
        
        # Verify metrics recorded
        mock_metrics.record_add.assert_called_once()
        args, kwargs = mock_metrics.record_add.call_args
        assert args[0] == "fastapi"  # package name
        assert args[2] == False  # dev flag
        assert args[3].success == True  # operation result
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.package_metrics')
    @patch('uvmgr.runtime.uv.span')
    @patch('uvmgr.runtime.uv.add_span_attributes')
    @patch('uvmgr.runtime.uv.add_span_event')
    def test_add_dev_packages(self, mock_event, mock_attrs, mock_span, mock_metrics, mock_call):
        """Test adding development packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        add(["pytest", "ruff"], dev=True)
        
        mock_call.assert_called_once_with("add --dev pytest ruff")
        mock_event.assert_any_call("uv.add.started", {"packages": ["pytest", "ruff"], "dev": True})
        
        # Verify metrics recorded for both packages
        assert mock_metrics.record_add.call_count == 2
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.package_metrics')
    @patch('uvmgr.runtime.uv.span')
    @patch('uvmgr.runtime.uv.add_span_attributes')
    @patch('uvmgr.runtime.uv.add_span_event')
    def test_add_package_failure(self, mock_event, mock_attrs, mock_span, mock_metrics, mock_call):
        """Test package addition failure handling."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        error = subprocess.CalledProcessError(1, "uv", "Package not found")
        mock_call.side_effect = error
        
        with pytest.raises(subprocess.CalledProcessError):
            add(["nonexistent-package"])
        
        # Verify failure is recorded in metrics
        mock_metrics.record_add.assert_called_once()
        args, kwargs = mock_metrics.record_add.call_args
        assert args[3].success == False  # operation result
        assert args[3].error == error
        
        mock_event.assert_any_call("uv.add.failed", {"error": str(error), "packages": ["nonexistent-package"]})


class TestUvRemove:
    """Test package removal functionality."""
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.package_metrics')
    @patch('uvmgr.runtime.uv.span')
    @patch('uvmgr.runtime.uv.add_span_attributes')
    @patch('uvmgr.runtime.uv.add_span_event')
    def test_remove_packages(self, mock_event, mock_attrs, mock_span, mock_metrics, mock_call):
        """Test removing packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        remove(["old-package", "unused-lib"])
        
        mock_call.assert_called_once_with("remove old-package unused-lib")
        mock_event.assert_any_call("uv.remove.started", {"packages": ["old-package", "unused-lib"]})
        mock_event.assert_any_call("uv.remove.completed", {"packages": ["old-package", "unused-lib"], "success": True})
        
        # Verify metrics recorded for both packages
        assert mock_metrics.record_remove.call_count == 2
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.package_metrics')
    @patch('uvmgr.runtime.uv.span')
    @patch('uvmgr.runtime.uv.add_span_attributes')
    @patch('uvmgr.runtime.uv.add_span_event')
    def test_remove_package_failure(self, mock_event, mock_attrs, mock_span, mock_metrics, mock_call):
        """Test package removal failure handling."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        error = subprocess.CalledProcessError(1, "uv", "Package not installed")
        mock_call.side_effect = error
        
        with pytest.raises(subprocess.CalledProcessError):
            remove(["not-installed"])
        
        # Verify failure is recorded in metrics
        mock_metrics.record_remove.assert_called_once()
        args, kwargs = mock_metrics.record_remove.call_args
        assert args[1].success == False  # operation result
        assert args[1].error == error
        
        mock_event.assert_any_call("uv.remove.failed", {"error": str(error), "packages": ["not-installed"]})


class TestUvUpgrade:
    """Test package upgrade functionality."""
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.span')
    def test_upgrade_all_packages(self, mock_span, mock_call):
        """Test upgrading all packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        upgrade(all_pkgs=True)
        
        mock_call.assert_called_once_with("upgrade --all")
        mock_span.assert_called_once_with("uv.upgrade", all=True, pkgs=[])
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.span')
    def test_upgrade_specific_packages(self, mock_span, mock_call):
        """Test upgrading specific packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        upgrade(pkgs=["fastapi", "uvicorn"])
        
        mock_call.assert_called_once_with("upgrade fastapi uvicorn")
        mock_span.assert_called_once_with("uv.upgrade", all=False, pkgs=["fastapi", "uvicorn"])
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.span')
    def test_upgrade_no_args(self, mock_span, mock_call):
        """Test upgrade with no arguments (should do nothing)."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        upgrade()
        
        mock_call.assert_not_called()
        mock_span.assert_called_once_with("uv.upgrade", all=False, pkgs=[])


class TestUvListPackages:
    """Test package listing functionality."""
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.span')
    def test_list_packages(self, mock_span, mock_call):
        """Test listing installed packages."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        mock_call.return_value = "fastapi==0.104.1\nuvicorn==0.24.0\n"
        
        result = list_pkgs()
        
        mock_call.assert_called_once_with("pip list", capture=True)
        assert result == "fastapi==0.104.1\nuvicorn==0.24.0\n"
    
    @patch('uvmgr.runtime.uv.call')
    @patch('uvmgr.runtime.uv.span')
    def test_list_packages_empty(self, mock_span, mock_call):
        """Test listing packages when none are installed."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        mock_call.return_value = None
        
        result = list_pkgs()
        
        assert result == ""


class TestIntegration:
    """Integration tests for UV module."""
    
    @patch('uvmgr.runtime.uv.run_logged')
    @patch('uvmgr.runtime.uv.package_metrics')
    def test_add_remove_workflow(self, mock_metrics, mock_run_logged):
        """Test a complete add-remove workflow."""
        with patch('uvmgr.runtime.uv.span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()
            
            # Add a package
            add(["requests"])
            
            # Remove the package
            remove(["requests"])
            
            # Verify both operations were called
            expected_calls = [
                call(["uv", "add", "requests"]),
                call(["uv", "remove", "requests"])
            ]
            mock_run_logged.assert_has_calls(expected_calls)
            
            # Verify metrics recorded for both operations
            assert mock_metrics.record_add.call_count == 1
            assert mock_metrics.record_remove.call_count == 1
    
    @patch.dict('os.environ', {'UV_OFFLINE': '1', 'UV_EXTRA_INDEX': 'https://test.pypi.org/simple/'})
    @patch('uvmgr.runtime.uv.run_logged')
    def test_environment_variable_integration(self, mock_run_logged):
        """Test that environment variables are properly integrated."""
        with patch('uvmgr.runtime.uv.span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()
            
            call("pip list")
            
            # Should include both offline and extra-index flags
            args = mock_run_logged.call_args[0][0]
            assert "--offline" in args
            assert "--extra-index-url" in args
            assert "https://test.pypi.org/simple/" in args