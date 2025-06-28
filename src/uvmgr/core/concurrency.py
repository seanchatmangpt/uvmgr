"""
uvmgr.core.concurrency – thread fan-out + async helper.
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
