#!/usr/bin/env python3
"""
uvmgr.runtime.autogit
====================

Runtime execution layer for Git automation operations.

This module handles actual Git command execution and file system operations
for the autogit functionality. All functions include proper error handling
and OpenTelemetry instrumentation.
"""

from __future__ import annotations

import subprocess
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("autogit.runtime.get_git_status_raw")
def get_git_status_raw(project_path: Path) -> Dict[str, Any]:
    """
    Get raw git status information.
    
    Args:
        project_path: Path to the Git repository
        
    Returns:
        Dict containing git status results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "git.operation": "status",
        "project.path": str(project_path)
    })
    
    try:
        # Get git status porcelain output
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse porcelain output
        modified_files = []
        untracked_files = []
        staged_files = []
        deleted_files = []
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            status_code = line[:2]
            filename = line[3:]
            
            # Parse status codes
            if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                staged_files.append(filename)
            
            if status_code[1] == 'M':
                modified_files.append(filename)
            elif status_code[1] == 'D':
                deleted_files.append(filename)
            elif status_code == '??':
                untracked_files.append(filename)
        
        span.set_attributes({
            "git.modified_files": len(modified_files),
            "git.untracked_files": len(untracked_files),
            "git.staged_files": len(staged_files),
            "git.deleted_files": len(deleted_files)
        })
        
        return {
            "success": True,
            "modified_files": modified_files,
            "untracked_files": untracked_files,
            "staged_files": staged_files,
            "deleted_files": deleted_files,
            "raw_output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Git status failed: {e.stderr}"
        }
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


@tracer.start_as_current_span("autogit.runtime.get_git_branch_info")
def get_git_branch_info(project_path: Path) -> Dict[str, Any]:
    """
    Get Git branch information including remote tracking.
    
    Args:
        project_path: Path to the Git repository
        
    Returns:
        Dict containing branch information
    """
    span = trace.get_current_span()
    span.set_attributes({
        "git.operation": "branch_info",
        "project.path": str(project_path)
    })
    
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = branch_result.stdout.strip()
        
        # Get ahead/behind information
        ahead = 0
        behind = 0
        
        try:
            status_result = subprocess.run(
                ["git", "status", "--porcelain=v1", "--branch"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse branch line for ahead/behind info
            for line in status_result.stdout.split('\n'):
                if line.startswith('##'):
                    # Look for [ahead N, behind M] pattern
                    ahead_match = re.search(r'ahead (\d+)', line)
                    behind_match = re.search(r'behind (\d+)', line)
                    
                    if ahead_match:
                        ahead = int(ahead_match.group(1))
                    if behind_match:
                        behind = int(behind_match.group(1))
                    break
        except subprocess.CalledProcessError:
            # Ignore errors for ahead/behind check
            pass
        
        span.set_attributes({
            "git.current_branch": current_branch,
            "git.ahead": ahead,
            "git.behind": behind
        })
        
        return {
            "success": True,
            "current_branch": current_branch,
            "ahead": ahead,
            "behind": behind
        }
        
    except subprocess.CalledProcessError as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Git branch info failed: {e.stderr}",
            "current_branch": "unknown",
            "ahead": 0,
            "behind": 0
        }
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "current_branch": "unknown",
            "ahead": 0,
            "behind": 0
        }


@tracer.start_as_current_span("autogit.runtime.analyze_file_changes")
def analyze_file_changes(project_path: Path, modified_files: List[str]) -> Dict[str, Any]:
    """
    Analyze changed files for patterns and content.
    
    Args:
        project_path: Path to the Git repository
        modified_files: List of modified file paths
        
    Returns:
        Dict containing file analysis results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "git.operation": "analyze_changes",
        "project.path": str(project_path),
        "git.files_analyzed": len(modified_files)
    })
    
    try:
        analysis = {
            "file_types": {},
            "large_files": [],
            "binary_files": [],
            "total_lines_changed": 0,
            "languages_detected": set()
        }
        
        for file_path in modified_files:
            try:
                full_path = project_path / file_path
                
                # Skip if file doesn't exist (deleted files)
                if not full_path.exists():
                    continue
                
                # Get file extension
                ext = full_path.suffix.lower()
                analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                
                # Detect language
                if ext in ['.py']:
                    analysis["languages_detected"].add('Python')
                elif ext in ['.js', '.ts']:
                    analysis["languages_detected"].add('JavaScript/TypeScript')
                elif ext in ['.md', '.rst']:
                    analysis["languages_detected"].add('Documentation')
                elif ext in ['.yaml', '.yml', '.json', '.toml']:
                    analysis["languages_detected"].add('Configuration')
                
                # Check file size
                try:
                    file_size = full_path.stat().st_size
                    if file_size > 100_000:  # 100KB
                        analysis["large_files"].append(file_path)
                except OSError:
                    pass
                
                # Check if binary
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        f.read(1024)  # Try to read first 1KB as text
                except (UnicodeDecodeError, PermissionError):
                    analysis["binary_files"].append(file_path)
                    
            except Exception:
                # Skip problematic files
                continue
        
        # Convert set to list for JSON serialization
        analysis["languages_detected"] = list(analysis["languages_detected"])
        
        span.set_attributes({
            "git.file_types_count": len(analysis["file_types"]),
            "git.large_files_count": len(analysis["large_files"]),
            "git.binary_files_count": len(analysis["binary_files"]),
            "git.languages_count": len(analysis["languages_detected"])
        })
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"File analysis failed: {str(e)}",
            "analysis": {}
        }


