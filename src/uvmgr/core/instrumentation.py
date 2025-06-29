"""
uvmgr.core.instrumentation
--------------------------
OpenTelemetry instrumentation decorators and utilities for CLI commands.

This module provides decorators and utilities to automatically instrument CLI commands
with OpenTelemetry spans and metrics, following semantic conventions defined in
weaver-forge/semantic-conventions.yaml.

The module includes:

• **Command Instrumentation**: `@instrument_command` decorator for CLI commands
• **Subcommand Instrumentation**: `@instrument_subcommand` decorator for subcommands
• **Attribute Management**: Functions to add attributes and events to spans
• **Graceful Degradation**: No-op implementations when OpenTelemetry is not available
• **Semantic Conventions**: Integration with uvmgr-specific semantic conventions

All decorators and functions are designed to work seamlessly whether OpenTelemetry
is available or not, ensuring the application continues to function normally.

Example
-------
    @app.command()
    @instrument_command("my_command")
    def my_command(name: str, verbose: bool = False):
        add_span_attributes(custom_name=name, verbose_mode=verbose)
        
        with span("my_operation", operation_type="custom"):
            result = perform_operation(name)
            return result

See Also
--------
- :mod:`uvmgr.core.telemetry` : Core telemetry functions
- :mod:`uvmgr.core.semconv` : Semantic conventions
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from .semconv import CliAttributes
from .telemetry import metric_counter, record_exception, span

# Import typer only when needed to avoid circular dependencies
try:
    import typer
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    typer = None

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
) -> Callable:
    """
    Decorator to instrument CLI commands with OpenTelemetry.
    
    This decorator automatically creates a span for the decorated function and
    adds semantic convention attributes for CLI commands. It extracts meaningful
    information from function arguments and Typer context to provide rich
    telemetry data.
    
    Parameters
    ----------
    name : str, optional
        Override name for the command. If not provided, uses the function name.
        This name will be used in the span name and CLI attributes.
    command_type : str, optional
        Type of command for span naming. Common values are "cli", "cli.subcommand".
        Default is "cli".
    track_args : bool, optional
        Whether to track command arguments in telemetry. When True, extracts
        argument information from the function signature and Typer context.
        Default is True.
    
    Returns
    -------
    Callable
        A decorator function that wraps the original function with telemetry.
    
    Notes
    -----
    The decorator automatically adds the following attributes to the span:
    - cli.command: The command name
    - cli.module: The module containing the command
    - code.function: The function name
    - code.namespace: The module namespace
    
    If track_args is True and the first argument is a Typer Context, it also adds:
    - cli.subcommand: The invoked subcommand (if any)
    - cli.args.count: Number of positional arguments
    
    Example
    -------
    >>> @app.command()
    ... @instrument_command("add_dependency")
    ... def add_dependency(ctx: typer.Context, package: str, dev: bool = False):
    ...     # Function body - automatically instrumented
    ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            command_name = name or func.__name__
            span_name = f"{command_type}.command.{command_name}"

            # Extract meaningful attributes from args/kwargs
            attributes = {
                CliAttributes.CLI_COMMAND: command_name,
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

                except Exception as e:
                    # Handle typer.Exit if available, otherwise treat as general exception
                    if TYPER_AVAILABLE and typer and isinstance(e, typer.Exit):
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
                    else:
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


@instrument_command("instrumentation_instrument_subcommand")
def instrument_subcommand(parent_command: str) -> Callable:
    """
    Decorator for subcommands to maintain trace hierarchy.
    
    Args:
        parent_command: Name of the parent command
        
    Returns
    -------
    Callable
        Decorator that instruments as a subcommand
    """
    with span("instrumentation.instrument_subcommand", parent_command=parent_command):
        add_span_event("instrumentation.subcommand.created", {"parent_command": parent_command})
        metric_counter("instrumentation.subcommand.created")(1, {"parent_command": parent_command})
        
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
