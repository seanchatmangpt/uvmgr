#!/usr/bin/env python3
"""
OTEL Performance Claim Validator
===============================

Validates ALL performance claims about uvmgr through actual OpenTelemetry
metrics and traces. No hardcoded values - only real telemetry data.

Performance Claims to Verify:
- Command startup: < 0.5s for help/version
- Deps list: < 2s for typical project  
- Single test: < 3s overhead
- Build wheel: < 5s for simple project
- Cache speedup: > 10% improvement
"""

import json
import statistics
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import subprocess
import tempfile

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode


@dataclass
class PerformanceBenchmark:
    """Represents a performance benchmark with OTEL evidence."""
    name: str
    description: str
    claimed_threshold: float  # Maximum allowed time in seconds
    measured_times: List[float]  # Actual measured times
    mean_time: float
    median_time: float
    p95_time: float
    min_time: float
    max_time: float
    success_rate: float  # Percentage of runs that succeeded
    threshold_met: bool
    performance_ratio: float  # actual_time / threshold (< 1.0 is good)
    evidence_spans: List[str]
    otel_metrics: Dict[str, Any]
    
    def __post_init__(self):
        if self.measured_times:
            self.mean_time = statistics.mean(self.measured_times)
            self.median_time = statistics.median(self.measured_times)
            self.p95_time = statistics.quantiles(self.measured_times, n=20)[18] if len(self.measured_times) >= 20 else max(self.measured_times)
            self.min_time = min(self.measured_times)
            self.max_time = max(self.measured_times)
            self.performance_ratio = self.mean_time / self.claimed_threshold
            self.threshold_met = self.mean_time <= self.claimed_threshold
        else:
            self.mean_time = float('inf')
            self.threshold_met = False
            self.performance_ratio = float('inf')