@tracer.start_as_current_span("autogit.runtime.generate_ai_commit_message")
def generate_ai_commit_message(
    project_path: Path,
    file_analysis: Dict[str, Any],
    conventional: bool = True
) -> Dict[str, Any]:
    """
    Generate AI-powered commit message based on changes.
    
    Args:
        project_path: Path to the Git repository
        file_analysis: Analysis of changed files
        conventional: Use conventional commit format
        
    Returns:
        Dict containing generated message
    """
    span = trace.get_current_span()
    span.set_attributes({
        "git.operation": "generate_ai_message",
        "project.path": str(project_path),
        "git.conventional": conventional
    })
    
    try:
        # For now, use a rule-based approach since AI client integration
        # would require additional setup
        analysis = file_analysis.get("analysis", {})
        languages = analysis.get("languages_detected", [])
        file_types = analysis.get("file_types", {})
        
        # Determine commit type and scope
        commit_type = "chore"
        scope = ""
        description = "general updates"
        
        if "Python" in languages:
            commit_type = "feat"
            scope = "python"
            description = "improve Python implementation"
        elif "Documentation" in languages:
            commit_type = "docs"
            description = "update documentation"
        elif "Configuration" in languages:
            commit_type = "config"
            description = "update configuration"
        elif ".py" in file_types:
            commit_type = "refactor"
            scope = "python"
            description = "refactor Python code"
        
        # Build message
        if conventional:
            if scope:
                message = f"{commit_type}({scope}): {description}"
            else:
                message = f"{commit_type}: {description}"
        else:
            message = description.capitalize()
        
        span.set_attributes({
            "git.commit_type": commit_type,
            "git.commit_scope": scope,
            "git.message_length": len(message)
        })
        
        return {
            "success": True,
            "message": message,
            "type": commit_type,
            "scope": scope
        }
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"AI message generation failed: {str(e)}",
            "message": "chore: update files"  # Fallback
        }


