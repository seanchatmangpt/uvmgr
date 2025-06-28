"""
Example CLI with OTEL instrumentation.
"""

import click
from demo_otel_app import tracer, request_counter, trace_function


@click.command()
@click.option("--name", default="World", help="Name to greet")
@trace_function()
def hello(name: str):
    """Example command with automatic tracing."""
    with tracer.start_as_current_span("greeting") as span:
        span.set_attribute("user.name", name)
        request_counter.add(1, {"command": "hello"})
        
        message = f"Hello, {name}!"
        span.add_event("greeting_generated", {"message": message})
        
        click.echo(message)
        return message


if __name__ == "__main__":
    hello()
