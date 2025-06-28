# uvmgr Advanced Search Guide

Comprehensive guide to uvmgr's powerful search capabilities across code, dependencies, files, logs, and more.

## Overview

uvmgr provides sophisticated search functionality that goes far beyond simple text matching. The search system includes:

- **AST-based Code Search**: Parse Python syntax trees for semantic code understanding
- **Dependency Analysis**: Comprehensive dependency tracking and vulnerability scanning  
- **Advanced File Search**: Content, metadata, and pattern-based file discovery
- **Log Aggregation**: Multi-source log search with real-time following
- **Semantic Search**: AI-powered semantic understanding using embeddings
- **Multi-faceted Search**: Unified search across all sources simultaneously

## Quick Start

```bash
# Search for function definitions
uvmgr search code "async def.*upload" --type function

# Find dependency usage
uvmgr search deps "requests" --show-usage --show-versions

# Search file contents with time filters
uvmgr search files "TODO" --modified-since "1 week ago"

# Search logs for errors
uvmgr search logs "error" --level error --since "24h"

# AI-powered semantic search
uvmgr search semantic "authentication middleware patterns"

# Search everything at once
uvmgr search all "database" --include-logs
```

## Code Search

### Basic Usage

Search Python code using AST parsing for precise semantic understanding:

```bash
# Find function definitions
uvmgr search code "process_data" --type function

# Search for classes with inheritance
uvmgr search code "class.*Model" --type class --include-docs

# Find async functions
uvmgr search code "async def" --type function
```

### Advanced Filtering

```bash
# Filter by complexity
uvmgr search code "def.*" --complexity-min 5 --complexity-max 15

# Include docstrings and comments
uvmgr search code "authentication" --include-docs --include-tests

# Filter by function length
uvmgr search code "def.*" --lines-min 10 --lines-max 50
```

### Search Types

- `function` - Function and method definitions
- `class` - Class definitions
- `variable` - Variable assignments
- `import` - Import statements
- `decorator` - Decorator usage
- `all` - All of the above

### Output Formats

```bash
# JSON output for automation
uvmgr search code "pattern" --format json

# CSV for spreadsheet analysis
uvmgr search code "pattern" --format csv

# LSP format for editor integration
uvmgr search code "pattern" --format lsp
```

## Dependency Search

### Installed Packages

```bash
# Search installed packages
uvmgr search deps "requests" --type installed --show-versions

# Check for vulnerabilities
uvmgr search deps "*" --show-vulnerabilities

# Find outdated packages
uvmgr search deps "*" --outdated-only
```

### Import Analysis

```bash
# Find where packages are imported
uvmgr search deps "pandas" --type imports --show-usage

# Check for unused dependencies
uvmgr search deps "*" --unused-only
```

### Requirements Analysis

```bash
# Search requirements files
uvmgr search deps "django" --type requirements

# Analyze pyproject.toml
uvmgr search deps "fastapi" --type pyproject --include-dev
```

### Vulnerability Scanning

```bash
# Check all dependencies for vulnerabilities
uvmgr search deps "*" --show-vulnerabilities --format json

# Export vulnerable packages
uvmgr search deps "*" --show-vulnerabilities --format requirements
```

## File Search

### Content Search

```bash
# Basic content search
uvmgr search files "TODO" --context 5

# Case-sensitive search
uvmgr search files "API_KEY" --case-sensitive

# Whole word matching
uvmgr search files "test" --whole-words
```

### File Type Filtering

```bash
# Search only source files
uvmgr search files "pattern" --types source

# Search configuration files
uvmgr search files "database" --types config

# Search documentation
uvmgr search files "installation" --types docs
```

### Metadata Filtering

```bash
# Files modified recently
uvmgr search files "pattern" --modified-since "1 week ago"

# Files created today
uvmgr search files "pattern" --created-since "today"

# Limit file size
uvmgr search files "pattern" --max-size "1MB"

# Include hidden files
uvmgr search files "pattern" --include-hidden
```

### File Name Patterns

```bash
# Search by filename pattern
uvmgr search files "content" --name "*.env*"

# Exclude directories
uvmgr search files "pattern" --exclude "__pycache__,node_modules"
```

## Log Search

