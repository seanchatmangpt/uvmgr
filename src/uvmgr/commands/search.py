"""
uvmgr.commands.search - Advanced Search Commands
===============================================

Comprehensive search capabilities across code, dependencies, files, logs, and more.

This module provides powerful search functionality that goes beyond simple grep,
offering AST-based code search, dependency analysis, semantic search, and 
multi-faceted filtering with OpenTelemetry instrumentation.

Key Features
-----------
• **Code Search**: AST-based Python code searching with semantic understanding
• **Dependency Search**: Search across installed packages, imports, and version constraints
• **File Search**: Advanced file pattern matching with content filtering
• **Log Search**: Search through uvmgr logs, OTEL traces, and system logs
• **Semantic Search**: AI-powered semantic code and documentation search
• **Multi-Format**: Support for Python, TOML, JSON, YAML, Markdown files
• **Performance Optimized**: Parallel processing and caching for large codebases

Available Commands
-----------------
- **code**: Search Python code using AST parsing and pattern matching
- **deps**: Search dependencies, imports, and package information
- **files**: Search files by name, content, or metadata
- **logs**: Search through logs, traces, and execution history
- **semantic**: AI-powered semantic search across code and docs
- **all**: Multi-faceted search across all available sources

Search Capabilities
------------------
- **Function/Class Search**: Find definitions, usages, inheritance chains
- **Import Analysis**: Track dependency usage and circular imports
- **Performance Patterns**: Identify performance bottlenecks and anti-patterns
- **Security Scanning**: Find potential security issues and vulnerabilities
- **Documentation Search**: Search docstrings, comments, and markdown files
- **Configuration Search**: Search across pyproject.toml, .env, and config files

Advanced Filters
---------------
- **Language Support**: Python, JavaScript, TypeScript, Rust, Go
- **File Type Filters**: Source code, config files, documentation
- **Date/Time Filters**: Last modified, created, accessed
- **Size Filters**: File size ranges and line count limits
- **Complexity Filters**: Cyclomatic complexity, nesting depth
- **Quality Metrics**: Test coverage, documentation coverage

Examples
--------
    Search for function definitions:
        uvmgr search code "def.*async.*" --type function --files "*.py"
    
    Find dependency usage:
        uvmgr search deps "requests" --show-usage --show-versions
    
    Search file contents with filters:
        uvmgr search files "TODO" --modified-since "1 week ago" --exclude tests
    
        uvmgr search logs "error" --level error --since "24h" --format json
    
    Semantic search with AI:
        uvmgr search semantic "authentication middleware patterns"
    
    Multi-faceted search:
        uvmgr search all "database" --include-docs --include-code --include-deps

Performance Features
-------------------
- **Parallel Processing**: Multi-threaded search across large codebases
- **Smart Caching**: Cache AST parsing and search results
- **Incremental Indexing**: Build and maintain search indexes
- **Memory Optimization**: Stream processing for large files
- **Progress Tracking**: Real-time progress for long-running searches

Integration Features
-------------------
- **Editor Integration**: Export results in LSP-compatible formats
- **CI/CD Integration**: Machine-readable output for automation
- **Git Integration**: Search across branches, commits, and diffs
- **OTEL Integration**: Full observability and performance tracking
- **AI Integration**: Leverage MCP for enhanced semantic understanding

See Also
--------
- :mod:`uvmgr.ops.search` : Search operations and algorithms
- :mod:`uvmgr.core.search_engine` : Core search engine implementation
- :mod:`uvmgr.core.ast_parser` : AST parsing and analysis
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import typer

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.semconv import SearchAttributes, SearchOperations
from uvmgr.core.shell import colour, dump_json
from uvmgr.ops import search as search_ops

# Standard uvmgr command pattern
app = typer.Typer(help="Advanced search across code, dependencies, files, and logs")


@app.command("code")
@instrument_command("search_code", track_args=True)
def search_code(
    ctx: typer.Context,
    pattern: str = typer.Argument(..., help="Search pattern or regex"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Search path (default: current directory)"),
    files: str = typer.Option("*.py", "--files", "-f", help="File pattern to search (e.g., '*.py', '**/*.ts')"),
    search_type: str = typer.Option("all", "--type", "-t", 
                                   help="Search type: all, function, class, method, variable, import, decorator"),
    include_tests: bool = typer.Option(False, "--include-tests", help="Include test files in search"),
    include_docs: bool = typer.Option(False, "--include-docs", help="Include docstrings and comments"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", "-c", help="Case-sensitive search"),
    exact_match: bool = typer.Option(False, "--exact", "-e", help="Exact match instead of regex"),
    show_context: int = typer.Option(3, "--context", help="Lines of context to show"),
    max_results: int = typer.Option(100, "--max-results", "-n", help="Maximum number of results"),
    output_format: str = typer.Option("text", "--format", help="Output format: text, json, csv, lsp"),
    exclude_dirs: str = typer.Option("__pycache__,.git,.venv,node_modules", "--exclude", 
                                    help="Comma-separated directories to exclude"),
    complexity_min: Optional[int] = typer.Option(None, "--complexity-min", help="Minimum cyclomatic complexity"),
    complexity_max: Optional[int] = typer.Option(None, "--complexity-max", help="Maximum cyclomatic complexity"),
    lines_min: Optional[int] = typer.Option(None, "--lines-min", help="Minimum lines in function/class"),
    lines_max: Optional[int] = typer.Option(None, "--lines-max", help="Maximum lines in function/class"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Use parallel processing"),
    cache: bool = typer.Option(True, "--cache/--no-cache", help="Use search result caching"),
):
    """Search Python code using AST parsing and advanced pattern matching.
    
    This command provides sophisticated code search capabilities that go beyond
    simple text matching. It parses Python AST to understand code structure
    and semantics.
    
    Examples:
        uvmgr search code "async def.*upload" --type function
        uvmgr search code "class.*Model" --include-docs --show-context 5
        uvmgr search code "import requests" --type import --files "**/*.py"
    """
    # Track search execution
    add_span_attributes(**{
        SearchAttributes.OPERATION: SearchOperations.CODE_SEARCH,
        SearchAttributes.PATTERN: pattern,
        SearchAttributes.FILE_PATTERN: files,
        SearchAttributes.SEARCH_TYPE: search_type,
        "search.path": path or ".",
        "search.include_tests": include_tests,
        "search.include_docs": include_docs,
        "search.parallel": parallel,
    })
    
    add_span_event("search.code.started", {
        "pattern": pattern,
        "search_type": search_type,
        "files": files,
        "max_results": max_results,
    })
    
    # Build search configuration
    config = {
        "pattern": pattern,
        "path": Path(path) if path else Path.cwd(),
        "files": files,
        "search_type": search_type,
        "include_tests": include_tests,
        "include_docs": include_docs,
        "case_sensitive": case_sensitive,
        "exact_match": exact_match,
        "context_lines": show_context,
        "max_results": max_results,
        "exclude_dirs": exclude_dirs.split(",") if exclude_dirs else [],
        "complexity_range": (complexity_min, complexity_max),
        "lines_range": (lines_min, lines_max),
        "parallel": parallel,
        "cache": cache,
    }
    
    try:
        # Execute code search
        results = search_ops.search_code(config)
        
        # Track results
        add_span_attributes(**{
            "search.results_count": len(results.get("matches", [])),
            "search.files_scanned": results.get("files_scanned", 0),
            "search.execution_time": results.get("execution_time", 0),
        })
        
        # Format and display results
        if output_format == "json":
            if ctx.meta.get("json"):
                dump_json(results)
            else:
                print(json.dumps(results, indent=2))
        elif output_format == "csv":
            _display_csv_results(results, "code")
        elif output_format == "lsp":
            _display_lsp_results(results)
        else:
            _display_code_search_results(results, show_context)
            
        add_span_event("search.code.completed", {
            "results_count": len(results.get("matches", [])),
            "success": True,
        })
        
    except Exception as e:
        add_span_event("search.code.failed", {"error": str(e)})
        colour(f"❌ Code search failed: {e}", "red")
        raise typer.Exit(code=1)


@app.command("deps")
@instrument_command("search_deps", track_args=True)
def search_deps(
    ctx: typer.Context,
    pattern: str = typer.Argument(..., help="Package name or pattern to search"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Search path (default: current directory)"),
    search_type: str = typer.Option("all", "--type", "-t", 
                                   help="Search type: all, installed, imports, requirements, pyproject"),
    show_usage: bool = typer.Option(False, "--show-usage", help="Show where dependencies are used"),
    show_versions: bool = typer.Option(False, "--show-versions", help="Show version information"),
    show_vulnerabilities: bool = typer.Option(False, "--show-vulnerabilities", help="Check for known vulnerabilities"),
    include_dev: bool = typer.Option(True, "--include-dev/--no-dev", help="Include development dependencies"),
    include_transitive: bool = typer.Option(False, "--include-transitive", help="Include transitive dependencies"),
    outdated_only: bool = typer.Option(False, "--outdated-only", help="Show only outdated packages"),
    unused_only: bool = typer.Option(False, "--unused-only", help="Show only unused dependencies"),
    output_format: str = typer.Option("text", "--format", help="Output format: text, json, csv, requirements"),
    max_results: int = typer.Option(50, "--max-results", "-n", help="Maximum number of results"),
):
    """Search dependencies, imports, and package information.
    
    This command provides comprehensive dependency analysis including
    installed packages, import usage, version constraints, and security
    vulnerability checking.
    
    Examples:
        uvmgr search deps "requests" --show-usage --show-versions
        uvmgr search deps "test" --type imports --include-dev
        uvmgr search deps "*" --outdated-only --show-vulnerabilities
    """
    add_span_attributes(**{
        SearchAttributes.OPERATION: SearchOperations.DEPS_SEARCH,
        SearchAttributes.PATTERN: pattern,
        SearchAttributes.SEARCH_TYPE: search_type,
        "search.show_usage": show_usage,
        "search.show_versions": show_versions,
        "search.include_dev": include_dev,
    })
    
    config = {
        "pattern": pattern,
        "path": Path(path) if path else Path.cwd(),
        "search_type": search_type,
        "show_usage": show_usage,
        "show_versions": show_versions,
        "show_vulnerabilities": show_vulnerabilities,
        "include_dev": include_dev,
        "include_transitive": include_transitive,
        "outdated_only": outdated_only,
        "unused_only": unused_only,
        "max_results": max_results,
    }
    
    try:
        results = search_ops.search_dependencies(config)
        
        add_span_attributes(**{
            "search.results_count": len(results.get("matches", [])),
            "search.vulnerabilities_found": len(results.get("vulnerabilities", [])),
        })
        
        if output_format == "json":
            if ctx.meta.get("json"):
                dump_json(results)
            else:
                print(json.dumps(results, indent=2))
        elif output_format == "requirements":
            _display_requirements_format(results)
        else:
            _display_deps_search_results(results)
            
    except Exception as e:
        colour(f"❌ Dependency search failed: {e}", "red")
        raise typer.Exit(code=1)


@app.command("files")
@instrument_command("search_files", track_args=True)
def search_files(
    ctx: typer.Context,
    pattern: str = typer.Argument(..., help="Content pattern to search for"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Search path (default: current directory)"),
    files: str = typer.Option("*", "--files", "-f", help="File pattern to search"),
    name_pattern: Optional[str] = typer.Option(None, "--name", "-n", help="Filename pattern to match"),
    file_types: str = typer.Option("all", "--types", help="File types: all, source, config, docs, data"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", "-c", help="Case-sensitive search"),
    whole_words: bool = typer.Option(False, "--whole-words", "-w", help="Match whole words only"),
    show_context: int = typer.Option(3, "--context", help="Lines of context to show"),
    max_results: int = typer.Option(100, "--max-results", help="Maximum number of results"),
    max_file_size: str = typer.Option("10MB", "--max-size", help="Maximum file size to search"),
    modified_since: Optional[str] = typer.Option(None, "--modified-since", help="Only files modified since (e.g., '1 week ago')"),
    created_since: Optional[str] = typer.Option(None, "--created-since", help="Only files created since"),
    exclude_dirs: str = typer.Option("__pycache__,.git,.venv,node_modules", "--exclude", 
                                    help="Comma-separated directories to exclude"),
    include_hidden: bool = typer.Option(False, "--include-hidden", help="Include hidden files and directories"),
    output_format: str = typer.Option("text", "--format", help="Output format: text, json, csv"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Use parallel processing"),
):
    """Search files by name, content, or metadata with advanced filtering.
    
    This command provides powerful file search capabilities with support for
    various file types, metadata filtering, and content searching.
    
    Examples:
        uvmgr search files "TODO" --modified-since "1 week ago"
        uvmgr search files "api_key" --types config --name "*.env*"
        uvmgr search files "class.*Test" --types source --files "*.py"
    """
    add_span_attributes(**{
        SearchAttributes.OPERATION: SearchOperations.FILE_SEARCH,
        SearchAttributes.PATTERN: pattern,
        SearchAttributes.FILE_PATTERN: files,
        "search.file_types": file_types,
        "search.max_file_size": max_file_size,
    })
    
    config = {
        "pattern": pattern,
        "path": Path(path) if path else Path.cwd(),
        "files": files,
        "name_pattern": name_pattern,
        "file_types": file_types,
        "case_sensitive": case_sensitive,
        "whole_words": whole_words,
        "context_lines": show_context,
        "max_results": max_results,
        "max_file_size": max_file_size,
        "modified_since": _parse_time_delta(modified_since) if modified_since else None,
        "created_since": _parse_time_delta(created_since) if created_since else None,
        "exclude_dirs": exclude_dirs.split(",") if exclude_dirs else [],
        "include_hidden": include_hidden,
        "parallel": parallel,
    }
    
    try:
        results = search_ops.search_files(config)
        
        add_span_attributes(**{
            "search.results_count": len(results.get("matches", [])),
            "search.files_scanned": results.get("files_scanned", 0),
        })
        
        if output_format == "json":
            if ctx.meta.get("json"):
                dump_json(results)
            else:
                print(json.dumps(results, indent=2))
        else:
            _display_file_search_results(results, show_context)
            
    except Exception as e:
        colour(f"❌ File search failed: {e}", "red")
        raise typer.Exit(code=1)


@app.command("logs")
@instrument_command("search_logs", track_args=True)
def search_logs(
    ctx: typer.Context,
    pattern: str = typer.Argument(..., help="Log pattern to search for"),
    log_sources: str = typer.Option("all", "--sources", help="Log sources: all, uvmgr, otel, system, custom"),
    level: str = typer.Option("all", "--level", help="Log level: all, debug, info, warning, error, critical"),
    since: Optional[str] = typer.Option(None, "--since", help="Search logs since (e.g., '24h', '1 week ago')"),
    until: Optional[str] = typer.Option(None, "--until", help="Search logs until"),
    service: Optional[str] = typer.Option(None, "--service", help="Filter by service name"),
    trace_id: Optional[str] = typer.Option(None, "--trace-id", help="Filter by trace ID"),
    span_id: Optional[str] = typer.Option(None, "--span-id", help="Filter by span ID"),
    max_results: int = typer.Option(100, "--max-results", help="Maximum number of results"),
    output_format: str = typer.Option("text", "--format", help="Output format: text, json, csv"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", "-c", help="Case-sensitive search"),
):
    """Search through logs, traces, and execution history.
    
    This command provides comprehensive log search across uvmgr logs,
    OpenTelemetry traces, and system logs with advanced filtering.
    
    Examples:
        uvmgr search logs "error" --level error --since "24h"
        uvmgr search logs "search_code" --sources otel --format json
        uvmgr search logs "failed" --service "uvmgr-search" --follow
    """
    add_span_attributes(**{
        SearchAttributes.OPERATION: SearchOperations.LOG_SEARCH,
        SearchAttributes.PATTERN: pattern,
        "search.log_sources": log_sources,
        "search.log_level": level,
        "search.follow": follow,
    })
    
    config = {
        "pattern": pattern,
        "log_sources": log_sources.split(",") if log_sources != "all" else ["all"],
        "level": level,
        "since": _parse_time_delta(since) if since else None,
        "until": _parse_time_delta(until) if until else None,
        "service": service,
        "trace_id": trace_id,
        "span_id": span_id,
        "max_results": max_results,
        "follow": follow,
        "case_sensitive": case_sensitive,
    }
    
    try:
        if follow:
            # Real-time log following
            search_ops.follow_logs(config, _display_log_line)
        else:
            results = search_ops.search_logs(config)
            
            add_span_attributes(**{
                "search.results_count": len(results.get("matches", [])),
                "search.log_files_scanned": results.get("files_scanned", 0),
            })
            
            if output_format == "json":
                if ctx.meta.get("json"):
                    dump_json(results)
                else:
                    print(json.dumps(results, indent=2))
            else:
                _display_log_search_results(results)
                
    except Exception as e:
        colour(f"❌ Log search failed: {e}", "red")
        raise typer.Exit(code=1)


@app.command("semantic")
@instrument_command("search_semantic", track_args=True)
def search_semantic(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Natural language search query"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Search path (default: current directory)"),
    search_scope: str = typer.Option("all", "--scope", help="Search scope: all, code, docs, comments, tests"),
    include_external: bool = typer.Option(False, "--include-external", help="Include external documentation"),
    similarity_threshold: float = typer.Option(0.7, "--threshold", help="Similarity threshold (0.0-1.0)"),
    max_results: int = typer.Option(20, "--max-results", help="Maximum number of results"),
    model: str = typer.Option("auto", "--model", help="AI model to use for semantic search"),
    explain_results: bool = typer.Option(False, "--explain", help="Explain why results were selected"),
    output_format: str = typer.Option("text", "--format", help="Output format: text, json, markdown"),
):
    """AI-powered semantic search across code and documentation.
    
    This command uses AI to understand the semantic meaning of your query
    and find relevant code, documentation, and comments even when exact
    keywords don't match.
    
    Examples:
        uvmgr search semantic "authentication middleware patterns"
        uvmgr search semantic "error handling for async operations" --scope code
        uvmgr search semantic "database connection pooling" --explain
    """
    add_span_attributes(**{
        SearchAttributes.OPERATION: SearchOperations.SEMANTIC_SEARCH,
        SearchAttributes.PATTERN: query,
        "search.scope": search_scope,
        "search.model": model,
        "search.threshold": similarity_threshold,
    })
    
    config = {
        "query": query,
        "path": Path(path) if path else Path.cwd(),
        "search_scope": search_scope,
        "include_external": include_external,
        "similarity_threshold": similarity_threshold,
        "max_results": max_results,
        "model": model,
        "explain_results": explain_results,
    }
    
    try:
        results = search_ops.search_semantic(config)
        
        add_span_attributes(**{
            "search.results_count": len(results.get("matches", [])),
            "search.avg_similarity": results.get("avg_similarity", 0),
        })
        
        if output_format == "json":
            if ctx.meta.get("json"):
                dump_json(results)
            else:
                print(json.dumps(results, indent=2))
        elif output_format == "markdown":
            _display_semantic_results_markdown(results)
        else:
            _display_semantic_search_results(results, explain_results)
            
    except Exception as e:
        colour(f"❌ Semantic search failed: {e}", "red")
        raise typer.Exit(code=1)


@app.command("all")
@instrument_command("search_all", track_args=True)
def search_all(
    ctx: typer.Context,
    pattern: str = typer.Argument(..., help="Search pattern"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Search path (default: current directory)"),
    include_code: bool = typer.Option(True, "--include-code/--no-code", help="Include code search"),
    include_deps: bool = typer.Option(True, "--include-deps/--no-deps", help="Include dependency search"),
    include_files: bool = typer.Option(True, "--include-files/--no-files", help="Include file search"),
    include_logs: bool = typer.Option(False, "--include-logs", help="Include log search"),
    include_docs: bool = typer.Option(True, "--include-docs/--no-docs", help="Include documentation"),
    max_results_per_type: int = typer.Option(25, "--max-per-type", help="Maximum results per search type"),
    output_format: str = typer.Option("text", "--format", help="Output format: text, json, markdown"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Run searches in parallel"),
):
    """Multi-faceted search across all available sources.
    
    This command performs comprehensive search across code, dependencies,
    files, logs, and documentation simultaneously, providing a unified
    view of all matches.
    
    Examples:
        uvmgr search all "database" --include-docs --include-logs
        uvmgr search all "error.*handling" --no-deps --format json
        uvmgr search all "authentication" --max-per-type 10
    """
    add_span_attributes(**{
        SearchAttributes.OPERATION: SearchOperations.MULTI_SEARCH,
        SearchAttributes.PATTERN: pattern,
        "search.include_code": include_code,
        "search.include_deps": include_deps,
        "search.include_files": include_files,
        "search.include_logs": include_logs,
        "search.parallel": parallel,
    })
    
    config = {
        "pattern": pattern,
        "path": Path(path) if path else Path.cwd(),
        "include_code": include_code,
        "include_deps": include_deps,
        "include_files": include_files,
        "include_logs": include_logs,
        "include_docs": include_docs,
        "max_results_per_type": max_results_per_type,
        "parallel": parallel,
    }
    
    try:
        results = search_ops.search_all(config)
        
        total_results = sum(len(results.get(key, {}).get("matches", [])) 
                          for key in ["code", "deps", "files", "logs"])
        
        add_span_attributes(**{
            "search.total_results": total_results,
            "search.code_results": len(results.get("code", {}).get("matches", [])),
            "search.deps_results": len(results.get("deps", {}).get("matches", [])),
            "search.files_results": len(results.get("files", {}).get("matches", [])),
            "search.logs_results": len(results.get("logs", {}).get("matches", [])),
        })
        
        if output_format == "json":
            if ctx.meta.get("json"):
                dump_json(results)
            else:
                print(json.dumps(results, indent=2))
        elif output_format == "markdown":
            _display_all_results_markdown(results)
        else:
            _display_all_search_results(results)
            
    except Exception as e:
        colour(f"❌ Multi-search failed: {e}", "red")
        raise typer.Exit(code=1)


# Helper functions for result display
def _display_code_search_results(results: Dict[str, Any], context_lines: int):
    """Display code search results in a formatted way."""
    matches = results.get("matches", [])
    
    if not matches:
        colour("No matches found.", "yellow")
        return
    
    colour(f"Found {len(matches)} matches in {results.get('files_scanned', 0)} files:", "green")
    print()
    
    for match in matches:
        file_path = match["file"]
        line_num = match["line"]
        match_type = match.get("type", "unknown")
        
        colour(f"📄 {file_path}:{line_num} ({match_type})", "cyan")
        
        # Show context lines
        context = match.get("context", [])
        for i, line in enumerate(context):
            line_number = line_num - context_lines + i
            if i == context_lines:  # Highlight the matching line
                colour(f"  {line_number:4d}: {line}", "yellow", bold=True)
            else:
                print(f"  {line_number:4d}: {line}")
        
        if match.get("complexity"):
            colour(f"    Complexity: {match['complexity']}", "blue")
        
        print()


def _display_deps_search_results(results: Dict[str, Any]):
    """Display dependency search results."""
    matches = results.get("matches", [])
    
    if not matches:
        colour("No dependencies found.", "yellow")
        return
    
    colour(f"Found {len(matches)} dependency matches:", "green")
    print()
    
    for match in matches:
        name = match["name"]
        version = match.get("version", "unknown")
        match_type = match.get("type", "unknown")
        
        colour(f"📦 {name} ({version}) - {match_type}", "cyan")
        
        if match.get("usage"):
            for usage in match["usage"]:
                print(f"    Used in: {usage['file']}:{usage['line']}")
        
        if match.get("vulnerabilities"):
            for vuln in match["vulnerabilities"]:
                colour(f"    ⚠️  Vulnerability: {vuln['id']} - {vuln['description']}", "red")
        
        print()


def _display_file_search_results(results: Dict[str, Any], context_lines: int):
    """Display file search results."""
    matches = results.get("matches", [])
    
    if not matches:
        colour("No file matches found.", "yellow")
        return
    
    colour(f"Found {len(matches)} matches in {results.get('files_scanned', 0)} files:", "green")
    print()
    
    for match in matches:
        file_path = match["file"]
        line_num = match.get("line")
        
        colour(f"📄 {file_path}", "cyan")
        if line_num:
            colour(f"    Line {line_num}:", "blue")
            
            context = match.get("context", [])
            for line in context:
                print(f"      {line}")
        
        print()


def _display_log_search_results(results: Dict[str, Any]):
    """Display log search results."""
    matches = results.get("matches", [])
    
    if not matches:
        colour("No log matches found.", "yellow")
        return
    
    colour(f"Found {len(matches)} log matches:", "green")
    print()
    
    for match in matches:
        timestamp = match.get("timestamp", "unknown")
        level = match.get("level", "info")
        service = match.get("service", "unknown")
        message = match.get("message", "")
        
        level_color = {
            "debug": "blue",
            "info": "green",
            "warning": "yellow",
            "error": "red",
            "critical": "red"
        }.get(level.lower(), "white")
        
        colour(f"[{timestamp}] {level.upper()}", level_color)
        colour(f"Service: {service}", "cyan")
        print(f"Message: {message}")
        
        if match.get("trace_id"):
            colour(f"Trace ID: {match['trace_id']}", "blue")
        
        print()


def _display_semantic_search_results(results: Dict[str, Any], explain: bool):
    """Display semantic search results."""
    matches = results.get("matches", [])
    
    if not matches:
        colour("No semantic matches found.", "yellow")
        return
    
    colour(f"Found {len(matches)} semantic matches:", "green")
    print()
    
    for match in matches:
        file_path = match["file"]
        similarity = match.get("similarity", 0)
        content_type = match.get("type", "unknown")
        
        colour(f"🔍 {file_path} (similarity: {similarity:.2f}) - {content_type}", "cyan")
        
        preview = match.get("preview", "")
        print(f"    {preview}")
        
        if explain and match.get("explanation"):
            colour(f"    Explanation: {match['explanation']}", "blue")
        
        print()


def _display_log_line(log_line: Dict[str, Any]):
    """Display a single log line for real-time following."""
    timestamp = log_line.get("timestamp", "")
    level = log_line.get("level", "info")
    message = log_line.get("message", "")
    
    level_color = {
        "debug": "blue",
        "info": "green", 
        "warning": "yellow",
        "error": "red",
        "critical": "red"
    }.get(level.lower(), "white")
    
    colour(f"[{timestamp}] {level.upper()}: {message}", level_color)


def _display_all_search_results(results: Dict[str, Any]):
    """Display results from multi-faceted search."""
    total_results = sum(len(results.get(key, {}).get("matches", [])) 
                       for key in ["code", "deps", "files", "logs"])
    
    if total_results == 0:
        colour("No matches found across any search types.", "yellow")
        return
    
    colour(f"Found {total_results} total matches across all search types:", "green")
    print()
    
    # Display each search type
    for search_type in ["code", "deps", "files", "logs"]:
        type_results = results.get(search_type, {})
        matches = type_results.get("matches", [])
        
        if matches:
            colour(f"🔍 {search_type.upper()} SEARCH ({len(matches)} matches)", "cyan", bold=True)
            print()
            
            # Display first few results for each type
            for i, match in enumerate(matches[:5]):
                if search_type == "code":
                    colour(f"  📄 {match['file']}:{match['line']} ({match.get('type', 'unknown')})", "blue")
                elif search_type == "deps":
                    colour(f"  📦 {match['name']} ({match.get('version', 'unknown')})", "blue")
                elif search_type == "files":
                    colour(f"  📄 {match['file']}", "blue")
                elif search_type == "logs":
                    colour(f"  📋 [{match.get('timestamp', 'unknown')}] {match.get('level', 'info').upper()}", "blue")
            
            if len(matches) > 5:
                colour(f"  ... and {len(matches) - 5} more", "yellow")
            
            print()


def _parse_time_delta(time_str: str) -> datetime:
    """Parse time delta strings like '1 week ago', '24h', etc."""
    now = datetime.now()
    
    if "ago" in time_str:
        # Parse formats like "1 week ago", "3 days ago"
        parts = time_str.replace(" ago", "").split()
        if len(parts) == 2:
            amount, unit = parts
            amount = int(amount)
            
            if "day" in unit:
                return now - timedelta(days=amount)
            elif "week" in unit:
                return now - timedelta(weeks=amount)
            elif "hour" in unit:
                return now - timedelta(hours=amount)
            elif "minute" in unit:
                return now - timedelta(minutes=amount)
    
    elif time_str.endswith("h"):
        # Parse formats like "24h", "1h"
        hours = int(time_str[:-1])
        return now - timedelta(hours=hours)
    
    elif time_str.endswith("d"):
        # Parse formats like "7d", "1d"
        days = int(time_str[:-1])
        return now - timedelta(days=days)
    
    # If we can't parse it, try to parse as ISO format
    try:
        return datetime.fromisoformat(time_str)
    except ValueError:
        return now


def _display_csv_results(results: Dict[str, Any], search_type: str):
    """Display results in CSV format."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if search_type == "code":
        writer.writerow(["file", "line", "type", "content", "complexity"])
        for match in results.get("matches", []):
            writer.writerow([
                match["file"],
                match.get("line", ""),
                match.get("type", ""),
                match.get("content", "").replace("\n", " "),
                match.get("complexity", "")
            ])
    
    print(output.getvalue())


