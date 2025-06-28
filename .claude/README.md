# Claude Code Custom Commands for uvmgr

This directory contains custom commands for Claude Code (claude.ai/code) to enhance AI-assisted development workflows with uvmgr.

## Installation

These commands are automatically available when Claude Code is working in the uvmgr repository. They can also be installed globally:

```bash
# Global installation (for use across all projects)
mkdir -p ~/.claude/commands
cp .claude/commands/*.md ~/.claude/commands/
```

## Available Commands

### `/project:analyze-uvmgr`
Deep component analysis with architecture validation, telemetry coverage, and code quality metrics.

### `/project:test-workflow`
Comprehensive test automation with coverage analysis, AI-assisted fixing, and performance optimization.

### `/project:search-optimize`
Multi-strategy search optimization leveraging uvmgr's AST parsing, dependency analysis, and semantic search.

### `/project:migrate-project`
Migrate existing Python projects to uvmgr with Substrate-inspired modern development practices.

## Command Structure

Each command follows a consistent structure:
- **Usage**: Command syntax and parameters
- **Purpose**: What the command accomplishes
- **Phases**: Step-by-step execution flow
- **Examples**: Common usage patterns
- **Output**: Expected results and formats

## Integration with uvmgr

All commands are designed to work seamlessly with uvmgr's features:
- Three-layer architecture (Commands → Ops → Runtime)
- OpenTelemetry instrumentation
- Advanced search capabilities
- AI integration through MCP
- Comprehensive error handling

## Development Guidelines

When creating new commands:
1. Follow the multi-phase execution pattern
2. Integrate with uvmgr's telemetry system
3. Provide clear examples and output formats
4. Include error handling and rollback options
5. Document integration points with uvmgr features

## Best Practices

1. **Use OTEL for Validation**: Always verify claims through telemetry data
2. **Leverage Search First**: Use uvmgr's search before making changes
3. **Test on External Projects**: Validate outside uvmgr's file tree
4. **Cache Appropriately**: Use search cache for repeated operations
5. **Follow Architecture**: Respect the three-layer separation

## Resources

- [Agent Guides](https://github.com/tokenbender/agent-guides) - Original inspiration
- [uvmgr Documentation](../CLAUDE.md) - Main project documentation
- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code) - Official documentation

## Contributing

To add new commands:
1. Create a new `.md` file in `.claude/commands/`
2. Follow the existing command format
3. Test the command thoroughly
4. Update this README with the new command
5. Submit a pull request with examples

## Command Naming Convention

- Use descriptive names that indicate the action
- Prefix with appropriate scope (e.g., `project:`, `test:`, `search:`)
- Keep names concise but clear
- Use hyphens for multi-word commands