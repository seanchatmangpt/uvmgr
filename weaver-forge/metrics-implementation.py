"""
Example metrics implementation for uvmgr operations.
Shows how to implement comprehensive metrics following OTEL patterns.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .enhanced_telemetry_core import metric_counter, metric_gauge, metric_histogram


@dataclass
class OperationResult:
    """Result of an operation with metrics data."""

    success: bool
    duration: float
    error: Exception | None = None
    metadata: dict[str, Any] = None


class BaseMetrics(ABC):
    """Base class for operation-specific metrics."""

    def __init__(self, namespace: str):
        self.namespace = namespace

    @abstractmethod
    def record_operation(self, operation: str, result: OperationResult):
        """Record metrics for an operation."""

    def _base_attributes(self, operation: str, result: OperationResult) -> dict[str, Any]:
        """Get base attributes for all metrics."""
        attrs = {
            "operation": operation,
            "namespace": self.namespace,
            "success": str(result.success),
        }
        if result.error:
            attrs["error_type"] = type(result.error).__name__
        return attrs


class DependencyMetrics(BaseMetrics):
    """Metrics for dependency management operations."""

    def __init__(self):
        super().__init__("deps")

    def record_operation(self, operation: str, result: OperationResult):
        """Record dependency operation metrics."""
        attrs = self._base_attributes(operation, result)

        # Add dependency-specific attributes
        if result.metadata:
            if "package_name" in result.metadata:
                attrs["package.name"] = result.metadata["package_name"]
            if "package_version" in result.metadata:
                attrs["package.version"] = result.metadata["package_version"]
            if "dev" in result.metadata:
                attrs["package.dev"] = str(result.metadata["dev"])

        # Record metrics
        metric_counter(f"{self.namespace}.operations", 1, attrs)
        metric_histogram(f"{self.namespace}.duration", result.duration, attrs)

        if not result.success:
            metric_counter(f"{self.namespace}.errors", 1, attrs)

    def record_add(self, package: str, version: str | None, dev: bool, result: OperationResult):
        """Record package add operation."""
        result.metadata = {
            "package_name": package,
            "package_version": version or "latest",
            "dev": dev,
        }
        self.record_operation("add", result)

        # Track total packages
        if result.success:
            metric_gauge("deps.total_packages", 1, {"type": "dev" if dev else "prod"})

    def record_remove(self, package: str, result: OperationResult):
        """Record package remove operation."""
        result.metadata = {"package_name": package}
        self.record_operation("remove", result)

        # Track total packages
        if result.success:
            metric_gauge("deps.total_packages", -1, {"type": "unknown"})

    def record_list(self, package_count: int, dev_count: int, result: OperationResult):
        """Record package list operation."""
        result.metadata = {
            "total_count": package_count,
            "dev_count": dev_count,
            "prod_count": package_count - dev_count,
        }
        self.record_operation("list", result)

        # Update package counts
        metric_gauge("deps.total_packages", package_count - dev_count, {"type": "prod"})
        metric_gauge("deps.total_packages", dev_count, {"type": "dev"})

    def record_lock(self, packages_locked: int, result: OperationResult):
        """Record dependency lock operation."""
        result.metadata = {"packages_locked": packages_locked}
        self.record_operation("lock", result)

        if result.success:
            metric_histogram("deps.lock_size", packages_locked)


class BuildMetrics(BaseMetrics):
    """Metrics for build operations."""

    def __init__(self):
        super().__init__("build")

    def record_operation(self, operation: str, result: OperationResult):
        """Record build operation metrics."""
        attrs = self._base_attributes(operation, result)

        # Add build-specific attributes
        if result.metadata:
            if "artifact_type" in result.metadata:
                attrs["build.type"] = result.metadata["artifact_type"]
            if "artifact_size" in result.metadata:
                attrs["build.size_category"] = self._categorize_size(result.metadata["artifact_size"])

        # Record metrics
        metric_counter(f"{self.namespace}.operations", 1, attrs)
        metric_histogram(f"{self.namespace}.duration", result.duration, attrs)

        if not result.success:
            metric_counter(f"{self.namespace}.errors", 1, attrs)

    def record_wheel(self, size: int, output_path: str, result: OperationResult):
        """Record wheel build metrics."""
        result.metadata = {
            "artifact_type": "wheel",
            "artifact_size": size,
            "output_path": output_path,
        }
        self.record_operation("wheel", result)

        if result.success:
            metric_histogram("build.artifact_size", size, {"type": "wheel"})
            metric_counter("build.artifacts_created", 1, {"type": "wheel"})

    def record_sdist(self, size: int, output_path: str, result: OperationResult):
        """Record sdist build metrics."""
        result.metadata = {
            "artifact_type": "sdist",
            "artifact_size": size,
            "output_path": output_path,
        }
        self.record_operation("sdist", result)

        if result.success:
            metric_histogram("build.artifact_size", size, {"type": "sdist"})
            metric_counter("build.artifacts_created", 1, {"type": "sdist"})

    def record_exe(self, size: int, platform: str, result: OperationResult):
        """Record executable build metrics."""
        result.metadata = {
            "artifact_type": "exe",
            "artifact_size": size,
            "platform": platform,
        }
        self.record_operation("exe", result)

        if result.success:
            metric_histogram("build.artifact_size", size, {"type": "exe", "platform": platform})
            metric_counter("build.artifacts_created", 1, {"type": "exe"})

    @staticmethod
    def _categorize_size(size_bytes: int) -> str:
        """Categorize file size for metrics."""
        mb = size_bytes / (1024 * 1024)
        if mb < 1:
            return "small"
        if mb < 10:
            return "medium"
        if mb < 100:
            return "large"
        return "xlarge"


class TestMetrics(BaseMetrics):
    """Metrics for test operations."""

    def __init__(self):
        super().__init__("test")

    def record_operation(self, operation: str, result: OperationResult):
        """Record test operation metrics."""
        attrs = self._base_attributes(operation, result)

        # Add test-specific attributes
        if result.metadata:
            if "framework" in result.metadata:
                attrs["test.framework"] = result.metadata["framework"]
            if "test_count" in result.metadata:
                attrs["test.count_category"] = self._categorize_count(result.metadata["test_count"])

        # Record metrics
        metric_counter(f"{self.namespace}.operations", 1, attrs)
        metric_histogram(f"{self.namespace}.duration", result.duration, attrs)

        if not result.success:
            metric_counter(f"{self.namespace}.errors", 1, attrs)

    def record_run(self, passed: int, failed: int, skipped: int, duration: float, result: OperationResult):
        """Record test run metrics."""
        total = passed + failed + skipped
        result.metadata = {
            "framework": "pytest",
            "test_count": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        }
        self.record_operation("run", result)

        # Record test results
        metric_counter("test.results", passed, {"status": "passed", "framework": "pytest"})
        metric_counter("test.results", failed, {"status": "failed", "framework": "pytest"})
        metric_counter("test.results", skipped, {"status": "skipped", "framework": "pytest"})

        # Record performance metrics
        if total > 0:
            metric_histogram("test.per_test_duration", duration / total, {"framework": "pytest"})

        # Track failure rate
        if total > 0:
            failure_rate = (failed / total) * 100
            metric_gauge("test.failure_rate", failure_rate, {"framework": "pytest"})

    def record_coverage(self, coverage_percent: float, lines_covered: int, lines_total: int, result: OperationResult):
        """Record coverage metrics."""
        result.metadata = {
            "coverage_percent": coverage_percent,
            "lines_covered": lines_covered,
            "lines_total": lines_total,
        }
        self.record_operation("coverage", result)

        if result.success:
            metric_gauge("test.coverage_percent", coverage_percent)
            metric_gauge("test.lines_covered", lines_covered)
            metric_gauge("test.lines_total", lines_total)

            # Track coverage trend
            metric_histogram("test.coverage_history", coverage_percent)

    @staticmethod
    def _categorize_count(count: int) -> str:
        """Categorize test count for metrics."""
        if count < 10:
            return "small"
        if count < 100:
            return "medium"
        if count < 1000:
            return "large"
        return "xlarge"


class AIMetrics(BaseMetrics):
    """Metrics for AI operations."""

    def __init__(self):
        super().__init__("ai")

    def record_operation(self, operation: str, result: OperationResult):
        """Record AI operation metrics."""
        attrs = self._base_attributes(operation, result)

        # Add AI-specific attributes
        if result.metadata:
            if "model" in result.metadata:
                attrs["ai.model"] = result.metadata["model"]
            if "provider" in result.metadata:
                attrs["ai.provider"] = result.metadata["provider"]

        # Record metrics
        metric_counter(f"{self.namespace}.operations", 1, attrs)
        metric_histogram(f"{self.namespace}.duration", result.duration, attrs)

        if not result.success:
            metric_counter(f"{self.namespace}.errors", 1, attrs)

    def record_completion(
        self,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        result: OperationResult
    ):
        """Record AI completion metrics."""
        result.metadata = {
            "model": model,
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
        }
        self.record_operation("completion", result)

        if result.success:
            # Token usage
            metric_histogram("ai.tokens", input_tokens, {"type": "input", "model": model})
            metric_histogram("ai.tokens", output_tokens, {"type": "output", "model": model})
            metric_counter("ai.total_tokens", input_tokens + output_tokens, {"model": model})

            # Cost tracking
            metric_histogram("ai.cost", cost, {"model": model, "provider": provider})
            metric_counter("ai.total_cost", cost, {"provider": provider})

            # Performance metrics
            if input_tokens > 0:
                tokens_per_second = (input_tokens + output_tokens) / result.duration
                metric_histogram("ai.tokens_per_second", tokens_per_second, {"model": model})


class ProcessMetrics(BaseMetrics):
    """Metrics for subprocess execution."""

    def __init__(self):
        super().__init__("process")

    def record_execution(
        self,
        command: str,
        executable: str,
        exit_code: int,
        duration: float,
        stdout_size: int,
        stderr_size: int
    ):
        """Record process execution metrics."""
        success = exit_code == 0
        result = OperationResult(
            success=success,
            duration=duration,
            metadata={
                "command": command,
                "executable": executable,
                "exit_code": exit_code,
                "stdout_size": stdout_size,
                "stderr_size": stderr_size,
            }
        )

        attrs = self._base_attributes("execute", result)
        attrs["process.executable"] = executable
        attrs["process.exit_code"] = str(exit_code)

        # Record metrics
        metric_counter("process.executions", 1, attrs)
        metric_histogram("process.duration", duration, attrs)

        if not success:
            metric_counter("process.failures", 1, attrs)

        # I/O metrics
        metric_histogram("process.output_size", stdout_size + stderr_size, {"executable": executable})

        # Track common executables
        if executable in ["python", "uv", "git", "npm", "pytest"]:
            metric_counter(f"process.{executable}_calls", 1, {"success": str(success)})


# Global metric instances
dependency_metrics = DependencyMetrics()
build_metrics = BuildMetrics()
test_metrics = TestMetrics()
ai_metrics = AIMetrics()
process_metrics = ProcessMetrics()


# Example usage in operations
def example_deps_add_with_metrics(package: str, dev: bool = False):
    """Example of how to use metrics in operations."""
    start_time = time.time()

    try:
        # Actual operation would go here
        # result = add_dependency(package, dev)

        # Record success
        result = OperationResult(
            success=True,
            duration=time.time() - start_time,
        )
        dependency_metrics.record_add(package, None, dev, result)

    except Exception as e:
        # Record failure
        result = OperationResult(
            success=False,
            duration=time.time() - start_time,
            error=e,
        )
        dependency_metrics.record_add(package, None, dev, result)
        raise


# Health check metrics
def record_health_metrics():
    """Record system health metrics."""
    import psutil

    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    metric_gauge("system.cpu_percent", cpu_percent)

    # Memory usage
    memory = psutil.virtual_memory()
    metric_gauge("system.memory_percent", memory.percent)
    metric_gauge("system.memory_available", memory.available, {"unit": "bytes"})

    # Disk usage
    disk = psutil.disk_usage("/")
    metric_gauge("system.disk_percent", disk.percent)
    metric_gauge("system.disk_free", disk.free, {"unit": "bytes"})

    # Process info
    process = psutil.Process()
    metric_gauge("process.memory_rss", process.memory_info().rss, {"unit": "bytes"})
    metric_gauge("process.cpu_percent", process.cpu_percent())
    metric_gauge("process.num_threads", process.num_threads())
    metric_gauge("process.open_files", len(process.open_files()))
