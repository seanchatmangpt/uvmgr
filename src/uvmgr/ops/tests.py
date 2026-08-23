"""Planning and orchestration for receipted test and CI capabilities."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from uvmgr.runtime.tests import (
    CommandCheck,
    CommandCheckResult,
    TestExecutionReceipt,
    cleanup_test_artifacts,
    command_check_result_as_dict,
    discover_test_files,
    execute_command_checks,
    execute_pytest,
    execute_test_command,
)
from uvmgr.runtime.tests import generate_coverage_report as runtime_generate_coverage_report
from uvmgr.runtime.tests import validate_test_environment as runtime_validate_test_environment


@dataclass(frozen=True)
class TestRunOptions:
    """uvmgr-owned test execution options."""

    verbose: bool = False
    parallel: bool = True
    coverage: bool = True
    fail_fast: bool = False
    test_types: tuple[str, ...] = ()
    markers: tuple[str, ...] = ()
    generate_report: bool = True


@dataclass(frozen=True)
class TestRunPlan:
    """Admitted test execution plan."""

    command: tuple[str, ...]
    working_directory: Path


@dataclass(frozen=True)
class CIPipelinePlan:
    """Deterministic CI checks and cleanup policy."""

    mode: str
    runner: str
    checks: tuple[CommandCheck, ...]
    working_directory: Path
    clean: bool
    verify_built_executable: bool


@dataclass(frozen=True)
class CIPipelineResult:
    """Observed CI results and bounded cleanup consequences."""

    mode: str
    runner: str
    checks: tuple[CommandCheckResult, ...]
    removed_artifacts: tuple[str, ...]

    @property
    def success(self) -> bool:
        """Return whether every required check executed successfully."""
        return all(
            not result.required or result.receipt.exit_code == 0
            for result in self.checks
        )


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
    options: TestRunOptions | None = None,
) -> TestRunPlan:
    """Construct exact pytest argv without interpreting pytest-owned flags."""
    selected = [str(selector) for selector in selectors]
    forwarded = [str(argument) for argument in passthrough]
    raw_arguments = [*selected, *forwarded]
    admitted = options or TestRunOptions()
    command = [sys.executable, "-m"]

    if admitted.coverage:
        command.extend(["coverage", "run", "--module", "pytest"])
    else:
        command.append("pytest")

    if admitted.verbose and not _has_option(raw_arguments, "-v", "--verbose"):
        command.append("-v")
    if admitted.fail_fast and not _has_option(raw_arguments, "-x", "--exitfirst"):
        command.append("-x")
    if admitted.parallel and not _has_option(raw_arguments, "-n", "--numprocesses"):
        command.extend(["-n", "auto"])

    marker_terms = [
        term for term in [*admitted.test_types, *admitted.markers] if term
    ]
    if marker_terms and not _has_option(raw_arguments, "-m", "--markers"):
        command.extend(["-m", " or ".join(f"({term})" for term in marker_terms)])

    command.extend(raw_arguments)
    return TestRunPlan(
        command=tuple(command),
        working_directory=(working_directory or Path.cwd()).resolve(),
    )


def execute_test_plan(
    plan: TestRunPlan,
    *,
    receipt_dir: Path | None = None,
    timeout: float | None = None,
) -> TestExecutionReceipt:
    """Actuate an admitted test plan through the runtime boundary."""
    return execute_test_command(
        plan.command,
        cwd=plan.working_directory,
        receipt_dir=receipt_dir,
        timeout=timeout,
    )


def build_coverage_report_plan(
    *,
    working_directory: Path | None = None,
    fail_under: int | None = None,
    format_type: str = "term",
) -> TestRunPlan:
    """Construct a post-test coverage projection command."""
    command = [sys.executable, "-m", "coverage"]
    if format_type == "html":
        command.extend(["html", "--directory=reports/htmlcov"])
    elif format_type == "xml":
        command.extend(["xml", "-o", "reports/coverage.xml"])
    elif format_type == "json":
        command.extend(["json", "-o", "reports/coverage.json"])
    else:
        command.append("report")
    if fail_under is not None:
        command.append(f"--fail-under={fail_under}")
    return TestRunPlan(
        command=tuple(command),
        working_directory=(working_directory or Path.cwd()).resolve(),
    )


def _uvmgr_command(*arguments: str) -> tuple[str, ...]:
    """Return an exact invocation of the current uvmgr interpreter."""
    return (sys.executable, "-m", "uvmgr.cli", *arguments)


def build_ci_plan(
    mode: str,
    *,
    runner: str = "native",
    skip_build: bool = False,
    clean: bool = True,
    working_directory: Path | None = None,
) -> CIPipelinePlan:
    """Build the legacy CI capability set as exact argv checks."""
    root = (working_directory or Path.cwd()).resolve()
    checks: list[CommandCheck] = []
    if mode == "quick":
        checks.extend(
            [
                CommandCheck("Python version", (sys.executable, "--version")),
                CommandCheck(
                    "PyInstaller import",
                    (
                        sys.executable,
                        "-c",
                        "import PyInstaller; print(PyInstaller.__version__)",
                    ),
                ),
                CommandCheck(
                    "PyInstaller unit tests",
                    (sys.executable, "-m", "pytest", "tests/test_build_exe.py", "-v"),
                ),
                CommandCheck(
                    "Generate spec file",
                    _uvmgr_command("build", "spec", "--name", "ci-test"),
                ),
            ]
        )
    elif mode == "verify":
        checks.extend(
            [
                CommandCheck("Python version", (sys.executable, "--version")),
                CommandCheck("uv version", ("uv", "--version")),
                CommandCheck(
                    "PyInstaller import",
                    (
                        sys.executable,
                        "-c",
                        "import PyInstaller; print(PyInstaller.__version__)",
                    ),
                ),
                CommandCheck("Installed packages", ("uv", "pip", "list"), required=False),
                CommandCheck(
                    "PyInstaller unit tests",
                    (sys.executable, "-m", "pytest", "tests/test_build_exe.py", "-v"),
                ),
                CommandCheck("Code linting", _uvmgr_command("lint", "check")),
            ]
        )
        if not skip_build:
            checks.extend(
                [
                    CommandCheck(
                        "Generate spec file",
                        _uvmgr_command(
                            "build",
                            "spec",
                            "--name",
                            "test-ci-build",
                        ),
                    ),
                    CommandCheck(
                        "Build test executable",
                        _uvmgr_command(
                            "build",
                            "exe",
                            "--name",
                            "test-ci",
                            "--exclude",
                            "numpy",
                            "--exclude",
                            "pandas",
                        ),
                    ),
                    CommandCheck(
                        "Build uvmgr dogfood executable",
                        _uvmgr_command(
                            "build",
                            "dogfood",
                            "--no-test",
                            "--no-platform",
                        ),
                    ),
                ]
            )
    elif mode == "run":
        if runner == "native":
            checks.extend(
                [
                    CommandCheck("Python version", (sys.executable, "--version")),
                    CommandCheck("Install project", ("uv", "pip", "install", "-e", ".")),
                    CommandCheck(
                        "Install PyInstaller",
                        (
                            "uv",
                            "pip",
                            "install",
                            "pyinstaller",
                            "pyinstaller-hooks-contrib",
                        ),
                    ),
                    CommandCheck("Run linting", _uvmgr_command("lint", "check")),
                    CommandCheck(
                        "Run tests",
                        _uvmgr_command(
                            "tests",
                            "run",
                            "--no-parallel",
                        ),
                    ),
                    CommandCheck(
                        "Run PyInstaller tests",
                        (
                            sys.executable,
                            "-m",
                            "pytest",
                            "tests/test_build_exe.py",
                            "-v",
                        ),
                    ),
                    CommandCheck(
                        "Test spec generation",
                        _uvmgr_command("build", "spec", "--name", "ci-test"),
                    ),
                    CommandCheck(
                        "Test executable build",
                        _uvmgr_command(
                            "build",
                            "exe",
                            "--name",
                            "ci-test",
                            "--clean",
                        ),
                    ),
                    CommandCheck(
                        "Test dogfood build",
                        _uvmgr_command(
                            "build",
                            "dogfood",
                            "--test",
                            "--no-platform",
                        ),
                    ),
                ]
            )
        elif runner == "act":
            checks.extend(
                [
                    CommandCheck("act version", ("act", "--version")),
                    CommandCheck(
                        "Run PyInstaller workflow",
                        (
                            "act",
                            "-j",
                            "test-pyinstaller",
                            "-P",
                            "ubuntu-latest=catthehacker/ubuntu:act-latest",
                        ),
                    ),
                    CommandCheck(
                        "Run test workflow",
                        (
                            "act",
                            "-j",
                            "test",
                            "-P",
                            "ubuntu-latest=catthehacker/ubuntu:act-latest",
                        ),
                    ),
                ]
            )
        elif runner == "docker":
            mount = f"{root}:/workspace"
            checks.extend(
                [
                    CommandCheck("Docker version", ("docker", "--version")),
                    CommandCheck(
                        "Build devcontainer",
                        (
                            "docker",
                            "build",
                            "-t",
                            "uvmgr-ci",
                            "-f",
                            ".devcontainer/Dockerfile",
                            ".",
                        ),
                    ),
                    CommandCheck(
                        "Run verification in container",
                        (
                            "docker",
                            "run",
                            "--rm",
                            "-v",
                            mount,
                            "-w",
                            "/workspace",
                            "uvmgr-ci",
                            "python",
                            "-m",
                            "uvmgr.cli",
                            "tests",
                            "ci",
                            "verify",
                            "--skip-build",
                            "--no-clean",
                        ),
                    ),
                ]
            )
        else:
            raise ValueError(f"unsupported CI runner: {runner}")
    else:
        raise ValueError(f"unsupported CI mode: {mode}")
    return CIPipelinePlan(
        mode=mode,
        runner=runner,
        checks=tuple(checks),
        working_directory=root,
        clean=clean,
        verify_built_executable=(
            (mode == "verify" and not skip_build)
            or (mode == "run" and runner == "native")
        ),
    )


def execute_ci_plan(
    plan: CIPipelinePlan,
    *,
    timeout: float | None = None,
    receipt_dir: Path | None = None,
) -> CIPipelineResult:
    """Execute a CI plan and apply only its bounded cleanup policy."""
    checks = list(
        execute_command_checks(
            plan.checks,
            cwd=plan.working_directory,
            receipt_dir=receipt_dir,
            timeout=timeout,
        )
    )
    if plan.verify_built_executable:
        candidates = sorted(
            candidate
            for candidate in (plan.working_directory / "dist").glob("uvmgr*")
            if candidate.is_file()
        )
        if candidates:
            executable_checks = tuple(
                CommandCheck(
                    f"Built executable {argument}",
                    (str(candidates[0]), argument),
                )
                for argument in ("--version", "--help")
            )
        else:
            executable_checks = (
                CommandCheck(
                    "Built executable discovery",
                    (
                        sys.executable,
                        "-c",
                        (
                            "from pathlib import Path; import sys; "
                            "raise SystemExit(0 if any(Path(sys.argv[1]).glob("
                            "'uvmgr*')) else 1)"
                        ),
                        str(plan.working_directory / "dist"),
                    ),
                ),
            )
        checks.extend(
            execute_command_checks(
                executable_checks,
                cwd=plan.working_directory,
                receipt_dir=receipt_dir,
                timeout=timeout,
            )
        )
    removed = cleanup_test_artifacts(plan.working_directory) if plan.clean else ()
    return CIPipelineResult(
        mode=plan.mode,
        runner=plan.runner,
        checks=tuple(checks),
        removed_artifacts=removed,
    )


def ci_pipeline_result_as_dict(result: CIPipelineResult) -> dict[str, object]:
    """Return a JSON-compatible CI result projection."""
    return {
        "mode": result.mode,
        "runner": result.runner,
        "success": result.success,
        "checks": [command_check_result_as_dict(check) for check in result.checks],
        "removed_artifacts": list(result.removed_artifacts),
    }


def run_test_suite(  # noqa: PLR0913
    verbose: bool = False,
    parallel: bool = True,
    coverage: bool = True,
    fail_fast: bool = False,
    test_types: Sequence[str] | None = None,
    markers: Sequence[str] | None = None,
    generate_report: bool = True,
) -> dict[str, Any]:
    """Preserve the historical test-suite API through the receipt boundary."""
    return execute_pytest(
        verbose=verbose,
        parallel=parallel,
        coverage=coverage,
        fail_fast=fail_fast,
        test_types=test_types,
        markers=markers,
        generate_report=generate_report,
    )


def generate_coverage_report(
    format_type: str = "html",
    min_coverage: float | None = None,
) -> dict[str, Any]:
    """Preserve the historical coverage API through the receipt boundary."""
    return runtime_generate_coverage_report(
        format_type=format_type,
        min_coverage=min_coverage,
    )


def run_ci_verification(
    quick: bool = False,
    comprehensive: bool = True,
) -> dict[str, Any]:
    """Preserve the historical CI API with deterministic exact-argv checks."""
    mode = "quick" if quick else "verify"
    plan = build_ci_plan(mode, skip_build=not comprehensive)
    return ci_pipeline_result_as_dict(execute_ci_plan(plan))


def discover_tests(
    path: Path | None = None,
    pattern: str = "test_*.py",
) -> dict[str, Any]:
    """Preserve the historical pure test-discovery API."""
    return discover_test_files(path=path, pattern=pattern)


def validate_test_environment() -> dict[str, Any]:
    """Preserve the historical environment validation API with receipts."""
    return runtime_validate_test_environment()


def assert_json_safe(value: object) -> None:
    """Raise when a public compatibility result is not JSON serializable."""
    json.dumps(value, sort_keys=True)
