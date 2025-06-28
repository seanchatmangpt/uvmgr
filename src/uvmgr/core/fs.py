"""
uvmgr.core.fs – hashing, atomic writes, temp helpers.

Enhanced with comprehensive OpenTelemetry instrumentation for file system operations monitoring.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path

from .paths import CACHE_DIR
from .telemetry import span, metric_counter, metric_histogram
from .instrumentation import add_span_attributes, add_span_event

__all__ = [
    "atomic_copy",
    "auto_name",
    "hash_bytes",
    "hash_file",
    "hash_str",
    "safe_write",
    "tempfile_in_cache",
]

_BLOCK = 1 << 20  # 1 MiB


def _digest(algo: str) -> hashlib._Hash:  # type: ignore[attr-defined]
    return hashlib.new(algo)


def hash_file(path: Path, *, algo: str = "sha1") -> str:
    """Hash file contents with telemetry tracking."""
    with span("fs.hash_file", path=str(path), algorithm=algo):
        add_span_event("fs.hash_file.starting", {"path": str(path), "algorithm": algo})
        
        start_time = time.time()
        file_size = 0
        
        try:
            h = _digest(algo)
            with path.open("rb") as fh:
                while chunk := fh.read(_BLOCK):
                    h.update(chunk)
                    file_size += len(chunk)
            
            hash_value = h.hexdigest()
            duration = time.time() - start_time
            
            # Record success metrics
            metric_counter("fs.hash_file.success")(1)
            metric_histogram("fs.hash_file.duration")(duration)
            metric_histogram("fs.hash_file.size_bytes")(file_size)
            
            add_span_attributes(**{
                "fs.file_path": str(path),
                "fs.file_size": file_size,
                "fs.hash_algorithm": algo,
                "fs.hash_value": hash_value,
                "fs.hash_duration": duration,
            })
            add_span_event("fs.hash_file.completed", {
                "path": str(path),
                "size": file_size,
                "hash": hash_value,
                "duration": duration,
            })
            
            return hash_value
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("fs.hash_file.failed")(1)
            
            add_span_event("fs.hash_file.failed", {
                "path": str(path),
                "error": str(e),
                "duration": duration,
            })
            raise


def hash_bytes(data: bytes, *, algo: str = "sha1") -> str:
    """Hash byte data with telemetry tracking."""
    with span("fs.hash_bytes", data_size=len(data), algorithm=algo):
        add_span_event("fs.hash_bytes.starting", {"data_size": len(data), "algorithm": algo})
        
        start_time = time.time()
        
        try:
            hash_value = _digest(algo)(data).hexdigest()
            duration = time.time() - start_time
            
            # Record metrics
            metric_counter("fs.hash_bytes.operations")(1)
            metric_histogram("fs.hash_bytes.duration")(duration)
            metric_histogram("fs.hash_bytes.size_bytes")(len(data))
            
            add_span_attributes(**{
                "fs.data_size": len(data),
                "fs.hash_algorithm": algo,
                "fs.hash_value": hash_value,
                "fs.hash_duration": duration,
            })
            add_span_event("fs.hash_bytes.completed", {
                "data_size": len(data),
                "hash": hash_value,
                "duration": duration,
            })
            
            return hash_value
            
        except Exception as e:
            duration = time.time() - start_time
            
            add_span_event("fs.hash_bytes.failed", {
                "data_size": len(data),
                "error": str(e),
                "duration": duration,
            })
            raise


def hash_str(text: str, *, algo: str = "sha1") -> str:
    """Hash string with telemetry tracking."""
    with span("fs.hash_str", text_length=len(text), algorithm=algo):
        add_span_event("fs.hash_str.starting", {"text_length": len(text), "algorithm": algo})
        
        return hash_bytes(text.encode(), algo=algo)


def safe_write(path: Path, data: str | bytes, *, mode: str | None = None) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    if isinstance(data, str):
        tmp.write_text(data, encoding="utf-8")
    else:
        tmp.write_bytes(data)
    if mode:
        tmp.chmod(int(mode, 8))
    tmp.replace(path)


def atomic_copy(src: Path, dst: Path) -> None:
    """Atomically copy file with telemetry tracking."""
    with span("fs.atomic_copy", src=str(src), dst=str(dst)):
        add_span_event("fs.atomic_copy.starting", {"src": str(src), "dst": str(dst)})
        
        start_time = time.time()
        
        try:
            # Get source file size for metrics
            src_size = src.stat().st_size if src.exists() else 0
            
            tmp = dst.with_suffix(".tmp")
            shutil.copy2(src, tmp)
            tmp.replace(dst)
            
            duration = time.time() - start_time
            
            # Record success metrics
            metric_counter("fs.atomic_copy.success")(1)
            metric_histogram("fs.atomic_copy.duration")(duration)
            metric_histogram("fs.atomic_copy.file_size")(src_size)
            
            add_span_attributes(**{
                "fs.src_path": str(src),
                "fs.dst_path": str(dst),
                "fs.file_size": src_size,
                "fs.copy_duration": duration,
            })
            add_span_event("fs.atomic_copy.completed", {
                "src": str(src),
                "dst": str(dst),
                "size": src_size,
                "duration": duration,
            })
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("fs.atomic_copy.failed")(1)
            
            add_span_event("fs.atomic_copy.failed", {
                "src": str(src),
                "dst": str(dst),
                "error": str(e),
                "duration": duration,
            })
            raise


def auto_name(prefix: str, ext: str = ".txt") -> Path:
    """Generate timestamped filename with telemetry tracking."""
    with span("fs.auto_name", prefix=prefix, extension=ext):
        add_span_event("fs.auto_name.starting", {"prefix": prefix, "extension": ext})
        
        start_time = time.time()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(f"{prefix}_{ts}{ext}")
        duration = time.time() - start_time
        
        # Record metrics
        metric_counter("fs.auto_name.generated")(1)
        metric_histogram("fs.auto_name.duration")(duration)
        
        add_span_attributes(**{
            "fs.prefix": prefix,
            "fs.extension": ext,
            "fs.generated_filename": str(filename),
            "fs.generation_duration": duration,
        })
        add_span_event("fs.auto_name.completed", {
            "prefix": prefix,
            "filename": str(filename),
            "duration": duration,
        })
        
        return filename


def tempfile_in_cache(*, suffix: str = "") -> Path:
    """Create temporary file in cache directory with telemetry tracking."""
    with span("fs.tempfile_in_cache", suffix=suffix):
        add_span_event("fs.tempfile.starting", {"suffix": suffix, "cache_dir": str(CACHE_DIR)})
        
        start_time = time.time()
        
        try:
            CACHE_DIR.mkdir(exist_ok=True, parents=True)
            fd, name = tempfile.mkstemp(dir=CACHE_DIR, suffix=suffix)
            os.close(fd)
            temp_path = Path(name)
            
            duration = time.time() - start_time
            
            # Record success metrics
            metric_counter("fs.tempfile.created")(1)
            metric_histogram("fs.tempfile.creation_duration")(duration)
            
            add_span_attributes(**{
                "fs.cache_dir": str(CACHE_DIR),
                "fs.temp_path": str(temp_path),
                "fs.suffix": suffix,
                "fs.creation_duration": duration,
            })
            add_span_event("fs.tempfile.created", {
                "path": str(temp_path),
                "suffix": suffix,
                "duration": duration,
            })
            
            return temp_path
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("fs.tempfile.failed")(1)
            
            add_span_event("fs.tempfile.failed", {
                "suffix": suffix,
                "cache_dir": str(CACHE_DIR),
                "error": str(e),
                "duration": duration,
            })
            raise
