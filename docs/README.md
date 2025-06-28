# uvmgr Documentation

Welcome to the comprehensive documentation for `uvmgr`, a unified Python workflow engine with advanced observability and AI integration capabilities.

## Documentation Overview

This documentation is organized into several sections to help you find the information you need quickly and efficiently.

## 📚 Documentation Index

### Getting Started
- **[README.md](../README.md)** - Project overview, quick start, and command reference
- **[HOWTO.md](../HOWTO.md)** - Comprehensive user guide with detailed examples
- **[NEW-PROJECT.md](../NEW-PROJECT.md)** - Guide for creating new Typer CLI projects

### Core Features

#### 🔧 Development Workflow
- **[Code Quality Guide](code-quality.md)** - Linting, formatting, and development server
- **[OpenTelemetry Guide](otel-guide.md)** - Comprehensive OTEL integration guide
- **[Weaver Command Suite](weaver-command-suite.md)** - Semantic convention management

#### 🤖 AI Integration
- **[MCP Integration](mcp/README.md)** - Model Context Protocol server for AI assistants

#### 📊 Observability
- **[OpenTelemetry Integration](otel-integration.md)** - OTEL setup and usage guide

### Project Documentation

#### 📋 Project Management
- **[NEW-PROJECT-PRD.md](../NEW-PROJECT-PRD.md)** - Product requirements document
- **[WEAVER-FORGE-COMPLETE-BLUEPRINT.md](../WEAVER-FORGE-COMPLETE-BLUEPRINT.md)** - Weaver implementation blueprint
- **[WEAVER-FORGE-IMPLEMENTATION-STATUS.md](../WEAVER-FORGE-IMPLEMENTATION-STATUS.md)** - Implementation status tracking
- **[WEAVER-FORGE-UPGRADE.md](../WEAVER-FORGE-UPGRADE.md)** - Upgrade guide

#### 🔍 Analysis and Reports
- **[OTEL_IMPLEMENTATION_SUMMARY.md](../OTEL_IMPLEMENTATION_SUMMARY.md)** - OTEL implementation summary
- **[OTEL_VALIDATION_SUMMARY.md](../OTEL_VALIDATION_SUMMARY.md)** - OTEL validation results
- **[CLAUDE.md](../CLAUDE.md)** - Claude AI integration notes

## 🚀 Quick Navigation

### I'm New to uvmgr
1. Start with **[README.md](../README.md)** for an overview
2. Follow the **[HOWTO.md](../HOWTO.md)** for detailed usage
3. Check **[NEW-PROJECT.md](../NEW-PROJECT.md)** if you want to create similar projects

### I Want to Use Code Quality Features
- **[Code Quality Guide](code-quality.md)** - Complete guide to linting and formatting

### I Want to Set Up Observability
- **[OpenTelemetry Guide](otel-guide.md)** - Comprehensive OTEL setup and usage
- **[OpenTelemetry Integration](otel-integration.md)** - Quick OTEL integration guide

### I Want to Use AI Integration
- **[MCP Integration](mcp/README.md)** - Set up AI assistant integration

### I Want to Manage Semantic Conventions
- **[Weaver Command Suite](weaver-command-suite.md)** - Complete Weaver documentation

## 📖 Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── code-quality.md             # Code quality and linting guide
├── otel-guide.md               # Comprehensive OpenTelemetry guide
├── weaver-command-suite.md     # Weaver semantic convention tools
├── otel-integration.md         # OTEL setup and usage guide
└── mcp/                        # Model Context Protocol documentation
    └── README.md               # MCP server and AI integration guide
```

## 🎯 Common Use Cases

### Setting Up a New Project
```bash
# Create new project
uvmgr new my-project

# Set up code quality
uvmgr lint fix

# Add dependencies
uvmgr deps add requests pytest

# Run tests
uvmgr tests run
```

### Setting Up Observability
```bash
# Start OTEL infrastructure
docker-compose -f docker-compose.otel.yml up -d

