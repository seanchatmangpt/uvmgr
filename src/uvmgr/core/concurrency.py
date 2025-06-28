"""
uvmgr.core.concurrency - Concurrency Utilities
=============================================

Thread fan-out and async helper utilities for concurrent execution.

This module provides utilities for running functions concurrently using
thread pools and handling async operations in various execution contexts.

Key Features
-----------
• **Thread Pool Execution**: Concurrent execution of functions with progress tracking
• **Async Support**: Helper for running async code in different contexts
• **Progress Tracking**: Visual progress bars for concurrent operations
• **Nested Loop Support**: Automatic handling of nested event loops

Available Functions
------------------
- **run_wave()**: Execute functions concurrently with thread pool
- **aio_run()**: Run async coroutine with nested loop support

Examples
--------
    >>> from uvmgr.core.concurrency import run_wave, aio_run
    >>> import asyncio
    >>> 
    >>> # Concurrent function execution
    >>> def fetch_data(id):
    >>>     return f"data_{id}"
    >>> 
    >>> results = run_wave([lambda: fetch_data(i) for i in range(5)])
    >>> 
    >>> # Async execution
    >>> async def async_task():
    >>>     await asyncio.sleep(1)
    >>>     return "completed"
    >>> 
    >>> result = aio_run(async_task())

Dependencies
-----------
- **nest_asyncio**: Optional dependency for nested event loop support
  - Automatically installed when needed
  - Provides fallback for RuntimeError when loop is already running

See Also
--------
- :mod:`uvmgr.core.shell` : Progress bar utilities
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from .shell import progress_bar

T = TypeVar("T")


def run_wave(funcs: Iterable[Callable[[], T]]) -> list[T]:
    funcs = list(funcs)
    with ThreadPoolExecutor() as pool, progress_bar(len(funcs)) as tick:
        futures = [pool.submit(f) for f in funcs]
        results = []
        for fut in futures:
            results.append(fut.result())
            tick()
    return results


def aio_run(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        try:
            import nest_asyncio

            nest_asyncio.apply()
        except ImportError as e:
            raise RuntimeError("loop running; install nest_asyncio") from e
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
