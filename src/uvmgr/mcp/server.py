"""
uvmgr MCP Server - Model Context Protocol interface for uvmgr.

This module provides the main MCP server setup that exposes uvmgr functionality
to AI assistants like Claude. It acts as a translation layer between the MCP
protocol and uvmgr's existing operations.

Enhanced with comprehensive OpenTelemetry instrumentation for observability.
"""

from dataclasses import dataclass
from typing import Any

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import McpAttributes, McpOperations, ServerAttributes, ServerOperations
from uvmgr.core.telemetry import metric_counter, span

try:
    from fastmcp import Context, FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is required for MCP server functionality. "
        "Install with: pip install 'uvmgr[mcp]' or 'pip install fastmcp'"
    )

from uvmgr.mcp._mcp_instance import mcp

# Note: Tool and resource imports are handled by the individual modules
# They register themselves with the mcp instance when imported

# -----------------------------------------------------------------------------
# Helper Classes
# -----------------------------------------------------------------------------


@dataclass
class OperationResult:
    """Standardized result format for MCP operations with telemetry support."""

    success: bool
    message: str
    details: dict[str, Any] | None = None
    operation: str | None = None
    duration: float | None = None

    def to_string(self) -> str:
        """Format result for LLM consumption."""
        result = f"{'✅' if self.success else '❌'} {self.message}"
        if self.details:
            result += "\n" + "\n".join(f"  {k}: {v}" for k, v in self.details.items())
        return result

    def record_telemetry(self):
        """Record telemetry data for this operation result."""
        if self.operation:
            # Record operation metrics
            counter = metric_counter(f"mcp.operations.{self.operation}")
            counter(1)
            
            if self.success:
                metric_counter("mcp.operations.success")(1)
            else:
                metric_counter("mcp.operations.failed")(1)
            
            # Add span attributes for current operation
            add_span_attributes(**{
                McpAttributes.OPERATION: self.operation,
                "mcp.success": self.success,
                "mcp.message": self.message,
            })
            
            # Record duration if available
            if self.duration:
                add_span_attributes(**{"mcp.duration": self.duration})
                
        add_span_event("mcp.operation.completed", {
            "success": self.success,
            "operation": self.operation or "unknown",
            "message": self.message,
        })


# -----------------------------------------------------------------------------
# Instrumented Server Functions
# -----------------------------------------------------------------------------

def run_mcp_server(host: str = "localhost", port: int = 8000):
    """Run MCP server with comprehensive OTEL instrumentation."""
    with span(
        "mcp.server.startup",
        **{
            ServerAttributes.HOST: host,
            ServerAttributes.PORT: port,
            ServerAttributes.PROTOCOL: "mcp",
            ServerAttributes.SERVICE: "uvmgr-mcp",
        }
    ):
        add_span_event("mcp.server.initializing", {
            "host": host,
            "port": port,
            "protocol": "mcp",
        })
        
        # Initialize telemetry counters
        metric_counter("mcp.server.starts")(1)
        
        try:
            add_span_event("mcp.server.starting")
            
            # Start the MCP server
            mcp.run()
            
            add_span_event("mcp.server.started", {
                "status": "running",
                "host": host,
                "port": port,
            })
            
            metric_counter("mcp.server.successful_starts")(1)
            
        except Exception as e:
            add_span_event("mcp.server.startup_failed", {
                "error": str(e),
                "error_type": type(e).__name__,
            })
            
            metric_counter("mcp.server.failed_starts")(1)
            
            # Re-raise the exception after logging
            raise


def create_instrumented_operation_result(
    success: bool,
    message: str,
    operation: str,
    duration: float | None = None,
    details: dict[str, Any] | None = None,
) -> OperationResult:
    """Create an OperationResult with automatic telemetry recording."""
    result = OperationResult(
        success=success,
        message=message,
        details=details,
        operation=operation,
        duration=duration,
    )
    
    # Automatically record telemetry
    result.record_telemetry()
    
    return result


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # This allows testing the server directly with telemetry
    run_mcp_server()
