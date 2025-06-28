"""
uvmgr.core.history – command execution & artefact tracker with comprehensive telemetry.

Enhanced with comprehensive OpenTelemetry instrumentation for command history tracking.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .instrumentation import add_span_attributes, add_span_event
from .paths import CONFIG_DIR
from .shell import rich_table
from .telemetry import metric_counter, metric_histogram, span

HIST: Path = CONFIG_DIR / "history.json"
CMD_HIST: Path = CONFIG_DIR / "command_history.json"

__all__ = [
    "log_output", 
    "last_files", 
    "history_menu",
    "log_command",
    "get_command_history", 
    "get_command_stats",
    "clear_history"
]


def _load() -> list[dict]:
    """Load file history with telemetry tracking."""
    with span("history.load_files"):
        start_time = time.time()
        
        if HIST.exists():
            try:
                data = json.loads(HIST.read_text())
                metric_counter("history.file_loads.success")(1)
                
                add_span_event("history.file_load.success", {
                    "entries_count": len(data),
                    "file_path": str(HIST),
                })
                
                return data
            except Exception as e:
                metric_counter("history.file_loads.failed")(1)
                add_span_event("history.file_load.failed", {"error": str(e)})
                return []
        else:
            metric_counter("history.file_loads.not_found")(1)
            add_span_event("history.file_load.not_found", {"file_path": str(HIST)})
            return []


def _load_commands() -> list[dict]:
    """Load command history with telemetry tracking."""
    with span("history.load_commands"):
        start_time = time.time()
        
        if CMD_HIST.exists():
            try:
                data = json.loads(CMD_HIST.read_text())
                metric_counter("history.command_loads.success")(1)
                
                add_span_event("history.command_load.success", {
                    "entries_count": len(data),
                    "file_path": str(CMD_HIST),
                })
                
                return data
            except Exception as e:
                metric_counter("history.command_loads.failed")(1)
                add_span_event("history.command_load.failed", {"error": str(e)})
                return []
        else:
            metric_counter("history.command_loads.not_found")(1)
            return []


def log_output(p: Path) -> None:
    """Log file output with comprehensive telemetry."""
    with span("history.log_output", file_path=str(p)):
        start_time = time.time()
        
        add_span_event("history.log_output.starting", {"file_path": str(p)})
        
        try:
            recs = _load()
            entry = {"ts": datetime.now().isoformat(), "file": str(p)}
            recs.append(entry)
            
            # Keep only last 100 entries
            trimmed_recs = recs[-100:]
            HIST.write_text(json.dumps(trimmed_recs, indent=2))
            
            duration = time.time() - start_time
            
            # Record metrics
            metric_counter("history.file_outputs.logged")(1)
            metric_histogram("history.log_output.duration")(duration)
            
            add_span_attributes(**{
                "history.file_path": str(p),
                "history.entries_count": len(trimmed_recs),
                "history.duration": duration,
            })
            
            add_span_event("history.log_output.completed", {
                "file_path": str(p),
                "entries_count": len(trimmed_recs),
                "duration": duration,
            })
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("history.file_outputs.failed")(1)
            
            add_span_event("history.log_output.failed", {
                "file_path": str(p),
                "error": str(e),
                "duration": duration,
            })
            raise


def last_files(n: int = 5) -> list[Path]:
    """Get last N files with telemetry tracking."""
    with span("history.last_files", requested_count=n):
        start_time = time.time()
        
        try:
            records = _load()
            result = [Path(r["file"]) for r in records[-n:]]
            duration = time.time() - start_time
            
            # Record metrics
            metric_counter("history.last_files.requests")(1)
            metric_histogram("history.last_files.duration")(duration)
            
            add_span_attributes(**{
                "history.requested_count": n,
                "history.returned_count": len(result),
                "history.total_available": len(records),
                "history.duration": duration,
            })
            
            add_span_event("history.last_files.completed", {
                "requested": n,
                "returned": len(result),
                "duration": duration,
            })
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("history.last_files.failed")(1)
            
            add_span_event("history.last_files.failed", {
                "requested": n,
                "error": str(e),
                "duration": duration,
            })
            raise


def history_menu(n: int = 10) -> None:
    """Interactive file history menu with telemetry tracking."""
    with span("history.menu", requested_count=n):
        start_time = time.time()
        
        add_span_event("history.menu.starting", {"requested_count": n})
        
        try:
            files = last_files(n)
            
            if not files:
                add_span_event("history.menu.no_files", {"requested_count": n})
                print("No files in history")
                return
            
            # Display menu
            rich_table(["#", "file"], [(i + 1, f) for i, f in enumerate(files)])
            
            try:
                sel = int(input("Open which? ")) - 1
                
                if 0 <= sel < len(files):
                    selected_file = files[sel]
                    editor = os.getenv("EDITOR", "nano")
                    
                    add_span_event("history.menu.file_selected", {
                        "selection": sel + 1,
                        "file_path": str(selected_file),
                        "editor": editor,
                    })
                    
                    os.system(f"'{editor}' '{selected_file}'")
                    
                    metric_counter("history.menu.files_opened")(1)
                    
                else:
                    add_span_event("history.menu.invalid_selection", {"selection": sel + 1})
                    print("Invalid selection")
                    
            except (ValueError, IndexError) as e:
                add_span_event("history.menu.cancelled", {"reason": str(e)})
                print("cancelled")
                
            duration = time.time() - start_time
            
            # Record metrics
            metric_counter("history.menu.sessions")(1)
            metric_histogram("history.menu.duration")(duration)
            
            add_span_attributes(**{
                "history.files_available": len(files),
                "history.duration": duration,
            })
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("history.menu.failed")(1)
            
            add_span_event("history.menu.failed", {
                "error": str(e),
                "duration": duration,
            })
            raise


# Command History Tracking Functions

def log_command(
    command: str, 
    args: Optional[List[str]] = None,
    exit_code: int = 0,
    duration: Optional[float] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log command execution with comprehensive telemetry and metadata."""
    with span("history.log_command", command=command, exit_code=exit_code):
        start_time = time.time()
        
        add_span_event("history.log_command.starting", {
            "command": command,
            "args_count": len(args) if args else 0,
            "exit_code": exit_code,
        })
        
        try:
            # Load existing command history
            commands = _load_commands()
            
            # Create command entry
            entry = {
                "ts": datetime.now().isoformat(),
                "command": command,
                "args": args or [],
                "exit_code": exit_code,
                "duration": duration,
                "error": error,
                "metadata": metadata or {},
                "working_dir": str(Path.cwd()),
                "user": os.getenv("USER", "unknown"),
            }
            
            commands.append(entry)
            
            # Keep only last 500 command entries
            trimmed_commands = commands[-500:]
            CMD_HIST.write_text(json.dumps(trimmed_commands, indent=2))
            
            operation_duration = time.time() - start_time
            
            # Record comprehensive metrics
            metric_counter("history.commands.logged")(1)
            metric_counter(f"history.commands.{command}")(1)
            metric_counter(f"history.exit_codes.{exit_code}")(1)
            metric_histogram("history.log_command.duration")(operation_duration)
            
            if duration:
                metric_histogram(f"history.command_duration.{command}")(duration)
            
            if exit_code != 0:
                metric_counter("history.commands.failed")(1)
            else:
                metric_counter("history.commands.succeeded")(1)
            
            add_span_attributes(**{
                "history.command": command,
                "history.args_count": len(args) if args else 0,
                "history.exit_code": exit_code,
                "history.duration": duration,
                "history.has_error": error is not None,
                "history.entries_count": len(trimmed_commands),
                "history.operation_duration": operation_duration,
            })
            
            add_span_event("history.log_command.completed", {
                "command": command,
                "exit_code": exit_code,
                "entries_count": len(trimmed_commands),
                "duration": operation_duration,
            })
            
        except Exception as e:
            operation_duration = time.time() - start_time
            
            metric_counter("history.commands.log_failed")(1)
            
            add_span_event("history.log_command.failed", {
                "command": command,
                "error": str(e),
                "duration": operation_duration,
            })
            # Don't raise - command logging should never break the main flow
            print(f"Warning: Failed to log command history: {e}")


