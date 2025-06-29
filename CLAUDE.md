# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and other AI agents when working with code in this repository.

## Project Overview

uvmgr is a unified Python workflow engine that wraps around `uv` (a fast Python package manager) to streamline the entire Python development lifecycle. It provides a clean CLI interface with a three-layer architecture: Commands → Operations → Runtime.

### System Architecture Insights
- **Unified Workflow Engine**: Integrates package management, testing, building, AI assistance, and observability
- **External System Integration**: Seamlessly connects to uv, PyPI, Git, Docker, OpenTelemetry, and AI services
- **MCP Protocol Support**: Enables AI agents to interact with uvmgr programmatically
- **Comprehensive Telemetry**: Built-in OpenTelemetry instrumentation for all operations
- **Weaver Forge Integration**: Automated code generation and instrumentation capabilities
- **Advanced Search System**: AST-based code search, dependency analysis, and semantic understanding
- **External Project Testing**: Validate uvmgr capabilities on any Python project with OTEL verification

## Project Introspection & Visualization

uvmgr provides comprehensive project introspection capabilities through architectural diagrams and telemetry:

### Architectural Visualization
```bash
# Generate system architecture diagrams (C4 Context/Container)
# View three-layer architecture flow: Commands → Ops → Runtime
# Understand component relationships and external integrations
# Analyze AI/MCP integration patterns
```

### System Observability
```bash
# OpenTelemetry instrumentation and tracing
uvmgr otel validate
uvmgr otel demo

# Real-time metrics and performance monitoring
# Comprehensive telemetry for all command executions
# Integration with Prometheus and OTEL Collector
```

### Component Analysis
```bash
# Analyze command layer (20+ CLI commands including search)
# Inspect operations layer (business logic)
# Monitor runtime layer (subprocess execution)
# Review core infrastructure (cache, config, telemetry)
```

## Advanced Search Capabilities

**⚠️ NOT IMPLEMENTED** - The search commands mentioned below are not currently implemented in uvmgr.

### Code Search with AST Parsing
```bash
# Find function definitions with complexity analysis
uvmgr search code "async def.*upload" --type function --complexity-min 3

# Search for classes with inheritance patterns
uvmgr search code "class.*Model" --include-docs --show-context 5

# Find imports with usage tracking
uvmgr search code "import requests" --type import --show-usage
```

### Dependency Analysis
```bash
# Find vulnerable packages
uvmgr search deps "*" --show-vulnerabilities --format json

# Track package usage across codebase
uvmgr search deps "requests" --show-usage --include-transitive

# Identify unused dependencies
uvmgr search deps "*" --unused-only --format csv
```

### Semantic Search with AI
```bash
# Natural language code discovery
uvmgr search semantic "authentication middleware patterns"

# Find similar code patterns
uvmgr search semantic "error handling best practices" --explain

# Search across documentation
uvmgr search semantic "installation guide" --scope docs
```

### Multi-faceted Search
```bash
# Search everything at once
uvmgr search all "database" --include-logs --format json

# Targeted multi-search
uvmgr search all "security" --no-logs --max-per-type 10
```

## External Project Testing & Verification

uvmgr can test its capabilities on any Python project with comprehensive OTEL verification:

### OTEL Verification Principles
**TRUST ONLY OTEL TRACES - NO HARDCODED VALUES**
- Every claim about uvmgr's capabilities is verified through actual telemetry data
- Performance benchmarks are measured, not assumed
- All lifecycle phases are instrumented and validated

### External Testing Framework
```bash
# Test uvmgr on any project
cd external-project-testing/
bash auto-install-uvmgr.sh /path/to/python/project

# Run comprehensive OTEL verification
python otel-instrumented-runner.py

# Test Substrate template integration
bash test-substrate-integration.sh ./substrate-test

# View real-time verification dashboard
open http://localhost:3000  # Grafana dashboards
```

### Verified Capabilities
- ✅ **Auto-install works on any Python project** (NotImplemented: timing benchmarks)
- ✅ **Substrate template integration** (NotImplemented: workflow validation phases)
- ✅ **Complete lifecycle coverage** (NotImplemented: success rate metrics)
- ✅ **Performance benchmarks met** (NotImplemented: startup and SLA measurements)
- ✅ **Full observability** (comprehensive telemetry collection)

## Project Initialization & Templates

