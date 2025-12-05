"""
uvmgr.core.cache - Command Result Caching
========================================

SHA1 command-result cache with comprehensive telemetry instrumentation.

This module provides a simple but effective caching system for command results
using SHA1 hashing of command strings. Cache entries are stored in JSONL format
for efficient appending and lookup operations.

Key Features
-----------
• **SHA1 Hashing**: Fast and reliable command string hashing
• **JSONL Storage**: Efficient append-only storage format
• **Telemetry Integration**: Full OpenTelemetry instrumentation
• **Performance Monitoring**: Duration tracking for all cache operations
• **Hit/Miss Tracking**: Comprehensive cache performance metrics

Available Functions
------------------
- **hash_cmd()**: Generate SHA1 hash for command string
- **cache_hit()**: Check if command result exists in cache
- **store_result()**: Store command result in cache

Cache Storage
------------
- **Location**: ~/.uvmgr_cache/runs.jsonl
- **Format**: JSONL (JSON Lines) with hash and timestamp
- **Structure**: {"k": "sha1_hash", "ts": timestamp}

Examples
--------
    >>> from uvmgr.core.cache import hash_cmd, cache_hit, store_result
    >>> 
    >>> # Check if command was previously executed
    >>> cmd = "python --version"
    >>> if cache_hit(cmd):
    ...     print("Command was cached")
    ... else:
    ...     print("Command not cached")
    ...     # store_result(cmd, "Python 3.12.0")

See Also
--------
- :mod:`uvmgr.core.fs` : File system operations
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
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

        # Check cache safely (TOCTOU fix: use try-except instead of check-then-use)
        try:
            cache_lines = _RUNS.read_text().splitlines()
        except FileNotFoundError:
            # Cache file doesn't exist yet - no hits possible
            cache_lines = []

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
            # Prevent DoS via unbounded cache growth (max 10MB)
            MAX_CACHE_SIZE = 10 * 1024 * 1024  # 10MB
            try:
                current_size = _RUNS.stat().st_size if _RUNS.exists() else 0
                if current_size > MAX_CACHE_SIZE:
                    _log.warning("Cache file exceeds maximum size (%d bytes), skipping store", current_size)
                    metric_counter("cache.stores.skipped")(1)
                    return
            except OSError as e:
                _log.warning("Could not check cache file size: %s", e)

            # Append to cache (safe enough since it's just one line per entry)
            # In production, consider using fcntl for file locking if multi-process contention is an issue
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

        except (IOError, OSError) as e:
            duration = time.time() - start_time

            # Record failure metrics
            metric_counter("cache.stores.failed")(1)

            add_span_event("cache.store.failed", {
                "error": str(e),
                "hash": h,
                "duration": duration,
            })
            raise
