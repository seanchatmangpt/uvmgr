"""Tests for Weaver command suite."""
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from uvmgr.commands.weaver import app

runner = CliRunner()


class TestWeaverCommands:
    """Test Weaver CLI commands."""

    @patch("subprocess.run")
    def test_check_command(self, mock_run):
        """Test weaver check command."""
        # Mock successful validation
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="✓ Registry valid",
            stderr=""
        )

        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "Registry validation passed" in result.stdout

        # Verify subprocess was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "registry" in call_args
        assert "check" in call_args
        assert "--future" in call_args

    @patch("subprocess.run")
    def test_check_command_failure(self, mock_run):
        """Test weaver check command with validation errors."""
        # Mock validation failure
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Invalid attribute"
        )

        result = runner.invoke(app, ["check"])
        assert result.exit_code == 1
        assert "Registry validation failed" in result.stdout
        assert "Invalid attribute" in result.stdout

    @patch("subprocess.run")
    @patch("uvmgr.commands.weaver.WEAVER_PATH", Path("/fake/weaver"))
    def test_install_not_found(self, mock_run):
        """Test install when weaver not found."""
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 1
        assert "Weaver not installed" in result.stdout

    def test_generate_python(self):
        """Test Python code generation."""
        # This uses our custom Python generator
        with patch("weaver_forge.validate_semconv.generate_python_constants") as mock_gen:
            result = runner.invoke(app, ["generate", "python"])
            assert result.exit_code == 0
            assert "Python constants generated" in result.stdout
            mock_gen.assert_called_once()

    @patch("subprocess.run")
    def test_resolve_command(self, mock_run):
        """Test resolve command."""
        resolved_data = {
            "groups": [
                {"id": "cli", "attributes": []}
            ]
        }

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(resolved_data),
            stderr=""
        )

        result = runner.invoke(app, ["resolve"])
        assert result.exit_code == 0
        # Should pretty-print JSON
        assert '"groups"' in result.stdout

    @patch("subprocess.run")
    def test_search_command(self, mock_run):
        """Test search command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Found: cli.command",
            stderr=""
        )

        result = runner.invoke(app, ["search", "command"])
        assert result.exit_code == 0
        assert "Found: cli.command" in result.stdout

    @patch("subprocess.run")
    def test_stats_command(self, mock_run):
        """Test stats command."""
        resolved_data = {
            "groups": [
                {
                    "id": "cli",
                    "type": "span",
                    "attributes": [{"id": "command"}, {"id": "args"}]
                },
                {
                    "id": "package",
                    "attributes": [{"id": "name"}]
                }
            ]
        }

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(resolved_data),
            stderr=""
        )

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Registry Statistics" in result.stdout
        assert "Groups" in result.stdout
        assert "Attributes" in result.stdout

    def test_init_command(self, tmp_path):
        """Test init command."""
        result = runner.invoke(app, [
            "init",
            "--name", "testapp",
            "--path", str(tmp_path)
        ])

        assert result.exit_code == 0
        assert "Registry 'testapp' initialized successfully" in result.stdout

        # Check created files
        registry_path = tmp_path / "registry"
        assert (registry_path / "registry_manifest.yaml").exists()
        assert (registry_path / "models" / "common.yaml").exists()
        assert (registry_path / ".gitignore").exists()

    def test_init_command_existing(self, tmp_path):
        """Test init command with existing registry."""
        registry_path = tmp_path / "registry"
        registry_path.mkdir(parents=True)

        result = runner.invoke(app, [
            "init",
            "--path", str(tmp_path)
        ], input="n\n")  # Don't overwrite

        assert result.exit_code == 1
        assert "Registry already exists" in result.stdout

    @patch("subprocess.run")
    def test_version_command(self, mock_run):
        """Test version command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="weaver 0.15.3",
            stderr=""
        )

        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "weaver 0.15.3" in result.stdout
        assert "OpenTelemetry Weaver" in result.stdout


class TestWeaverInstallation:
    """Test Weaver installation functionality."""

    @patch("subprocess.run")
    @patch("platform.system")
    @patch("platform.machine")
    def test_install_macos_arm64(self, mock_machine, mock_system, mock_run):
        """Test installation on macOS ARM64."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"

        # Mock successful download and extraction
        mock_run.return_value = MagicMock(returncode=0, stdout="weaver 0.15.3")

        with patch("uvmgr.commands.weaver.WEAVER_PATH", Path("/tmp/test_weaver")):
            result = runner.invoke(app, ["install", "--force"])

        assert result.exit_code == 0
        assert "Platform: darwin/arm64" in result.stdout
        assert "Artifact: weaver-aarch64-apple-darwin" in result.stdout

    @patch("subprocess.run")
    @patch("platform.system")
    @patch("platform.machine")
    def test_install_linux_x86(self, mock_machine, mock_system, mock_run):
        """Test installation on Linux x86_64."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"

        mock_run.return_value = MagicMock(returncode=0, stdout="weaver 0.15.3")

        with patch("uvmgr.commands.weaver.WEAVER_PATH", Path("/tmp/test_weaver")):
            result = runner.invoke(app, ["install", "--force"])

        assert result.exit_code == 0
        assert "Platform: linux/x86_64" in result.stdout
        assert "Artifact: weaver-x86_64-unknown-linux-gnu" in result.stdout


class TestWeaverDiff:
    """Test registry diff functionality."""

    @patch("subprocess.run")
    def test_diff_command(self, mock_run):
        """Test diff between two registries."""
        # Mock resolve outputs
        data1 = {"groups": [{"id": "cli", "attributes": []}]}
        data2 = {"groups": [{"id": "cli", "attributes": []}, {"id": "new", "attributes": []}]}

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps(data1)),
            MagicMock(returncode=0, stdout=json.dumps(data2))
        ]

        result = runner.invoke(app, ["diff", "reg1", "reg2"])
        assert result.exit_code == 0
        assert "Added:" in result.stdout
        assert "Group: new" in result.stdout


class TestWeaverDocumentation:
    """Test documentation generation."""

    @patch("subprocess.run")
    def test_docs_command(self, mock_run, tmp_path):
        """Test documentation generation."""
        resolved_data = {
            "groups": [{
                "id": "cli",
                "brief": "CLI attributes",
                "attributes": [{
                    "id": "command",
                    "type": "string",
                    "brief": "Command name",
                    "requirement_level": "required"
                }]
            }]
        }

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(resolved_data),
            stderr=""
        )

        result = runner.invoke(app, [
            "docs",
            "--output", str(tmp_path)
        ])

        assert result.exit_code == 0
        assert "Documentation generated" in result.stdout

        # Check generated files
        assert (tmp_path / "index.md").exists()
        assert (tmp_path / "cli.md").exists()
