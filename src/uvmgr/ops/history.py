"""
Command history and analytics operations for uvmgr.

This module provides business logic for tracking command execution history,
analyzing usage patterns, and providing intelligent recommendations. It follows
the 80/20 principle by focusing on the most valuable history operations.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, span
from uvmgr.core.semconv import CliAttributes
from uvmgr.runtime import history as history_runtime


def record_command_execution(
    command: str,
    subcommand: Optional[str] = None,
    args: Optional[List[str]] = None,
    exit_code: int = 0,
    execution_time: float = 0.0,
    working_directory: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Record a command execution in the history.
    
    Parameters
    ----------
    command : str
        Primary command that was executed
    subcommand : Optional[str]
        Subcommand if applicable
    args : Optional[List[str]]
        Command arguments
    exit_code : int
        Exit code of the command
    execution_time : float
        Time taken to execute the command
    working_directory : Optional[Path]
        Directory where command was executed
        
    Returns
    -------
    Dict[str, Any]
        Recording results
    """
    with span("history.record_execution") as current_span:
        add_span_attributes(**{
            CliAttributes.CLI_COMMAND: command,
            CliAttributes.CLI_SUBCOMMAND: subcommand,
            CliAttributes.CLI_EXIT_CODE: exit_code,
            "history.execution_time": execution_time,
            "history.working_directory": str(working_directory) if working_directory else None,
        })
        
        # Delegate to runtime
        result = history_runtime.store_command_record(
            command=command,
            subcommand=subcommand,
            args=args or [],
            exit_code=exit_code,
            execution_time=execution_time,
            working_directory=working_directory,
            timestamp=datetime.now()
        )
        
        add_span_attributes(**{
            "history.record_success": result.get("success", False),
            "history.record_id": result.get("record_id", ""),
        })
        
        return result


def get_command_history(
    limit: int = 50,
    command_filter: Optional[str] = None,
    days_back: int = 30,
    include_failures: bool = True
) -> Dict[str, Any]:
    """
    Retrieve command execution history.
    
    Parameters
    ----------
    limit : int
        Maximum number of records to return
    command_filter : Optional[str]
        Filter by specific command
    days_back : int
        Number of days to look back
    include_failures : bool
        Whether to include failed commands
        
    Returns
    -------
    Dict[str, Any]
        Command history records
    """
    with span("history.get_history") as current_span:
        add_span_attributes(**{
            "history.limit": limit,
            "history.command_filter": command_filter,
            "history.days_back": days_back,
            "history.include_failures": include_failures,
        })
        
        # Calculate date range
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Delegate to runtime
        result = history_runtime.query_command_history(
            limit=limit,
            command_filter=command_filter,
            start_date=start_date,
            include_failures=include_failures
        )
        
        add_span_attributes(**{
            "history.query_success": result.get("success", False),
            "history.records_found": len(result.get("records", [])),
        })
        
        return result