def _display_lsp_results(results: Dict[str, Any]):
    """Display results in LSP (Language Server Protocol) format."""
    lsp_results = []
    
    for match in results.get("matches", []):
        lsp_results.append({
            "uri": f"file://{match['file']}",
            "range": {
                "start": {"line": match.get("line", 0) - 1, "character": 0},
                "end": {"line": match.get("line", 0) - 1, "character": 100}
            },
            "kind": match.get("type", "unknown")
        })
    
    print(json.dumps(lsp_results, indent=2))


def _display_requirements_format(results: Dict[str, Any]):
    """Display dependencies in requirements.txt format."""
    for match in results.get("matches", []):
        name = match["name"]
        version = match.get("version")
        if version and version != "unknown":
            print(f"{name}=={version}")
        else:
            print(name)


def _display_semantic_results_markdown(results: Dict[str, Any]):
    """Display semantic search results in markdown format."""
    print("# Semantic Search Results\n")
    
    for i, match in enumerate(results.get("matches", []), 1):
        print(f"## {i}. {match['file']} (similarity: {match.get('similarity', 0):.2f})\n")
        print(f"**Type:** {match.get('type', 'unknown')}\n")
        print(f"**Preview:**\n```\n{match.get('preview', '')}\n```\n")
        
        if match.get("explanation"):
            print(f"**Why this matches:** {match['explanation']}\n")
        
        print("---\n")


def _display_all_results_markdown(results: Dict[str, Any]):
    """Display multi-search results in markdown format."""
    print("# Multi-Search Results\n")
    
    for search_type in ["code", "deps", "files", "logs"]:
        type_results = results.get(search_type, {})
        matches = type_results.get("matches", [])
        
        if matches:
            print(f"## {search_type.title()} Search ({len(matches)} matches)\n")
            
            for match in matches[:10]:  # Show first 10 of each type
                if search_type == "code":
                    print(f"- `{match['file']}:{match['line']}` - {match.get('type', 'unknown')}")
                elif search_type == "deps":
                    print(f"- **{match['name']}** ({match.get('version', 'unknown')})")
                elif search_type == "files":
                    print(f"- `{match['file']}`")
                elif search_type == "logs":
                    print(f"- [{match.get('timestamp', 'unknown')}] {match.get('level', 'info').upper()}")
            
            if len(matches) > 10:
                print(f"- ... and {len(matches) - 10} more")
            
            print()