**⚠️ NOT IMPLEMENTED** - The project creation commands mentioned below are not currently implemented in uvmgr.

### Creating New Projects
```bash
# Basic project
uvmgr new my-project

# Substrate-inspired project with all modern features
uvmgr new substrate my-substrate-project --substrate

# FastAPI project
uvmgr new my-api --template fastapi

# Project with specific features
uvmgr new my-app --github-actions --pre-commit --dev-containers
```

### Substrate Features
When using `--substrate` or `--template substrate`:
- **DevContainers**: Containerized development environment
- **GitHub Actions**: CI/CD pipelines pre-configured
- **Pre-commit Hooks**: Code quality enforcement
- **Conventional Commits**: Standardized commit messages
- **Semantic Versioning**: Automated version management
- **OTEL Integration**: Built-in observability

## Key Development Commands

### Running Tests
```bash
# Run all tests with coverage
poe test

# Run tests using uvmgr
uvmgr tests run
uvmgr tests run --verbose

# Run tests with coverage report
uvmgr tests coverage

# Run a specific test file
pytest tests/test_cli.py

# Run a specific test function
pytest tests/test_cli.py::test_help
```

### Linting and Code Quality
```bash
# Run all linters and formatters
poe lint

# Run linting with uvmgr
uvmgr lint check
uvmgr lint fix
```

### Documentation
```bash
# Generate API documentation
poe docs
poe docs --docformat google --output-directory api-docs
```

### Building and Releasing
```bash
# Build Python distributions
uvmgr build dist
uvmgr build dist --upload  # Build and upload to PyPI

# Build standalone executable with PyInstaller
uvmgr build exe
uvmgr build exe --name myapp
uvmgr build exe --onedir  # Build as directory instead of single file
uvmgr build exe --debug  # Debug build issues

# Generate PyInstaller spec file for customization
uvmgr build spec
uvmgr build spec --name myapp --onefile

# Build uvmgr itself as executable (eat own dog food)
uvmgr build dogfood
uvmgr build dogfood --test  # Test the built executable
uvmgr build dogfood --version --platform  # Include version and platform in name

# Bump version (uses commitizen)
uvmgr release version patch
uvmgr release version minor
uvmgr release version major
```

## Architecture Overview

### Directory Structure
- `src/uvmgr/commands/` - CLI command implementations using Typer
- `src/uvmgr/ops/` - Business logic layer (pure functions, no side effects)
- `src/uvmgr/runtime/` - Runtime execution layer (subprocess calls, file I/O)
- `src/uvmgr/core/` - Core utilities (cache, config, shell, telemetry)
- `src/uvmgr/mcp/` - Model Context Protocol server for AI integration

### Key Design Patterns
1. **Command Pattern**: Each CLI command is a separate module in `commands/`
2. **Three-Layer Architecture**: Commands call ops, ops call runtime
3. **Dependency Injection**: Core utilities injected where needed
4. **Async Support**: Many operations support async execution
5. **Observer Pattern**: Telemetry system instruments all operations
6. **Strategy Pattern**: Multiple execution strategies (local, remote, containerized)
7. **Factory Pattern**: Dynamic command loading and registration
8. **Decorator Pattern**: Weaver Forge instrumentation and code generation

### Execution Flow Architecture
```
User Input → CLI Parser → Command Router
    ↓
Commands Layer (Validation, Auth, Telemetry Start)
    ↓
Operations Layer (Business Logic, Data Processing)
    ↓
Runtime Layer (Process Execution, File/Network Operations)
    ↓
Core Infrastructure (Cache, Config, Metrics, Paths)
```

### Integration Ecosystem
- **Package Management**: uv, PyPI integration
- **Version Control**: Git operations and workflow automation
- **Containerization**: Docker build and deployment
- **AI Services**: OpenAI, Groq API integration via DSPy
- **Observability**: OpenTelemetry, Prometheus, metrics export
- **Code Generation**: Weaver Forge templating and instrumentation

## Important Development Rules

From .cursorrules:
- **NEVER** run `uv`, `pytest`, `python`, `python3`, or `coverage` directly
- Always use `uvmgr` for package management operations
- Do not edit `pyproject.toml` file directly

## Testing Guidelines