def analyze_usage_patterns(
    days_back: int = 30,
    include_trends: bool = True,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Analyze command usage patterns and trends.
    
    Parameters
    ----------
    days_back : int
        Number of days to analyze
    include_trends : bool
        Whether to include trend analysis
    include_recommendations : bool
        Whether to include usage recommendations
        
    Returns
    -------
    Dict[str, Any]
        Usage pattern analysis results
    """
    with span("history.analyze_patterns") as current_span:
        start_time = time.time()
        
        add_span_attributes(**{
            "history.analysis_days": days_back,
            "history.include_trends": include_trends,
            "history.include_recommendations": include_recommendations,
        })
        
        # Calculate date range
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Delegate to runtime
        result = history_runtime.analyze_command_patterns(
            start_date=start_date,
            include_trends=include_trends,
            include_recommendations=include_recommendations
        )
        
        analysis_time = time.time() - start_time
        add_span_attributes(**{
            "history.analysis_success": result.get("success", False),
            "history.analysis_time": analysis_time,
            "history.commands_analyzed": result.get("commands_analyzed", 0),
            "history.patterns_found": len(result.get("patterns", [])),
        })
        
        return result


def get_command_statistics(
    command: Optional[str] = None,
    days_back: int = 30
) -> Dict[str, Any]:
    """
    Get statistics for specific commands or overall usage.
    
    Parameters
    ----------
    command : Optional[str]
        Specific command to get stats for (all if None)
    days_back : int
        Number of days to include in statistics
        
    Returns
    -------
    Dict[str, Any]
        Command statistics
    """
    with span("history.get_statistics") as current_span:
        add_span_attributes(**{
            "history.command": command,
            "history.days_back": days_back,
        })
        
        # Calculate date range
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Delegate to runtime
        result = history_runtime.calculate_command_statistics(
            command=command,
            start_date=start_date
        )
        
        add_span_attributes(**{
            "history.stats_success": result.get("success", False),
            "history.total_executions": result.get("total_executions", 0),
            "history.success_rate": result.get("success_rate", 0.0),
            "history.avg_execution_time": result.get("avg_execution_time", 0.0),
        })
        
        return result


def find_similar_sessions(
    current_commands: List[str],
    similarity_threshold: float = 0.6,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Find similar command execution sessions.
    
    Parameters
    ----------
    current_commands : List[str]
        Current session commands to match against
    similarity_threshold : float
        Minimum similarity score (0.0 to 1.0)
    max_results : int
        Maximum number of similar sessions to return
        
    Returns
    -------
    Dict[str, Any]
        Similar sessions results
    """
    with span("history.find_similar_sessions") as current_span:
        add_span_attributes(**{
            "history.current_commands": ",".join(current_commands),
            "history.similarity_threshold": similarity_threshold,
            "history.max_results": max_results,
        })
        
        # Delegate to runtime
        result = history_runtime.find_similar_command_sessions(
            current_commands=current_commands,
            similarity_threshold=similarity_threshold,
            max_results=max_results
        )
        
        add_span_attributes(**{
            "history.similarity_success": result.get("success", False),
            "history.similar_sessions_found": len(result.get("similar_sessions", [])),
            "history.avg_similarity": result.get("avg_similarity", 0.0),
        })
        
        return result


def get_productivity_insights(
    days_back: int = 30,
    include_suggestions: bool = True
) -> Dict[str, Any]:
    """
    Generate productivity insights from command history.
    
    Parameters
    ----------
    days_back : int
        Number of days to analyze
    include_suggestions : bool
        Whether to include productivity suggestions
        
    Returns
    -------
    Dict[str, Any]
        Productivity insights and suggestions
    """
    with span("history.productivity_insights") as current_span:
        add_span_attributes(**{
            "history.analysis_days": days_back,
            "history.include_suggestions": include_suggestions,
        })
        
        # Calculate date range
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Delegate to runtime
        result = history_runtime.analyze_productivity_metrics(
            start_date=start_date,
            include_suggestions=include_suggestions
        )
        
        add_span_attributes(**{
            "history.insights_success": result.get("success", False),
            "history.insights_count": len(result.get("insights", [])),
            "history.suggestions_count": len(result.get("suggestions", [])),
        })
        
        return result


def export_history(
    output_path: Path,
    format_type: str = "json",
    days_back: Optional[int] = None,
    command_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export command history to a file.
    
    Parameters
    ----------
    output_path : Path
        Where to save the exported history
    format_type : str
        Export format (json, csv, yaml)
    days_back : Optional[int]
        Number of days to export (all if None)
    command_filter : Optional[str]
        Filter by specific command
        
    Returns
    -------
    Dict[str, Any]
        Export operation results
    """
    with span("history.export") as current_span:
        add_span_attributes(**{
            "history.output_path": str(output_path),
            "history.format_type": format_type,
            "history.days_back": days_back,
            "history.command_filter": command_filter,
        })
        
        # Calculate date range if specified
        start_date = None
        if days_back:
            start_date = datetime.now() - timedelta(days=days_back)
        
        # Delegate to runtime
        result = history_runtime.export_command_history(
            output_path=output_path,
            format_type=format_type,
            start_date=start_date,
            command_filter=command_filter
        )
        
        add_span_attributes(**{
            "history.export_success": result.get("success", False),
            "history.records_exported": result.get("records_exported", 0),
            "history.file_size": result.get("file_size", 0),
        })
        
        return result


def clear_history(
    older_than_days: Optional[int] = None,
    command_filter: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Clear command history records.
    
    Parameters
    ----------
    older_than_days : Optional[int]
        Clear records older than this many days (all if None)
    command_filter : Optional[str]
        Clear only records for specific command
    dry_run : bool
        Whether to only show what would be cleared
        
    Returns
    -------
    Dict[str, Any]
        Clear operation results
    """
    with span("history.clear") as current_span:
        add_span_attributes(**{
            "history.older_than_days": older_than_days,
            "history.command_filter": command_filter,
            "history.dry_run": dry_run,
        })
        
        # Calculate cutoff date if specified
        cutoff_date = None
        if older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        # Delegate to runtime
        result = history_runtime.clear_command_history(
            cutoff_date=cutoff_date,
            command_filter=command_filter,
            dry_run=dry_run
        )
        
        add_span_attributes(**{
            "history.clear_success": result.get("success", False),
            "history.records_cleared": result.get("records_cleared", 0),
        })
        
        return result