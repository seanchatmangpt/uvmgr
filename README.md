# uvmgr

[![PyPI Version](https://img.shields.io/pypi/v/uvmgr.svg)](https://pypi.org/project/uvmgr/)
[![License](https://img.shields.io/pypi/l/uvmgr.svg)](https://github.com/seanchatmangpt/uvmgr/blob/main/LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/seanchatmangpt/uvmgr/ci.yml)](https://github.com/seanchatmangpt/uvmgr/actions)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Enabled-green.svg)](https://opentelemetry.io/)

**`uvmgr`** is a unified Python workflow engine powered by `uv` with advanced AI capabilities, comprehensive OpenTelemetry observability, Weaver Forge integration, and intelligent automation. It provides a single, consistent command-line interface that streamlines the entire development lifecycle with built-in artificial intelligence and autonomous learning.

## 🚀 Key Features

### Core Development
* **Dependency Management**: Intelligent dependency resolution and management with `uv`
* **Testing & Coverage**: Comprehensive test suite execution with intelligent optimization
* **Builds & Distribution**: Automated package building with wheel and sdist support
* **Code Quality**: Advanced linting, formatting, and security scanning with Ruff integration
* **Cache Management**: Intelligent caching for dependencies and build artifacts

### 🤖 AI & AGI Capabilities
* **Intent Inference Engine**: Understands the "why" behind commands through AGI reasoning
* **Causal Discovery**: Discovers cause-effect relationships from temporal patterns
* **Autonomous Learning**: Self-improving agents that learn from experience
* **Cross-Domain Intelligence**: Pattern recognition that transfers across different project types
* **Meta-Cognition**: Agents that think about thinking and optimize their own learning processes
* **DSPy Integration**: Intelligent information design and optimization

### 📊 Observability & Telemetry
* **100% OpenTelemetry Coverage**: Complete instrumentation across all layers
* **Weaver Integration**: Semantic convention management and validation
* **Real-time Metrics**: Performance monitoring and optimization insights
* **Distributed Tracing**: End-to-end request tracking across the development workflow
* **Intelligent Alerting**: AI-powered anomaly detection and performance insights
* **SpiffWorkflow Integration**: BPMN workflow execution with full OTEL instrumentation

### 🔧 Advanced Automation
* **Definition of Done (DoD)**: Automated DoD criteria validation with Weaver Forge exoskeleton
* **Workflow Orchestration**: BPMN workflow execution with SpiffWorkflow integration
* **Git Worktree Management**: Multi-project development with isolated environments
* **Information Design**: Intelligent documentation and architecture generation
* **Mermaid Integration**: Advanced diagram generation with Weaver Forge + DSPy

### 🛡️ Security & Compliance
* **Vulnerability Scanning**: Automated security analysis and dependency auditing
* **Code Security**: Comprehensive security linting and validation
* **Compliance Monitoring**: Automated compliance checking and reporting
* **Terraform Integration**: Enterprise Terraform support with 8020 Weaver Forge integration

## 🎯 Quick Start

### Installation

```bash
pip install uvmgr
```

### Basic Usage

```bash
# Add dependencies with intelligent suggestions
uvmgr deps add "fastapi[all]" "sqlalchemy" "alembic"

# Run tests with intelligent optimization
uvmgr tests run --optimize

# Build packages
uvmgr build dist

# Check code quality
uvmgr lint check --fix
```

### AI-Powered Development

```bash
# Generate intelligent documentation
uvmgr docs generate --executive

# Create Mermaid diagrams with Weaver Forge
uvmgr mermaid generate --weaver

# Execute Definition of Done automation
uvmgr dod complete

# Validate OTEL integration
uvmgr otel validate --comprehensive
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

## 📚 Complete Command Reference

### Core Development Commands

#### Dependency Management (`uvmgr deps`)
```bash
uvmgr deps add <package> [--dev] [--optional]                    # Add packages
uvmgr deps remove <package>                                      # Remove packages
uvmgr deps upgrade [--all] [--major]                             # Upgrade packages
uvmgr deps list                                                  # List installed packages
uvmgr deps lock                                                  # Generate/update lock file
```

#### Build System (`uvmgr build`)
```bash
uvmgr build dist                                                 # Build wheel + sdist
uvmgr build wheel                                                # Build Python wheel
uvmgr build sdist                                                # Build source distribution
uvmgr build exe                                                  # Build standalone executable
uvmgr build spec                                                 # Generate PyInstaller spec
uvmgr build dogfood                                              # Build uvmgr executable
```

#### Testing (`uvmgr tests`)
```bash
uvmgr tests run                                                  # Run comprehensive test suite
uvmgr tests discover                                             # Discover and analyze test structure
uvmgr tests generate                                             # Generate test templates (8020)
uvmgr tests coverage                                             # Generate coverage reports
uvmgr tests ci                                                   # Run CI tests locally
```

#### Code Quality (`uvmgr lint`)
```bash
uvmgr lint check                                                 # Run Ruff linter
uvmgr lint format                                                # Format code with Ruff
uvmgr lint fix                                                   # Fix auto-fixable issues
```

#### Cache Management (`uvmgr cache`)
```bash
uvmgr cache dir                                                  # Show cache directory
uvmgr cache prune                                                # Clean up cache
```

### AI & Intelligence Commands

#### Information Design (`uvmgr infodesign`)
```bash
uvmgr infodesign analyze                                         # Analyze information structure
uvmgr infodesign generate                                        # Generate intelligent documentation
uvmgr infodesign optimize                                        # Optimize information architecture
uvmgr infodesign extract                                         # Extract knowledge entities
uvmgr infodesign graph                                           # Create knowledge graphs
uvmgr infodesign template                                        # Manage information templates
```

#### Mermaid Integration (`uvmgr mermaid`)
```bash
uvmgr mermaid generate                                           # Generate diagrams with DSPy
uvmgr mermaid weaver                                             # Generate from Weaver Forge data
uvmgr mermaid export                                             # Export to various formats
uvmgr mermaid validate                                           # Validate diagram syntax
uvmgr mermaid preview                                            # Preview diagrams
uvmgr mermaid templates                                          # Manage diagram templates
uvmgr mermaid analyze                                            # Analyze and improve diagrams
```

#### Agent Guides (`uvmgr guides`)
```bash
uvmgr guides catalog                                             # Browse guide catalog
uvmgr guides fetch                                               # Fetch guides from repository
uvmgr guides list                                                # List cached guides
uvmgr guides update                                              # Update guides
uvmgr guides validate                                            # Validate guide structure
uvmgr guides pin                                                 # Pin guide versions
uvmgr guides cache                                               # Manage guide cache
```

### Observability Commands

#### OpenTelemetry (`uvmgr otel`)
```bash
uvmgr otel coverage                                              # Validate OTEL instrumentation
uvmgr otel validate                                              # Run 8020 OTEL validation
uvmgr otel test                                                  # Generate test telemetry
uvmgr otel semconv                                               # Manage semantic conventions
uvmgr otel status                                                # Show OTEL status
uvmgr otel demo                                                  # Demonstrate OTEL features
uvmgr otel workflow-validate                                     # OTEL validation with SpiffWorkflow
uvmgr otel export                                                # Export telemetry configuration
uvmgr otel dashboard                                             # Manage OTEL dashboard stack
uvmgr otel config                                                # Manage OTLP exporter
```

### Automation Commands

#### Definition of Done (`uvmgr dod`)
```bash
uvmgr dod complete                                               # Execute complete DoD automation
uvmgr dod exoskeleton                                            # Initialize Weaver Forge exoskeleton
uvmgr dod validate                                               # Validate DoD criteria
uvmgr dod pipeline                                               # Create DevOps pipeline automation
uvmgr dod testing                                                # Execute comprehensive testing
uvmgr dod status                                                 # Show project DoD status
```

#### Documentation (`uvmgr docs`)
```bash
uvmgr docs generate                                              # Generate complete documentation
uvmgr docs executive                                             # Generate executive documentation
uvmgr docs architecture                                          # Generate solution architecture
uvmgr docs implementation                                        # Generate implementation docs
uvmgr docs developer                                             # Generate developer docs
uvmgr docs coverage                                              # Analyze documentation coverage
uvmgr docs publish                                               # Publish documentation
```

#### Git Worktree (`uvmgr worktree`)
```bash
uvmgr worktree create                                            # Create new Git worktree
uvmgr worktree list                                              # List all worktrees
uvmgr worktree remove                                            # Remove worktree
uvmgr worktree switch                                            # Switch worktree
uvmgr worktree isolate                                           # Create isolated environment
uvmgr worktree cleanup                                           # Clean up unused worktrees
uvmgr worktree status                                            # Show worktree status
```

### Infrastructure Commands

#### Terraform (`uvmgr terraform`)
```bash
uvmgr terraform init                                             # Initialize workspace with 8020 patterns
uvmgr terraform plan                                             # Generate plan with 8020 analysis
uvmgr terraform apply                                            # Apply infrastructure with validation
uvmgr terraform 8020-plan                                        # Generate 8020 infrastructure plan
uvmgr terraform weaver-forge                                     # Run Weaver Forge optimization
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

- **Intent Inference**: Commands understand context and purpose through AGI reasoning
- **Causal Discovery**: Automatic pattern recognition across workflows
- **Autonomous Learning**: Self-improving performance over time
- **Cross-Domain Transfer**: Knowledge sharing between project types
- **Meta-Cognition**: Self-optimizing learning processes

## 🔧 Advanced Configuration

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

### Weaver Forge Integration

```bash
# Initialize Weaver Forge exoskeleton
uvmgr dod exoskeleton

# Run Weaver Forge optimization
uvmgr terraform weaver-forge --optimize --otel-validate

# Generate Mermaid diagrams from Weaver data
uvmgr mermaid weaver --export png
```

### Definition of Done Automation

```bash
# Execute complete DoD automation
uvmgr dod complete

# Validate DoD criteria
uvmgr dod validate --detailed

# Show project DoD status
uvmgr dod status
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
- **[DSPy](https://github.com/stanfordnlp/dspy)**: Declarative self-improving language programs

## 📞 Support

- **Documentation**: [Comprehensive User Guide](CLAUDE.md)
- **Issues**: [GitHub Issues](https://github.com/seanchatmangpt/uvmgr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/seanchatmangpt/uvmgr/discussions)

---

**Built with ❤️ and AI by the uvmgr community**