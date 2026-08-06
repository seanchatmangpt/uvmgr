"""Runtime boundary for executing test commands and emitting receipts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestExecutionReceipt:
    """Observed consequence of one test-process actuation."""

    command: tuple[str, ...]
    working_directory: str
    exit_code: int
    outcome: str
    started_ns: int
    duration_ms: float
    error: str | None
    receipt_path: str
    receipt_sha256: str


def _write_receipt(
    payload: dict[str, object],
    *,
    receipt_dir: Path,
    started_ns: int,
) -> tuple[Path, str]:
    """Write a canonical JSON receipt atomically and return its identity."""
    receipt_dir.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    document = {**payload, "receipt_sha256": digest}
    target = receipt_dir / f"tests-run-{started_ns}.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target, digest


def execute_test_command(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    receipt_dir: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> TestExecutionReceipt:
    """Execute an exact argv vector and emit a receipt for success or failure."""
    argv = tuple(str(part) for part in command)
    if not argv:
        raise ValueError("test command must not be empty")

    working_directory = (cwd or Path.cwd()).resolve()
    receipts = receipt_dir or working_directory / "reports" / "receipts"
    started_ns = time.time_ns()
    started = time.perf_counter()
    exit_code = 127
    error: str | None = None
    outcome = "UNSUPPORTED"

    try:
        completed = subprocess.run(
            list(argv),
            cwd=working_directory,
            env=dict(os.environ) | dict(env or {}),
            check=False,
        )
        exit_code = completed.returncode
        outcome = "ALIVE" if exit_code == 0 else "BUILD_BROKEN"
    except OSError as exc:
        error = f"{type(exc).__name__}: {exc}"

    duration_ms = (time.perf_counter() - started) * 1000
    payload: dict[str, object] = {
        "command": list(argv),
        "working_directory": str(working_directory),
        "exit_code": exit_code,
        "outcome": outcome,
        "started_ns": started_ns,
        "duration_ms": round(duration_ms, 3),
        "error": error,
    }
    receipt_path, receipt_sha256 = _write_receipt(
        payload,
        receipt_dir=receipts,
        started_ns=started_ns,
    )
    return TestExecutionReceipt(
        command=argv,
        working_directory=str(working_directory),
        exit_code=exit_code,
        outcome=outcome,
        started_ns=started_ns,
        duration_ms=duration_ms,
        error=error,
        receipt_path=str(receipt_path),
        receipt_sha256=receipt_sha256,
    )


def receipt_as_dict(receipt: TestExecutionReceipt) -> dict[str, object]:
    """Return a JSON-compatible representation of a receipt."""
    return asdict(receipt)
