"""Test uvmgr CLI."""

from typer.testing import CliRunner

from uvmgr.cli import app

runner = CliRunner()


def test_help() -> None:
    """Test that the --help option works as expected."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