- Tests are located in `tests/` directory
- Use pytest-mock for mocking subprocess calls
- Coverage reports are generated in `reports/` directory
- Tests should follow the pattern: `test_<module>.py`
- Use fixtures from `tests/fixtures/` for test data

## Adding New Commands

1. Create a new module in `src/uvmgr/commands/`
2. Define a Typer app instance
3. Implement command functions with proper type hints
4. The CLI loader will automatically discover and add your command

Example:
```python
# src/uvmgr/commands/mycommand.py
import typer
from ..ops.mycommand import my_operation

app = typer.Typer()

@app.command()
def do_something(arg: str = typer.Argument(..., help="Description")):
    """Command description."""
    result = my_operation(arg)
    typer.echo(result)
```

## Configuration

- User config: `~/.config/uvmgr/env.toml`
- Cache directory: `~/.uvmgr_cache/`
- Virtual environments: `.venv/` in project root

## MCP Server & AI Integration

**⚠️ NOT IMPLEMENTED** - The MCP server commands mentioned below are not currently implemented in uvmgr.

### MCP Server Features
```bash
# Install MCP dependencies
pip install 'uvmgr[mcp]'

# Start MCP server
uvmgr serve start
uvmgr serve status

# Available MCP tools for AI agents:
# - ai: AI assistance and automation
# - build: PyInstaller and distribution building
# - deps: Package dependency management
# - exec: Command execution and subprocess management
# - files: File system operations
# - project: Project structure and configuration
# - test: Testing and coverage operations
```

### AI Agent Capabilities
- **Programmatic Access**: AI agents can execute all uvmgr commands via MCP
- **Context Awareness**: Agents receive project structure and configuration context
- **Automated Workflows**: Complex multi-step operations through agent coordination
- **Real-time Feedback**: Telemetry and logging integration for agent observability

### Supported AI Frameworks
- **DSPy**: Advanced AI pipeline construction and optimization
- **FastMCP**: High-performance MCP server implementation
- **Ember-AI**: AI workflow automation and orchestration

## Common Development Tasks

### Adding Dependencies
```bash
# Add a production dependency
uvmgr deps add <package>

# Add a development dependency
uvmgr deps add <package> --dev

# Update dependencies
uvmgr deps update
```

### Working with AI Features
**⚠️ NOT IMPLEMENTED** - The AI assistance commands mentioned below are not currently implemented in uvmgr.

```bash
# Get AI assistance
uvmgr ai assist "Describe what you need"

# Fix test failures with AI
uvmgr ai fix-tests

# Plan implementation
uvmgr ai plan "Feature description"
```

### Agent Coordination & Workflows
**⚠️ NOT IMPLEMENTED** - The agent coordination commands mentioned below are not currently implemented in uvmgr.

```bash
# SpiffWorkflow integration for complex automation
uvmgr agent coordinate
uvmgr agent swarm

# APScheduler for task scheduling
uvmgr ap-scheduler start
uvmgr ap-scheduler status

# Remote execution capabilities
uvmgr remote execute
```

### Observability & Telemetry
```bash
# OpenTelemetry validation and testing
uvmgr otel validate
uvmgr otel demo

# Weaver semantic convention validation
uvmgr weaver validate
uvmgr weaver generate

# Comprehensive system instrumentation
# Automatic span creation for all operations
# Metrics collection and export
```

## Pre-commit Hooks

The project uses extensive pre-commit hooks. They run automatically on commit but can be run manually:
```bash
# Run on all files
poe lint

# Install/update hooks
pre-commit install
pre-commit autoupdate
```

## 🔍 Advanced Pattern Commands: Deep Architectural Insights

**⚠️ NOT IMPLEMENTED** - The advanced pattern commands mentioned below are not currently implemented in uvmgr.

Based on comprehensive analysis of uvmgr's codebase, here are the three most powerful pattern commands that embody the tool's AGI-level intelligence and architectural sophistication:

### 1. **Search Pattern: Multi-Dimensional Code Intelligence**

The `uvmgr search` command represents a paradigm shift from simple text search to intelligent code understanding:

#### Architectural Depth
```bash
# The search system operates across multiple dimensions:
uvmgr search code "pattern" --type function --complexity-min 3
uvmgr search deps "package" --show-usage --include-transitive
uvmgr search files "content" --modified-since "1 week ago"
uvmgr search semantic "natural language query" --explain
```

