"""Behavioral tests for the receipted test execution boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from uvmgr.ops.tests import build_test_plan
from uvmgr.runtime.tests import execute_test_command


def test_build_test_plan_preserves_selectors_and_pytest_flags(tmp_path: Path) -> None:
    """Unknown pytest flags and exact selectors must survive planning."""
    plan = build_test_plan(
        ["tests/e2e/", "tests/test_cli.py::test_help"],
        ["--tb=short", "--maxfail=2"],
        working_directory=tmp_path,
        verbose=True,
        parallel=False,
        coverage=False,
    )

    assert plan.command == (
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "tests/e2e/",
        "tests/test_cli.py::test_help",
        "--tb=short",
        "--maxfail=2",
    )


def test_runtime_emits_receipt_for_success(tmp_path: Path) -> None:
    """Every executed test process must produce a replayable receipt."""
    receipt = execute_test_command(
        [sys.executable, "-c", "raise SystemExit(0)"],
        cwd=tmp_path,
    )

    assert receipt.exit_code == 0
    assert receipt.outcome == "ALIVE"
    receipt_path = Path(receipt.receipt_path)
    assert receipt_path.is_file()
    document = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert document["command"] == [sys.executable, "-c", "raise SystemExit(0)"]
    assert document["receipt_sha256"] == receipt.receipt_sha256


def test_runtime_emits_receipt_for_failure(tmp_path: Path) -> None:
    """A failed process is observed and receipted rather than hidden."""
    receipt = execute_test_command(
        [sys.executable, "-c", "raise SystemExit(7)"],
        cwd=tmp_path,
    )

    assert receipt.exit_code == 7
    assert receipt.outcome == "BUILD_BROKEN"
    assert Path(receipt.receipt_path).is_file()
