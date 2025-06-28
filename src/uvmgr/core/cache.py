"""
uvmgr.core.cache – SHA1 command-result cache.

Enhanced with comprehensive OpenTelemetry instrumentation for cache operations monitoring.
"""

from __future__ import annotations

import json
import time

from .fs import hash_str
from .instrumentation import add_span_attributes, add_span_event
from .paths import CACHE_DIR
from .telemetry import metric_counter, metric_histogram, span

_RUNS = CACHE_DIR / "runs.jsonl"
_RUNS.touch(exist_ok=True)

__all__ = ["cache_hit", "hash_cmd", "store_result"]


def hash_cmd(cmd: str) -> str:
    """Hash command string for cache key with telemetry."""
    with span("cache.hash_cmd", command_length=len(cmd)):
        add_span_event("cache.hash.starting", {"command_preview": cmd[:50] + "..." if len(cmd) > 50 else cmd})

        start_time = time.time()
        hash_value = hash_str(cmd)
        duration = time.time() - start_time

        # Record metrics
        metric_counter("cache.hash_operations")(1)
        metric_histogram("cache.hash_duration")(duration)

        add_span_attributes(**{
            "cache.hash": hash_value,
            "cache.command_length": len(cmd),
            "cache.hash_duration": duration,
        })
        add_span_event("cache.hash.completed", {"hash": hash_value, "duration": duration})

        return hash_value


def cache_hit(cmd: str) -> bool:
    """Check if command result exists in cache with comprehensive telemetry."""
    with span("cache.lookup", command=cmd):
        add_span_event("cache.lookup.starting", {"command": cmd[:50] + "..." if len(cmd) > 50 else cmd})

        start_time = time.time()
        h = hash_cmd(cmd)

        # Check cache
        cache_lines = _RUNS.read_text().splitlines() if _RUNS.exists() else []
        hit = any(h in line for line in cache_lines)
        duration = time.time() - start_time

        # Record metrics
        if hit:
            metric_counter("cache.hits")(1)
            add_span_event("cache.lookup.hit", {"hash": h, "duration": duration})
        else:
            metric_counter("cache.misses")(1)
            add_span_event("cache.lookup.miss", {"hash": h, "duration": duration})

        metric_histogram("cache.lookup_duration")(duration)

        add_span_attributes(**{
            "cache.hit": hit,
            "cache.hash": h,
            "cache.entries_checked": len(cache_lines),
            "cache.lookup_duration": duration,
        })

        return hit


def store_result(cmd: str) -> None:
    """Store command result in cache with telemetry tracking."""
    with span("cache.store", command=cmd):
        add_span_event("cache.store.starting", {"command": cmd[:50] + "..." if len(cmd) > 50 else cmd})

        start_time = time.time()
        h = hash_cmd(cmd)
        entry = {"k": h, "ts": time.time()}

        try:
            _RUNS.write_text(json.dumps(entry) + "\n", mode="a")
            duration = time.time() - start_time

            # Record success metrics
            metric_counter("cache.stores.success")(1)
            metric_histogram("cache.store_duration")(duration)

            add_span_attributes(**{
                "cache.hash": h,
                "cache.store_duration": duration,
                "cache.entry_size": len(json.dumps(entry)),
            })
            add_span_event("cache.store.completed", {
                "hash": h,
                "duration": duration,
                "timestamp": entry["ts"],
            })

        except Exception as e:
            duration = time.time() - start_time

            # Record failure metrics
            metric_counter("cache.stores.failed")(1)

            add_span_event("cache.store.failed", {
                "error": str(e),
                "hash": h,
                "duration": duration,
            })
            raise