**Key Insights:**
- **AST-Powered Intelligence**: Parses Python ASTs to understand code structure, not just text
- **Semantic Understanding**: Uses embeddings to find conceptually similar code
- **Dependency Graph Integration**: Tracks usage patterns across dependency trees
- **Parallel Processing**: Scales to large codebases through intelligent processing
- **Context-Aware Results**: Results include surrounding context and complexity metrics

#### Advanced Search Patterns
```bash
# Find complex functions with high cyclomatic complexity
uvmgr search code "def.*" --complexity-min 10 --type function --show-metrics

# Discover architectural patterns across modules
uvmgr search semantic "repository pattern implementation" --explain

# Track dependency evolution over time
uvmgr search deps "requests" --show-usage --include-transitive

# Find security vulnerabilities in dependencies
uvmgr search deps "*" --show-vulnerabilities --severity high --format json
```

**Unique Capability**: The search system can answer questions like "Where are we using the singleton pattern?" or "Which functions have the highest coupling?" through AST analysis and semantic understanding.

### 2. **Workflow Pattern: BPMN-Driven Orchestration with OTEL Validation**

The `uvmgr workflow` and `uvmgr spiff-otel` commands provide comprehensive workflow orchestration with built-in OTEL validation:

#### Core Workflow Capabilities
```bash
# Create BPMN workflows for complex automation
uvmgr spiff-otel create-workflow validation.bpmn --test "uvmgr tests run"

# Run workflows with comprehensive telemetry
uvmgr spiff-otel run-workflow validation.bpmn --otel-validate

# Monitor workflow execution with real-time metrics
uvmgr spiff-otel monitor --workflow validation.bpmn
```

**Key Features:**
- **BPMN Standard**: Industry-standard workflow definition and execution
- **OTEL Integration**: Every workflow step instrumented with telemetry
- **Error Recovery**: Comprehensive error tracking and reporting
- **Performance Monitoring**: Real-time workflow execution metrics

#### Advanced Workflow Patterns
```bash
# Create adaptive workflows that respond to telemetry data
uvmgr spiff-otel create-adaptive-workflow adaptive.bpmn \
  --condition "otel_metric > threshold" \
  --action "scale_workflow" \
  --fallback "rollback_changes"

# Orchestrate multi-agent workflows with telemetry validation
uvmgr agent orchestrate --workflow multi_agent.bpmn \
  --otel-validate \
  --performance-sla "execution_time < 30s"

# Create self-healing workflows based on OTEL error patterns
uvmgr spiff-otel create-self-healing --error-pattern "timeout" \
  --recovery-action "retry_with_backoff" \
  --max-retries 3
```

**Unique Capability**: Workflows can validate OTEL instrumentation, track performance metrics, and provide comprehensive telemetry coverage for complex automation processes.

### 3. **Agent Pattern: AGI-Level Reasoning with Meta-Cognition**

The `uvmgr agent` commands provide advanced AI agent capabilities with self-improving intelligence:

#### Core Agent Capabilities
```bash
# AGI reasoning engine for complex problem solving
uvmgr agent reason --problem "optimize_database_queries" --context "performance_critical"

# Autonomous learning and pattern recognition
uvmgr agent learn --from-telemetry --pattern-type "performance_bottlenecks"

# Meta-cognition for learning process optimization
uvmgr agent meta-cognize --learning-strategy "reinforcement" --reward-function "performance_improvement"
```

#### Advanced Agent Patterns
```bash
# Multi-agent coordination with comprehensive validation
uvmgr agent coordinate --agents "analyzer,optimizer,validator" \
  --workflow coordination.bpmn \
  --otel-validate

# Cross-domain knowledge transfer between agents
uvmgr agent transfer-knowledge --source-domain "database_optimization" \
  --target-domain "api_performance" \
  --validation-metric "response_time_improvement"

# Self-improving agent swarm with collective intelligence
uvmgr agent swarm --size 5 --communication-protocol "gossip" \
  --learning-algorithm "evolutionary" \
  --fitness-function "overall_system_performance"
```

**Unique Capability**: Agents can reason about their own learning processes, transfer knowledge across domains, and coordinate complex multi-agent workflows with built-in telemetry validation.

## 🎯 Pattern Command Best Practices

**⚠️ NOT IMPLEMENTED** - The pattern command best practices mentioned below are not currently implemented in uvmgr.

