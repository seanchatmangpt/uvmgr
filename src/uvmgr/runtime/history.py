"""
Command history runtime implementation.

This module handles the actual storage and retrieval of command execution history
at the runtime layer. It manages database operations, file I/O, and analytics
calculations for command usage tracking.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import span


def store_command_record(
    command: str,
    subcommand: Optional[str] = None,
    args: Optional[List[str]] = None,
    exit_code: int = 0,
    execution_time: float = 0.0,
    working_directory: Optional[Path] = None,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Store a command execution record.
    
    Parameters
    ----------
    command : str
        Primary command executed
    subcommand : Optional[str]
        Subcommand if applicable
    args : Optional[List[str]]
        Command arguments
    exit_code : int
        Command exit code
    execution_time : float
        Execution time in seconds
    working_directory : Optional[Path]
        Working directory
    timestamp : Optional[datetime]
        Execution timestamp
        
    Returns
    -------
    Dict[str, Any]
        Storage results
    """
    with span("runtime.history.store_record"):
        try:
            db_path = _get_history_db_path()
            timestamp = timestamp or datetime.now()
            
            with sqlite3.connect(db_path) as conn:
                _ensure_schema(conn)
                
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO command_history 
                    (command, subcommand, args, exit_code, execution_time, 
                     working_directory, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    command,
                    subcommand,
                    json.dumps(args or []),
                    exit_code,
                    execution_time,
                    str(working_directory) if working_directory else None,
                    timestamp.isoformat()
                ))
                
                record_id = cursor.lastrowid
                conn.commit()
                
            return {
                "success": True,
                "record_id": str(record_id)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def query_command_history(
    limit: int = 50,
    command_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    include_failures: bool = True
) -> Dict[str, Any]:
    """
    Query command execution history.
    
    Parameters
    ----------
    limit : int
        Maximum records to return
    command_filter : Optional[str]
        Filter by command
    start_date : Optional[datetime]
        Start date for query
    include_failures : bool
        Whether to include failed commands
        
    Returns
    -------
    Dict[str, Any]
        Query results
    """
    with span("runtime.history.query"):
        try:
            db_path = _get_history_db_path()
            
            with sqlite3.connect(db_path) as conn:
                _ensure_schema(conn)
                
                # Build query
                query = "SELECT * FROM command_history WHERE 1=1"
                params = []
                
                if command_filter:
                    query += " AND command = ?"
                    params.append(command_filter)
                    
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                    
                if not include_failures:
                    query += " AND exit_code = 0"
                    
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                records = []
                for row in cursor.fetchall():
                    records.append({
                        "id": row[0],
                        "command": row[1],
                        "subcommand": row[2],
                        "args": json.loads(row[3]) if row[3] else [],
                        "exit_code": row[4],
                        "execution_time": row[5],
                        "working_directory": row[6],
                        "timestamp": row[7]
                    })
                    
            return {
                "success": True,
                "records": records
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "records": []
            }


def analyze_command_patterns(
    start_date: Optional[datetime] = None,
    include_trends: bool = True,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Analyze command usage patterns.
    
    Parameters
    ----------
    start_date : Optional[datetime]
        Start date for analysis
    include_trends : bool
        Whether to include trend analysis
    include_recommendations : bool
        Whether to include recommendations
        
    Returns
    -------
    Dict[str, Any]
        Pattern analysis results
    """
    with span("runtime.history.analyze_patterns"):
        try:
            db_path = _get_history_db_path()
            
            with sqlite3.connect(db_path) as conn:
                _ensure_schema(conn)
                
                # Get basic usage statistics
                cursor = conn.cursor()
                
                query = """
                    SELECT command, COUNT(*) as usage_count, 
                           AVG(execution_time) as avg_time,
                           SUM(CASE WHEN exit_code = 0 THEN 1 ELSE 0 END) as success_count
                    FROM command_history
                """
                params = []
                
                if start_date:
                    query += " WHERE timestamp >= ?"
                    params.append(start_date.isoformat())
                    
                query += " GROUP BY command ORDER BY usage_count DESC"
                
                cursor.execute(query, params)
                command_stats = cursor.fetchall()
                
                patterns = []
                for stat in command_stats:
                    command, usage_count, avg_time, success_count = stat
                    success_rate = (success_count / usage_count) * 100 if usage_count > 0 else 0
                    
                    patterns.append({
                        "command": command,
                        "usage_count": usage_count,
                        "avg_execution_time": round(avg_time, 3) if avg_time else 0,
                        "success_rate": round(success_rate, 1)
                    })
                    
                # Generate trends if requested
                trends = []
                if include_trends:
                    trends = _analyze_usage_trends(conn, start_date)
                    
                # Generate recommendations if requested
                recommendations = []
                if include_recommendations:
                    recommendations = _generate_usage_recommendations(patterns)
                    
            return {
                "success": True,
                "commands_analyzed": len(patterns),
                "patterns": patterns,
                "trends": trends,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def calculate_command_statistics(
    command: Optional[str] = None,
    start_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Calculate statistics for commands.
    
    Parameters
    ----------
    command : Optional[str]
        Specific command to analyze
    start_date : Optional[datetime]
        Start date for statistics
        
    Returns
    -------
    Dict[str, Any]
        Command statistics
    """
    with span("runtime.history.calculate_stats"):
        try:
            db_path = _get_history_db_path()
            
            with sqlite3.connect(db_path) as conn:
                _ensure_schema(conn)
                
                cursor = conn.cursor()
                
                # Build query
                query = """
                    SELECT COUNT(*) as total_executions,
                           SUM(CASE WHEN exit_code = 0 THEN 1 ELSE 0 END) as successful_executions,
                           AVG(execution_time) as avg_execution_time,
                           MIN(timestamp) as first_execution,
                           MAX(timestamp) as last_execution
                    FROM command_history WHERE 1=1
                """
                params = []
                
                if command:
                    query += " AND command = ?"
                    params.append(command)
                    
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                    
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                total_executions = row[0] or 0
                successful_executions = row[1] or 0
                avg_execution_time = row[2] or 0.0
                first_execution = row[3]
                last_execution = row[4]
                
                success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
                
            return {
                "success": True,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": total_executions - successful_executions,
                "success_rate": round(success_rate, 1),
                "avg_execution_time": round(avg_execution_time, 3),
                "first_execution": first_execution,
                "last_execution": last_execution
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def find_similar_command_sessions(
    current_commands: List[str],
    similarity_threshold: float = 0.6,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Find similar command execution sessions.
    
    Parameters
    ----------
    current_commands : List[str]
        Current session commands
    similarity_threshold : float
        Minimum similarity score
    max_results : int
        Maximum results to return
        
    Returns
    -------
    Dict[str, Any]
        Similar sessions
    """
    with span("runtime.history.find_similar_sessions"):
        try:
            db_path = _get_history_db_path()
            
            with sqlite3.connect(db_path) as conn:
                _ensure_schema(conn)
                
                # Get command sessions (grouped by time windows)
                sessions = _extract_command_sessions(conn)
                
                similar_sessions = []
                
                for session in sessions:
                    session_commands = [record["command"] for record in session["commands"]]
                    similarity = _calculate_command_similarity(current_commands, session_commands)
                    
                    if similarity >= similarity_threshold:
                        similar_sessions.append({
                            "session_id": session["session_id"],
                            "commands": session_commands,
                            "similarity": similarity,
                            "timestamp": session["timestamp"],
                            "duration": session["duration"]
                        })
                        
                # Sort by similarity and limit results
                similar_sessions.sort(key=lambda x: x["similarity"], reverse=True)
                similar_sessions = similar_sessions[:max_results]
                
                avg_similarity = sum(s["similarity"] for s in similar_sessions) / len(similar_sessions) if similar_sessions else 0.0
                
            return {
                "success": True,
                "similar_sessions": similar_sessions,
                "avg_similarity": round(avg_similarity, 3)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def analyze_productivity_metrics(
    start_date: Optional[datetime] = None,
    include_suggestions: bool = True
) -> Dict[str, Any]:
    """
    Analyze productivity metrics from command history.
    
    Parameters
    ----------
    start_date : Optional[datetime]
        Start date for analysis
    include_suggestions : bool
        Whether to include suggestions
        
    Returns
    -------
    Dict[str, Any]
        Productivity insights
    """
    with span("runtime.history.analyze_productivity"):
        try:
            db_path = _get_history_db_path()
            
            with sqlite3.connect(db_path) as conn:
                _ensure_schema(conn)
                
                # Calculate productivity metrics
                insights = []
                
                # Most used commands
                most_used = _get_most_used_commands(conn, start_date)
                insights.append({
                    "type": "usage",
                    "title": "Most Used Commands",
                    "data": most_used
                })
                
                # Time efficiency
                time_efficiency = _analyze_time_efficiency(conn, start_date)
                insights.append({
                    "type": "efficiency",
                    "title": "Time Efficiency",
                    "data": time_efficiency
                })
                
                # Error patterns
                error_patterns = _analyze_error_patterns(conn, start_date)
                insights.append({
                    "type": "errors",
                    "title": "Error Patterns",
                    "data": error_patterns
                })
                
                # Generate suggestions
                suggestions = []
                if include_suggestions:
                    suggestions = _generate_productivity_suggestions(insights)
                    
            return {
                "success": True,
                "insights": insights,
                "suggestions": suggestions
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def export_command_history(
    output_path: Path,
    format_type: str = "json",
    start_date: Optional[datetime] = None,
    command_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export command history to a file.
    
    Parameters
    ----------
    output_path : Path
        Output file path
    format_type : str
        Export format (json, csv, yaml)
    start_date : Optional[datetime]
        Start date for export
    command_filter : Optional[str]
        Command filter
        
    Returns
    -------
    Dict[str, Any]
        Export results
    """
    with span("runtime.history.export"):
        try:
            # Query history records
            query_result = query_command_history(
                limit=10000,  # Large limit for export
                command_filter=command_filter,
                start_date=start_date
            )
            
            if not query_result["success"]:
                return query_result
                
            records = query_result["records"]
            
            # Export based on format
            if format_type == "json":
                _export_json(output_path, records)
            elif format_type == "csv":
                _export_csv(output_path, records)
            elif format_type == "yaml":
                _export_yaml(output_path, records)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format_type}"
                }
                
            # Get file size
            file_size = output_path.stat().st_size if output_path.exists() else 0
            
            return {
                "success": True,
                "records_exported": len(records),
                "file_size": file_size,
                "output_path": str(output_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def clear_command_history(
    cutoff_date: Optional[datetime] = None,
    command_filter: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Clear command history records.
    
    Parameters
    ----------
    cutoff_date : Optional[datetime]
        Clear records older than this date
    command_filter : Optional[str]
        Clear only records for specific command
    dry_run : bool
        Whether to only simulate the clear
        
    Returns
    -------
    Dict[str, Any]
        Clear operation results
    """
    with span("runtime.history.clear"):
        try:
            db_path = _get_history_db_path()
            
            with sqlite3.connect(db_path) as conn:
                _ensure_schema(conn)
                
                # Count records to be cleared
                count_query = "SELECT COUNT(*) FROM command_history WHERE 1=1"
                params = []
                
                if cutoff_date:
                    count_query += " AND timestamp < ?"
                    params.append(cutoff_date.isoformat())
                    
                if command_filter:
                    count_query += " AND command = ?"
                    params.append(command_filter)
                    
                cursor = conn.cursor()
                cursor.execute(count_query, params)
                records_to_clear = cursor.fetchone()[0]
                
                if not dry_run and records_to_clear > 0:
                    # Actually clear the records
                    delete_query = "DELETE FROM command_history WHERE 1=1"
                    if cutoff_date:
                        delete_query += " AND timestamp < ?"
                    if command_filter:
                        delete_query += " AND command = ?"
                        
                    cursor.execute(delete_query, params)
                    conn.commit()
                    
            return {
                "success": True,
                "records_cleared": records_to_clear,
                "dry_run": dry_run
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Helper functions

def _get_history_db_path() -> Path:
    """Get path to history database."""
    history_dir = Path.home() / ".uvmgr" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir / "commands.db"


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure database schema exists."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            subcommand TEXT,
            args TEXT,
            exit_code INTEGER,
            execution_time REAL,
            working_directory TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_command ON command_history(command)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON command_history(timestamp)")
    conn.commit()


def _analyze_usage_trends(conn: sqlite3.Connection, start_date: Optional[datetime]) -> List[Dict[str, Any]]:
    """Analyze usage trends over time."""
    cursor = conn.cursor()
    
    # Get daily usage counts
    query = """
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM command_history
    """
    params = []
    
    if start_date:
        query += " WHERE timestamp >= ?"
        params.append(start_date.isoformat())
        
    query += " GROUP BY DATE(timestamp) ORDER BY date"
    
    cursor.execute(query, params)
    daily_counts = cursor.fetchall()
    
    trends = []
    if len(daily_counts) > 1:
        # Calculate trend direction
        recent_avg = sum(count for _, count in daily_counts[-7:]) / min(7, len(daily_counts))
        overall_avg = sum(count for _, count in daily_counts) / len(daily_counts)
        
        if recent_avg > overall_avg * 1.1:
            trends.append({"type": "increasing", "description": "Command usage is trending up"})
        elif recent_avg < overall_avg * 0.9:
            trends.append({"type": "decreasing", "description": "Command usage is trending down"})
        else:
            trends.append({"type": "stable", "description": "Command usage is stable"})
            
    return trends


def _generate_usage_recommendations(patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate usage recommendations based on patterns."""
    recommendations = []
    
    # Find commands with low success rates
    for pattern in patterns:
        if pattern["success_rate"] < 80 and pattern["usage_count"] > 5:
            recommendations.append({
                "type": "reliability",
                "command": pattern["command"],
                "message": f"Command '{pattern['command']}' has low success rate ({pattern['success_rate']}%). Consider investigating common failure causes."
            })
            
    # Find commands with high execution times
    for pattern in patterns:
        if pattern["avg_execution_time"] > 10:
            recommendations.append({
                "type": "performance",
                "command": pattern["command"],
                "message": f"Command '{pattern['command']}' takes an average of {pattern['avg_execution_time']:.1f}s to execute. Consider optimization."
            })
            
    return recommendations


def _extract_command_sessions(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Extract command sessions from history."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM command_history 
        ORDER BY timestamp
    """)
    
    records = cursor.fetchall()
    sessions = []
    current_session = []
    last_timestamp = None
    session_id = 0
    
    for record in records:
        timestamp = datetime.fromisoformat(record[7])
        
        # Start new session if gap > 30 minutes
        if last_timestamp and (timestamp - last_timestamp).total_seconds() > 1800:
            if current_session:
                sessions.append({
                    "session_id": session_id,
                    "commands": current_session,
                    "timestamp": current_session[0]["timestamp"],
                    "duration": (datetime.fromisoformat(current_session[-1]["timestamp"]) - 
                               datetime.fromisoformat(current_session[0]["timestamp"])).total_seconds()
                })
                session_id += 1
                current_session = []
                
        current_session.append({
            "command": record[1],
            "subcommand": record[2],
            "timestamp": record[7]
        })
        last_timestamp = timestamp
        
    # Add final session
    if current_session:
        sessions.append({
            "session_id": session_id,
            "commands": current_session,
            "timestamp": current_session[0]["timestamp"],
            "duration": (datetime.fromisoformat(current_session[-1]["timestamp"]) - 
                       datetime.fromisoformat(current_session[0]["timestamp"])).total_seconds()
        })
        
    return sessions


def _calculate_command_similarity(commands1: List[str], commands2: List[str]) -> float:
    """Calculate similarity between two command lists."""
    if not commands1 or not commands2:
        return 0.0
        
    set1 = set(commands1)
    set2 = set(commands2)
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union) if union else 0.0


def _get_most_used_commands(conn: sqlite3.Connection, start_date: Optional[datetime]) -> List[Dict[str, Any]]:
    """Get most used commands."""
    cursor = conn.cursor()
    
    query = """
        SELECT command, COUNT(*) as usage_count
        FROM command_history
    """
    params = []
    
    if start_date:
        query += " WHERE timestamp >= ?"
        params.append(start_date.isoformat())
        
    query += " GROUP BY command ORDER BY usage_count DESC LIMIT 10"
    
    cursor.execute(query, params)
    return [{"command": row[0], "usage_count": row[1]} for row in cursor.fetchall()]


def _analyze_time_efficiency(conn: sqlite3.Connection, start_date: Optional[datetime]) -> Dict[str, Any]:
    """Analyze time efficiency metrics."""
    cursor = conn.cursor()
    
    query = """
        SELECT AVG(execution_time) as avg_time, 
               MIN(execution_time) as min_time,
               MAX(execution_time) as max_time
        FROM command_history WHERE execution_time > 0
    """
    params = []
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date.isoformat())
        
    cursor.execute(query, params)
    row = cursor.fetchone()
    
    return {
        "avg_execution_time": round(row[0], 3) if row[0] else 0,
        "min_execution_time": round(row[1], 3) if row[1] else 0,
        "max_execution_time": round(row[2], 3) if row[2] else 0
    }


def _analyze_error_patterns(conn: sqlite3.Connection, start_date: Optional[datetime]) -> Dict[str, Any]:
    """Analyze error patterns."""
    cursor = conn.cursor()
    
    query = """
        SELECT command, COUNT(*) as error_count
        FROM command_history 
        WHERE exit_code != 0
    """
    params = []
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date.isoformat())
        
    query += " GROUP BY command ORDER BY error_count DESC LIMIT 5"
    
    cursor.execute(query, params)
    error_commands = [{"command": row[0], "error_count": row[1]} for row in cursor.fetchall()]
    
    return {
        "commands_with_errors": error_commands,
        "total_error_commands": len(error_commands)
    }


def _generate_productivity_suggestions(insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate productivity suggestions."""
    suggestions = []
    
    # Find error-prone commands
    for insight in insights:
        if insight["type"] == "errors":
            error_commands = insight["data"]["commands_with_errors"]
            if error_commands:
                suggestions.append({
                    "type": "reliability",
                    "message": f"Command '{error_commands[0]['command']}' has frequent errors. Consider reviewing usage patterns."
                })
                
    return suggestions


def _export_json(output_path: Path, records: List[Dict[str, Any]]) -> None:
    """Export records to JSON format."""
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)


def _export_csv(output_path: Path, records: List[Dict[str, Any]]) -> None:
    """Export records to CSV format."""
    if not records:
        return
        
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def _export_yaml(output_path: Path, records: List[Dict[str, Any]]) -> None:
    """Export records to YAML format."""
    import yaml
    
    with open(output_path, 'w') as f:
        yaml.dump(records, f, default_flow_style=False)