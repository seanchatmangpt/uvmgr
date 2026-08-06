"""Behavioral tests for receipted tests and capability inspection."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
import typer

import uvmgr.core.capabilities as capability_module
from uvmgr.core.capabilities import CapabilityStanding, inspect_capabilities
from uvmgr.ops.tests import TestRunOptions, build_test_plan
from uvmgr.runtime.tests import execute_test_command

FAILURE_EXIT_CODE = 7


def test_build_test_plan_preserves_selectors_and_pytest_flags(tmp_path: Path) -> None:
    """Unknown pytest flags and exact selectors must survive planning."""
    plan = build_test_plan(
        ["tests/e2e/", "tests/test_cli.py::test_help"],
        ["--tb=short", "--maxfail=2"],
        working_directory=tmp_path,
        options=TestRunOptions(
            verbose=True,
            parallel=False,
            coverage=False,
        ),
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


def test_build_test_plan_does_not_duplicate_raw_options(tmp_path: Path) -> None:
    """Options parsed as selectors remain authoritative and are not duplicated."""
    plan = build_test_plan(
        ["tests/e2e/", "-v", "-n=2"],
        working_directory=tmp_path,
        options=TestRunOptions(
            verbose=True,
            parallel=True,
            coverage=False,
        ),
    )

    assert plan.command.count("-v") == 1
    assert "-n" not in plan.command
    assert "-n=2" in plan.command


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
        [sys.executable, "-c", f"raise SystemExit({FAILURE_EXIT_CODE})"],
        cwd=tmp_path,
    )

    assert receipt.exit_code == FAILURE_EXIT_CODE
    assert receipt.outcome == "BUILD_BROKEN"
    assert Path(receipt.receipt_path).is_file()


def _all_modules_exist(_package: str, _name: str) -> bool:
    """Supply complete structural closure to capability tests."""
    return True


def test_unadmitted_capability_is_not_imported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inventory must not import or actuate an unadmitted command candidate."""
    monkeypatch.setattr(
        capability_module,
        "discover_command_names",
        lambda: ("candidate",),
    )
    monkeypatch.setattr(capability_module, "_module_exists", _all_modules_exist)

    def unexpected_import(_name: str) -> ModuleType:
        raise AssertionError("unadmitted command was imported")

    monkeypatch.setattr(capability_module.importlib, "import_module", unexpected_import)
    record = inspect_capabilities(enabled=(), excluded=())[0]

    assert record.standing == CapabilityStanding.PARTIAL_ALIVE
    assert record.observed
    assert not record.admitted
    assert not record.imported
    assert not record.executed


def test_structural_closure_does_not_claim_alive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Import and layer inspection remain below behavioral execution standing."""
    module = ModuleType("uvmgr.commands.candidate")
    module.__dict__["app"] = typer.Typer()
    monkeypatch.setattr(
        capability_module,
        "discover_command_names",
        lambda: ("candidate",),
    )
    monkeypatch.setattr(capability_module, "_module_exists", _all_modules_exist)
    monkeypatch.setattr(capability_module.importlib, "import_module", lambda _name: module)

    record = inspect_capabilities(enabled=("candidate",), excluded=())[0]

    assert record.standing == CapabilityStanding.PARTIAL_ALIVE
    assert record.admitted
    assert record.imported
    assert record.typer_app
    assert not record.executed