def get_command_history(
    command: Optional[str] = None, 
    limit: int = 50,
    successful_only: bool = False
) -> List[Dict[str, Any]]:
    """Retrieve command history with filtering and telemetry."""
    with span("history.get_command_history", command=command, limit=limit):
        start_time = time.time()
        
        add_span_event("history.get_command_history.starting", {
            "command_filter": command,
            "limit": limit,
            "successful_only": successful_only,
        })
        
        try:
            commands = _load_commands()
            
            # Apply filters
            filtered_commands = commands
            
            if command:
                filtered_commands = [c for c in filtered_commands if c.get("command") == command]
            
            if successful_only:
                filtered_commands = [c for c in filtered_commands if c.get("exit_code", 0) == 0]
            
            # Apply limit
            result = filtered_commands[-limit:] if limit else filtered_commands
            
            duration = time.time() - start_time
            
            # Record metrics
            metric_counter("history.get_command_history.requests")(1)
            metric_histogram("history.get_command_history.duration")(duration)
            
            add_span_attributes(**{
                "history.command_filter": command,
                "history.limit": limit,
                "history.successful_only": successful_only,
                "history.total_commands": len(commands),
                "history.filtered_commands": len(filtered_commands),
                "history.returned_commands": len(result),
                "history.duration": duration,
            })
            
            add_span_event("history.get_command_history.completed", {
                "total": len(commands),
                "filtered": len(filtered_commands),
                "returned": len(result),
                "duration": duration,
            })
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("history.get_command_history.failed")(1)
            
            add_span_event("history.get_command_history.failed", {
                "error": str(e),
                "duration": duration,
            })
            raise


