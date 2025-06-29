"""
Performance Runtime Operations
==============================

This module provides performance profiling and optimization operations.
Implements the 80/20 principle: focuses on the most impactful performance
optimizations that provide 80% of the speed improvements.

Key Features:
- CPU profiling and analysis
- Memory usage tracking
- I/O performance monitoring
- Dependency resolution optimization
- Build time analysis
- Runtime bottleneck detection
- Performance regression testing
"""

from __future__ import annotations

import asyncio
import gc
import os
import psutil
import resource
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.process import run_logged
from uvmgr.core.semconv import PerformanceAttributes, PerformanceOperations
from uvmgr.core.telemetry import metric_counter, metric_histogram, span, record_exception


@dataclass
class PerformanceMetrics:
    """Performance measurement results."""
    operation: str
    duration: float
    cpu_usage: float
    memory_usage: int  # bytes
    peak_memory: int   # bytes
    io_read: int       # bytes
    io_write: int      # bytes
    context_switches: int
    timestamp: str


@dataclass
class ProfileResult:
    """Code profiling result."""
    function_name: str
    filename: str
    line_number: int
    calls: int
    total_time: float
    per_call_time: float
    cumulative_time: float
    percentage: float


@dataclass
class BottleneckAnalysis:
    """Performance bottleneck analysis."""
    category: str  # cpu, memory, io, network
    severity: str  # high, medium, low
    description: str
    recommendation: str
    potential_improvement: str


def get_system_info() -> Dict[str, Any]:
    """Get system performance information."""
    with span("performance.system_info"):
        try:
            # CPU information
            cpu_info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "cpu_percent": psutil.cpu_percent(interval=1, percpu=True),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percentage": memory.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percentage": swap.percent
            }
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percentage": (disk.used / disk.total) * 100,
                "io_counters": disk_io._asdict() if disk_io else None
            }
            
            # Network information
            network_io = psutil.net_io_counters()
            network_info = {
                "io_counters": network_io._asdict() if network_io else None,
                "connections": len(psutil.net_connections()) if hasattr(psutil, 'net_connections') else 0
            }
            
            return {
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "python": {
                    "version": sys.version,
                    "executable": sys.executable,
                    "platform": sys.platform
                }
            }
        except Exception as e:
            record_exception(e, attributes={"operation": "get_system_info"})
            return {}


@instrument_command("performance_profile_function")
def profile_function(func: "Callable", *args, duration: int = 10, **kwargs) -> ProfileResult:
    """Profile a function's performance."""
    import cProfile
    import pstats
    import io
    
    with span("performance.profile_function",
              **{PerformanceAttributes.OPERATION: PerformanceOperations.PROFILE,
                 "function.name": func.__name__}):
        
        # Create profiler
        profiler = cProfile.Profile()
        
        # Get initial resource usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        initial_cpu_time = process.cpu_times()
        
        start_time = time.time()
        
        try:
            # Run profiling
            profiler.enable()
            result = func(*args, **kwargs)
            profiler.disable()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Get final resource usage
            final_memory = process.memory_info().rss
            final_cpu_time = process.cpu_times()
            
            # Analyze profiling results
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative')
            
            # Get the top function stats
            stats = ps.get_stats_profile()
            func_stats = None
            
            for (filename, line_num, func_name), (calls, total_time, cumulative_time, callers) in stats.items():
                if func_name == func.__name__:
                    func_stats = (filename, line_num, func_name, calls, total_time, cumulative_time)
                    break
            
            if func_stats:
                filename, line_num, func_name, calls, total_time, cumulative_time = func_stats
                
                profile_result = ProfileResult(
                    function_name=func_name,
                    filename=filename,
                    line_number=line_num,
                    calls=calls,
                    total_time=total_time,
                    per_call_time=total_time / calls if calls > 0 else 0,
                    cumulative_time=cumulative_time,
                    percentage=(cumulative_time / duration) * 100 if duration > 0 else 0
                )
            else:
                profile_result = ProfileResult(
                    function_name=func.__name__,
                    filename="unknown",
                    line_number=0,
                    calls=1,
                    total_time=duration,
                    per_call_time=duration,
                    cumulative_time=duration,
                    percentage=100.0
                )
            
            # Record metrics
            memory_delta = final_memory - initial_memory
            cpu_delta = (final_cpu_time.user + final_cpu_time.system) - (initial_cpu_time.user + initial_cpu_time.system)
            
            add_span_attributes(**{
                "profile.duration": duration,
                "profile.memory_delta": memory_delta,
                "profile.cpu_delta": cpu_delta,
                "profile.calls": profile_result.calls
            })
            
            metric_histogram("performance.function.duration")(duration)
            
            return profile_result
            
        except Exception as e:
            record_exception(e, attributes={
                "function": func.__name__,
                "operation": "profile_function"
            })
            raise


