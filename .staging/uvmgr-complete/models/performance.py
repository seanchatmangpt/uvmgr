"""Performance profiling and benchmark models."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkResult(BaseModel):
    """Single benchmark result."""

    model_config = ConfigDict(extra="forbid")

    operation: str
    duration_ns: int
    iterations: int
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, any] = Field(default_factory=dict)

    @property
    def ops_per_second(self) -> float:
        """Calculate operations per second."""
        return 1_000_000_000 / self.duration_ns


class PerformanceProfile(BaseModel):
    """Performance profile for uvmgr operations."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    benchmarks: list[BenchmarkResult] = Field(default_factory=list)
    system_info: dict[str, str] = Field(default_factory=dict)

    def add_benchmark(self, operation: str, duration_ns: int, iterations: int = 1):
        """Add a benchmark result."""
        self.benchmarks.append(
            BenchmarkResult(
                operation=operation,
                duration_ns=duration_ns,
                iterations=iterations
            )
        )

    def get_summary(self) -> dict[str, float]:
        """Get performance summary."""
        summary = {}
        for bench in self.benchmarks:
            summary[bench.operation] = bench.duration_ns
        return summary
