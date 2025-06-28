"""
uvmgr.core.config – env override & typed TOML loader.

Enhanced with comprehensive OpenTelemetry instrumentation for configuration operations monitoring.
"""

from __future__ import annotations

import os
import time
import tomllib
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .paths import CONFIG_DIR
from .telemetry import span, metric_counter, metric_histogram
from .instrumentation import add_span_attributes, add_span_event

T = TypeVar("T", bound=BaseModel)

__all__ = ["env_or", "load_toml"]


def env_or(key: str, default: str | None = None) -> str | None:
    """Get configuration value from environment or TOML file with telemetry."""
    with span("config.env_or", key=key, has_default=default is not None):
        add_span_event("config.lookup.starting", {"key": key, "default": default})
        
        start_time = time.time()
        source = None
        value = None
        
        # Check environment first
        if key in os.environ:
            value = os.environ[key]
            source = "environment"
            metric_counter("config.lookups.env")(1)
            add_span_event("config.lookup.env_hit", {"key": key, "value_set": bool(value)})
        else:
            # Check TOML file
            env_file = CONFIG_DIR / "env.toml"
            if env_file.exists():
                try:
                    data = tomllib.loads(env_file.read_text())
                    if key in data:
                        value = str(data[key])
                        source = "toml_file"
                        metric_counter("config.lookups.toml")(1)
                        add_span_event("config.lookup.toml_hit", {"key": key, "file": str(env_file)})
                    else:
                        metric_counter("config.lookups.toml_miss")(1)
                        add_span_event("config.lookup.toml_miss", {"key": key})
                except Exception as e:
                    metric_counter("config.lookups.toml_error")(1)
                    add_span_event("config.lookup.toml_error", {"key": key, "error": str(e)})
            else:
                metric_counter("config.lookups.toml_missing")(1)
                add_span_event("config.lookup.toml_file_missing", {"key": key, "expected_path": str(env_file)})
        
        # Use default if no value found
        if value is None:
            value = default
            source = "default"
            metric_counter("config.lookups.default")(1)
            add_span_event("config.lookup.using_default", {"key": key, "default": default})
        
        duration = time.time() - start_time
        
        # Record metrics and attributes
        metric_histogram("config.lookup_duration")(duration)
        
        add_span_attributes(**{
            "config.key": key,
            "config.source": source,
            "config.has_value": value is not None,
            "config.lookup_duration": duration,
        })
        add_span_event("config.lookup.completed", {
            "key": key,
            "source": source,
            "has_value": value is not None,
            "duration": duration,
        })
        
        return value


def load_toml(path: Path, model: type[T]) -> T:
    """Load and validate TOML configuration file with telemetry."""
    with span("config.load_toml", path=str(path), model=model.__name__):
        add_span_event("config.toml.loading", {"path": str(path), "model": model.__name__})
        
        start_time = time.time()
        
        try:
            # Load TOML data
            content = path.read_text()
            data = tomllib.loads(content)
            
            # Validate with Pydantic model
            validated_config = model.model_validate(data)
            
            duration = time.time() - start_time
            
            # Record success metrics
            metric_counter("config.toml_loads.success")(1)
            metric_histogram("config.toml_load_duration")(duration)
            
            add_span_attributes(**{
                "config.file_path": str(path),
                "config.file_size": len(content),
                "config.model": model.__name__,
                "config.keys_count": len(data) if isinstance(data, dict) else 0,
                "config.load_duration": duration,
            })
            add_span_event("config.toml.loaded", {
                "path": str(path),
                "model": model.__name__,
                "keys_count": len(data) if isinstance(data, dict) else 0,
                "duration": duration,
            })
            
            return validated_config
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record failure metrics
            metric_counter("config.toml_loads.failed")(1)
            
            add_span_event("config.toml.load_failed", {
                "path": str(path),
                "model": model.__name__,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": duration,
            })
            raise
