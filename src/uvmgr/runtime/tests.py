"""Receipted runtime boundary for test and CI process execution."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_MAX_CAPTURE_CHARS = 16_384
_TIMEOUT_EXIT_CODE = 124
_MISSING_EXECUTABLE_EXIT_CODE = 127


@dataclass(frozen=True)
class TestExecutionReceipt:
    """Observed consequence of one process actuation."""

    command: tuple[str, ...]
    working_directory: str
    exit_code: int
    outcome: str
    started_ns: int
    duration_ms: float
    timed_out: bool
    error: str | None
    stdout: str
    stderr: str
    receipt_path: str
    receipt_sha256: str


@dataclass(frozen=True)
class CommandCheck:
    """One named CI command with an explicit failure policy."""

    description: str
    command: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class CommandCheckResult:
    """Receipted result for one named CI command."""

    description: str
    required: bool
    receipt: TestExecutionReceipt


def _bounded_output(value: str | bytes | None) -> str:
    """Convert captured output to bounded UTF-8 text."""
    if value is None:
        return ""
    text = value.decode(errors="replace") if isinstance(value, bytes) else value
    if len(text) <= _MAX_CAPTURE_CHARS:
        return text
    return text[:_MAX_CAPTURE_CHARS] + "\n...[truncated]"


def _write_receipt(
    payload: dict[str, object],
    *,
    receipt_dir: Path,
    started_ns: int,
) -> tuple[Path, str]:
    """Write a canonical JSON receipt atomically and return its identity."""
    receipt_dir.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    document = {**payload, "receipt_sha256": digest}
    target = receipt_dir / f"tests-run-{started_ns}.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target, digest


def execute_test_command(  # noqa: PLR0913
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    receipt_dir: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
    capture_output: bool = False,
) -> TestExecutionReceipt:
    """Execute exact argv and emit a receipt for every observed consequence."""
    argv = tuple(str(part) for part in command)
    if not argv:
        raise ValueError("test command must not be empty")

    working_directory = (cwd or Path.cwd()).resolve()
    receipts = receipt_dir or working_directory / "reports" / "receipts"
    started_ns = time.time_ns()
    started = time.perf_counter()
    exit_code = _MISSING_EXECUTABLE_EXIT_CODE
    timed_out = False
    error: str | None = None
    stdout = ""
    stderr = ""
    outcome = "UNSUPPORTED"

    try:
        completed = subprocess.run(
            list(argv),
            cwd=working_directory,
            env=dict(os.environ) | dict(env or {}),
            check=False,
            capture_output=capture_output,
            text=capture_output,
            timeout=timeout,
        )
        exit_code = completed.returncode
        stdout = _bounded_output(completed.stdout)
        stderr = _bounded_output(completed.stderr)
        outcome = "ALIVE" if exit_code == 0 else "BUILD_BROKEN"
    except subprocess.TimeoutExpired as exc:
        exit_code = _TIMEOUT_EXIT_CODE
        timed_out = True
        stdout = _bounded_output(exc.stdout)
        stderr = _bounded_output(exc.stderr)
        error = f"TimeoutExpired: exceeded {timeout} seconds"
        outcome = "BLOCKED"
    except OSError as exc:
        error = f"{type(exc).__name__}: {exc}"

    duration_ms = (time.perf_counter() - started) * 1000
    payload: dict[str, object] = {
        "command": list(argv),
        "working_directory": str(working_directory),
        "exit_code": exit_code,
        "outcome": outcome,
        "started_ns": started_ns,
        "duration_ms": round(duration_ms, 3),
        "timed_out": timed_out,
        "error": error,
        "stdout": stdout,
        "stderr": stderr,
    }
    receipt_path, receipt_sha256 = _write_receipt(
        payload,
        receipt_dir=receipts,
        started_ns=started_ns,
    )
    return TestExecutionReceipt(
        command=argv,
        working_directory=str(working_directory),
        exit_code=exit_code,
        outcome=outcome,
        started_ns=started_ns,
        duration_ms=duration_ms,
        timed_out=timed_out,
        error=error,
        stdout=stdout,
        stderr=stderr,
        receipt_path=str(receipt_path),
        receipt_sha256=receipt_sha256,
    )


def execute_command_checks(
    checks: Iterable[CommandCheck],
    *,
    cwd: Path | None = None,
    receipt_dir: Path | None = None,
    timeout: float | None = None,
) -> tuple[CommandCheckResult, ...]:
    """Execute named checks in order and receipt every attempt."""
    results: list[CommandCheckResult] = []
    for check in checks:
        receipt = execute_test_command(
            check.command,
            cwd=cwd,
            receipt_dir=receipt_dir,
            timeout=timeout,
            capture_output=True,
        )
        results.append(
            CommandCheckResult(
                description=check.description,
                required=check.required,
                receipt=receipt,
            )
        )
    return tuple(results)


def receipt_as_dict(receipt: TestExecutionReceipt) -> dict[str, object]:
    """Return a JSON-compatible representation of a receipt."""
    return asdict(receipt)


def command_check_result_as_dict(result: CommandCheckResult) -> dict[str, object]:
    """Return a JSON-compatible representation of a CI check result."""
    return {
        "description": result.description,
        "required": result.required,
        "receipt": receipt_as_dict(result.receipt),
    }


def discover_test_files(
    path: Path | None = None,
    pattern: str = "test_*.py",
) -> dict[str, Any]:
    """Discover and classify test files without importing or executing them."""
    search_path = (path or Path.cwd()).resolve()
    test_files = sorted(file for file in search_path.rglob(pattern) if file.is_file())
    test_types: dict[str, list[str]] = {
        "unit": [],
        "integration": [],
        "e2e": [],
    }
    for test_file in test_files:
        relative = test_file.relative_to(search_path)
        path_text = relative.as_posix()
        if "e2e" in path_text:
            test_types["e2e"].append(str(test_file))
        elif "integration" in path_text:
            test_types["integration"].append(str(test_file))
        else:
            test_types["unit"].append(str(test_file))
    return {
        "test_files": [str(file) for file in test_files],
        "test_types": test_types,
        "total_files": len(test_files),
    }


def cleanup_test_artifacts(root: Path) -> tuple[str, ...]:
    """Remove only known CI artifacts located under the admitted project root."""
    admitted_root = root.resolve()
    removed: list[str] = []
    file_names = {
        "ci-test.spec",
        "test-ci-build.spec",
        "test-ci.spec",
        "uvmgr-demo.spec",
    }
    for file_name in sorted(file_names):
        candidate = (admitted_root / file_name).resolve()
        if candidate.parent == admitted_root and candidate.is_file():
            candidate.unlink()
            removed.append(str(candidate))
    for directory_name in ("build", "dist"):
        candidate = (admitted_root / directory_name).resolve()
        if candidate.parent == admitted_root and candidate.is_dir():
            shutil.rmtree(candidate)
            removed.append(str(candidate))
    return tuple(removed)


def _parse_junit_report(path: Path) -> dict[str, int]:
    """Parse pytest JUnit summary when the configured report exists."""
    if not path.is_file():
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = sum(int(suite.attrib.get("tests", 0)) for suite in suites)
    failed = sum(int(suite.attrib.get("failures", 0)) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", 0)) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", 0)) for suite in suites)
    return {
        "total": total,
        "passed": max(total - failed - errors - skipped, 0),
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }


def _coverage_percentage(path: Path) -> float:
    """Read the overall percentage from a coverage JSON report."""
    if not path.is_file():
        return 0.0
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        return float(document.get("totals", {}).get("percent_covered", 0.0))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return 0.0


def execute_pytest(  # noqa: PLR0913
    verbose: bool = False,
    parallel: bool = True,
    coverage: bool = True,
    fail_fast: bool = False,
    test_types: Sequence[str] | None = None,
    markers: Sequence[str] | None = None,
    generate_report: bool = True,
    selectors: Sequence[str] | None = None,
    passthrough: Sequence[str] | None = None,
    cwd: Path | None = None,
    timeout: float | None = 300,
) -> dict[str, Any]:
    """Execute pytest compatibly through the receipted runtime boundary."""
    working_directory = (cwd or Path.cwd()).resolve()
    command = [sys.executable, "-m"]
    if coverage:
        command.extend(["coverage", "run", "--module", "pytest"])
    else:
        command.append("pytest")
    command.append("-v" if verbose else "-q")
    if parallel:
        command.extend(["-n", "auto"])
    if fail_fast:
        command.append("-x")
    marker_terms = [term for term in [*(test_types or ()), *(markers or ())] if term]
    if marker_terms:
        command.extend(["-m", " or ".join(f"({term})" for term in marker_terms)])
    command.extend(str(selector) for selector in selectors or ())
    command.extend(str(argument) for argument in passthrough or ())
    receipt = execute_test_command(
        command,
        cwd=working_directory,
        timeout=timeout,
        capture_output=True,
    )
    test_results = _parse_junit_report(working_directory / "reports" / "pytest.xml")
    coverage_result: dict[str, Any] = {}
    coverage_receipt: TestExecutionReceipt | None = None
    if coverage and receipt.exit_code == 0:
        coverage_path = working_directory / "reports" / "coverage.json"
        coverage_receipt = execute_test_command(
            [
                sys.executable,
                "-m",
                "coverage",
                "json",
                "-o",
                str(coverage_path),
            ],
            cwd=working_directory,
            timeout=timeout,
            capture_output=True,
        )
        coverage_result = {
            "percentage": _coverage_percentage(coverage_path),
            "format": "json",
            "receipt": receipt_as_dict(coverage_receipt),
        }
    return {
        "success": receipt.exit_code == 0,
        "exit_code": receipt.exit_code,
        "stdout": receipt.stdout,
        "stderr": receipt.stderr,
        "total_tests": test_results["total"],
        "passed": test_results["passed"],
        "failed": test_results["failed"],
        "skipped": test_results["skipped"],
        "coverage": coverage_result,
        "test_results": test_results,
        "generate_report": generate_report,
        "receipt": receipt_as_dict(receipt),
    }


def generate_coverage_report(
    format_type: str = "html",
    min_coverage: float | None = None,
    *,
    cwd: Path | None = None,
    timeout: float | None = 300,
) -> dict[str, Any]:
    """Generate one coverage projection through the receipted boundary."""
    working_directory = (cwd or Path.cwd()).resolve()
    command = [sys.executable, "-m", "coverage"]
    if format_type == "html":
        command.extend(["html", "--directory=reports/htmlcov"])
    elif format_type == "xml":
        command.extend(["xml", "-o", "reports/coverage.xml"])
    elif format_type == "json":
        command.extend(["json", "-o", "reports/coverage.json"])
    else:
        command.append("report")
    if min_coverage is not None:
        command.append(f"--fail-under={min_coverage}")
    receipt = execute_test_command(
        command,
        cwd=working_directory,
        timeout=timeout,
        capture_output=True,
    )
    percentage = _coverage_percentage(working_directory / "reports" / "coverage.json")
    return {
        "success": receipt.exit_code == 0,
        "format": format_type,
        "percentage": percentage,
        "output": receipt.stdout,
        "stderr": receipt.stderr,
        "meets_threshold": min_coverage is None or percentage >= min_coverage,
        "receipt": receipt_as_dict(receipt),
    }


def validate_test_environment(
    *,
    cwd: Path | None = None,
    timeout: float | None = 30,
) -> dict[str, Any]:
    """Validate pytest, coverage, and test-tree availability with receipts."""
    working_directory = (cwd or Path.cwd()).resolve()
    checks = (
        CommandCheck("pytest", (sys.executable, "-m", "pytest", "--version")),
        CommandCheck("coverage", (sys.executable, "-m", "coverage", "--version")),
    )
    results = execute_command_checks(checks, cwd=working_directory, timeout=timeout)
    issues = [result.description for result in results if result.receipt.exit_code != 0]
    if not (working_directory / "tests").is_dir():
        issues.append("tests directory not found")
    return {
        "valid": not issues,
        "dependencies_available": all(
            result.receipt.exit_code == 0 for result in results
        ),
        "issues": issues,
        "checks": [command_check_result_as_dict(result) for result in results],
    }