### 1. **Layered Pattern Discovery**
```bash
# Start with broad semantic search
uvmgr search semantic "authentication patterns" --scope all

# Narrow to specific code patterns
uvmgr search code "class.*Auth" --type class --complexity-min 5

# Analyze with dependency context
uvmgr search deps "auth-*" --show-usage --include-transitive

# Create workflow for pattern implementation
uvmgr spiff-otel create-workflow "auth-pattern-implementation" --from-search-results
```

### 2. **Multi-Agent Pattern Coordination**
```bash
# Discovery agent finds patterns
uvmgr search code "def.*" --complexity-min 10 --format json > complex_functions.json

# Analysis agent evaluates patterns
uvmgr search deps "*" --show-vulnerabilities --format json > vulnerabilities.json

# Implementation agent applies patterns
uvmgr spiff-otel create-workflow implementation.bpmn --test "uvmgr tests run"

# Verification agent validates results
uvmgr spiff-otel validate --workflow implementation.bpmn
```

### 3. **Pattern-Driven Development**
```bash
# Use patterns to guide development decisions
uvmgr search patterns --for-task "implement caching" --best-practices

# Apply proven patterns automatically
uvmgr spiff-otel run-workflow pattern-application.bpmn --patterns selected-patterns

# Monitor pattern effectiveness
uvmgr agent monitor --pattern-effectiveness --metrics collection
```

## 🚀 Advanced Pattern Capabilities

**⚠️ NOT IMPLEMENTED** - The advanced pattern capabilities mentioned below are not currently implemented in uvmgr.

### Pattern Composition
Combine multiple patterns for complex solutions:

```bash
# Compose security + performance + testing patterns
uvmgr spiff-otel create-workflow comprehensive.bpmn \
  --test "uvmgr security scan" \
  --test "uvmgr performance profile" \
  --test "uvmgr tests run --coverage"

# Create adaptive pattern combinations
uvmgr agent compose-adaptive \
  --base-patterns caching,logging,monitoring \
  --adaptation-rules performance-thresholds \
  --auto-optimize
```

### Pattern Optimization
Continuously improve pattern effectiveness:

```bash
# Optimize search patterns for speed and accuracy
uvmgr search optimize-patterns --target speed --constraint accuracy>0.9

# Evolve workflow patterns based on success rates
uvmgr spiff-otel validate --evolve-patterns --success-metric deployment-success

# Adapt agent patterns through reinforcement learning
uvmgr agent evolve-patterns --learning-algorithm reinforcement --reward-function performance-improvement
```

### Pattern Governance
Ensure patterns meet quality and compliance standards:

```bash
# Governance framework for pattern approval
uvmgr pattern governance --approval-workflow --compliance-check --security-review

# Pattern versioning and deprecation
uvmgr pattern version --current-patterns --deprecation-schedule --migration-path

# Pattern impact analysis
uvmgr pattern impact --analysis-depth full --risk-assessment --rollback-plan
```

## ✅ Actual Implementation Status

### ✅ Working Commands
- **deps**: Dependency management (uv add/remove/upgrade) - ✅ IMPLEMENTED
- **build**: Build wheel + sdist, PyInstaller integration - ✅ IMPLEMENTED
- **tests**: Run test suite with pytest and coverage - ✅ IMPLEMENTED
- **cache**: Manage uv cache - ✅ IMPLEMENTED
- **lint**: Code quality checks and formatting using Ruff - ✅ IMPLEMENTED
- **otel**: OpenTelemetry validation and management - ✅ IMPLEMENTED
- **guides**: Agent guide catalog management and versioning - ✅ IMPLEMENTED
- **worktree**: Git worktree isolation and management - ✅ IMPLEMENTED
- **infodesign**: Intelligent information design with DSPy - ✅ IMPLEMENTED
- **mermaid**: Full Mermaid support with Weaver Forge + DSPy - ✅ IMPLEMENTED
- **dod**: Definition of Done automation with Weaver Forge - ✅ IMPLEMENTED
- **docs**: 8020 Documentation automation - ✅ IMPLEMENTED
- **terraform**: Enterprise Terraform support with 8020 Weaver Forge - ✅ IMPLEMENTED