# Run commands with telemetry
uvmgr deps add requests
uvmgr tests run

# View traces in Jaeger: http://localhost:16686
# View metrics in Prometheus: http://localhost:9090
```

### Setting Up AI Integration
```bash
# Start MCP server
uvmgr mcp serve

# Configure Claude Desktop to use uvmgr
# Add to Claude Desktop config:
# "uvmgr": {
#   "command": "python3.12",
#   "args": ["-m", "uvmgr", "mcp", "serve"]
# }
```

### Managing Semantic Conventions
```bash
# Install Weaver
uvmgr weaver install

# Validate conventions
uvmgr weaver check

# Generate code from conventions
uvmgr weaver generate python
```

## 🔧 Command Reference

### Core Development
- `uvmgr new` - Create new Python project
- `uvmgr deps` - Manage dependencies
- `uvmgr tests` - Run test suite
- `uvmgr build` - Build packages
- `uvmgr release` - Manage versions

### Code Quality
- `uvmgr lint check` - Check code for issues
- `uvmgr lint format` - Format code
- `uvmgr lint fix` - Fix all auto-fixable issues
- `uvmgr serve` - Start development server

### Observability
- `uvmgr otel coverage` - Analyze telemetry coverage
- `uvmgr otel validate` - Validate OTEL setup
- `uvmgr otel test` - Test telemetry functionality
- `uvmgr weaver` - Manage semantic conventions

### AI Integration
- `uvmgr mcp serve` - Start MCP server
- `uvmgr ai ask` - Ask AI for help
- `uvmgr ai plan` - Generate development plans

### Utilities
- `uvmgr exec` - Execute scripts
- `uvmgr shell` - Open interactive shell
- `uvmgr tool` - Install and run tools
- `uvmgr cache` - Manage cache
- `uvmgr agent` - Run BPMN workflows

## 📝 Contributing to Documentation

### Adding New Documentation

1. **Create the file** in the appropriate directory
2. **Update this index** to include the new file
3. **Add cross-references** to related documentation
4. **Include examples** and practical usage
5. **Test the examples** to ensure they work

### Documentation Standards

- Use clear, concise language
- Include practical examples
- Provide both basic and advanced usage
- Cross-reference related documentation
- Keep examples up-to-date with the codebase

### Documentation Structure

Each documentation file should include:

1. **Overview** - What the feature does
2. **Quick Start** - Basic usage examples
3. **Detailed Guide** - Comprehensive coverage
4. **Configuration** - Setup and customization
5. **Examples** - Practical use cases
6. **Troubleshooting** - Common issues and solutions
7. **References** - Links to related documentation

## 🆘 Getting Help

### Documentation Issues
- Check if the information is in the right place
- Look for cross-references to related topics
- Search for similar issues in the documentation

### Code Issues
- Check the [GitHub issues](https://github.com/seanchatmangpt/uvmgr/issues)
- Review the [OpenTelemetry documentation](https://opentelemetry.io/docs/)
- Check the [Weaver documentation](https://opentelemetry.io/docs/weaver/)

### Community Support
- [GitHub Discussions](https://github.com/seanchatmangpt/uvmgr/discussions)
- [OpenTelemetry Slack](https://cloud-native.slack.com/archives/C01N7PP1THC)

## 📈 Documentation Metrics

This documentation covers:

- **Core Features**: 15+ major command groups
- **Advanced Features**: OTEL, Weaver, MCP integration
- **Examples**: 100+ practical code examples
- **Configuration**: Complete setup guides
- **Troubleshooting**: Common issues and solutions

## 🔄 Documentation Updates

This documentation is updated regularly to reflect:

- New features and commands
- Updated configuration options
- Improved examples and workflows
- Bug fixes and workarounds
- Community feedback and requests

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Maintainer**: uvmgr Documentation Team

For questions about this documentation, please open an issue on GitHub or contribute directly through pull requests. 