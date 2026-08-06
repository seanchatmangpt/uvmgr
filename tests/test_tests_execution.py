"""Behavioral tests for receipted tests and capability inspection."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
import typer

import uvmgr.core.capabilities as capability_module
import uvmgr.ops.tests as test_operations
from uvmgr.core.capabilities import CapabilityStanding, inspect_capabilities
from uvmgr.ops.tests import TestRunOptions, build_ci_plan, build_test_plan
from uvmgr.runtime.tests import cleanup_test_artifacts, execute_test_command

FAILURE_EXIT_CODE = 7
TIMEOUT_EXIT_CODE = 124


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
    assert not receipt.timed_out
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


def test_runtime_receipts_timeout(tmp_path: Path) -> None:
    """A timeout is classified and receipted as a blocked execution edge."""
    receipt = execute_test_command(
        [sys.executable, "-c", "import time; time.sleep(1)"],
        cwd=tmp_path,
        timeout=0.01,
        capture_output=True,
    )

    assert receipt.exit_code == TIMEOUT_EXIT_CODE
    assert receipt.outcome == "BLOCKED"
    assert receipt.timed_out
    assert Path(receipt.receipt_path).is_file()


def test_exact_argv_does_not_invoke_host_shell(tmp_path: Path) -> None:
    """Shell metacharacters remain inert data in exact argv execution."""
    marker = tmp_path / "ambient-actuation"
    argument = f"value;touch {marker}"
    receipt = execute_test_command(
        [sys.executable, "-c", "import sys; print(sys.argv[1])", argument],
        cwd=tmp_path,
        capture_output=True,
    )

    assert receipt.exit_code == 0
    assert argument in receipt.stdout
    assert not marker.exists()


def test_ci_plans_use_exact_argv_without_host_shell(tmp_path: Path) -> None:
    """Every restored CI capability is represented as an argv vector."""
    for mode, runner in (
        ("quick", "native"),
        ("verify", "native"),
        ("run", "native"),
        ("run", "act"),
        ("run", "docker"),
    ):
        plan = build_ci_plan(mode, runner=runner, working_directory=tmp_path)
        assert plan.checks
        for check in plan.checks:
            assert isinstance(check.command, tuple)
            assert check.command
            assert check.command[0] not in {"bash", "cmd", "pwsh", "sh"}


def test_cleanup_is_bounded_to_known_project_artifacts(tmp_path: Path) -> None:
    """Cleanup cannot remove unrelated or parent-directory files."""
    allowed_spec = tmp_path / "ci-test.spec"
    unrelated_spec = tmp_path / "customer.spec"
    outside = tmp_path.parent / "outside.spec"
    allowed_spec.write_text("generated", encoding="utf-8")
    unrelated_spec.write_text("keep", encoding="utf-8")
    outside.write_text("keep", encoding="utf-8")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "artifact").write_text("generated", encoding="utf-8")

    removed = cleanup_test_artifacts(tmp_path)

    assert str(allowed_spec) in removed
    assert str(tmp_path / "build") in removed
    assert not allowed_spec.exists()
    assert not (tmp_path / "build").exists()
    assert unrelated_spec.is_file()
    assert outside.is_file()
    outside.unlink()


def test_compatibility_api_result_is_json_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The historical operations API preserves JSON-safe result contracts."""
    expected = {
        "success": True,
        "exit_code": 0,
        "receipt": {"receipt_sha256": "abc"},
    }
    monkeypatch.setattr(test_operations, "execute_pytest", lambda **_kwargs: expected)

    result = test_operations.run_test_suite(verbose=True)

    assert result == expected
    test_operations.assert_json_safe(result)


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
