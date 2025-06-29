"""
Unit tests for uvmgr.runtime.build module.

Tests build operations including distribution building, executable creation,
and PyInstaller spec file generation.
"""

import pytest
import sys
import tempfile
from unittest.mock import Mock, patch, mock_open, call
from pathlib import Path

from uvmgr.runtime.build import (
    dist, upload, exe, generate_spec, verify_executable
)


class TestDist:
    """Test distribution building functionality."""
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('uvmgr.runtime.build.span')
    def test_dist_basic(self, mock_span, mock_run_logged):
        """Test basic distribution building."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        dist()
        
        mock_run_logged.assert_called_once_with(["python", "-m", "build"])
        mock_span.assert_called_once_with("build.dist")
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('uvmgr.runtime.build.span')
    def test_dist_with_outdir(self, mock_span, mock_run_logged):
        """Test distribution building with custom output directory."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        outdir = Path("/custom/output")
        dist(outdir=outdir)
        
        expected_cmd = ["python", "-m", "build", "--outdir", "/custom/output"]
        mock_run_logged.assert_called_once_with(expected_cmd)


class TestUpload:
    """Test package upload functionality."""
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('uvmgr.runtime.build.span')
    def test_upload_default_dist_dir(self, mock_span, mock_run_logged):
        """Test uploading from default dist directory."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        upload()
        
        mock_run_logged.assert_called_once_with(["twine", "upload", "dist/*"])
        mock_span.assert_called_once_with("build.upload")
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('uvmgr.runtime.build.span')
    def test_upload_custom_dist_dir(self, mock_span, mock_run_logged):
        """Test uploading from custom dist directory."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        custom_dist = Path("/custom/dist")
        upload(dist_dir=custom_dist)
        
        mock_run_logged.assert_called_once_with(["twine", "upload", "/custom/dist/*"])


class TestExe:
    """Test executable building functionality."""
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('uvmgr.runtime.build.span')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_exe_basic(self, mock_unlink, mock_tempfile, mock_span, mock_run_logged):
        """Test basic executable building."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock temporary file
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/entry_script.py"
        mock_tempfile.return_value.__enter__ = Mock(return_value=mock_temp_file)
        mock_tempfile.return_value.__exit__ = Mock()
        
        result = exe()
        
        # Verify PyInstaller was called with expected arguments
        args = mock_run_logged.call_args[0][0]
        assert args[0] == "pyinstaller"
        assert "/tmp/entry_script.py" in args
        assert "--name" in args
        assert "uvmgr" in args
        assert "--onefile" in args
        assert "--clean" in args
        
        # Verify hidden imports were added
        assert "--hidden-import" in args
        hidden_import_indices = [i for i, arg in enumerate(args) if arg == "--hidden-import"]
        hidden_imports = [args[i + 1] for i in hidden_import_indices]
        assert "uvmgr.commands" in hidden_imports
        assert "uvmgr.core" in hidden_imports
        assert "typer" in hidden_imports
        
        # Verify cleanup was attempted
        mock_unlink.assert_called_once_with("/tmp/entry_script.py")
        
        # Verify return path
        if sys.platform == "win32":
            expected_path = Path("dist") / "uvmgr.exe"
        else:
            expected_path = Path("dist") / "uvmgr"
        assert result == expected_path
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('uvmgr.runtime.build.span')
    def test_exe_with_spec_file(self, mock_span, mock_run_logged):
        """Test executable building with existing spec file."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        spec_file = Path("/path/to/uvmgr.spec")
        result = exe(spec_file=spec_file)
        
        args = mock_run_logged.call_args[0][0]
        assert args[0] == "pyinstaller"
        assert str(spec_file) in args
        assert "--name" not in args  # Should not set name when using spec file
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('uvmgr.runtime.build.span')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_exe_with_custom_options(self, mock_unlink, mock_tempfile, mock_span, mock_run_logged):
        """Test executable building with custom options."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/entry_script.py"
        mock_tempfile.return_value.__enter__ = Mock(return_value=mock_temp_file)
        mock_tempfile.return_value.__exit__ = Mock()
        
        icon_path = Path("/path/to/icon.ico")
        result = exe(
            name="custom-app",
            onefile=False,
            clean=False,
            icon=icon_path,
            hidden_imports=["custom.module"],
            exclude_modules=["unnecessary.module"],
            debug=True
        )
        
        args = mock_run_logged.call_args[0][0]
        assert "--name" in args
        assert "custom-app" in args
        assert "--onefile" not in args  # onefile=False
        assert "--clean" not in args    # clean=False
        assert "--icon" in args
        assert str(icon_path) in args
        assert "--debug=all" in args
        
        # Check custom hidden import and exclude
        hidden_import_indices = [i for i, arg in enumerate(args) if arg == "--hidden-import"]
        hidden_imports = [args[i + 1] for i in hidden_import_indices]
        assert "custom.module" in hidden_imports
        
        exclude_indices = [i for i, arg in enumerate(args) if arg == "--exclude-module"]
        excludes = [args[i + 1] for i in exclude_indices]
        assert "unnecessary.module" in excludes
        
        # Verify return path for directory build
        if sys.platform == "win32":
            expected_path = Path("dist") / "custom-app" / "custom-app.exe"
        else:
            expected_path = Path("dist") / "custom-app" / "custom-app"
        assert result == expected_path
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('uvmgr.runtime.build.span')
    @patch('tempfile.NamedTemporaryFile')
    @patch('pathlib.Path.exists')
    def test_exe_with_mcp_resources(self, mock_exists, mock_tempfile, mock_span, mock_run_logged):
        """Test executable building includes MCP resources."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        mock_temp_file = Mock()
        mock_temp_file.name = "/tmp/entry_script.py"
        mock_tempfile.return_value.__enter__ = Mock(return_value=mock_temp_file)
        mock_tempfile.return_value.__exit__ = Mock()
        
        # Mock MCP resources file exists
        mock_exists.return_value = True
        
        exe()
        
        args = mock_run_logged.call_args[0][0]
        assert "--add-data" in args
        
        # Find the MCP resources add-data argument
        add_data_indices = [i for i, arg in enumerate(args) if arg == "--add-data"]
        add_data_values = [args[i + 1] for i in add_data_indices]
        mcp_data = [val for val in add_data_values if "mcp" in val and "resources.py" in val]
        assert len(mcp_data) > 0