class OTELPerformanceValidator:
    """Validates performance claims through OpenTelemetry measurement."""
    
    def __init__(self, collector_endpoint: str = "http://localhost:4317"):
        self.collector_endpoint = collector_endpoint
        self.benchmarks: List[PerformanceBenchmark] = []
        
        # Performance thresholds from claims
        self.performance_claims = {
            "command_startup": {
                "description": "Command startup time for help/version",
                "threshold": 0.5,  # 500ms
                "commands": [
                    ["uvmgr", "--help"],
                    ["uvmgr", "--version"],
                    ["uvmgr", "deps", "--help"],
                    ["uvmgr", "tests", "--help"]
                ],
                "runs": 10
            },
            "deps_list": {
                "description": "Dependencies list for typical project",
                "threshold": 2.0,  # 2 seconds
                "commands": [
                    ["uvmgr", "deps", "list"]
                ],
                "runs": 5,
                "setup_required": True
            },
            "test_overhead": {
                "description": "Test execution overhead vs direct pytest",
                "threshold": 1.5,  # 50% overhead maximum
                "commands": [
                    ["uvmgr", "tests", "run"],
                    ["pytest"]  # Direct comparison
                ],
                "runs": 3,
                "setup_required": True,
                "comparison": True
            },
            "build_simple": {
                "description": "Build wheel for simple project",
                "threshold": 5.0,  # 5 seconds
                "commands": [
                    ["uvmgr", "build", "dist"]
                ],
                "runs": 3,
                "setup_required": True
            },
            "cache_speedup": {
                "description": "Cache speedup comparison (cold vs warm)",
                "threshold": 0.9,  # 10% improvement minimum (ratio < 0.9)
                "commands": [
                    ["uvmgr", "deps", "list"]  # Run twice for cache comparison
                ],
                "runs": 5,
                "setup_required": True,
                "cache_test": True
            }
        }
        
        self._setup_otel()
    
    def _setup_otel(self):
        """Set up OpenTelemetry for performance measurement."""
        resource = Resource.create({
            "service.name": "uvmgr-performance-validator",
            "service.version": "1.0.0",
            "environment": "performance-testing",
            "validator.type": "performance"
        })
        
        # Tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        self.tracer = trace.get_tracer(__name__)
        
        otlp_exporter = OTLPSpanExporter(endpoint=self.collector_endpoint, insecure=True)
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Metrics
        otlp_metric_exporter = OTLPMetricExporter(endpoint=self.collector_endpoint, insecure=True)
        metrics.set_meter_provider(MeterProvider(
            resource=resource,
            metric_readers=[PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=5000)]
        ))
        
        self.meter = metrics.get_meter(__name__)
        
        # Performance metrics
        self.command_duration_histogram = self.meter.create_histogram(
            "uvmgr_performance_command_duration_seconds",
            description="Command execution duration for performance testing",
            unit="s"
        )
        
        self.performance_ratio_gauge = self.meter.create_gauge(
            "uvmgr_performance_threshold_ratio",
            description="Performance ratio vs claimed thresholds"
        )
        
        self.benchmark_counter = self.meter.create_counter(
            "uvmgr_performance_benchmarks_total",
            description="Total performance benchmarks executed"
        )
        
        print("🔧 OTEL Performance Validator initialized")
    
    def measure_command_performance(self, command: List[str], runs: int = 5, 
                                  cwd: Optional[Path] = None) -> Tuple[List[float], float]:
        """Measure command performance with OTEL instrumentation."""
        
        cmd_name = "_".join(command[:2]) if len(command) >= 2 else command[0]
        
        with self.tracer.start_as_current_span(f"benchmark_command.{cmd_name}") as span:
            span.set_attribute("command.name", command[0])
            span.set_attribute("command.args", " ".join(command))
            span.set_attribute("benchmark.runs", runs)
            span.set_attribute("benchmark.cwd", str(cwd) if cwd else "")
            
            execution_times = []
            successful_runs = 0
            
            for run_number in range(runs):
                with self.tracer.start_as_current_span(f"command_run.{run_number}") as run_span:
                    run_span.set_attribute("run.number", run_number)
                    
                    start_time = time.time()
                    
                    try:
                        result = subprocess.run(
                            command,
                            cwd=cwd,
                            capture_output=True,
                            text=True,
                            timeout=30  # 30s timeout for performance tests
                        )
                        
                        execution_time = time.time() - start_time
                        
                        run_span.set_attribute("run.duration", execution_time)
                        run_span.set_attribute("run.returncode", result.returncode)
                        run_span.set_attribute("run.success", result.returncode == 0)
                        
                        if result.returncode == 0:
                            execution_times.append(execution_time)
                            successful_runs += 1
                            
                            # Record metric
                            self.command_duration_histogram.record(
                                execution_time,
                                {"command": cmd_name, "run": str(run_number), "status": "success"}
                            )
                        else:
                            run_span.set_status(Status(StatusCode.ERROR, f"Command failed: {result.returncode}"))
                            self.command_duration_histogram.record(
                                execution_time,
                                {"command": cmd_name, "run": str(run_number), "status": "error"}
                            )
                    
                    except subprocess.TimeoutExpired:
                        execution_time = time.time() - start_time
                        run_span.set_attribute("run.timeout", True)
                        run_span.set_attribute("run.duration", execution_time)
                        run_span.set_status(Status(StatusCode.ERROR, "Command timeout"))
                    
                    except Exception as e:
                        execution_time = time.time() - start_time
                        run_span.record_exception(e)
                        run_span.set_status(Status(StatusCode.ERROR, str(e)))
            
            success_rate = successful_runs / runs if runs > 0 else 0
            
            span.set_attribute("benchmark.successful_runs", successful_runs)
            span.set_attribute("benchmark.success_rate", success_rate)
            
            if execution_times:
                mean_time = statistics.mean(execution_times)
                span.set_attribute("benchmark.mean_duration", mean_time)
                span.set_attribute("benchmark.min_duration", min(execution_times))
                span.set_attribute("benchmark.max_duration", max(execution_times))
                
                self.benchmark_counter.add(1, {"command": cmd_name, "status": "completed"})
            else:
                span.set_status(Status(StatusCode.ERROR, "No successful runs"))
                self.benchmark_counter.add(1, {"command": cmd_name, "status": "failed"})
            
            return execution_times, success_rate
    
    def setup_test_project(self, workspace: Path) -> Path:
        """Set up a test project for performance testing."""
        
        with self.tracer.start_as_current_span("setup_test_project") as span:
            project_dir = workspace / "performance-test-project"
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a simple but realistic Python project
            pyproject_content = '''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "performance-test"
version = "0.1.0"
description = "Performance testing project"
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0"
]

[project.scripts]
perf-test = "performance_test.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=performance_test"
'''
            
            (project_dir / "pyproject.toml").write_text(pyproject_content)
            
            # Create source structure
            src_dir = project_dir / "src" / "performance_test"
            src_dir.mkdir(parents=True, exist_ok=True)
            
            (src_dir / "__init__.py").write_text('"""Performance test package."""\n__version__ = "0.1.0"')
            
            # CLI module
            cli_content = '''"""CLI for performance test package."""
import click
import requests

@click.command()
@click.option('--count', default=1, help='Number of iterations')
def main(count):
    """Main CLI function."""
    for i in range(count):
        click.echo(f"Iteration {i+1}")
        # Simulate some work
        response = requests.get('https://httpbin.org/get', timeout=1)
        click.echo(f"Status: {response.status_code}")

if __name__ == "__main__":
    main()
'''
            (src_dir / "cli.py").write_text(cli_content)
            
            # Core module
            core_content = '''"""Core functionality."""

def calculate_fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(data):
    """Process some data."""
    return [x * 2 for x in data if x > 0]

class DataProcessor:
    """Data processing class."""
    
    def __init__(self):
        self.data = []
    
    def add_data(self, item):
        """Add data item."""
        self.data.append(item)
    
    def process_all(self):
        """Process all data."""
        return process_data(self.data)
'''
            (src_dir / "core.py").write_text(core_content)
            
            # Tests
            tests_dir = project_dir / "tests"
            tests_dir.mkdir(exist_ok=True)
            
            test_content = '''"""Tests for performance test package."""
import pytest
from performance_test.core import calculate_fibonacci, DataProcessor

def test_fibonacci():
    """Test fibonacci calculation."""
    assert calculate_fibonacci(0) == 0
    assert calculate_fibonacci(1) == 1
    assert calculate_fibonacci(5) == 5

def test_data_processor():
    """Test data processor."""
    processor = DataProcessor()
    processor.add_data(1)
    processor.add_data(-1)
    processor.add_data(2)
    
    result = processor.process_all()
    assert result == [2, 4]

def test_slow_operation():
    """Test that takes some time."""
    import time
    time.sleep(0.1)  # 100ms
    assert True

@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_parametrized(n):
    """Parametrized test."""
    assert n > 0
'''
            (tests_dir / "test_core.py").write_text(test_content)
            (tests_dir / "__init__.py").write_text("")
            
            # README
            readme_content = """# Performance Test Project

Test project for uvmgr performance validation.

## Commands

```bash
# Install dependencies
uvmgr deps add pytest --dev

# Run tests  
uvmgr tests run

# Build package
uvmgr build dist

# Run CLI
python -m performance_test.cli --count 3
```
"""
            (project_dir / "README.md").write_text(readme_content)
            
            span.set_attribute("project.path", str(project_dir))
            span.set_attribute("project.files_created", len(list(project_dir.rglob("*"))))
            
            print(f"📦 Test project created: {project_dir}")
            
            return project_dir
    
    def validate_command_startup_performance(self, workspace: Path) -> PerformanceBenchmark:
        """Validate command startup performance claims."""
        
        claim = self.performance_claims["command_startup"]
        
        with self.tracer.start_as_current_span("validate_command_startup") as span:
            span.set_attribute("claim.description", claim["description"])
            span.set_attribute("claim.threshold", claim["threshold"])
            
            all_times = []
            span_names = []
            
            for command in claim["commands"]:
                times, success_rate = self.measure_command_performance(
                    command, runs=claim["runs"]
                )
                all_times.extend(times)
                span_names.append(f"command_startup.{command[0]}_{command[1] if len(command) > 1 else 'base'}")
            
            benchmark = PerformanceBenchmark(
                name="command_startup",
                description=claim["description"],
                claimed_threshold=claim["threshold"],
                measured_times=all_times,
                mean_time=0.0,  # Will be calculated in __post_init__
                median_time=0.0,
                p95_time=0.0,
                min_time=0.0,
                max_time=0.0,
                success_rate=success_rate,
                threshold_met=False,  # Will be calculated
                performance_ratio=0.0,
                evidence_spans=span_names,
                otel_metrics={}
            )
            
            # Record performance ratio
            self.performance_ratio_gauge.set(
                benchmark.performance_ratio,
                {"benchmark": "command_startup"}
            )
            
            span.set_attribute("benchmark.mean_time", benchmark.mean_time)
            span.set_attribute("benchmark.threshold_met", benchmark.threshold_met)
            span.set_attribute("benchmark.performance_ratio", benchmark.performance_ratio)
            
            return benchmark
    
    def validate_deps_list_performance(self, project_dir: Path) -> PerformanceBenchmark:
        """Validate deps list performance claims."""
        
        claim = self.performance_claims["deps_list"]
        
        with self.tracer.start_as_current_span("validate_deps_list") as span:
            span.set_attribute("claim.description", claim["description"])
            span.set_attribute("claim.threshold", claim["threshold"])
            span.set_attribute("project.path", str(project_dir))
            
            # First install uvmgr in the project
            with self.tracer.start_as_current_span("setup_uvmgr") as setup_span:
                auto_install_script = Path(__file__).parent / "auto-install-uvmgr.sh"
                if auto_install_script.exists():
                    subprocess.run(
                        ["bash", str(auto_install_script), str(project_dir)],
                        capture_output=True, timeout=120
                    )
                    setup_span.set_attribute("uvmgr.installed", True)
                else:
                    setup_span.set_attribute("uvmgr.installed", False)
            
            times, success_rate = self.measure_command_performance(
                claim["commands"][0], runs=claim["runs"], cwd=project_dir
            )
            
            benchmark = PerformanceBenchmark(
                name="deps_list",
                description=claim["description"],
                claimed_threshold=claim["threshold"],
                measured_times=times,
                mean_time=0.0,
                median_time=0.0,
                p95_time=0.0,
                min_time=0.0,
                max_time=0.0,
                success_rate=success_rate,
                threshold_met=False,
                performance_ratio=0.0,
                evidence_spans=["validate_deps_list"],
                otel_metrics={}
            )
            
            self.performance_ratio_gauge.set(
                benchmark.performance_ratio,
                {"benchmark": "deps_list"}
            )
            
            span.set_attribute("benchmark.mean_time", benchmark.mean_time)
            span.set_attribute("benchmark.threshold_met", benchmark.threshold_met)
            
            return benchmark
    
    def validate_test_overhead_performance(self, project_dir: Path) -> PerformanceBenchmark:
        """Validate test execution overhead claims."""
        
        claim = self.performance_claims["test_overhead"]
        
        with self.tracer.start_as_current_span("validate_test_overhead") as span:
            span.set_attribute("claim.description", claim["description"])
            span.set_attribute("claim.threshold", claim["threshold"])
            
            # Measure uvmgr tests run
            uvmgr_times, uvmgr_success = self.measure_command_performance(
                ["uvmgr", "tests", "run"], runs=claim["runs"], cwd=project_dir
            )
            
            # Measure direct pytest
            pytest_times, pytest_success = self.measure_command_performance(
                ["pytest"], runs=claim["runs"], cwd=project_dir
            )
            
            # Calculate overhead ratio
            if pytest_times and uvmgr_times:
                uvmgr_mean = statistics.mean(uvmgr_times)
                pytest_mean = statistics.mean(pytest_times)
                overhead_ratio = uvmgr_mean / pytest_mean
                
                span.set_attribute("uvmgr.mean_time", uvmgr_mean)
                span.set_attribute("pytest.mean_time", pytest_mean)
                span.set_attribute("overhead.ratio", overhead_ratio)
                
                # For overhead test, threshold is the maximum allowed ratio
                threshold_met = overhead_ratio <= claim["threshold"]
                
                benchmark = PerformanceBenchmark(
                    name="test_overhead",
                    description=claim["description"],
                    claimed_threshold=claim["threshold"],
                    measured_times=[overhead_ratio],  # Store ratio instead of times
                    mean_time=overhead_ratio,
                    median_time=overhead_ratio,
                    p95_time=overhead_ratio,
                    min_time=overhead_ratio,
                    max_time=overhead_ratio,
                    success_rate=min(uvmgr_success, pytest_success),
                    threshold_met=threshold_met,
                    performance_ratio=overhead_ratio / claim["threshold"],
                    evidence_spans=["validate_test_overhead"],
                    otel_metrics={
                        "uvmgr_times": uvmgr_times,
                        "pytest_times": pytest_times
                    }
                )
            else:
                # If we couldn't measure, create a failed benchmark
                benchmark = PerformanceBenchmark(
                    name="test_overhead",
                    description=claim["description"],
                    claimed_threshold=claim["threshold"],
                    measured_times=[],
                    mean_time=float('inf'),
                    median_time=float('inf'),
                    p95_time=float('inf'),
                    min_time=float('inf'),
                    max_time=float('inf'),
                    success_rate=0.0,
                    threshold_met=False,
                    performance_ratio=float('inf'),
                    evidence_spans=["validate_test_overhead"],
                    otel_metrics={}
                )
            
            self.performance_ratio_gauge.set(
                benchmark.performance_ratio,
                {"benchmark": "test_overhead"}
            )
            
            return benchmark
    
    def validate_build_performance(self, project_dir: Path) -> PerformanceBenchmark:
        """Validate build performance claims."""
        
        claim = self.performance_claims["build_simple"]
        
        with self.tracer.start_as_current_span("validate_build_performance") as span:
            span.set_attribute("claim.description", claim["description"])
            span.set_attribute("claim.threshold", claim["threshold"])
            
            times, success_rate = self.measure_command_performance(
                claim["commands"][0], runs=claim["runs"], cwd=project_dir
            )
            
            benchmark = PerformanceBenchmark(
                name="build_simple",
                description=claim["description"],
                claimed_threshold=claim["threshold"],
                measured_times=times,
                mean_time=0.0,
                median_time=0.0,
                p95_time=0.0,
                min_time=0.0,
                max_time=0.0,
                success_rate=success_rate,
                threshold_met=False,
                performance_ratio=0.0,
                evidence_spans=["validate_build_performance"],
                otel_metrics={}
            )
            
            self.performance_ratio_gauge.set(
                benchmark.performance_ratio,
                {"benchmark": "build_simple"}
            )
            
            return benchmark
    
    def validate_cache_speedup_performance(self, project_dir: Path) -> PerformanceBenchmark:
        """Validate cache speedup claims."""
        
        claim = self.performance_claims["cache_speedup"]
        
        with self.tracer.start_as_current_span("validate_cache_speedup") as span:
            span.set_attribute("claim.description", claim["description"])
            span.set_attribute("claim.threshold", claim["threshold"])
            
            # Clear cache first
            cache_dir = project_dir / ".uvmgr_cache"
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
            
            # Cold run (no cache)
            cold_times, cold_success = self.measure_command_performance(
                claim["commands"][0], runs=claim["runs"], cwd=project_dir
            )
            
            # Warm runs (with cache)
            warm_times, warm_success = self.measure_command_performance(
                claim["commands"][0], runs=claim["runs"], cwd=project_dir
            )
            
            if cold_times and warm_times:
                cold_mean = statistics.mean(cold_times)
                warm_mean = statistics.mean(warm_times)
                speedup_ratio = warm_mean / cold_mean
                
                span.set_attribute("cold.mean_time", cold_mean)
                span.set_attribute("warm.mean_time", warm_mean)
                span.set_attribute("speedup.ratio", speedup_ratio)
                
                # For cache test, we want ratio < threshold (improvement)
                threshold_met = speedup_ratio <= claim["threshold"]
                
                benchmark = PerformanceBenchmark(
                    name="cache_speedup",
                    description=claim["description"],
                    claimed_threshold=claim["threshold"],
                    measured_times=[speedup_ratio],
                    mean_time=speedup_ratio,
                    median_time=speedup_ratio,
                    p95_time=speedup_ratio,
                    min_time=speedup_ratio,
                    max_time=speedup_ratio,
                    success_rate=min(cold_success, warm_success),
                    threshold_met=threshold_met,
                    performance_ratio=speedup_ratio / claim["threshold"],
                    evidence_spans=["validate_cache_speedup"],
                    otel_metrics={
                        "cold_times": cold_times,
                        "warm_times": warm_times
                    }
                )
            else:
                benchmark = PerformanceBenchmark(
                    name="cache_speedup",
                    description=claim["description"],
                    claimed_threshold=claim["threshold"],
                    measured_times=[],
                    mean_time=float('inf'),
                    median_time=float('inf'),
                    p95_time=float('inf'),
                    min_time=float('inf'),
                    max_time=float('inf'),
                    success_rate=0.0,
                    threshold_met=False,
                    performance_ratio=float('inf'),
                    evidence_spans=["validate_cache_speedup"],
                    otel_metrics={}
                )
            
            self.performance_ratio_gauge.set(
                benchmark.performance_ratio,
                {"benchmark": "cache_speedup"}
            )
            
            return benchmark
    
    def validate_all_performance_claims(self, workspace: Optional[Path] = None) -> Dict[str, Any]:
        """Validate all performance claims through OTEL measurement."""
        
        if workspace is None:
            workspace = Path(tempfile.mkdtemp(prefix="uvmgr-perf-test-"))
        
        with self.tracer.start_as_current_span("validate_all_performance_claims") as main_span:
            main_span.set_attribute("workspace", str(workspace))
            main_span.set_attribute("validation.start_time", time.time())
            
            print("🏃 OTEL Performance Validation")
            print("=" * 40)
            print("MEASURING ACTUAL PERFORMANCE - NO ASSUMPTIONS")
            print("=" * 40)
            
            # Set up test project
            project_dir = self.setup_test_project(workspace)
            
            # Run all performance validations
            validators = [
                ("command_startup", lambda: self.validate_command_startup_performance(workspace)),
                ("deps_list", lambda: self.validate_deps_list_performance(project_dir)),
                ("test_overhead", lambda: self.validate_test_overhead_performance(project_dir)),
                ("build_simple", lambda: self.validate_build_performance(project_dir)),
                ("cache_speedup", lambda: self.validate_cache_speedup_performance(project_dir))
            ]
            
            for benchmark_name, validator in validators:
                print(f"\n🧪 Validating: {benchmark_name}")
                
                try:
                    benchmark = validator()
                    self.benchmarks.append(benchmark)
                    
                    if benchmark.threshold_met:
                        print(f"✅ {benchmark.description}: PASS")
                        print(f"   📊 Mean: {benchmark.mean_time:.3f}s (threshold: {benchmark.claimed_threshold:.3f}s)")
                        print(f"   📊 Ratio: {benchmark.performance_ratio:.2f}")
                    else:
                        print(f"❌ {benchmark.description}: FAIL")
                        print(f"   📊 Mean: {benchmark.mean_time:.3f}s (threshold: {benchmark.claimed_threshold:.3f}s)")
                        print(f"   📊 Ratio: {benchmark.performance_ratio:.2f}")
                    
                    print(f"   📊 Success Rate: {benchmark.success_rate:.1%}")
                    
                except Exception as e:
                    print(f"💥 {benchmark_name}: ERROR - {e}")
                    main_span.record_exception(e)
            
            # Generate summary
            total_benchmarks = len(self.benchmarks)
            passed_benchmarks = sum(1 for b in self.benchmarks if b.threshold_met)
            
            summary = {
                "total_benchmarks": total_benchmarks,
                "passed_benchmarks": passed_benchmarks,
                "failed_benchmarks": total_benchmarks - passed_benchmarks,
                "success_rate": passed_benchmarks / total_benchmarks if total_benchmarks > 0 else 0,
                "overall_success": passed_benchmarks == total_benchmarks,
                "validation_timestamp": time.time(),
                "workspace": str(workspace),
                "collector_endpoint": self.collector_endpoint
            }
            
            main_span.set_attribute("summary.total_benchmarks", summary["total_benchmarks"])
            main_span.set_attribute("summary.passed_benchmarks", summary["passed_benchmarks"])
            main_span.set_attribute("summary.success_rate", summary["success_rate"])
            main_span.set_attribute("summary.overall_success", summary["overall_success"])
            
            print(f"\n📊 Performance Validation Summary")
            print(f"   Total Benchmarks: {total_benchmarks}")
            print(f"   Passed: {passed_benchmarks}")
            print(f"   Failed: {total_benchmarks - passed_benchmarks}")
            print(f"   Success Rate: {summary['success_rate']:.1%}")
            print(f"   Overall: {'✅ ALL PERFORMANCE CLAIMS VERIFIED' if summary['overall_success'] else '❌ SOME CLAIMS NOT MET'}")
            
            return {
                "summary": summary,
                "benchmarks": [asdict(b) for b in self.benchmarks],
                "performance_claims": self.performance_claims,
                "otel_metadata": {
                    "trace_id": format(main_span.get_span_context().trace_id, "032x"),
                    "collector_endpoint": self.collector_endpoint,
                    "measurement_method": "otel_instrumented"
                }
            }
    
    def save_performance_report(self, results: Dict[str, Any], output_path: Optional[Path] = None):
        """Save performance validation report."""
        
        if output_path is None:
            output_path = Path("otel-performance-validation-report.json")
        
        with self.tracer.start_as_current_span("save_performance_report") as span:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            span.set_attribute("report.path", str(output_path))
            span.set_attribute("report.size", output_path.stat().st_size)
            
            print(f"📄 Performance report saved: {output_path}")


def main():
    """Main performance validation entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate uvmgr performance claims through OTEL")
    parser.add_argument("--collector", default="http://localhost:4317",
                       help="OTEL collector endpoint")
    parser.add_argument("--workspace", type=Path,
                       help="Test workspace directory")
    parser.add_argument("--output", type=Path,
                       help="Output report path")
    
    args = parser.parse_args()
    
    try:
        validator = OTELPerformanceValidator(collector_endpoint=args.collector)
        results = validator.validate_all_performance_claims(workspace=args.workspace)
        validator.save_performance_report(results, output_path=args.output)
        
        success = results["summary"]["overall_success"]
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Performance validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()