### Basic Log Search

```bash
# Search all logs
uvmgr search logs "error" --sources all

# Search specific sources
uvmgr search logs "search" --sources uvmgr,otel

# Filter by log level
uvmgr search logs "failed" --level error
```

### Time-based Filtering

```bash
# Recent logs
uvmgr search logs "error" --since "24h"

# Specific time range
uvmgr search logs "startup" --since "2023-06-01" --until "2023-06-02"
```

### Trace Integration

```bash
# Filter by trace ID
uvmgr search logs "request" --trace-id "abc123"

# Filter by service
uvmgr search logs "error" --service "uvmgr-search"
```

### Real-time Following

```bash
# Follow logs in real-time
uvmgr search logs "info" --follow --service "uvmgr"

# Follow with filtering
uvmgr search logs "error" --follow --level error
```

## Semantic Search

### Natural Language Queries

```bash
# Find authentication code
uvmgr search semantic "user authentication and login"

# Database optimization patterns
uvmgr search semantic "database connection pooling strategies"

# Error handling patterns
uvmgr search semantic "exception handling best practices"
```

### Scope Control

```bash
# Search only code
uvmgr search semantic "async patterns" --scope code

# Search only documentation
uvmgr search semantic "installation guide" --scope docs

# Search comments and docstrings
uvmgr search semantic "TODO items" --scope comments
```

### Similarity Tuning

```bash
# Higher similarity threshold
uvmgr search semantic "query" --threshold 0.8

# Get explanations
uvmgr search semantic "query" --explain

# Use specific model
uvmgr search semantic "query" --model custom-model
```

## Multi-faceted Search

### Search Everything

```bash
# Search across all sources
uvmgr search all "authentication"

# Selective inclusion
uvmgr search all "database" --no-logs --include-docs

# Limit results per type
uvmgr search all "pattern" --max-per-type 10
```

### Parallel Processing

```bash
# Enable parallel search (default)
uvmgr search all "pattern" --parallel

# Disable for sequential processing
uvmgr search all "pattern" --no-parallel
```

## Performance Optimization

### Caching

```bash
# Enable caching (default)
uvmgr search code "pattern" --cache

# Disable caching for fresh results
uvmgr search code "pattern" --no-cache
```

### Parallel Processing

```bash
# Use parallel processing (default)
uvmgr search code "pattern" --parallel

# Sequential processing for debugging
uvmgr search code "pattern" --no-parallel
```

### Result Limiting

```bash
# Limit results
uvmgr search code "pattern" --max-results 50

# Show context lines
uvmgr search code "pattern" --context 5
```

## Integration Examples

### CI/CD Integration

```bash
# Find security issues in CI
uvmgr search code "password|secret|key" --format json > security-scan.json

# Check for TODOs before release
uvmgr search files "TODO|FIXME|XXX" --format csv > todos.csv

# Dependency vulnerability check
uvmgr search deps "*" --show-vulnerabilities --format json > vulns.json
```

### Editor Integration

```bash
# LSP-compatible output
uvmgr search code "function_name" --format lsp

# JSON for custom tooling
uvmgr search all "pattern" --format json
```

### Automation Scripts

```bash
#!/bin/bash
# Comprehensive code quality check

echo "Searching for security patterns..."
uvmgr search code "password|secret|api_key" --format json > security.json

echo "Finding complex functions..."
uvmgr search code "def.*" --complexity-min 10 --format csv > complexity.csv

echo "Checking for vulnerabilities..."
uvmgr search deps "*" --show-vulnerabilities --format json > vulns.json

echo "Finding TODOs..."
uvmgr search files "TODO|FIXME|XXX" --format json > todos.json
```

## Advanced Examples

### Code Quality Analysis

```bash
# Find overly complex functions
uvmgr search code "def.*" --complexity-min 15 --format csv

# Identify missing error handling
uvmgr search code "def.*" --type function | grep -v "try\|except"

# Find long functions that need refactoring
uvmgr search code "def.*" --lines-min 50 --format json
```

### Security Scanning

```bash
# Find hardcoded secrets
uvmgr search code "password.*=|api_key.*=|secret.*=" --case-sensitive

# Check for SQL injection patterns
uvmgr search code "execute.*%|query.*format" --type function

# Find unsafe file operations
uvmgr search code "open.*w|write.*input" --include-docs
```

