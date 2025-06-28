"""
uvmgr.core.config - Configuration Management
===========================================

Environment override and typed TOML loader with comprehensive telemetry.

This module provides flexible configuration management that supports both
environment variables and TOML files, with automatic validation using
Pydantic models. All operations are instrumented with OpenTelemetry for
monitoring configuration loading and lookup patterns.

Key Features
-----------
• **Environment Priority**: Environment variables override TOML settings
• **TOML Support**: Load configuration from TOML files
• **Type Validation**: Pydantic model validation for configuration
• **Telemetry Integration**: Full OpenTelemetry instrumentation
• **Performance Monitoring**: Duration tracking for configuration operations
• **Error Handling**: Comprehensive error tracking and metrics

Available Functions
------------------
- **env_or()**: Get configuration value from environment or TOML with fallback
- **load_toml()**: Load and validate TOML configuration file

Configuration Sources (Priority Order)
-------------------------------------
1. **Environment Variables**: Direct environment variable lookup
2. **TOML File**: Configuration from ~/.config/uvmgr/env.toml
3. **Default Values**: Fallback to provided default

Examples
--------
    >>> from uvmgr.core.config import env_or, load_toml
    >>> from pydantic import BaseModel
    >>> 
    >>> # Get configuration with fallback
    >>> api_key = env_or("API_KEY", "default_key")
    >>> api_key
    'default_key'
    >>> 
    >>> # Define typed configuration
    >>> class AppConfig(BaseModel):
    ...     debug: bool = False
    ...     port: int = 8000
    >>> 
    >>> AppConfig().debug
    False

See Also
--------
- :mod:`uvmgr.core.paths` : Path management
- :mod:`uvmgr.core.telemetry` : Telemetry and observability
"""

from __future__ import annotations

import os
import time
import tomllib
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .instrumentation import add_span_attributes, add_span_event
from .paths import CONFIG_DIR
from .telemetry import metric_counter, metric_histogram, span

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
