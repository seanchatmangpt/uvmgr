"""
uvmgr mcp serve
===============

Start the MCP (Model Context Protocol) server for AI assistant integration.

The MCP server enables AI assistants like Claude to interact with your Python projects
through a standardized protocol. It supports multiple transport methods:

- stdio: Direct communication through standard I/O (best for Claude Desktop)
- SSE: Server-Sent Events for real-time streaming (good for web clients)
- HTTP: RESTful HTTP endpoints for traditional API access

Each transport method has different use cases and configuration options.
"""

import typer
from uvmgr.core.shell import colour
from .. import main as cli_root

mcp_app = typer.Typer(help="MCP (Model Context Protocol) server commands.")
cli_root.app.add_typer(mcp_app, name="mcp")


@mcp_app.command("serve")
def serve(
    transport: str = typer.Option(
        "stdio", 
        "--transport", 
        "-t",
        help="Transport protocol to use. Options:\n"
             "- stdio: Direct communication (default, best for Claude Desktop)\n"
             "- sse: Server-Sent Events for real-time streaming\n"
             "- http: RESTful HTTP endpoints"
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        help="Host address to bind the server to. Use 0.0.0.0 to allow external connections"
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port number to listen on. Only used for SSE and HTTP transports"
    ),
    auth_token: str = typer.Option(
        None,
        "--auth-token",
        envvar="UVMGR_MCP_AUTH_TOKEN",
        help="Bearer token for authentication. Required for secure deployments"
    ),
):
    """
    Start the MCP server for uvmgr functionality.
    
    MCP enables AI assistants to interact with your Python projects through a
    standardized protocol. This command starts an MCP server that can be
    connected to by compatible clients like Claude Desktop or custom applications.
    
    The server supports three transport methods:
    
    1. stdio (default):
       - Direct communication through standard I/O
       - Best for Claude Desktop integration
       - No network configuration needed
       
    2. SSE (Server-Sent Events):
       - Real-time streaming communication
       - Good for web clients and custom applications
       - Requires host and port configuration
       
    3. HTTP:
       - Traditional RESTful API endpoints
       - Compatible with any HTTP client
       - Supports authentication for secure deployments
    
    Examples:
        # Start server with stdio transport (for Claude Desktop)
        uvmgr mcp serve
        
        # Start SSE server on custom port for web clients
        uvmgr mcp serve --transport sse --port 3000
        
        # Start HTTP server with authentication
        uvmgr mcp serve --transport http --auth-token mytoken
        
        # Allow external connections on HTTP server
        uvmgr mcp serve --transport http --host 0.0.0.0 --port 8080
    """
    try:
        from uvmgr.mcp import mcp
        if auth_token:
            colour(f"🔒 Enabling authentication", "yellow")
            try:
                from fastmcp.auth import BearerTokenAuth
                mcp.add_auth(BearerTokenAuth(token=auth_token))
            except ImportError:
                colour("❌ FastMCP auth not available", "red")
                raise typer.Exit(1)
        if transport == "stdio":
            colour("🚀 Starting MCP server (stdio transport)...", "green")
            colour("Connect with Claude Desktop or compatible MCP client", "cyan")
            mcp.run()
        elif transport == "sse":
            colour(f"🚀 Starting MCP server (SSE transport) on http://{host}:{port}/sse", "green")
            mcp.run(transport="sse", host=host, port=port)
        elif transport == "http":
            colour(f"🚀 Starting MCP server (HTTP transport) on http://{host}:{port}/mcp", "green")
            mcp.run(transport="streamable-http", host=host, port=port, path="/mcp")
        else:
            colour(f"❌ Unknown transport: {transport}", "red")
            colour("Valid options: stdio, sse, http", "yellow")
            raise typer.Exit(1)
    except ImportError as e:
        if "fastmcp" in str(e).lower():
            colour("❌ FastMCP is not installed", "red")
            colour("Install with: pip install 'uvmgr[mcp]' or 'pip install fastmcp'", "yellow")
        else:
            colour(f"❌ Import error: {e}", "red")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        colour("\n✋ MCP server stopped", "yellow")
        raise typer.Exit(0)
    except Exception as e:
        colour(f"❌ Error running MCP server: {e}", "red")
        raise typer.Exit(1)