def get_command_stats() -> Dict[str, Any]:
    """Get command usage statistics with comprehensive telemetry."""
    with span("history.get_command_stats"):
        start_time = time.time()
        
        add_span_event("history.get_command_stats.starting")
        
        try:
            commands = _load_commands()
            
            if not commands:
                return {
                    "total_commands": 0,
                    "unique_commands": 0,
                    "success_rate": 0.0,
                    "most_used": [],
                    "recent_activity": {},
                }
            
            # Calculate statistics
            total_commands = len(commands)
            unique_commands = len(set(c.get("command", "") for c in commands))
            successful_commands = sum(1 for c in commands if c.get("exit_code", 0) == 0)
            success_rate = (successful_commands / total_commands) * 100 if total_commands > 0 else 0
            
            # Command frequency analysis
            command_counts = {}
            for cmd in commands:
                command_name = cmd.get("command", "unknown")
                command_counts[command_name] = command_counts.get(command_name, 0) + 1
            
            most_used = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Recent activity (last 24 hours)
            now = datetime.now()
            recent_commands = []
            for cmd in commands:
                try:
                    cmd_time = datetime.fromisoformat(cmd.get("ts", ""))
                    if (now - cmd_time).total_seconds() < 86400:  # 24 hours
                        recent_commands.append(cmd)
                except ValueError:
                    continue
            
            recent_activity = {
                "last_24h": len(recent_commands),
                "success_rate_24h": (
                    sum(1 for c in recent_commands if c.get("exit_code", 0) == 0) / len(recent_commands) * 100
                    if recent_commands else 0
                ),
            }
            
            # Average durations
            durations = [c.get("duration", 0) for c in commands if c.get("duration")]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            stats = {
                "total_commands": total_commands,
                "unique_commands": unique_commands,
                "success_rate": success_rate,
                "most_used": most_used,
                "recent_activity": recent_activity,
                "avg_duration": avg_duration,
                "failed_commands": total_commands - successful_commands,
            }
            
            duration = time.time() - start_time
            
            # Record metrics
            metric_counter("history.get_command_stats.requests")(1)
            metric_histogram("history.get_command_stats.duration")(duration)
            
            add_span_attributes(**{
                "history.total_commands": total_commands,
                "history.unique_commands": unique_commands,
                "history.success_rate": success_rate,
                "history.avg_duration": avg_duration,
                "history.calculation_duration": duration,
            })
            
            add_span_event("history.get_command_stats.completed", {
                "total_commands": total_commands,
                "success_rate": success_rate,
                "calculation_duration": duration,
            })
            
            return stats
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("history.get_command_stats.failed")(1)
            
            add_span_event("history.get_command_stats.failed", {
                "error": str(e),
                "duration": duration,
            })
            raise


def clear_history(command_history: bool = True, file_history: bool = False) -> None:
    """Clear history data with telemetry tracking."""
    with span("history.clear_history", command_history=command_history, file_history=file_history):
        start_time = time.time()
        
        add_span_event("history.clear_history.starting", {
            "command_history": command_history,
            "file_history": file_history,
        })
        
        try:
            cleared_files = []
            
            if command_history and CMD_HIST.exists():
                # Get count before clearing
                commands = _load_commands()
                cmd_count = len(commands)
                
                CMD_HIST.unlink()
                cleared_files.append("command_history")
                
                metric_counter("history.clear_history.commands")(cmd_count)
                
                add_span_event("history.clear_history.commands_cleared", {
                    "count": cmd_count,
                })
            
            if file_history and HIST.exists():
                # Get count before clearing
                files = _load()
                file_count = len(files)
                
                HIST.unlink()
                cleared_files.append("file_history")
                
                metric_counter("history.clear_history.files")(file_count)
                
                add_span_event("history.clear_history.files_cleared", {
                    "count": file_count,
                })
            
            duration = time.time() - start_time
            
            # Record metrics
            metric_counter("history.clear_history.operations")(1)
            metric_histogram("history.clear_history.duration")(duration)
            
            add_span_attributes(**{
                "history.command_history_cleared": command_history,
                "history.file_history_cleared": file_history,
                "history.cleared_files": cleared_files,
                "history.duration": duration,
            })
            
            add_span_event("history.clear_history.completed", {
                "cleared_files": cleared_files,
                "duration": duration,
            })
            
        except Exception as e:
            duration = time.time() - start_time
            
            metric_counter("history.clear_history.failed")(1)
            
            add_span_event("history.clear_history.failed", {
                "error": str(e),
                "duration": duration,
            })
            raise
