"""Tests for PyInstaller executable building functionality."""

import pathlib
import sys
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import uvmgr.commands as commands_package
from uvmgr.commands import build as build_commands
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

        result = build_rt.exe(name="test-app")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "pyinstaller"
        assert args[1].endswith(".py")
        assert "--name" in args
        assert "test-app" in args
        assert "--onefile" in args

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
        build_rt.exe(spec_file=spec_file)

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "pyinstaller"
        assert args[1] == "custom.spec"

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

        assert spec_file.exists()
        content = spec_file.read_text()
        assert "name='test-app'" in content
        assert "'module1'" in content
        assert "'module2'" in content
        assert "'exclude1'" in content
        assert "a.scripts," in content
        assert "a.binaries," in content
        assert "a.zipfiles," in content
        assert "a.datas," in content
        assert result == spec_file

    def test_command_repair_sources_are_bundled(self):
        """Frozen builds must carry exact source consumed by the repair loader."""
        data_files = build_rt._command_repair_data_files()
        observed = {(source.name, destination) for source, destination in data_files}
        assert observed == {
            ("automation.py", "uvmgr/commands"),
            ("performance.py", "uvmgr/commands"),
            ("security.py", "uvmgr/commands"),
        }
        assert all(source.is_file() for source, _destination in data_files)

    def test_frozen_import_closure_contains_every_admitted_command(self):
        """The frozen graph must be projected from the canonical command registry."""
        hidden_imports = set(build_rt._default_hidden_imports())
        assert build_rt._admitted_command_names() == tuple(commands_package.__all__)
        assert all(
            f"uvmgr.commands.{command}" in hidden_imports
            for command in commands_package.__all__
        )
        assert "uvmgr.commands.claude" not in hidden_imports
        assert "uvmgr.mcp" not in hidden_imports
        assert "ember_ai" not in hidden_imports
        assert "spiffworkflow" not in hidden_imports

    def test_test_executable(self, mocker):
        """Test executable verification covers every admitted CLI route."""
        mock_subprocess = mocker.patch("subprocess.run")
        mock_span = mocker.patch("uvmgr.runtime.build.span")
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock()
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="healthy",
            stderr="",
        )

        result = build_rt.test_executable(pathlib.Path("/path/to/exe"))

        assert result["success"] is True
        assert result["command_count"] == len(commands_package.__all__)
        assert result["commands_tested"] == list(commands_package.__all__)
        assert "admitted_commands" in result["tests_passed"]
        assert "capabilities_verify" in result["tests_passed"]
        assert mock_subprocess.call_count == len(commands_package.__all__) + 3

        observed_argv = [call.args[0] for call in mock_subprocess.call_args_list]
        assert ["/path/to/exe", "ap-scheduler", "--help"] in observed_argv
        assert ["/path/to/exe", "weaver-forge", "--help"] in observed_argv
        assert ["/path/to/exe", "ap_scheduler", "--help"] not in observed_argv
        assert ["/path/to/exe", "weaver_forge", "--help"] not in observed_argv
        assert {"module": "ap_scheduler", "cli": "ap-scheduler"} in result[
            "command_routes"
        ]

    def test_test_executable_allows_typed_refusal_in_capability_ledger(self, mocker):
        """Typed refusal is admissible evidence, not executable corruption."""
        mock_subprocess = mocker.patch("subprocess.run")
        mock_span = mocker.patch("uvmgr.runtime.build.span")
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock()

        def fake_run(command, **_kwargs):
            stdout = (
                "REFUSED:EXCLUDED_BY_REGISTRY"
                if command[1:] == ["capabilities", "verify"]
                else "healthy"
            )
            return MagicMock(returncode=0, stdout=stdout, stderr="")

        mock_subprocess.side_effect = fake_run
        result = build_rt.test_executable(pathlib.Path("/path/to/exe"))

        assert result["success"] is True
        assert result["command_count"] == len(commands_package.__all__)

    def test_test_executable_failure(self, mocker):
        """Test executable verification fails on a non-zero process exit."""
        mock_subprocess = mocker.patch("subprocess.run")
        mock_span = mocker.patch("uvmgr.runtime.build.span")
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock()
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error message",
        )

        result = build_rt.test_executable(pathlib.Path("/path/to/exe"))

        assert result["success"] is False
        assert "Version check failed with exit 1" in result["error"]

    def test_test_executable_rejects_exit_zero_build_broken_placeholder(self, mocker):
        """An exit-zero placeholder must not manufacture false executable health."""
        mock_subprocess = mocker.patch("subprocess.run")
        mock_span = mocker.patch("uvmgr.runtime.build.span")
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock()
        mock_subprocess.side_effect = [
            MagicMock(returncode=0, stdout="uvmgr 0.0.0", stderr=""),
            MagicMock(returncode=0, stdout="help", stderr=""),
            MagicMock(
                returncode=0,
                stdout="BUILD_BROKEN: enabled command failed to load",
                stderr="",
            ),
        ]

        result = build_rt.test_executable(pathlib.Path("/path/to/exe"))

        assert result["success"] is False
        assert "exposed incomplete standing BUILD_BROKEN:" in result["error"]

    def test_dogfood_command_fails_closed_when_self_test_fails(self, mocker):
        """Dogfood must propagate failed verification as a non-zero CLI result."""
        mocker.patch(
            "uvmgr.commands.build.build_ops.exe",
            return_value={"output_file": "dist/uvmgr"},
        )
        mocker.patch(
            "uvmgr.commands.build.build_ops.test_executable",
            return_value={"success": False, "error": "BUILD_BROKEN"},
        )

        result = CliRunner().invoke(
            build_commands.app,
            ["dogfood", "--no-platform", "--test"],
        )

        assert result.exit_code == 1
        assert "executable test failed: BUILD_BROKEN" in result.output

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

        result = build_ops.generate_spec(outfile=pathlib.Path("uvmgr.spec"), name="uvmgr")

        assert result["spec_file"] == "uvmgr.spec"
        mock_rt_spec.assert_called_once()
