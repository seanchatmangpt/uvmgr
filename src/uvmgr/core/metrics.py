"""
uvmgr.core.metrics
------------------
Metrics collection classes for different operation types.

Provides metric collection for:
- Package management (deps)
- Build operations
- Test execution
- AI operations
- Process execution
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from .semconv import (
    AIAttributes,
    BuildAttributes,
    PackageAttributes,
    ProcessAttributes,
    TestAttributes,
)
from .telemetry import metric_counter, metric_gauge, metric_histogram


@dataclass
class OperationResult:
    """Result of an operation with timing and context information."""

    success: bool
    duration: float
    error: Exception | None = None
    metadata: dict[str, Any] | None = None


class BaseMetrics:
    """Base class for metrics collection."""

    def __init__(self, namespace: str):
        self.namespace = namespace
        self._init_metrics()

    def _init_metrics(self):
        """Initialize metrics - to be overridden by subclasses."""
        # Common metrics
        self.operation_counter = metric_counter(f"{self.namespace}.operations")
        self.error_counter = metric_counter(f"{self.namespace}.errors")
        self.duration_histogram = metric_histogram(f"{self.namespace}.duration", unit="s")
        self.active_gauge = metric_gauge(f"{self.namespace}.active")

    @contextmanager
    def timer(self):
        """Context manager to time operations."""
        start = time.time()
        self.active_gauge(1)
        try:
            yield lambda: time.time() - start
        finally:
            self.active_gauge(-1)

    def record_operation(
        self,
        operation: str,
        duration: float,
        success: bool,
        attributes: dict[str, Any] | None = None,
    ):
        """Record metrics for an operation."""
        attrs = attributes or {}
        attrs["operation"] = operation
        attrs["success"] = str(success)

        self.operation_counter(1, **attrs)
        self.duration_histogram(duration, **attrs)

        if not success:
            self.error_counter(1, **attrs)


class PackageMetrics(BaseMetrics):
    """Metrics for package management operations."""

    def __init__(self):
        super().__init__("package")

    def _init_metrics(self):
        super()._init_metrics()
        # Package-specific metrics
        self.packages_added = metric_counter("package.packages_added")
        self.packages_removed = metric_counter("package.packages_removed")
        self.packages_updated = metric_counter("package.packages_updated")
        self.dependency_resolution_time = metric_histogram("package.resolution_time", unit="s")

    def record_package_operation(
        self,
        operation: str,
        package_name: str,
        version: str | None = None,
        dev: bool = False,
        duration: float = 0.0,
        success: bool = True,
    ):
        """Record package-specific metrics."""
        attributes = {
            PackageAttributes.OPERATION: operation,
            PackageAttributes.NAME: package_name,
            PackageAttributes.DEV_DEPENDENCY: str(dev),
        }

        if version:
            attributes[PackageAttributes.VERSION] = version

        self.record_operation(operation, duration, success, attributes)

        # Update specific counters
        if success:
            if operation == "add":
                self.packages_added(1, **attributes)
            elif operation == "remove":
                self.packages_removed(1, **attributes)
            elif operation == "update":
                self.packages_updated(1, **attributes)

    def record_add(self, package_name: str, version: str | None, dev: bool, result: OperationResult):
        """Record package add operation."""
        self.record_package_operation("add", package_name, version, dev, result.duration, result.success)

    def record_remove(self, package_name: str, result: OperationResult):
        """Record package remove operation."""
        self.record_package_operation("remove", package_name, None, False, result.duration, result.success)


class BuildMetrics(BaseMetrics):
    """Metrics for build operations."""

    def __init__(self):
        super().__init__("build")

    def _init_metrics(self):
        super()._init_metrics()
        # Build-specific metrics
        self.artifact_size = metric_histogram("build.artifact_size", unit="By")
        self.builds_by_type = metric_counter("build.builds_by_type")

    def record_build_operation(
        self,
        build_type: str,
        duration: float,
        success: bool = True,
        artifact_size: int | None = None,
        output_path: str | None = None,
    ):
        """Record build-specific metrics."""
        attributes = {
            BuildAttributes.TYPE: build_type,
        }

        if output_path:
            attributes[BuildAttributes.OUTPUT_PATH] = output_path

        self.record_operation(build_type, duration, success, attributes)

        if success:
            self.builds_by_type(1, **attributes)
            if artifact_size:
                self.artifact_size(artifact_size, **attributes)
                attributes[BuildAttributes.SIZE] = str(artifact_size)

    def record_wheel(self, artifact_size: int, output_path: str, result: OperationResult):
        """Record wheel build operation."""
        self.record_build_operation("wheel", result.duration, result.success, artifact_size, output_path)

    def record_exe(self, artifact_size: int, platform: str, result: OperationResult):
        """Record executable build operation."""
        self.record_build_operation("exe", result.duration, result.success, artifact_size)


class TestMetrics(BaseMetrics):
    """Metrics for test operations."""

    def __init__(self):
        super().__init__("test")

    def _init_metrics(self):
        super()._init_metrics()
        # Test-specific metrics
        self.tests_passed = metric_counter("test.tests_passed")
        self.tests_failed = metric_counter("test.tests_failed")
        self.tests_skipped = metric_counter("test.tests_skipped")
        self.coverage_percentage = metric_histogram("test.coverage_percentage", unit="%")

    def record_test_operation(
        self,
        operation: str,
        duration: float,
        passed: int = 0,
        failed: int = 0,
        skipped: int = 0,
        coverage: float | None = None,
        framework: str = "pytest",
    ):
        """Record test-specific metrics."""
        attributes = {
            TestAttributes.OPERATION: operation,
            TestAttributes.FRAMEWORK: framework,
            TestAttributes.TEST_COUNT: str(passed + failed + skipped),
            TestAttributes.PASSED: str(passed),
            TestAttributes.FAILED: str(failed),
            TestAttributes.SKIPPED: str(skipped),
        }

        success = failed == 0
        self.record_operation(operation, duration, success, attributes)

        # Update specific counters
        if passed > 0:
            self.tests_passed(passed, **attributes)
        if failed > 0:
            self.tests_failed(failed, **attributes)
        if skipped > 0:
            self.tests_skipped(skipped, **attributes)

        if coverage is not None:
            self.coverage_percentage(coverage, **attributes)
            attributes[TestAttributes.COVERAGE_PERCENTAGE] = str(coverage)


class AiMetrics(BaseMetrics):
    """Metrics for AI operations."""

    def __init__(self):
        super().__init__("ai")

    def _init_metrics(self):
        super()._init_metrics()
        # AI-specific metrics
        self.tokens_input = metric_histogram("ai.tokens_input", unit="1")
        self.tokens_output = metric_histogram("ai.tokens_output", unit="1")
        self.ai_cost = metric_histogram("ai.cost", unit="$")
        self.model_calls = metric_counter("ai.model_calls")

    def record_ai_operation(
        self,
        operation: str,
        model: str,
        provider: str = "ollama",
        duration: float = 0.0,
        success: bool = True,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost: float | None = None,
    ):
        """Record AI-specific metrics."""
        attributes = {
            AIAttributes.OPERATION: operation,
            AIAttributes.MODEL: model,
            AIAttributes.PROVIDER: provider,
        }

        self.record_operation(operation, duration, success, attributes)

        if success:
            self.model_calls(1, **attributes)

            if input_tokens:
                self.tokens_input(input_tokens, **attributes)
                attributes[AIAttributes.TOKENS_INPUT] = str(input_tokens)

            if output_tokens:
                self.tokens_output(output_tokens, **attributes)
                attributes[AIAttributes.TOKENS_OUTPUT] = str(output_tokens)

            if cost:
                self.ai_cost(cost, **attributes)
                attributes[AIAttributes.COST] = str(cost)

    def record_completion(self, model: str, provider: str, input_tokens: int, output_tokens: int, cost: float, result: OperationResult):
        """Record AI completion operation."""
        self.record_ai_operation("completion", model, provider, result.duration, result.success, input_tokens, output_tokens, cost)


class ProcessMetrics(BaseMetrics):
    """Metrics for process execution."""

    def __init__(self):
        super().__init__("process")

    def _init_metrics(self):
        super()._init_metrics()
        # Process-specific metrics
        self.exit_codes = metric_histogram("process.exit_codes", unit="1")
        self.process_by_executable = metric_counter("process.by_executable")

    def record_process_operation(
        self,
        command: str,
        executable: str,
        duration: float,
        exit_code: int = 0,
        working_directory: str | None = None,
    ):
        """Record process-specific metrics."""
        attributes = {
            ProcessAttributes.COMMAND: command,
            ProcessAttributes.EXECUTABLE: executable,
            ProcessAttributes.EXIT_CODE: str(exit_code),
        }

        if working_directory:
            attributes[ProcessAttributes.WORKING_DIRECTORY] = working_directory

        success = exit_code == 0
        self.record_operation(executable, duration, success, attributes)

        # Update specific metrics
        self.exit_codes(exit_code, **attributes)
        self.process_by_executable(1, **attributes)


class ProjectMetrics(BaseMetrics):
    """Metrics for project scaffolding operations."""

    def __init__(self):
        super().__init__("project")

    def _init_metrics(self):
        super()._init_metrics()
        # Project-specific metrics
        self.templates_used = metric_counter("project.templates_used")
        self.projects_created = metric_counter("project.projects_created")

    def record_project_operation(
        self,
        operation: str,
        template_name: str | None = None,
        duration: float = 0.0,
        success: bool = True,
    ):
        """Record project-specific metrics."""
        attributes = {"operation": operation}
        
        if template_name:
            attributes["template_name"] = template_name

        self.record_operation(operation, duration, success, attributes)

        if success:
            if operation == "create":
                self.projects_created(1, **attributes)
            if template_name:
                self.templates_used(1, **attributes)

    def record_creation(
        self,
        name: str,
        template: str,
        files_created: int,
        result: OperationResult,
    ):
        """Record project creation metrics."""
        attributes = {
            "template": template,
            "files_created": files_created,
            "success": result.success,
        }
        
        self.record_operation("create", result.duration, result.success, attributes)
        
        if result.success:
            self.projects_created(1, **attributes)
            self.templates_used(1, template=template)
            
            # Record files created
            metric_histogram("project.files_created")(files_created, **attributes)
            
        # Record any error information
        if result.error:
            metric_counter("project.creation_errors")(1, error_type=type(result.error).__name__)


# Global metric instances
package_metrics = PackageMetrics()
build_metrics = BuildMetrics()
test_metrics = TestMetrics()
ai_metrics = AiMetrics()
process_metrics = ProcessMetrics()
project_metrics = ProjectMetrics()