@instrument_command("performance_measure_operation")
def measure_operation(operation_name: str, operation: "Callable", 
                     warmup_runs: int = 1, measurement_runs: int = 5) -> PerformanceMetrics:
    """Measure performance of an operation with multiple runs."""
    with span("performance.measure_operation",
              **{PerformanceAttributes.OPERATION: PerformanceOperations.MEASURE,
                 "operation.name": operation_name}):
        
        process = psutil.Process()
        
        # Warmup runs
        for _ in range(warmup_runs):
            try:
                operation()
            except Exception:
                pass
        
        # Garbage collect before measurement
        gc.collect()
        
        # Measurement runs
        durations = []
        cpu_usages = []
        memory_usages = []
        peak_memories = []
        io_reads = []
        io_writes = []
        context_switches = []
        
        for run in range(measurement_runs):
            # Get initial state
            initial_memory = process.memory_info().rss
            try:
                initial_io = process.io_counters()
            except AttributeError:
                # io_counters() not available on some systems (e.g., macOS)
                initial_io = None
            try:
                initial_ctx_switches = process.num_ctx_switches()
            except AttributeError:
                # num_ctx_switches() not available on some systems
                initial_ctx_switches = None
            
            start_time = time.time()
            cpu_start = time.process_time()
            
            try:
                # Run operation
                operation()
                
                # Get final state
                end_time = time.time()
                cpu_end = time.process_time()
                
                final_memory = process.memory_info().rss
                try:
                    final_io = process.io_counters()
                except AttributeError:
                    final_io = None
                try:
                    final_ctx_switches = process.num_ctx_switches()
                except AttributeError:
                    final_ctx_switches = None
                
                # Calculate metrics
                duration = end_time - start_time
                cpu_time = cpu_end - cpu_start
                cpu_usage = (cpu_time / duration) * 100 if duration > 0 else 0
                
                memory_delta = final_memory - initial_memory
                peak_memory = max(initial_memory, final_memory)
                
                # Calculate I/O metrics if available
                if initial_io and final_io:
                    io_read_delta = final_io.read_bytes - initial_io.read_bytes
                    io_write_delta = final_io.write_bytes - initial_io.write_bytes
                else:
                    io_read_delta = 0
                    io_write_delta = 0
                
                # Calculate context switch metrics if available
                if initial_ctx_switches and final_ctx_switches:
                    ctx_switch_delta = (final_ctx_switches.voluntary + final_ctx_switches.involuntary) - \
                                     (initial_ctx_switches.voluntary + initial_ctx_switches.involuntary)
                else:
                    ctx_switch_delta = 0
                
                durations.append(duration)
                cpu_usages.append(cpu_usage)
                memory_usages.append(memory_delta)
                peak_memories.append(peak_memory)
                io_reads.append(io_read_delta)
                io_writes.append(io_write_delta)
                context_switches.append(ctx_switch_delta)
                
            except Exception as e:
                record_exception(e, attributes={
                    "operation": operation_name,
                    "run": run
                })
        
        if not durations:
            raise RuntimeError(f"All measurement runs failed for operation: {operation_name}")
        
        # Calculate averages
        avg_duration = sum(durations) / len(durations)
        avg_cpu = sum(cpu_usages) / len(cpu_usages)
        avg_memory = sum(memory_usages) / len(memory_usages)
        avg_peak_memory = sum(peak_memories) / len(peak_memories)
        avg_io_read = sum(io_reads) / len(io_reads)
        avg_io_write = sum(io_writes) / len(io_writes)
        avg_ctx_switches = sum(context_switches) / len(context_switches)
        
        metrics = PerformanceMetrics(
            operation=operation_name,
            duration=avg_duration,
            cpu_usage=avg_cpu,
            memory_usage=int(avg_memory),
            peak_memory=int(avg_peak_memory),
            io_read=int(avg_io_read),
            io_write=int(avg_io_write),
            context_switches=int(avg_ctx_switches),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Record metrics
        metric_histogram("performance.operation.duration")(avg_duration)
        metric_histogram("performance.operation.memory")(avg_memory)
        metric_counter("performance.measurements")(1)
        
        add_span_attributes(**{
            "metrics.duration": avg_duration,
            "metrics.cpu_usage": avg_cpu,
            "metrics.memory_usage": avg_memory,
            "metrics.runs": measurement_runs
        })
        
        return metrics


@instrument_command("performance_benchmark_deps")
def benchmark_dependency_resolution(project_path: Path) -> PerformanceMetrics:
    """Benchmark dependency resolution performance."""
    with span("performance.benchmark_deps",
              **{PerformanceAttributes.OPERATION: PerformanceOperations.BENCHMARK,
                 "project.path": str(project_path)}):
        
        def resolve_deps():
            # Test dependency resolution using uv
            try:
                subprocess.run(
                    ["uv", "pip", "compile", "--dry-run", "pyproject.toml"],
                    cwd=project_path,
                    capture_output=True,
                    timeout=60,
                    check=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to pip-tools if available
                try:
                    subprocess.run(
                        ["pip-compile", "--dry-run", "pyproject.toml"],
                        cwd=project_path,
                        capture_output=True,
                        timeout=60,
                        check=True
                    )
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
        
        return measure_operation("dependency_resolution", resolve_deps, warmup_runs=1, measurement_runs=3)


@instrument_command("performance_benchmark_tests")
def benchmark_test_execution(project_path: Path) -> PerformanceMetrics:
    """Benchmark test execution performance."""
    with span("performance.benchmark_tests",
              **{PerformanceAttributes.OPERATION: PerformanceOperations.BENCHMARK,
                 "project.path": str(project_path)}):
        
        def run_tests():
            try:
                subprocess.run(
                    ["python", "-m", "pytest", "--collect-only", "-q"],
                    cwd=project_path,
                    capture_output=True,
                    timeout=30,
                    check=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        return measure_operation("test_collection", run_tests, warmup_runs=1, measurement_runs=3)


@instrument_command("performance_analyze_bottlenecks")
def analyze_bottlenecks(metrics: List[PerformanceMetrics]) -> List[BottleneckAnalysis]:
    """Analyze performance metrics to identify bottlenecks."""
    with span("performance.analyze_bottlenecks",
              **{PerformanceAttributes.OPERATION: PerformanceOperations.ANALYZE}):
        
        bottlenecks = []
        
        for metric in metrics:
            # CPU bottlenecks
            if metric.cpu_usage > 80:
                bottlenecks.append(BottleneckAnalysis(
                    category="cpu",
                    severity="high" if metric.cpu_usage > 95 else "medium",
                    description=f"High CPU usage: {metric.cpu_usage:.1f}% for {metric.operation}",
                    recommendation="Consider optimizing algorithms or using parallel processing",
                    potential_improvement="20-50% performance improvement"
                ))
            
            # Memory bottlenecks
            memory_mb = metric.memory_usage / (1024 * 1024)
            if memory_mb > 100:  # > 100MB
                bottlenecks.append(BottleneckAnalysis(
                    category="memory",
                    severity="high" if memory_mb > 500 else "medium",
                    description=f"High memory usage: {memory_mb:.1f}MB for {metric.operation}",
                    recommendation="Consider memory profiling and optimization",
                    potential_improvement="10-30% memory reduction"
                ))
            
            # I/O bottlenecks
            total_io = metric.io_read + metric.io_write
            io_mb = total_io / (1024 * 1024)
            if io_mb > 10:  # > 10MB I/O
                bottlenecks.append(BottleneckAnalysis(
                    category="io",
                    severity="medium" if io_mb > 50 else "low",
                    description=f"High I/O usage: {io_mb:.1f}MB for {metric.operation}",
                    recommendation="Consider I/O optimization or caching",
                    potential_improvement="15-40% I/O reduction"
                ))
            
            # Context switching bottlenecks
            if metric.context_switches > 1000:
                bottlenecks.append(BottleneckAnalysis(
                    category="cpu",
                    severity="medium",
                    description=f"High context switches: {metric.context_switches} for {metric.operation}",
                    recommendation="Consider reducing concurrency or optimizing thread usage",
                    potential_improvement="10-25% performance improvement"
                ))
            
            # Duration bottlenecks
            if metric.duration > 10:  # > 10 seconds
                bottlenecks.append(BottleneckAnalysis(
                    category="general",
                    severity="high" if metric.duration > 60 else "medium",
                    description=f"Slow operation: {metric.duration:.1f}s for {metric.operation}",
                    recommendation="Profile the operation to identify specific bottlenecks",
                    potential_improvement="Variable, requires detailed analysis"
                ))
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        bottlenecks.sort(key=lambda x: severity_order[x.severity])
        
        add_span_attributes(**{
            "bottlenecks.total": len(bottlenecks),
            "bottlenecks.high": len([b for b in bottlenecks if b.severity == "high"]),
            "bottlenecks.medium": len([b for b in bottlenecks if b.severity == "medium"]),
            "bottlenecks.low": len([b for b in bottlenecks if b.severity == "low"])
        })
        
        return bottlenecks


@instrument_command("performance_optimize_project")
def optimize_project(project_path: Path) -> Dict[str, Any]:
    """Run comprehensive performance optimization analysis."""
    with span("performance.optimize_project",
              **{PerformanceAttributes.OPERATION: PerformanceOperations.OPTIMIZE,
                 "project.path": str(project_path)}):
        
        optimization_results = {
            "system_info": get_system_info(),
            "benchmarks": {},
            "bottlenecks": [],
            "recommendations": []
        }
        
        try:
            # Benchmark key operations
            metrics = []
            
            # Dependency resolution benchmark
            dep_metrics = benchmark_dependency_resolution(project_path)
            metrics.append(dep_metrics)
            optimization_results["benchmarks"]["dependency_resolution"] = dep_metrics.__dict__
            
            # Test execution benchmark
            test_metrics = benchmark_test_execution(project_path)
            metrics.append(test_metrics)
            optimization_results["benchmarks"]["test_execution"] = test_metrics.__dict__
            
            # Analyze bottlenecks
            bottlenecks = analyze_bottlenecks(metrics)
            optimization_results["bottlenecks"] = [b.__dict__ for b in bottlenecks]
            
            # Generate recommendations
            recommendations = _generate_optimization_recommendations(bottlenecks, project_path)
            optimization_results["recommendations"] = recommendations
            
            # Overall score
            optimization_results["performance_score"] = _calculate_performance_score(metrics, bottlenecks)
            
        except Exception as e:
            record_exception(e, attributes={
                "operation": "optimize_project",
                "project_path": str(project_path)
            })
            optimization_results["error"] = str(e)
        
        return optimization_results


def _generate_optimization_recommendations(bottlenecks: List[BottleneckAnalysis], 
                                         project_path: Path) -> List[Dict[str, Any]]:
    """Generate specific optimization recommendations."""
    recommendations = []
    
    # Check for common optimization opportunities
    pyproject_file = project_path / "pyproject.toml"
    if pyproject_file.exists():
        recommendations.append({
            "type": "dependency_optimization",
            "priority": "medium",
            "description": "Consider using uv for faster dependency resolution",
            "action": "Install uv and update CI/CD to use uv instead of pip",
            "impact": "20-50% faster dependency installation"
        })
    
    # Check for test optimization opportunities
    if any(p.suffix == ".py" for p in (project_path / "tests").rglob("*") if (project_path / "tests").exists()):
        recommendations.append({
            "type": "test_optimization",
            "priority": "medium",
            "description": "Consider parallel test execution",
            "action": "Use pytest-xdist for parallel test execution",
            "impact": "30-70% faster test execution"
        })
    
    # Check for caching opportunities
    if (project_path / ".github/workflows").exists():
        recommendations.append({
            "type": "ci_optimization",
            "priority": "low",
            "description": "Implement dependency caching in CI",
            "action": "Add caching steps to GitHub Actions workflows",
            "impact": "50-80% faster CI builds"
        })
    
    # Add bottleneck-specific recommendations
    for bottleneck in bottlenecks:
        if bottleneck.severity == "high":
            recommendations.append({
                "type": f"{bottleneck.category}_optimization",
                "priority": "high",
                "description": bottleneck.description,
                "action": bottleneck.recommendation,
                "impact": bottleneck.potential_improvement
            })
    
    return recommendations


def _calculate_performance_score(metrics: List[PerformanceMetrics], 
                               bottlenecks: List[BottleneckAnalysis]) -> Dict[str, Any]:
    """Calculate overall performance score."""
    if not metrics:
        return {"score": 0, "grade": "F", "description": "No metrics available"}
    
    # Base score starts at 100
    score = 100
    
    # Deduct points for bottlenecks
    high_bottlenecks = len([b for b in bottlenecks if b.severity == "high"])
    medium_bottlenecks = len([b for b in bottlenecks if b.severity == "medium"])
    low_bottlenecks = len([b for b in bottlenecks if b.severity == "low"])
    
    score -= high_bottlenecks * 20
    score -= medium_bottlenecks * 10
    score -= low_bottlenecks * 5
    
    # Deduct points for slow operations
    avg_duration = sum(m.duration for m in metrics) / len(metrics)
    if avg_duration > 30:
        score -= 20
    elif avg_duration > 10:
        score -= 10
    elif avg_duration > 5:
        score -= 5
    
    # Ensure score is not negative
    score = max(0, score)
    
    # Assign grade
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"
    
    descriptions = {
        "A": "Excellent performance",
        "B": "Good performance with minor optimization opportunities",
        "C": "Acceptable performance with some optimization needed",
        "D": "Poor performance requiring optimization",
        "F": "Very poor performance requiring immediate attention"
    }
    
    return {
        "score": score,
        "grade": grade,
        "description": descriptions[grade],
        "metrics_count": len(metrics),
        "bottlenecks_count": len(bottlenecks)
    }