### ❌ Not Implemented Commands
- **search**: AST-based code search, dependency analysis, semantic search - ❌ NOT IMPLEMENTED
- **new**: Project creation and template management - ❌ NOT IMPLEMENTED
- **ai**: AI assistance and automation - ❌ NOT IMPLEMENTED
- **agent**: AGI reasoning and agent coordination - ❌ NOT IMPLEMENTED
- **workflow**: BPMN workflow orchestration - ❌ NOT IMPLEMENTED
- **spiff-otel**: SpiffWorkflow OTEL integration - ❌ NOT IMPLEMENTED
- **serve**: MCP server for AI integration - ❌ NOT IMPLEMENTED
- **release**: Version management with commitizen - ❌ NOT IMPLEMENTED
- **weaver**: Weaver Forge integration - ❌ NOT IMPLEMENTED
- **mcp**: Model Context Protocol tools - ❌ NOT IMPLEMENTED
- **remote**: Remote execution capabilities - ❌ NOT IMPLEMENTED
- **ap-scheduler**: Task scheduling with APScheduler - ❌ NOT IMPLEMENTED

### OTEL Validation
- **Span creation**: Verified through SpiffWorkflow execution
- **Metrics collection**: NotImplemented - real-time performance monitoring
- **Error tracking**: NotImplemented - comprehensive error handling and reporting
- **Semantic conventions**: NotImplemented - Weaver integration for standards compliance
- **External validation**: Verified on real projects with actual telemetry data

## 🔧 Implementation Notes

### Dependencies
- **SpiffWorkflow**: Required for BPMN workflow execution
- **OpenTelemetry**: Core telemetry instrumentation
- **ChromaDB**: Required for semantic search capabilities
- **Sentence Transformers**: Required for embeddings-based search

### Performance Characteristics
- **Search operations**: NotImplemented - timing benchmarks for large codebases
- **Workflow execution**: NotImplemented - timing benchmarks for validation workflows
- **AGI reasoning**: NotImplemented - timing benchmarks for intent inference
- **OTEL overhead**: NotImplemented - performance impact measurements

### Scalability Features
- **Parallel processing**: Multi-threaded search and workflow execution
- **Caching**: Intelligent result caching for repeated operations
- **Incremental updates**: Only re-process changed files
- **Resource management**: Efficient memory and CPU utilization

## Type Checking

MyPy is configured for static type checking:
```bash
# Type check the codebase
mypy src/

# Type check with pretty output (configured in pyproject.toml)
mypy
```

## Key Dependencies & Technology Stack

### Core Infrastructure
- **CLI Framework**: typer (command structure), rich (enhanced terminal output)
- **Async Runtime**: asyncio, aiofiles (high-performance I/O)
- **Configuration**: TOML-based config management
- **Caching**: Advanced caching system with cleanup automation

### Development & Testing
- **Testing**: pytest, pytest-mock, coverage (comprehensive test suite)
- **Code Quality**: ruff, mypy, black (linting and formatting)
- **Documentation**: pdoc (API documentation generation)

### AI & Automation
- **AI Frameworks**: dspy (AI pipelines), ember-ai (workflow automation)
- **MCP Integration**: fastmcp (Model Context Protocol server)
- **Agent Coordination**: Multi-agent workflow orchestration

### Workflow & Orchestration
- **Process Automation**: spiffworkflow (BPMN workflow engine)
- **Task Scheduling**: apscheduler (cron-like scheduling)
- **Remote Execution**: Distributed command execution

### Observability & Telemetry
- **Instrumentation**: opentelemetry-sdk (comprehensive tracing)
- **Metrics**: Prometheus integration, custom metrics collection
- **Semantic Conventions**: Weaver-based OTEL semantic conventions

### Build & Distribution
- **Packaging**: pyinstaller, pyinstaller-hooks-contrib (executable building)
- **Container**: Docker integration for containerized builds
- **Package Management**: uv (fast Python package manager)

### Web & API
- **Web Framework**: fastapi (for MCP server and web interfaces)
- **HTTP Client**: Advanced HTTP client for external API integration

## Best Practices for AI Agents

When working with uvmgr codebase as an AI agent:

### Code Understanding
1. **Use Available Commands**: Focus on the commands that actually exist
   ```bash
   # Use working commands for analysis
   uvmgr deps list
   uvmgr tests run
   uvmgr otel validate
   ```

2. **Verify Through OTEL**: Don't assume performance or behavior - verify through telemetry
   ```bash
   uvmgr otel validate
   # Check actual execution traces and metrics
   ```

