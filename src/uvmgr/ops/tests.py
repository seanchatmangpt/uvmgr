"""Pure planning and orchestration for the ``uvmgr tests`` capability."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from uvmgr.runtime.tests import TestExecutionReceipt, execute_test_command


@dataclass(frozen=True)
class TestRunPlan:
    """Admitted test execution plan."""

    command: tuple[str, ...]
    working_directory: Path


def _has_option(arguments: Sequence[str], *names: str) -> bool:
    """Return whether argv already contains one of the supplied options."""
    return any(
        argument == name or argument.startswith(f"{name}=")
        for argument in arguments
        for name in names
    )


def build_test_plan(
    selectors: Iterable[str] = (),
    passthrough: Iterable[str] = (),
    *,
    working_directory: Path | None = None,
    verbose: bool = False,
    parallel: bool = True,
    coverage: bool = True,
    fail_fast: bool = False,
    test_types: Iterable[str] = (),
    markers: Iterable[str] = (),
) -> TestRunPlan:
    """Construct an exact pytest argv without interpreting pytest-owned flags."""
    forwarded = [str(argument) for argument in passthrough]
    selected = [str(selector) for selector in selectors]
    command = [sys.executable, "-m"]

    if coverage:
        command.extend(["coverage", "run", "--module", "pytest"])
    else:
        command.append("pytest")

    if verbose and not _has_option(forwarded, "-v", "--verbose"):
        command.append("-v")
    if fail_fast and not _has_option(forwarded, "-x", "--exitfirst"):
        command.append("-x")
    if parallel and not _has_option(forwarded, "-n", "--numprocesses"):
        command.extend(["-n", "auto"])

    marker_terms = [term for term in [*test_types, *markers] if term]
    if marker_terms and not _has_option(forwarded, "-m", "--markers"):
        command.extend(["-m", " or ".join(f"({term})" for term in marker_terms)])

    command.extend(selected)
    command.extend(forwarded)
    return TestRunPlan(
        command=tuple(command),
        working_directory=(working_directory or Path.cwd()).resolve(),
    )


def execute_test_plan(
    plan: TestRunPlan,
    *,
    receipt_dir: Path | None = None,
) -> TestExecutionReceipt:
    """Actuate an admitted test plan through the runtime boundary."""
    return execute_test_command(
        plan.command,
        cwd=plan.working_directory,
        receipt_dir=receipt_dir,
    )


def build_coverage_report_plan(
    *,
    working_directory: Path | None = None,
    fail_under: int | None = None,
) -> TestRunPlan:
    """Construct the post-test coverage report command."""
    command = [sys.executable, "-m", "coverage", "report"]
    if fail_under is not None:
        command.append(f"--fail-under={fail_under}")
    return TestRunPlan(
        command=tuple(command),
        working_directory=(working_directory or Path.cwd()).resolve(),
    )
