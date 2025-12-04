# Re-Enabled Commands Guide

This guide covers the three advanced commands that have been re-enabled and hardened: `search`, `agent`, and `spiff_otel`.

## Overview

| Command | Lines | Status | Dependencies |
|---------|-------|--------|--------------|
| **search** | 2000+ | ✅ Ready | chromadb, sentence-transformers |
| **agent** | 2000+ | ✅ Ready | spiffworkflow |
| **spiff_otel** | 1800+ | ✅ Ready | spiffworkflow |

## Installation

### Prerequisites
- Python 3.11+
- uvmgr installed: `pip install -e .`

### Install Dependencies for Re-Enabled Commands

```bash
# For search command (semantic search with AI)
pip install chromadb sentence-transformers tree-sitter

# For agent and spiff_otel commands (BPMN workflow execution)
pip install spiffworkflow opentelemetry-sdk

# Or install everything
pip install -e ".[full]"
```

---

## 1. Search Command

Advanced code and dependency search with AST parsing, semantic understanding, and caching.

### Basic Usage

```bash
# Search Python code by pattern
uvmgr search code "def.*async" --type function

# Find dependency usage
uvmgr search deps "requests" --show-usage

# Semantic search (AI-powered)
uvmgr search semantic "authentication patterns"

# Search files
uvmgr search files "*.py" --modified-since "1 week ago"

# Multi-faceted search
uvmgr search all "database" --include-code --include-deps
```

### Advanced Options

```bash
# Search with complexity filtering
uvmgr search code "def" --complexity-min 3 --complexity-max 10

# Include test files and documentation
uvmgr search code "function" --include-tests --include-docs

# Show context lines
uvmgr search code "pattern" --context 10

# Output as JSON
uvmgr search code "def" --format json
```

### Features

- **AST-based**: Understands Python code structure, not just text
- **Semantic**: Uses AI embeddings for intelligent searching
- **Cached**: Results cached for performance
- **Parallel**: Processes large codebases efficiently
- **Type-aware**: Find functions, classes, variables, imports, decorators

---

## 2. Agent Command

Execute BPMN (Business Process Model and Notation) workflows with SpiffWorkflow engine.

### Basic Usage

```bash
# Run a BPMN workflow
uvmgr agent run workflow.bpmn

# Validate BPMN file structure
uvmgr agent validate workflow.bpmn

# Test workflow execution with OTEL validation
uvmgr agent test workflow.bpmn

# Get workflow statistics
uvmgr agent stats workflow.bpmn

# Parse and display workflow structure
uvmgr agent parse workflow.bpmn --format json
```

### BPMN File Example

Create a file named `example.bpmn`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                 xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                 id="Definitions_1">
  <bpmn:process id="Process_1" name="Example Process">
    <bpmn:startEvent id="StartEvent_1"/>
    <bpmn:task id="Task_1" name="Do Something">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:endEvent id="EndEvent_1">
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1"/>
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1"/>
  </bpmn:process>
</bpmn:definitions>
```

Then run:

```bash
uvmgr agent run example.bpmn
```

### Features

- **Full BPMN Support**: Execute BPMN 2.0 workflows
- **Instrumented**: Comprehensive OpenTelemetry tracing
- **Validated**: Built-in BPMN validation
- **Observable**: Real-time execution metrics
- **Error Tracking**: Full error context with traces

---

## 3. SpiffOTEL Command

SpiffWorkflow-based OpenTelemetry validation and testing.

### Basic Usage

```bash
# Run OTEL validation workflow
uvmgr spiff_otel validate

# Run with custom workflow
uvmgr spiff_otel validate --workflow custom_otel.bpmn

# Validate external projects
uvmgr spiff_otel validate --external-project /path/to/project

# Export validation results
uvmgr spiff_otel validate --export results.json

# List available workflows
uvmgr spiff_otel list-workflows