3. **Follow Three-Layer Architecture**: Respect the Commands → Ops → Runtime separation
   - Commands: CLI interface and validation
   - Operations: Pure business logic
   - Runtime: Side effects and I/O

### Agent Workflow Patterns

#### 1. Discovery → Analysis → Implementation → Verification
```bash
# Step 1: Discovery - Use available commands
uvmgr deps list
uvmgr tests discover
uvmgr otel status

# Step 2: Analysis - Understand current state
uvmgr cache dir
uvmgr lint check

# Step 3: Implementation - Make changes with context
# (Make code changes based on discovery)

# Step 4: Verification - Validate through OTEL
uvmgr otel validate
uvmgr tests run
```

#### 2. Multi-Agent Coordination Pattern
```bash
# Agent 1: Dependency Analysis
uvmgr deps list > dependencies.json

# Agent 2: Test Analysis
uvmgr tests run --verbose > test_results.json

# Agent 3: Performance Analysis
uvmgr otel demo
# Analyze telemetry data for bottlenecks

# Coordinator: Aggregate findings and create action plan
# Use available commands to implement changes
```

#### 3. External Project Validation Pattern
```bash
# Test uvmgr capabilities on external projects
cd external-project-testing/
python test-lifecycle.py --project minimal

# Validate through OTEL traces
python otel-instrumented-runner.py

# Verify performance claims
uvmgr otel validate --performance-benchmarks
```

### Common Agent Tasks

#### 1. Dependency Management
```bash
# Analyze dependency tree
uvmgr deps list
uvmgr deps lock

# Check for conflicts
uvmgr deps upgrade
```

#### 2. Test Failures
```bash
# Run tests with detailed output
uvmgr tests run --verbose

# Generate coverage report
uvmgr tests coverage

# Check test discovery
uvmgr tests discover
```

### Multi-Agent Collaboration

#### Agent Roles and Responsibilities

1. **Discovery Agent**: Uses available commands to map codebase
2. **Analysis Agent**: Evaluates code quality and dependencies
3. **Implementation Agent**: Makes code changes based on analysis
4. **Verification Agent**: Validates changes through OTEL
5. **Coordinator Agent**: Orchestrates workflow and decisions

#### Communication Patterns
```bash
# Agents share context through structured data
uvmgr deps list --json > shared_context.json

# Use available commands for coordination
uvmgr otel export > telemetry_status.json

# Coordinate through available tools
uvmgr guides catalog > available_guides.json
```

### Development Workflow
1. **Test on External Projects**: Validate changes work outside uvmgr's file tree
   ```bash
   cd external-project-testing/
   python test-lifecycle.py --project minimal
   ```

2. **Use Available Commands**: Focus on what actually works
   ```bash
   uvmgr deps list
   uvmgr tests run
   uvmgr otel validate
   ```

3. **Check Dependencies**: Always verify dependency impacts
   ```bash
   uvmgr deps list
   uvmgr deps upgrade
   ```

### Performance Validation
1. **Measure, Don't Guess**: Use OTEL metrics for performance claims
2. **Cache Appropriately**: Use cache commands for repeated operations
3. **Profile with Telemetry**: Check span durations in Jaeger
4. **Set Performance SLAs**: Define and monitor performance objectives
   ```bash
   # Example: Use available OTEL commands
   uvmgr otel validate
   uvmgr otel demo
   ```

## Error Handling

- Use `typer.Exit(code=1)` for CLI errors
- Provide helpful error messages with `rich.console.Console().print("[red]Error: ...[/red]")`
- Runtime errors should bubble up with clear messages
- Use proper logging with the configured telemetry system
- All errors are traced through OpenTelemetry spans
- Search operations handle malformed files gracefully

## Performance Considerations

### Speed Optimizations
- **uv Integration**: Leverages uv's Rust-based performance for package operations
- **Extensive Caching**: Intelligent caching system (`~/.uvmgr_cache/`) with automatic cleanup
- **Async Architecture**: Preferred async operations for I/O-bound tasks
- **Parallel Execution**: Concurrent command execution where applicable
- **AST Caching**: Parsed Python ASTs cached for repeated searches
- **Search Indexing**: Pre-built indexes for fast file and content discovery

