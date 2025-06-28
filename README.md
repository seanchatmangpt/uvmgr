# uvmgr

[![PyPI Version](https://img.shields.io/pypi/v/uvmgr.svg)](https://pypi.org/project/uvmgr/)
[![License](https://img.shields.io/pypi/l/uvmgr.svg)](https://github.com/seanchatmangpt/uvmgr/blob/main/LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/seanchatmangpt/uvmgr/ci.yml)](https://github.com/seanchatmangpt/uvmgr/actions)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Enabled-green.svg)](https://opentelemetry.io/)

**`uvmgr`** is a next-generation unified Python workflow engine powered by `uv` with advanced AGI capabilities, comprehensive observability, and intelligent automation. It provides a single, consistent command-line interface that streamlines the entire development lifecycle—from project creation to production deployment—with built-in artificial intelligence and autonomous learning.

## 🚀 Key Features

### Core Development
* **Project Scaffolding**: Create modern Python projects from templates with AI-assisted customization
* **Dependency Management**: Intelligent dependency resolution and management with `uv`
* **Testing & Coverage**: Comprehensive test suite execution with intelligent test optimization
* **Builds & Releases**: Automated package building and semantic versioning with Commitizen
* **Code Quality**: Advanced linting, formatting, and security scanning with Ruff integration

### 🤖 AI & AGI Capabilities
* **Intent Inference Engine**: Understands the "why" behind commands, not just the "what"
* **Causal Reasoning**: Discovers cause-effect relationships from temporal patterns
* **Autonomous Learning**: Self-improving agents that learn from experience
* **Cross-Domain Intelligence**: Pattern recognition that transfers across different project types
* **Meta-Cognition**: Agents that think about thinking and optimize their own learning processes
* **AI-Assisted Development**: Leverage language models for code review, planning, and test generation

### 📊 Observability & Telemetry
* **100% OpenTelemetry Coverage**: Complete instrumentation across all layers
* **Weaver Integration**: Semantic convention management and validation
* **Real-time Metrics**: Performance monitoring and optimization insights
* **Distributed Tracing**: End-to-end request tracking across the development workflow
* **Intelligent Alerting**: AI-powered anomaly detection and performance insights

### 🔧 Advanced Automation
* **Workflow Orchestration**: BPMN workflow execution with SpiffWorkflow integration
* **Task Scheduling**: Advanced process scheduling with APScheduler
* **MCP Server**: Model Context Protocol server for AI assistant integration
* **Plugin System**: Extensible architecture with custom command plugins
* **Remote Execution**: Distributed command execution across multiple environments

### 🛡️ Security & Compliance
* **Vulnerability Scanning**: Automated security analysis with Safety integration
* **Code Security**: Bandit integration for security linting
* **Dependency Auditing**: Comprehensive dependency vulnerability assessment
* **Compliance Monitoring**: Automated compliance checking and reporting

## 🎯 Quick Start

### Installation

```bash
pip install uvmgr
```

### Create Your First Project

```bash
# Create a new FastAPI project with AI-assisted setup
uvmgr new my-awesome-api --fastapi --ai-guided

# Navigate to your project
cd my-awesome-api

# Add dependencies with intelligent suggestions
uvmgr deps add "fastapi[all]" "sqlalchemy" "alembic"

# Run tests with intelligent optimization
uvmgr tests run --optimize

# Build and release with automated versioning
uvmgr build dist --upload
```

### AI-Powered Development

```bash
# Ask AI for development guidance
uvmgr ai ask "How can I optimize this FastAPI endpoint for high concurrency?"

# Generate intelligent test plans
uvmgr ai plan "Implement Redis caching layer" --out CACHING_PLAN.md

# Auto-fix failing tests with AI assistance
uvmgr ai fix-tests --auto-patch

# Get intelligent code reviews
uvmgr ai review src/my_awesome_api/api.py
```

### Observability & Monitoring

```bash
# Start comprehensive observability stack
docker-compose -f docker-compose.otel.yml up -d

# Run commands with full telemetry
uvmgr deps add requests --trace
uvmgr tests run --metrics

# View traces in Jaeger (http://localhost:16686)
# View metrics in Prometheus (http://localhost:9090)
# View logs in Grafana (http://localhost:3000)
```

## 📚 Command Reference

### Core Development Commands
```bash
uvmgr new <name> [--template] [--fastapi] [--cli] [--ai-guided]  # Create new project
uvmgr deps add <package> [--dev] [--optional]                    # Add dependencies
uvmgr deps remove <package>                                      # Remove dependencies
uvmgr deps upgrade [--all] [--major]                             # Upgrade dependencies
uvmgr tests run [--optimize] [--parallel] [--coverage]           # Run test suite
uvmgr build dist [--upload] [--sign]                             # Build packages
uvmgr release bump [--major|--minor|--patch]                     # Version management
```

### AI & Intelligence Commands
```bash
uvmgr ai ask <question> [--model] [--context]                    # AI assistance
uvmgr ai plan <task> [--out] [--detailed]                        # Generate plans
uvmgr ai review <file> [--suggestions]                           # Code review
uvmgr ai fix-tests [--auto-patch] [--explain]                    # Test fixing
uvmgr agent run <workflow> [--autonomous]                        # Run AI agents
uvmgr knowledge search <query> [--semantic]                      # Knowledge search
```

### Observability Commands
```bash
uvmgr otel validate [--comprehensive]                            # Validate OTEL setup
uvmgr otel metrics [--export] [--dashboard]                      # View metrics
uvmgr otel traces [--filter] [--analyze]                         # Analyze traces
uvmgr weaver install [--semantic-conventions]                    # Install Weaver
uvmgr weaver validate [--strict] [--fix]                         # Validate conventions
uvmgr forge generate [--template] [--customize]                  # Generate code
```

### Automation Commands
```bash
uvmgr workflow run <bpmn-file> [--variables]                     # Run BPMN workflows
uvmgr ap-scheduler add <task> [--cron] [--interval]              # Schedule tasks
uvmgr automation create <name> [--template]                      # Create automation
uvmgr remote execute <command> [--hosts] [--parallel]            # Remote execution
```

### Quality & Security Commands
```bash
uvmgr lint check [--fix] [--strict]                              # Code linting
uvmgr lint format [--check] [--diff]                             # Code formatting
uvmgr security scan [--vulnerabilities] [--compliance]           # Security scanning
uvmgr performance profile [--memory] [--cpu] [--io]              # Performance analysis
```

## 🏗️ Architecture

uvmgr follows a clean, three-layer architecture designed for extensibility and observability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Layer                            │
│  (CLI Interface - Typer Applications)                       │
├─────────────────────────────────────────────────────────────┤
│                   Operations Layer                          │
│  (Business Logic - Pure Python)                             │
├─────────────────────────────────────────────────────────────┤
│                    Runtime Layer                            │
│  (Side Effects - Subprocesses, Network Calls)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  OpenTelemetry  │
                    │   Observability │
                    └─────────────────┘
```

### AGI Integration

The AGI capabilities are built into every layer:

- **Intent Inference**: Commands understand context and purpose
- **Causal Discovery**: Automatic pattern recognition across workflows
- **Autonomous Learning**: Self-improving performance over time
- **Cross-Domain Transfer**: Knowledge sharing between project types
- **Meta-Cognition**: Self-optimizing learning processes

## 🔧 Advanced Configuration

### Dependency Groups

uvmgr supports comprehensive dependency management with specialized groups:

```bash
# Core development
uvmgr deps add pytest --group dev

# Web development
uvmgr deps add fastapi uvicorn --group web

# Data science
uvmgr deps add pandas numpy --group data

# Cloud deployment
uvmgr deps add boto3 azure-identity --group cloud

# Full stack (all groups)
uvmgr deps add --group full
```

### OpenTelemetry Configuration

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:9464

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

### AI Model Configuration

```bash
# Use local Ollama models
export OLLAMA_BASE_URL=http://localhost:11434
uvmgr ai ask "Explain async programming" --model ollama/phi3:medium-128k

# Use cloud models
export OPENAI_API_KEY=your-key
uvmgr ai ask "Review this code" --model gpt-4

# Use Claude models
export ANTHROPIC_API_KEY=your-key
uvmgr ai ask "Generate tests" --model claude-3-sonnet
```

## 📊 Performance & Scalability

### Intelligent Optimization

- **Test Parallelization**: Automatic test suite optimization
- **Dependency Resolution**: Smart caching and conflict resolution
- **Build Acceleration**: Incremental builds with intelligent caching
- **Memory Management**: Efficient resource utilization
- **Network Optimization**: Intelligent retry and fallback strategies

### Monitoring & Alerting

- **Real-time Metrics**: Performance counters and histograms
- **Anomaly Detection**: AI-powered performance monitoring
- **Resource Tracking**: Memory, CPU, and I/O monitoring
- **Error Analysis**: Intelligent error categorization and resolution
- **Performance Insights**: Automated optimization recommendations

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Set up development environment**:
   ```bash
   git clone <your-fork>
   cd uvmgr
   uvmgr deps sync --all-extras
   pre-commit install
   ```
3. **Run tests**:
   ```bash
   uvmgr tests run --coverage
   ```
4. **Make your changes** and submit a pull request

### Development Guidelines

- Follow the existing code style (Ruff + MyPy)
- Add comprehensive tests for new features
- Update documentation for API changes
- Ensure OpenTelemetry instrumentation for new commands
- Follow semantic versioning for releases

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **[uv](https://github.com/astral-sh/uv)**: Fast Python package installer and resolver
- **[OpenTelemetry](https://opentelemetry.io/)**: Observability framework
- **[Weaver](https://github.com/open-telemetry/semantic-conventions)**: Semantic conventions
- **[SpiffWorkflow](https://github.com/sartography/SpiffWorkflow)**: BPMN workflow engine
- **[FastMCP](https://github.com/jlowin/fastmcp)**: Model Context Protocol server

## 📞 Support

- **Documentation**: [Comprehensive User Guide](HOWTO.md)
- **Issues**: [GitHub Issues](https://github.com/seanchatmangpt/uvmgr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/seanchatmangpt/uvmgr/discussions)
- **AI Assistant**: Use `uvmgr ai ask` for instant help

---

**Built with ❤️ and AI by the uvmgr community**