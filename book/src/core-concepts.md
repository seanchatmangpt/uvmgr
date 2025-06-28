# Core Concepts

## Unified Workflow
uvmgr provides a single CLI to manage the entire Python project lifecycle, abstracting away the complexity of multiple tools.

## Project Structure
- Uses `pyproject.toml` for configuration
- Source code in `src/`
- Tests in `tests/`
- Documentation in `docs/` and `book/`

## Command Groups
- **Development:** Project creation, dependency management, testing, building, releasing
- **Quality:** Linting, formatting, code quality checks
- **AI & Automation:** AI integration, workflow automation, MCP server
- **Observability:** OpenTelemetry, semantic conventions

## Extensibility
- Easily integrates with new tools and workflows
- Designed for modern Python development 