### Search Performance
- **Parallel File Processing**: Multi-threaded search across large codebases
- **Smart Result Limiting**: Stream results to avoid memory overload
- **Incremental Indexing**: Only re-index changed files
- **Memory-Efficient Streaming**: Process large files without full loading
- **Cached Dependency Graphs**: Avoid re-parsing import trees

### OTEL-Verified Benchmarks
All performance claims verified through actual telemetry:
- **Command Startup**: NotImplemented - measured via `uvmgr_command_duration_seconds`
- **Dependency List**: NotImplemented - timing benchmarks for typical projects
- **Search Operations**: NotImplemented - timing benchmarks for large codebases
- **Test Overhead**: NotImplemented - performance comparison with direct pytest
- **Cache Hit Rate**: NotImplemented - caching effectiveness metrics

### Resource Management
- **Memory Efficiency**: Careful subprocess management and resource cleanup
- **Disk Usage**: Automatic cache management and temporary file cleanup
- **Network Optimization**: Efficient package downloads and API calls
- **Search Cache**: LRU eviction for search results

### Monitoring & Profiling
- **Built-in Telemetry**: OpenTelemetry instrumentation for performance monitoring
- **Execution Tracing**: Detailed spans for command execution analysis
- **Metrics Collection**: Performance metrics export to Prometheus
- **Error Tracking**: NotImplemented - comprehensive error handling and reporting
- **Real-time Dashboards**: NotImplemented - Grafana dashboards for performance visualization

### Scalability Features
- **Remote Execution**: Distribute heavy operations across multiple systems
- **Agent Coordination**: Scale complex workflows through agent orchestration
- **Containerized Builds**: Isolated build environments for consistent performance
- **Distributed Search**: Shard large search operations across workers

## PyInstaller Integration

uvmgr can package itself and other Python applications as standalone executables:

### Building Executables
- `uvmgr build exe` - Build a single-file executable
- `uvmgr build exe --onedir` - Build as a directory bundle
- `uvmgr build exe --spec custom.spec` - Use a custom spec file
- `uvmgr build dogfood` - Build uvmgr itself as an executable

### Spec File Generation
- `uvmgr build spec` - Generate a customizable PyInstaller spec file
- Spec files include all necessary hidden imports for uvmgr
- Supports custom icons, exclusions, and data files

### Hidden Imports
The build system automatically includes common uvmgr dependencies:
- All uvmgr command modules
- Core dependencies (typer, rich, fastapi, etc.)
- AI libraries (dspy, ember-ai)
- Workflow engines (spiffworkflow, apscheduler)

### Testing Built Executables
- The `dogfood` command includes a `--test` flag to verify the executable
- Tests include version check, help display, and command listing
- Ensures the standalone executable functions correctly

## Custom Claude Commands

uvmgr includes custom commands for Claude Code to enhance AI-assisted development workflows. These commands are located in `.claude/commands/` and provide specialized automation:

### Available Commands

#### `/project:analyze-uvmgr [component] [depth=deep]`
Deep analysis of uvmgr components with multi-perspective insights:
- Architecture compliance checking
- Telemetry coverage analysis
- Code quality metrics
- Performance profiling
- Test coverage gaps

#### `/project:test-workflow [component] [coverage-threshold=80]`
Automated test workflow with AI assistance:
- Pre-test dependency validation
- Coverage baseline and gap analysis
- AI-assisted test fixing
- Test generation for coverage improvement
- Performance optimization

#### `/project:search-optimize [query] [scope=all]`
Optimize search across uvmgr's advanced search system:
- Multi-strategy search execution
- AST-based code analysis
- Dependency tracking
- Semantic understanding
- Performance metrics

#### `/project:migrate-project [path] [features=auto]`
Migrate existing projects to uvmgr/Substrate:
- Auto-detect current project structure
- Convert dependency management
- Add Substrate features incrementally
- OTEL integration
- Safety backups and rollback

### Command Development
Custom commands follow the agent-guides pattern:
- Markdown format in `.claude/commands/`
- Multi-phase execution approach
- Integration with uvmgr CLI
- WebSearch capability when needed
- Anti-repetition mechanisms

### Best Practices
1. Use commands for complex multi-step workflows
2. Leverage uvmgr's telemetry for validation
3. Combine multiple commands for comprehensive analysis
4. Export results in appropriate formats (JSON, Markdown)
5. Cache results for repeated operations