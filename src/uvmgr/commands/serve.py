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

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import ServerAttributes, ServerOperations
from uvmgr.core.shell import colour, colour_stderr

from .. import main as cli_root

mcp_app = typer.Typer(help="MCP (Model Context Protocol) server commands.")
cli_root.app.add_typer(mcp_app, name="mcp")


@mcp_app.command("serve")
@instrument_command("mcp_serve", track_args=True)
def serve(
    transport: str = typer.Option(
        "stdio",
        "--transport",
        "-t",
        help="Transport protocol to use. Options:\n"
        "- stdio: Direct communication (default, best for Claude Desktop)\n"
        "- sse: Server-Sent Events for real-time streaming\n"
        "- http: RESTful HTTP endpoints",
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        help="Host address to bind the server to. Use 0.0.0.0 to allow external connections",
    ),
    port: int = typer.Option(
        8000, "--port", "-p", help="Port number to listen on. Only used for SSE and HTTP transports"
    ),
    auth_token: str = typer.Option(
        None,
        "--auth-token",
        envvar="UVMGR_MCP_AUTH_TOKEN",
        help="Bearer token for authentication. Required for secure deployments",
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

    Examples
    --------
        # Start server with stdio transport (for Claude Desktop)
        uvmgr mcp serve

        # Start SSE server on custom port for web clients
        uvmgr mcp serve --transport sse --port 3000

        # Start HTTP server with authentication
        uvmgr mcp serve --transport http --auth-token mytoken

        # Allow external connections on HTTP server
        uvmgr mcp serve --transport http --host 0.0.0.0 --port 8080
    """
    # Track MCP server startup
    add_span_attributes(
        **{
            ServerAttributes.OPERATION: ServerOperations.START,
            ServerAttributes.PROTOCOL: "mcp",
            ServerAttributes.HOST: host,
            ServerAttributes.PORT: port,
            "server.transport": transport,
            "server.auth_enabled": auth_token is not None,
        }
    )
    add_span_event("mcp.server.startup", {
        "transport": transport,
        "host": host,
        "port": port,
        "auth": auth_token is not None
    })
    try:
        from uvmgr.mcp import mcp

        # Use stderr for stdio transport to avoid interfering with MCP protocol
        print_fn = colour_stderr if transport == "stdio" else colour

        # Print server info
        print_fn("\n═══════════════════════════════════════════════════════", "blue")
        print_fn(f"  uvmgr MCP Server - {mcp.name}", "blue")
        print_fn("═══════════════════════════════════════════════════════", "blue")

        # Installation instructions
        print_fn("\n📋 Installation Requirements:", "yellow")
        print_fn("  • Python 3.12 or higher", "white")
        print_fn("  • Install uvmgr: pip install uvmgr", "white")
        print_fn("  • Or from source: pip install -e .", "white")

        # Count available features - simplified approach
        print_fn("\n📦 Available features:", "green")
        print_fn("  • Multiple tools for project management", "white")
        print_fn("  • Resources for project information", "white")
        print_fn("  • Prompts for AI assistance", "white")

        if auth_token:
            print_fn("\n🔒 Authentication enabled", "yellow")
            try:
                from fastmcp.auth import BearerTokenAuth

                mcp.add_auth(BearerTokenAuth(token=auth_token))
                print_fn("  ✓ Bearer token authentication configured", "green")
            except ImportError:
                print_fn("  ⚠️  FastMCP auth module not available", "yellow")
                print_fn("  Server will run without authentication", "yellow")
                auth_token = None  # Disable auth for display purposes
        if transport == "stdio":
            print_fn("🚀 Starting MCP server (stdio transport)...", "green")
            print_fn("\nMCP server now available via stdio", "cyan")
            print_fn("Connection: Direct stdio communication", "cyan")
            print_fn("\nFor Claude Desktop, add to config:", "yellow")
            print_fn("  1. Open Claude Desktop settings", "white")
            print_fn("  2. Go to 'Developer' > 'Edit Config'", "white")
            print_fn("  3. Add this to the 'mcpServers' section:", "white")
            print_fn('     "uvmgr": {', "cyan")
            print_fn('       "command": "python3.12",', "cyan")
            print_fn('       "args": ["-m", "uvmgr", "mcp", "serve"]', "cyan")
            print_fn("     }", "cyan")
            print_fn("\nPress Ctrl+C to stop the server", "yellow")
            mcp.run()
        elif transport == "sse":
            url = f"http://{host}:{port}/sse"
            print_fn("🚀 Starting MCP server (SSE transport)...", "green")
            print_fn("\nMCP server now available at:", "cyan")
            print_fn(f"  {url}", "white")
            print_fn("\nConnect with:", "yellow")
            print_fn(f'  Client("{url}")', "white")
            print_fn("\nFor Claude.ai web interface:", "yellow")
            print_fn("  1. Click 'Add integration' in settings", "white")
            print_fn("  2. Integration name: uvmgr", "white")
            print_fn(f"  3. Integration URL: {url}", "white")
            print_fn("\nPress Ctrl+C to stop the server", "yellow")
            mcp.run(transport="sse", host=host, port=port)
        elif transport == "http":
            url = f"http://{host}:{port}/mcp"
            print_fn("🚀 Starting MCP server (HTTP transport)...", "green")
            print_fn("\nMCP server now available at:", "cyan")
            print_fn(f"  {url}", "white")
            if auth_token:
                print_fn("\nAuthentication required:", "yellow")
                print_fn(f"  Bearer token: {auth_token[:8]}...", "white")
            print_fn("\nConnect with:", "yellow")
            print_fn(f'  Client("{url}")', "white")
            print_fn("\nFor Claude.ai web interface:", "yellow")
            print_fn("  1. Click 'Add integration' in settings", "white")
            print_fn("  2. Integration name: uvmgr", "white")
            print_fn(f"  3. Integration URL: {url}", "white")
            print_fn("\nPress Ctrl+C to stop the server", "yellow")
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
        colour("\n\n✋ MCP server stopped by user", "yellow")
        colour("Thank you for using uvmgr MCP!", "cyan")
        raise typer.Exit(0)
    except Exception as e:
        colour(f"❌ Error running MCP server: {e}", "red")
        raise typer.Exit(1)
