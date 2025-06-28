"""
uvmgr.core.instrumentation
--------------------------
OpenTelemetry instrumentation decorators for CLI commands.

This module provides decorators to automatically instrument CLI commands
with OpenTelemetry spans and metrics, following semantic conventions
defined in weaver-forge/semantic-conventions.yaml.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

import typer

from .semconv import CliAttributes
from .telemetry import metric_counter, record_exception, span

# Try to import OTEL components for type checking and constants
try:
    from opentelemetry import trace
    from opentelemetry.semconv.trace import SpanAttributes
    from opentelemetry.trace import Status, StatusCode

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False
    # Define fallback types/constants for graceful degradation
    class StatusCode:
        OK = 0
        ERROR = 1

    class Status:
        def __init__(self, code, description=None):
            self.code = code
            self.description = description

    class SpanAttributes:
        CODE_FUNCTION = "code.function"
        CODE_NAMESPACE = "code.namespace"

    class trace:
        class SpanKind:
            SERVER = 1

        @staticmethod
        def get_current_span():
            # Return a dummy span object
            class DummySpan:
                def set_attribute(self, key, value): pass
                def set_status(self, status): pass
                def add_event(self, name, attributes=None): pass
                def is_recording(self): return False
            return DummySpan()


def instrument_command(
    name: str = None,
    command_type: str = "cli",
    track_args: bool = True
) -> Callable[[Callable], Callable]:
    """
    Decorator to instrument CLI commands with OpenTelemetry.
    
    Args:
        name: Override name for the command (defaults to function name)
        command_type: Type of command (cli, cli.subcommand, etc.)
        track_args: Whether to track command arguments
        
    Returns
    -------
        Decorated function with OTEL instrumentation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            command_name = name or func.__name__
            span_name = f"{command_type}.command.{command_name}"

            # Extract meaningful attributes from args/kwargs
            attributes = {
                CliAttributes.COMMAND: command_name,
                "cli.module": func.__module__.split(".")[-1],
                SpanAttributes.CODE_FUNCTION: func.__name__,
                SpanAttributes.CODE_NAMESPACE: func.__module__,
            }

            # Add CLI-specific attributes
            if track_args and args:
                # Safely serialize args for telemetry
                attributes["cli.args.count"] = len(args)
                # Check if first arg is Typer context
                if hasattr(args[0], "__class__") and args[0].__class__.__name__ == "Context":
                    ctx = args[0]
                    if hasattr(ctx, "invoked_subcommand"):
                        attributes[CliAttributes.SUBCOMMAND] = str(ctx.invoked_subcommand)

            # Add options from kwargs if present
            if kwargs:
                # Filter out Typer context and sensitive data
                safe_options = {
                    k: str(v) for k, v in kwargs.items()
                    if k not in ("ctx", "password", "token", "secret", "key")
                }
                if safe_options:
                    import json
                    attributes[CliAttributes.OPTIONS] = json.dumps(safe_options)

            with span(
                span_name,
                span_kind=trace.SpanKind.SERVER if HAS_OTEL else None,
                **attributes
            ):
                current_span = trace.get_current_span()

                # Increment command counter metric
                metric_counter(f"cli.command.{command_name}.calls")(1)

                try:
                    # Add pre-execution event
                    current_span.add_event(
                        "command.started",
                        {CliAttributes.COMMAND: command_name}
                    )

                    # Execute the actual command
                    result = func(*args, **kwargs)

                    # Success - set OK status
                    current_span.set_status(Status(StatusCode.OK))
                    current_span.add_event(
                        "command.completed",
                        {CliAttributes.COMMAND: command_name, "cli.success": True}
                    )

                    return result

                except typer.Exit as e:
                    # Normal exit (like --help)
                    exit_code = e.exit_code
                    if exit_code == 0:
                        current_span.set_status(Status(StatusCode.OK))
                    else:
                        current_span.set_status(
                            Status(StatusCode.ERROR, f"Exit code: {exit_code}")
                        )
                    current_span.set_attribute(CliAttributes.EXIT_CODE, exit_code)
                    raise

                except Exception as e:
                    # Error - record exception and set error status
                    record_exception(e, escaped=True)
                    current_span.set_status(
                        Status(StatusCode.ERROR, str(e))
                    )
                    current_span.add_event(
                        "command.failed",
                        {
                            CliAttributes.COMMAND: command_name,
                            "cli.success": False,
                            "exception.type": type(e).__name__,
                        }
                    )

                    # Increment error counter
                    metric_counter(f"cli.command.{command_name}.errors")(1)
                    raise

        return wrapper
    return decorator


def instrument_subcommand(parent_command: str) -> Callable[[Callable], Callable]:
    """
    Decorator for subcommands to maintain trace hierarchy.
    
    Args:
        parent_command: Name of the parent command
        
    Returns
    -------
        Decorator that instruments as a subcommand
    """
    def decorator(func: Callable) -> Callable:
        return instrument_command(
            f"{parent_command}_{func.__name__}",
            command_type="cli.subcommand"
        )(func)
    return decorator


def add_span_attributes(**attributes):
    """
    Add attributes to the current span.
    
    Useful for adding command-specific attributes within the command implementation.
    """
    if HAS_OTEL:
        current_span = trace.get_current_span()
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict = None):
    """
    Add an event to the current span.
    
    Args:
        name: Event name
        attributes: Optional event attributes
    """
    if HAS_OTEL:
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.add_event(name, attributes or {})