@tracer.start_as_current_span("autogit.runtime.execute_git_commit")
def execute_git_commit(
    project_path: Path,
    message: str,
    files: List[str],
    add_all: bool = False
) -> Dict[str, Any]:
    """
    Execute git commit with specified files and message.
    
    Args:
        project_path: Path to the Git repository
        message: Commit message
        files: List of files to commit
        add_all: Add all files before committing
        
    Returns:
        Dict containing commit results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "git.operation": "commit",
        "project.path": str(project_path),
        "git.files_count": len(files),
        "git.add_all": add_all,
        "git.message_length": len(message)
    })
    
    try:
        # Add files to staging area
        if add_all:
            add_result = subprocess.run(
                ["git", "add", "."],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
        elif files:
            # Add specific files
            add_result = subprocess.run(
                ["git", "add"] + files,
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
        
        # Commit changes
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = hash_result.stdout.strip()
        
        span.set_attributes({
            "git.commit_hash": commit_hash,
            "git.success": True
        })
        
        return {
            "success": True,
            "commit_hash": commit_hash,
            "message": message,
            "files_committed": files,
            "output": commit_result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        span.record_exception(e)
        error_msg = e.stderr or str(e)
        return {
            "success": False,
            "error": f"Git commit failed: {error_msg}"
        }
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


@tracer.start_as_current_span("autogit.runtime.execute_git_sync")
def execute_git_sync(
    project_path: Path,
    remote: str,
    branch: str,
    pull_first: bool = True,
    force: bool = False,
    conflict_strategy: str = "merge"
) -> Dict[str, Any]:
    """
    Execute git sync operations with remote repository.
    
    Args:
        project_path: Path to the Git repository
        remote: Remote repository name
        branch: Branch to sync
        pull_first: Pull changes before pushing
        force: Force push
        conflict_strategy: How to handle conflicts
        
    Returns:
        Dict containing sync results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "git.operation": "sync",
        "project.path": str(project_path),
        "git.remote": remote,
        "git.branch": branch,
        "git.pull_first": pull_first,
        "git.force": force
    })
    
    try:
        operations_performed = []
        commits_pulled = 0
        commits_pushed = 0
        
        # Pull first if requested
        if pull_first:
            try:
                pull_result = subprocess.run(
                    ["git", "pull", remote, branch],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                operations_performed.append(f"Pulled from {remote}/{branch}")
                
                # Count commits pulled (rough estimate)
                if "Fast-forward" in pull_result.stdout:
                    commits_pulled = pull_result.stdout.count("commit")
                    
            except subprocess.CalledProcessError as e:
                if "CONFLICT" in e.stdout or "conflict" in e.stderr.lower():
                    return {
                        "success": False,
                        "error": "Merge conflicts detected",
                        "conflicts": _parse_conflicts(e.stdout),
                        "operations_performed": operations_performed
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Pull failed: {e.stderr}",
                        "operations_performed": operations_performed
                    }
        
        # Push changes
        push_command = ["git", "push", remote, branch]
        if force:
            push_command.append("--force")
            
        try:
            push_result = subprocess.run(
                push_command,
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            operations_performed.append(f"Pushed to {remote}/{branch}")
            
            # Count commits pushed (rough estimate)
            if "objects" in push_result.stderr:
                commits_pushed = 1  # At least one commit pushed
                
        except subprocess.CalledProcessError as e:
            if "rejected" in e.stderr:
                return {
                    "success": False,
                    "error": "Push rejected - try pulling first",
                    "operations_performed": operations_performed
                }
            else:
                return {
                    "success": False,
                    "error": f"Push failed: {e.stderr}",
                    "operations_performed": operations_performed
                }
        
        span.set_attributes({
            "git.operations_count": len(operations_performed),
            "git.commits_pulled": commits_pulled,
            "git.commits_pushed": commits_pushed,
            "git.success": True
        })
        
        return {
            "success": True,
            "operations_performed": operations_performed,
            "commits_pulled": commits_pulled,
            "commits_pushed": commits_pushed,
            "remote": remote,
            "branch": branch
        }
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Sync failed: {str(e)}",
            "operations_performed": operations_performed
        }


def _parse_conflicts(output: str) -> List[Dict[str, Any]]:
    """Parse git conflict output for resolution suggestions."""
    conflicts = []
    
    # Look for conflict markers in output
    lines = output.split('\n')
    for line in lines:
        if "CONFLICT" in line:
            # Extract file name from conflict line
            file_match = re.search(r'CONFLICT.*in (.+)', line)
            if file_match:
                conflicts.append({
                    "file": file_match.group(1),
                    "type": "merge_conflict",
                    "suggestion": "Manually resolve conflicts and commit"
                })
    
    return conflicts