# Create new validation workflow
uvmgr spiff_otel create-workflow new_validator.bpmn
```

### What It Validates

- ✅ Span creation and management
- ✅ Metrics collection
- ✅ Error tracking and reporting
- ✅ Semantic conventions compliance
- ✅ Performance tracking
- ✅ Instrumentation effectiveness

### Features

- **Workflow-Based**: Uses BPMN workflows to drive validation
- **Comprehensive**: Tests all OTEL features
- **Automated**: Batch validate multiple projects
- **Reportable**: Detailed validation reports
- **Extensible**: Create custom validation workflows

---

## Security Notes

### Recent Security Hardening

These commands have been hardened against:

✅ **Command Injection** - Package names with shell metacharacters
✅ **Path Traversal** - Malicious path inputs
✅ **Temporary File Vulnerabilities** - Secure permissions (0o600)
✅ **Resource Exhaustion** - Bounded cache, rate limiting
✅ **Race Conditions** - Atomic file operations

All commands use:
- List-based subprocess calls (no shell parsing)
- Input validation
- Proper error handling with logging
- Secure default permissions
- Resource limits

---

## Troubleshooting

### Command Not Found

```bash
# Verify command is in __all__
python -c "from uvmgr.commands import __all__; print('search' in __all__)"

# Check if command imports
python -c "from uvmgr.commands import search; print('✓ OK')"
```

### Missing Dependencies

```bash
# Error: No module named 'spiffworkflow'
pip install spiffworkflow

# Error: No module named 'chromadb'
pip install chromadb sentence-transformers
```

### BPMN File Issues

```bash
# Validate BPMN file structure
uvmgr agent validate workflow.bpmn --detailed

# Parse to see structure
uvmgr agent parse workflow.bpmn --format json
```

---

## Performance Tips

### Search Command

```bash
# Use parallel processing for large codebases
uvmgr search code "pattern" --parallel

# Cache results for repeated searches
uvmgr search code "pattern" --cache

# Limit results for faster queries
uvmgr search code "pattern" --max-results 50
```

### Agent Command

```bash
# Run with timeout to prevent hangs
uvmgr agent run workflow.bpmn --timeout 30

# Validate before running large workflows
uvmgr agent validate complex_workflow.bpmn --detailed
```

---

## Examples

### Example 1: Find All Async Functions

```bash
uvmgr search code "async def" --type function --include-docs
```

Output shows:
- Function name and location
- Complexity metrics
- Documentation strings

### Example 2: Validate Project Dependencies

```bash
uvmgr search deps "*" --show-vulnerabilities --format json > deps.json
```

Useful for:
- Dependency audits
- Vulnerability scanning
- Unused dependency detection

### Example 3: Run a Data Processing Pipeline

Create `pipeline.bpmn` with tasks for:
1. Read data
2. Process data
3. Write results

Then:
```bash
uvmgr agent run pipeline.bpmn --verbose
```

Monitor execution with OTEL traces in Jaeger/Grafana.

---

## Integration Examples

### With CI/CD

```bash
# In GitHub Actions
- name: Search for security issues
  run: uvmgr search code "password|secret|token" --case-sensitive

- name: Validate BPMN workflows
  run: uvmgr agent validate workflow.bpmn
```

### With Python Scripts

```python
from uvmgr.commands.search import search_code
from uvmgr.ops.search import CodeSearchEngine

# Use search engine directly
engine = CodeSearchEngine()
results = engine.search("async def", type="function")
for result in results:
    print(f"{result['file']}:{result['line']}")
```

---

## Next Steps

1. **Install dependencies**: `pip install spiffworkflow chromadb`
2. **Try a command**: `uvmgr search code "def" --max-results 5`
3. **Check results**: Review output and performance
4. **Read logs**: Check `~/.uvmgr_cache/` for cached results
5. **Explore OTEL**: Set up OpenTelemetry collector to see traces

---

## Support

For issues or questions:
- Check `/home/user/uvmgr/CLAUDE.md` for architecture overview
- Review test cases in `tests/test_reenabled_commands.py`
- Check OTEL traces for detailed execution information

---

**Last Updated**: 2025-12-04
**Status**: All 3 re-enabled commands fully functional and hardened
