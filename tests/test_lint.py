"""
Tests for the lint command.
"""

import json
import subprocess
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from uvmgr.cli import app

runner = CliRunner()


@pytest.fixture
def mock_ruff():
    """Mock Ruff subprocess calls."""
    with patch("uvmgr.core.process.run") as mock_run:
        mock_run.return_value = None  # run() doesn't return anything on success
        yield mock_run


def test_lint_check_success(mock_ruff):
    """Test successful lint check."""
    result = runner.invoke(app, ["lint", "check"])
    assert result.exit_code == 0
    assert "✅ No Ruff violations found" in result.stdout


def test_lint_check_with_fix(mock_ruff):
    """Test lint check with --fix flag."""
    result = runner.invoke(app, ["lint", "check", "--fix"])
    assert result.exit_code == 0
    mock_ruff.assert_called_with(["ruff", "check", "--fix", "."])


def test_lint_check_with_show_fixes(mock_ruff):
    """Test lint check with --show-fixes flag."""
    result = runner.invoke(app, ["lint", "check", "--show-fixes"])
    assert result.exit_code == 0
    mock_ruff.assert_called_with(["ruff", "check", "--show-fixes", "."])


def test_lint_check_with_path(mock_ruff):
    """Test lint check with specific path."""
    result = runner.invoke(app, ["lint", "check", "src/"])
    assert result.exit_code == 0
    mock_ruff.assert_called_with(["ruff", "check", "src"])


def test_lint_check_failure(mock_ruff):
    """Test lint check with violations."""
    mock_ruff.side_effect = subprocess.CalledProcessError(1, ["ruff", "check"])
    result = runner.invoke(app, ["lint", "check"])
    assert result.exit_code == 1
    assert "❌ Ruff violations found" in result.stdout


def test_lint_format_success(mock_ruff):
    """Test successful formatting."""
    result = runner.invoke(app, ["lint", "format"])
    assert result.exit_code == 0
    assert "✅ Code formatted successfully" in result.stdout
    mock_ruff.assert_called_with(["ruff", "format", "."])


def test_lint_format_check(mock_ruff):
    """Test format check without making changes."""
    result = runner.invoke(app, ["lint", "format", "--check"])
    assert result.exit_code == 0
    mock_ruff.assert_called_with(["ruff", "format", "--check", "."])


def test_lint_format_failure(mock_ruff):
    """Test formatting with issues."""
    mock_ruff.side_effect = subprocess.CalledProcessError(1, ["ruff", "format"])
    result = runner.invoke(app, ["lint", "format"])
    assert result.exit_code == 1
    assert "❌ Formatting issues found" in result.stdout


def test_lint_fix_success(mock_ruff):
    """Test successful fix command."""
    result = runner.invoke(app, ["lint", "fix"])
    assert result.exit_code == 0
    assert "✅ All issues fixed successfully" in result.stdout
    assert mock_ruff.call_count == 2
    mock_ruff.assert_any_call(["ruff", "format", "."])
    mock_ruff.assert_any_call(["ruff", "check", "--fix", "."])


def test_lint_fix_format_failure(mock_ruff):
    """Test fix command with formatting failure."""
    mock_ruff.side_effect = subprocess.CalledProcessError(1, ["ruff", "format"])
    result = runner.invoke(app, ["lint", "fix"])
    assert result.exit_code == 1
    assert "❌ Formatting failed" in result.stdout
    assert mock_ruff.call_count == 1


def test_lint_fix_check_failure(mock_ruff):
    """Test fix command with check failure."""
    mock_ruff.side_effect = [
        None,  # format succeeds
        subprocess.CalledProcessError(1, ["ruff", "check", "--fix"]),  # check fails
    ]
    result = runner.invoke(app, ["lint", "fix"])
    assert result.exit_code == 1
    assert "❌ Some issues could not be fixed automatically" in result.stdout
    assert mock_ruff.call_count == 2


def test_lint_json_output(mock_ruff):
    """Test JSON output for all commands."""
    # Test check command
    result = runner.invoke(app, ["--json", "lint", "check"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "status": "success",
        "message": "✅ No Ruff violations found",
    }

    # Test format command
    mock_ruff.return_value.returncode = 0
    result = runner.invoke(app, ["--json", "lint", "format"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "status": "success",
        "message": "✅ Code formatted successfully",
    }

    # Test fix command
    mock_ruff.return_value.returncode = 0
    result = runner.invoke(app, ["--json", "lint", "fix"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "status": "success",
        "message": "✅ All issues fixed successfully",
    }

    # Test error case
    mock_ruff.return_value.returncode = 1
    result = runner.invoke(app, ["--json", "lint", "check"])
    assert result.exit_code == 1
    assert json.loads(result.stdout) == {"status": "error", "message": "❌ Ruff violations found"}


def test_lint_invalid_path():
    """Test lint command with invalid path."""
    result = runner.invoke(app, ["lint", "check", "nonexistent/"])
    assert result.exit_code != 0
    assert "does not exist" in result.stdout
