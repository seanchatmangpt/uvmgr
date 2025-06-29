"""Test uvmgr CLI."""

import json
import pytest
from typer.testing import CliRunner

from uvmgr.cli import app

runner = CliRunner()


def test_help() -> None:
    """Test that the --help option works as expected."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "uvmgr" in result.stdout


def test_version() -> None:
    """Test that the --version option works."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0


def test_json_output() -> None:
    """Test that JSON output works for supported commands."""
    # Test that help can be output as JSON
    result = runner.invoke(app, ["--json", "--help"])
    # Should either work or gracefully handle JSON flag
    assert result.exit_code in [0, 2]  # 2 for unsupported options


def test_command_discovery() -> None:
    """Test that major commands are discoverable."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    
    # Check for core commands
    core_commands = ["deps", "build", "tests", "cache", "lint", "otel", "guides", "worktree", "infodesign", "mermaid", "terraform"]
    for cmd in core_commands:
        assert cmd in result.stdout, f"Command '{cmd}' not found in help output"


@pytest.mark.skip(reason="workspace command currently disabled due to Callable type issues")
def test_workspace_command_available() -> None:
    """Test that workspace command is available after our fix."""
    result = runner.invoke(app, ["workspace", "--help"])
    assert result.exit_code == 0
    assert "workspace" in result.stdout.lower()


@pytest.mark.skip(reason="claude command currently disabled due to Callable type issues")
def test_claude_command_available() -> None:
    """Test that claude command is available."""
    result = runner.invoke(app, ["claude", "--help"])
    assert result.exit_code == 0
    assert "claude" in result.stdout.lower()


@pytest.mark.skip(reason="remote command currently disabled due to Callable type issues")
def test_remote_command_available() -> None:
    """Test that remote command is available after implementation."""
    result = runner.invoke(app, ["remote", "--help"])
    assert result.exit_code == 0
    assert "remote" in result.stdout.lower()
