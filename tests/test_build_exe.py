"""Tests for PyInstaller executable building functionality."""

import pathlib
import sys
from unittest.mock import MagicMock, patch

import pytest

from uvmgr.ops import build as build_ops
from uvmgr.runtime import build as build_rt


class TestBuildExe:
    """Test executable building functionality."""

    def test_exe_command_basic(self, mocker):
        """Test basic exe build command."""
        mock_run = mocker.patch("uvmgr.runtime.build.run_logged")
        mock_span = mocker.patch("uvmgr.runtime.build.span")
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock()

        # Call exe function
        result = build_rt.exe(name="test-app")

        # Check that pyinstaller was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "pyinstaller"
        # Check that a temp file was passed (not -m)
        assert args[1].endswith(".py")
        assert "--name" in args
        assert "test-app" in args
        assert "--onefile" in args

        # Check return path
        if sys.platform == "win32":
            assert result == pathlib.Path("dist/test-app.exe")
        else:
            assert result == pathlib.Path("dist/test-app")

    def test_exe_with_spec_file(self, mocker):
        """Test exe build with spec file."""
        mock_run = mocker.patch("uvmgr.runtime.build.run_logged")
        mock_span = mocker.patch("uvmgr.runtime.build.span")
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock()

        spec_file = pathlib.Path("custom.spec")
        result = build_rt.exe(spec_file=spec_file)

        # Check that pyinstaller was called with spec file
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "pyinstaller"
        assert args[1] == "custom.spec"
        # May include additional data files

    def test_generate_spec(self, tmp_path):
        """Test spec file generation."""
        spec_file = tmp_path / "test.spec"

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock()
        mock_span.__exit__ = MagicMock()
        with patch("uvmgr.runtime.build.span", return_value=mock_span):
            result = build_rt.generate_spec(
                outfile=spec_file,
                name="test-app",
                onefile=True,
                hidden_imports=["module1", "module2"],
                exclude_modules=["exclude1"],
            )

        # Check spec file was created
        assert spec_file.exists()
        content = spec_file.read_text()

        # Check content
        assert "name='test-app'" in content
        assert "'module1'" in content
        assert "'module2'" in content
        assert "'exclude1'" in content
        # For onefile mode, check that the EXE contains all components
        assert "a.scripts," in content
        assert "a.binaries," in content
        assert "a.zipfiles," in content
        assert "a.datas," in content
        assert result == spec_file

    def test_test_executable(self, mocker):
        """Test executable testing functionality."""
        mock_subprocess = mocker.patch("subprocess.run")
        mock_span = mocker.patch("uvmgr.runtime.build.span")
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock()

        # Mock successful runs
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        result = build_rt.test_executable(pathlib.Path("/path/to/exe"))

        assert result["success"] is True
        assert "version" in result["tests_passed"]
        assert "help" in result["tests_passed"]
        assert "commands" in result["tests_passed"]

        # Check subprocess was called 3 times
        assert mock_subprocess.call_count == 3

    def test_test_executable_failure(self, mocker):
        """Test executable testing with failure."""
        mock_subprocess = mocker.patch("subprocess.run")
        mock_span = mocker.patch("uvmgr.runtime.build.span")
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock()

        # Mock failed run
        mock_subprocess.return_value = MagicMock(returncode=1, stderr="Error message")

        result = build_rt.test_executable(pathlib.Path("/path/to/exe"))

        assert result["success"] is False
        assert "Version check failed" in result["error"]

    def test_ops_exe(self, mocker):
        """Test ops layer exe function."""
        mock_rt_exe = mocker.patch("uvmgr.runtime.build.exe")
        mock_rt_exe.return_value = pathlib.Path("dist/uvmgr")

        result = build_ops.exe(name="uvmgr", onefile=True)

        assert result["output_file"] == "dist/uvmgr"
        assert result["name"] == "uvmgr"
        assert result["type"] == "onefile"

        mock_rt_exe.assert_called_once()

    def test_ops_generate_spec(self, mocker):
        """Test ops layer generate_spec function."""
        mock_rt_spec = mocker.patch("uvmgr.runtime.build.generate_spec")
        mock_rt_spec.return_value = pathlib.Path("uvmgr.spec")

        result = build_ops.generate_spec(
            outfile=pathlib.Path("uvmgr.spec"),
            name="uvmgr"
        )

        assert result["spec_file"] == "uvmgr.spec"
        mock_rt_spec.assert_called_once()