class TestGenerateSpec:
    """Test PyInstaller spec file generation."""
    
    @patch('pathlib.Path.write_text')
    @patch('uvmgr.runtime.build.span')
    def test_generate_spec_basic(self, mock_span, mock_write_text):
        """Test basic spec file generation."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        outfile = Path("/path/to/uvmgr.spec")
        result = generate_spec(outfile)
        
        # Verify spec file content was written
        mock_write_text.assert_called_once()
        spec_content = mock_write_text.call_args[0][0]
        
        # Check key elements in spec content
        assert "Analysis(" in spec_content
        assert "PYZ(" in spec_content
        assert "EXE(" in spec_content
        assert "uvmgr.commands" in spec_content
        assert "typer" in spec_content
        assert "name='uvmgr'" in spec_content
        
        assert result == outfile
    
    @patch('pathlib.Path.write_text')
    @patch('uvmgr.runtime.build.span')
    def test_generate_spec_custom_options(self, mock_span, mock_write_text):
        """Test spec file generation with custom options."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        outfile = Path("/path/to/custom.spec")
        icon_path = Path("/path/to/icon.ico")
        
        result = generate_spec(
            outfile,
            name="custom-app",
            onefile=False,
            icon=icon_path,
            hidden_imports=["custom.module"],
            exclude_modules=["unwanted.module"]
        )
        
        spec_content = mock_write_text.call_args[0][0]
        
        # Check custom options
        assert "name='custom-app'" in spec_content
        assert "custom.module" in spec_content
        assert "unwanted.module" in spec_content
        assert str(icon_path) in spec_content
        assert "COLLECT(" in spec_content  # onefile=False should include COLLECT