### Dependency Management

```bash
# Find all requests usage
uvmgr search deps "requests" --show-usage --format json

# Check for mixed async/sync patterns
uvmgr search code "requests\." --include-tests

# Identify packages that can be removed
uvmgr search deps "*" --unused-only --format csv
```

### Documentation Audit

```bash
# Find missing docstrings
uvmgr search code "def.*|class.*" --no-docs --format csv

# Locate outdated TODO items
uvmgr search files "TODO.*201[0-9]|TODO.*202[0-2]" --format json

# Find broken documentation links
uvmgr search files "http.*404|broken.*link" --types docs
```

## Best Practices

### Search Strategy

1. **Start Broad**: Use multi-faceted search first to understand scope
2. **Narrow Down**: Use specific search types for detailed analysis
3. **Use Filters**: Apply complexity, time, and type filters to focus results
4. **Leverage AI**: Use semantic search for concept-based discovery

### Performance Tips

1. **Enable Caching**: Use `--cache` for repeated searches
2. **Use Parallel Processing**: Enable `--parallel` for large codebases
3. **Limit Results**: Use `--max-results` to avoid overwhelming output
4. **Exclude Unnecessary Dirs**: Use `--exclude` to skip large directories

### Output Management

1. **Use JSON for Automation**: `--format json` for scripts and CI/CD
2. **Use CSV for Analysis**: `--format csv` for spreadsheet analysis
3. **Use LSP for Editors**: `--format lsp` for editor integration
4. **Save Results**: Redirect output to files for later analysis

## Troubleshooting

### Common Issues

**No Results Found**
```bash
# Check if files exist
uvmgr search files "*" --path /your/path

# Verify pattern syntax
uvmgr search code "test.*pattern" --exact  # Try exact match
```

**Performance Issues**
```bash
# Disable parallel processing
uvmgr search all "pattern" --no-parallel

# Reduce result set
uvmgr search code "pattern" --max-results 10

# Exclude large directories
uvmgr search files "pattern" --exclude "node_modules,__pycache__"
```

**Semantic Search Not Working**
```bash
# Check if dependencies are installed
pip install sentence-transformers

# Lower similarity threshold
uvmgr search semantic "query" --threshold 0.5
```

### Debug Mode

```bash
# Enable verbose output
export UVMGR_DEBUG=1
uvmgr search code "pattern"

# Check search cache
uvmgr search code "pattern" --no-cache
```

## Configuration

### Environment Variables

```bash
# Set default search path
export UVMGR_SEARCH_PATH="/path/to/project"

# Configure cache directory
export UVMGR_CACHE_DIR="/path/to/cache"

# Set parallel processing threads
export UVMGR_SEARCH_THREADS=8

# Configure semantic search model
export UVMGR_SEMANTIC_MODEL="all-MiniLM-L6-v2"
```

### Project Configuration

Create `.uvmgr/search.toml` in your project:

```toml
[search]
default_excludes = ["__pycache__", "node_modules", ".git"]
max_file_size = "10MB"
parallel_enabled = true
cache_enabled = true

[search.code]
include_tests = true
include_docs = true
default_context = 3

[search.deps]
check_vulnerabilities = true
include_dev = true

[search.semantic]
similarity_threshold = 0.7
model = "all-MiniLM-L6-v2"
```

## Integration with Other Tools

### Git Integration

```bash
# Search in specific branch
git checkout feature-branch
uvmgr search code "new_feature"

# Search changed files only
git diff --name-only | xargs uvmgr search files "pattern" --files
```

### IDE Integration

Most IDEs can integrate with uvmgr search using the LSP format:

```bash
# VS Code task configuration
{
    "label": "uvmgr search",
    "type": "shell", 
    "command": "uvmgr search code '${input:searchPattern}' --format lsp"
}
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Security Scan
  run: |
    uvmgr search code "password|secret|key" --format json > security.json
    test $(jq '.matches | length' security.json) -eq 0
```

This comprehensive search system makes uvmgr a powerful tool for code analysis, security scanning, dependency management, and project understanding.