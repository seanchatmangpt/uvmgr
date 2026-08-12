"""Test uvmgr CLI."""

from typer.testing import CliRunner

from uvmgr.cli import app
from uvmgr.commands import EXCLUDED_COMMANDS

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
    result = runner.invoke(app, ["--json", "--help"])
    assert result.exit_code in [0, 2]


def test_command_discovery() -> None:
    """Test that major admitted commands are discoverable."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    core_commands = [
        "deps",
        "build",
        "tests",
        "cache",
        "lint",
        "otel",
        "guides",
        "worktree",
        "infodesign",
        "mermaid",
        "terraform",
    ]
    for command in core_commands:
        assert command in result.stdout, f"Command {command!r} not found in help output"


def test_workspace_command_available() -> None:
    """Test that the admitted workspace command constructs."""
    result = runner.invoke(app, ["workspace", "--help"])
    assert result.exit_code == 0
    assert "workspace" in result.stdout.lower()


def test_claude_command_is_explicitly_refused() -> None:
    """Test that excluded Claude capability does not leak into the CLI."""
    assert "claude" in EXCLUDED_COMMANDS
    result = runner.invoke(app, ["claude", "--help"])
    assert result.exit_code == 2
    assert "No such command 'claude'" in result.output


def test_remote_command_available() -> None:
    """Test that the admitted remote command constructs."""
    result = runner.invoke(app, ["remote", "--help"])
    assert result.exit_code == 0
    assert "remote" in result.stdout.lower()
