# Model Context Protocol (MCP) Integration

The `uvmgr` MCP server enables AI assistants like Claude to interact with your Python projects through a standardized protocol. This integration provides AI assistants with access to project information, tools, and resources.

## Overview

The MCP server provides:

- **Tools**: Commands that AI assistants can execute on your behalf
- **Resources**: Read-only access to project files and information
- **Prompts**: Pre-defined prompts for common development tasks
- **Multiple Transport Methods**: stdio, SSE, and HTTP protocols

## Quick Start

### 1. Start the MCP Server

```bash
# Start with stdio transport (recommended for Claude Desktop)
uvmgr mcp serve

# Start with SSE transport for web clients
uvmgr mcp serve --transport sse --port 3000

# Start with HTTP transport and authentication
uvmgr mcp serve --transport http --auth-token mytoken
```

### 2. Connect from Claude Desktop

1. Open Claude Desktop settings
2. Go to 'Developer' > 'Edit Config'
3. Add to the 'mcpServers' section:
   ```json
   "uvmgr": {
     "command": "python3.12",
     "args": ["-m", "uvmgr", "mcp", "serve"]
   }
   ```

### 3. Connect from Claude.ai Web Interface

1. Click 'Add integration' in settings
2. Integration name: `uvmgr`
3. Integration URL: 
   - For SSE: `http://localhost:8000/sse`
   - For HTTP: `http://localhost:8000/mcp`

## Transport Methods

### stdio (Default)
- **Best for**: Claude Desktop
- **Configuration**: No network setup required
- **Usage**: Direct communication through standard I/O

### SSE (Server-Sent Events)
- **Best for**: Web clients, real-time streaming
- **Configuration**: Requires host and port
- **Usage**: Real-time event streaming

### HTTP
- **Best for**: Traditional API access, secure deployments
- **Configuration**: Requires host, port, and optional authentication
- **Usage**: RESTful HTTP endpoints

## Available Tools

The MCP server provides the following tools that AI assistants can use:

### Project Management
- `list_files`: List project files and directories
- `read_file`: Read file contents
- `write_file`: Write content to files
- `run_command`: Execute shell commands
- `search_files`: Search for files by pattern

### Dependency Management
- `add_dependency`: Add packages to project
- `remove_dependency`: Remove packages from project
- `list_dependencies`: List installed dependencies
- `update_dependencies`: Update project dependencies

### Testing and Quality
- `run_tests`: Execute test suite
- `run_lint`: Run code linting
- `run_format`: Format code
- `check_coverage`: Generate coverage reports

### Build and Release
- `build_package`: Build distribution packages
- `bump_version`: Bump project version
- `create_release`: Create new release

### Development Tools
- `start_server`: Start development server
- `open_shell`: Open interactive Python shell
- `install_tool`: Install development tools

## Available Resources

### Project Information
- `pyproject.toml`: Project configuration
- `README.md`: Project documentation
- `CHANGELOG.md`: Release history
- `requirements.txt`: Dependencies (if present)

### Source Code
- `src/`: Source code directory
- `tests/`: Test files
- `docs/`: Documentation files
- `examples/`: Example code

### Configuration Files
- `.gitignore`: Git ignore rules
- `.pre-commit-config.yaml`: Pre-commit hooks
- `docker-compose.yml`: Container configuration
- `Dockerfile`: Container definition

## Available Prompts

The MCP server provides pre-defined prompts for common development tasks:

### Code Review
- "Review this code for best practices"
- "Check for security vulnerabilities"
- "Suggest performance improvements"

### Testing
- "Generate unit tests for this function"
- "Create integration tests"
- "Write test documentation"

### Documentation
- "Generate docstring for this function"
- "Create API documentation"
- "Write user guide"

### Refactoring
- "Refactor this code for better readability"
- "Extract common functionality"
- "Improve error handling"

## Security Considerations

### Authentication
For production deployments, use authentication:

```bash
# Set authentication token
export UVMGR_MCP_AUTH_TOKEN="your-secure-token"

# Start server with authentication
uvmgr mcp serve --transport http --auth-token $UVMGR_MCP_AUTH_TOKEN
```

### Network Security
- Use `127.0.0.1` (default) for local-only access
- Use `0.0.0.0` only when external access is required
- Consider using HTTPS in production environments

### File Access
- The MCP server respects file permissions
- Only files accessible to the running user can be read/written
- Consider using a dedicated user for the MCP server

## Troubleshooting

### Connection Issues
```bash
# Check if server is running
curl http://localhost:8000/health

# Check server logs
uvmgr mcp serve --transport http --port 8000
```

### Authentication Issues
```bash
# Verify token is set
echo $UVMGR_MCP_AUTH_TOKEN

# Test with curl
curl -H "Authorization: Bearer $UVMGR_MCP_AUTH_TOKEN" \
     http://localhost:8000/mcp
```

### Permission Issues
```bash
# Check file permissions
ls -la

# Run with appropriate user
sudo -u mcp-user uvmgr mcp serve
```

## Advanced Configuration

### Custom Transport Configuration
```bash
# Custom host and port
uvmgr mcp serve --transport http --host 0.0.0.0 --port 8080

# Custom path for HTTP transport
uvmgr mcp serve --transport http --path /api/mcp
```

### Environment Variables
```bash
# Set authentication token
export UVMGR_MCP_AUTH_TOKEN="your-token"

# Set custom endpoint
export UVMGR_MCP_ENDPOINT="https://your-server.com/mcp"

# Set log level
export UVMGR_LOG_LEVEL="DEBUG"
```

### Integration with Other Tools
```bash
# Start with systemd service
systemctl start uvmgr-mcp

# Start with Docker
docker run -p 8000:8000 uvmgr mcp serve --transport http

# Start with Kubernetes
kubectl apply -f k8s/mcp-deployment.yaml
```

## Examples

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "uvmgr": {
      "command": "python3.12",
      "args": ["-m", "uvmgr", "mcp", "serve"],
      "env": {
        "UVMGR_MCP_AUTH_TOKEN": "your-token"
      }
    }
  }
}
```

### Web Client Integration
```javascript
// Connect to SSE server
const client = new MCPClient("http://localhost:8000/sse");

// Connect to HTTP server
const client = new MCPClient("http://localhost:8000/mcp", {
  headers: {
    "Authorization": "Bearer your-token"
  }
});
```

### Python Client
```python
from mcp import Client

# Connect to server
client = Client("http://localhost:8000/mcp")

# List available tools
tools = await client.list_tools()

# Execute a tool
result = await client.call_tool("list_files", {"path": "."})
```

## Development

### Adding New Tools
To add new tools to the MCP server:

1. Create tool function in `src/uvmgr/mcp/tools/`
2. Register tool in `src/uvmgr/mcp/__init__.py`
3. Add tool documentation

### Adding New Resources
To add new resources:

1. Create resource handler in `src/uvmgr/mcp/resources/`
2. Register resource in `src/uvmgr/mcp/__init__.py`
3. Add resource documentation

### Testing MCP Server
```bash
# Test with built-in client
uvmgr mcp test

# Test specific transport
uvmgr mcp test --transport http --port 8000
```

## Support

For issues and questions:

1. Check the [main documentation](../README.md)
2. Review [OpenTelemetry integration](../otel-integration.md)
3. Open an issue on GitHub
4. Check the logs for detailed error messages 