class TestTestExecutable:
    """Test executable testing functionality."""
    
    @patch('subprocess.run')
    @patch('uvmgr.runtime.build.span')
    def test_verify_executable_success(self, mock_span, mock_subprocess):
        """Test successful executable testing."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock successful subprocess calls
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "uvmgr version 1.0.0"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        exe_path = Path("/path/to/uvmgr")
        result = verify_executable(exe_path)
        
        assert result["success"] is True
        assert result["tests_passed"] == ["version", "help", "commands"]
        assert result["executable"] == str(exe_path)
        
        # Verify all test commands were called
        assert mock_subprocess.call_count == 3
        called_commands = [call.args[0] for call in mock_subprocess.call_args_list]
        
        # Check for version, help, and command listing tests
        version_cmd = [str(exe_path), "--version"]
        help_cmd = [str(exe_path), "--help"]
        commands_cmd = [str(exe_path)]
        
        assert version_cmd in called_commands
        assert help_cmd in called_commands
        assert commands_cmd in called_commands
    
    @patch('subprocess.run')
    @patch('uvmgr.runtime.build.span')
    def test_verify_executable_version_failure(self, mock_span, mock_subprocess):
        """Test executable testing with version check failure."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock failed version check
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: Version not found"
        mock_subprocess.return_value = mock_result
        
        exe_path = Path("/path/to/uvmgr")
        result = verify_executable(exe_path)
        
        assert result["success"] is False
        assert "Version check failed" in result["error"]
        assert "Error: Version not found" in result["error"]
    
    @patch('subprocess.run')
    @patch('uvmgr.runtime.build.span')
    def test_verify_executable_timeout(self, mock_span, mock_subprocess):
        """Test executable testing with timeout."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock timeout
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired("cmd", 10)
        
        exe_path = Path("/path/to/uvmgr")
        result = verify_executable(exe_path)
        
        assert result["success"] is False
        assert "timed out" in result["error"]
    
    @patch('subprocess.run')
    @patch('uvmgr.runtime.build.span')
    def test_verify_executable_exception(self, mock_span, mock_subprocess):
        """Test executable testing with unexpected exception."""
        mock_span.return_value.__enter__ = Mock()
        mock_span.return_value.__exit__ = Mock()
        
        # Mock exception
        mock_subprocess.side_effect = Exception("Unexpected error")
        
        exe_path = Path("/path/to/uvmgr")
        result = verify_executable(exe_path)
        
        assert result["success"] is False
        assert "Unexpected error" in result["error"]


class TestIntegration:
    """Integration tests for build module."""
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('pathlib.Path.write_text')
    def test_spec_generation_and_build_workflow(self, mock_write_text, mock_run_logged):
        """Test complete spec generation and build workflow."""
        with patch('uvmgr.runtime.build.span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()
            
            # 1. Generate spec file
            spec_file = Path("/tmp/test.spec")
            generate_spec(spec_file, name="test-app")
            
            # Verify spec was written
            mock_write_text.assert_called_once()
            spec_content = mock_write_text.call_args[0][0]
            assert "test-app" in spec_content
            
            # 2. Build executable using spec
            exe(spec_file=spec_file)
            
            # Verify PyInstaller was called with spec file
            args = mock_run_logged.call_args[0][0]
            assert "pyinstaller" in args
            assert str(spec_file) in args
    
    @patch('uvmgr.runtime.build.run_logged')
    @patch('subprocess.run')
    def test_build_and_test_workflow(self, mock_subprocess_test, mock_run_logged):
        """Test complete build and test workflow."""
        with patch('uvmgr.runtime.build.span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()
            
            with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
                with patch('os.unlink'):
                    # Mock temporary file for exe build
                    mock_temp_file = Mock()
                    mock_temp_file.name = "/tmp/entry_script.py"
                    mock_tempfile.return_value.__enter__ = Mock(return_value=mock_temp_file)
                    mock_tempfile.return_value.__exit__ = Mock()
                    
                    # 1. Build executable
                    exe_path = exe(name="test-exe")
                    
                    # 2. Test executable
                    mock_test_result = Mock()
                    mock_test_result.returncode = 0
                    mock_test_result.stdout = "Success"
                    mock_test_result.stderr = ""
                    mock_subprocess_test.return_value = mock_test_result
                    
                    test_result = verify_executable(exe_path)
                    
                    # Verify both operations succeeded
                    assert mock_run_logged.called  # Build was called
                    assert test_result["success"] is True  # Test passed
                    assert test_result["executable"] == str(exe_path)