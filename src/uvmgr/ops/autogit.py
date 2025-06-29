#!/usr/bin/env python3
"""
uvmgr.ops.autogit
================

Business logic for intelligent Git automation operations.

This module provides the core business logic for autogit functionality including:
• Git status analysis with AI insights
• Intelligent commit message generation
• Repository synchronization with conflict resolution
• Change pattern analysis and recommendations

All functions are pure business logic with no side effects - actual Git operations
are handled by the runtime layer.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from opentelemetry import trace

from ..runtime.autogit import (
    get_git_status_raw,
    get_git_branch_info,
    execute_git_commit,
    execute_git_sync,
    analyze_file_changes,
    generate_ai_commit_message
)

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("autogit.analyze_git_status")
def analyze_git_status(
    project_path: Path,
    detailed: bool = False,
    ai_insights: bool = True
) -> Dict[str, Any]:
    """
    Analyze Git repository status with optional AI insights.
    
    Args:
        project_path: Path to the Git repository
        detailed: Include detailed file analysis
        ai_insights: Generate AI-powered insights and recommendations
        
    Returns:
        Dict containing status analysis results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "autogit.operation": "analyze_status",
        "autogit.detailed": detailed,
        "autogit.ai_insights": ai_insights,
        "project.path": str(project_path)
    })
    
    try:
        # Get raw git status
        status_result = get_git_status_raw(project_path)
        if not status_result["success"]:
            return status_result
        
        # Get branch information
        branch_result = get_git_branch_info(project_path)
        
        # Analyze files if detailed mode
        file_analysis = {}
        if detailed:
            file_analysis = analyze_file_changes(
                project_path, 
                status_result.get("modified_files", [])
            )
        
        # Generate AI insights if requested
        ai_analysis = {}
        if ai_insights:
            ai_analysis = _generate_status_insights(
                project_path,
                status_result,
                file_analysis
            )
        
        # Combine all analysis
        result = {
            "success": True,
            "timestamp": time.time(),
            "branch": branch_result.get("current_branch", "unknown"),
            "ahead_remote": branch_result.get("ahead", 0),
            "behind_remote": branch_result.get("behind", 0),
            "modified_files": status_result.get("modified_files", []),
            "untracked_files": status_result.get("untracked_files", []),
            "staged_files": status_result.get("staged_files", []),
            "deleted_files": status_result.get("deleted_files", []),
            "files_changed": len(status_result.get("modified_files", [])),
            "is_clean": len(status_result.get("modified_files", [])) == 0 and len(status_result.get("untracked_files", [])) == 0
        }
        
        if detailed:
            result["file_analysis"] = file_analysis
            
        if ai_insights:
            result["ai_insights"] = ai_analysis
        
        span.set_attributes({
            "autogit.files_changed": result["files_changed"],
            "autogit.untracked_files": len(result["untracked_files"]),
            "autogit.is_clean": result["is_clean"],
            "autogit.branch": result["branch"]
        })
        
        return result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Status analysis failed: {str(e)}"
        }


@tracer.start_as_current_span("autogit.generate_commit")
def generate_commit(
    project_path: Path,
    message: Optional[str] = None,
    ai_generate: bool = True,
    conventional: bool = True,
    batch: bool = False,
    dry_run: bool = False,
    add_all: bool = False
) -> Dict[str, Any]:
    """
    Generate and execute intelligent commit with AI-powered messages.
    
    Args:
        project_path: Path to the Git repository
        message: Custom commit message (overrides AI generation)
        ai_generate: Use AI to generate commit message
        conventional: Format message using conventional commits
        batch: Commit all changes in batch
        dry_run: Preview without executing
        add_all: Add all changed files before committing
        
    Returns:
        Dict containing commit results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "autogit.operation": "generate_commit",
        "autogit.ai_generate": ai_generate,
        "autogit.conventional": conventional,
        "autogit.batch": batch,
        "autogit.dry_run": dry_run,
        "project.path": str(project_path)
    })
    
    try:
        # Analyze current status
        status_result = analyze_git_status(project_path, detailed=True, ai_insights=False)
        if not status_result["success"]:
            return status_result
        
        # Check if there are changes to commit
        if status_result["is_clean"] and not add_all:
            return {
                "success": False,
                "error": "No changes to commit. Use --add-all to include untracked files."
            }
        
        # Generate commit message if not provided
        commit_message = message
        if not commit_message and ai_generate:
            ai_result = generate_ai_commit_message(
                project_path,
                status_result.get("file_analysis", {}),
                conventional=conventional
            )
            if ai_result["success"]:
                commit_message = ai_result["message"]
            else:
                # Fallback to simple message
                commit_message = _generate_fallback_message(status_result, conventional)
        elif not commit_message:
            # Generate simple message without AI
            commit_message = _generate_fallback_message(status_result, conventional)
        
        # Determine files to commit
        files_to_commit = []
        if batch or add_all:
            files_to_commit.extend(status_result.get("modified_files", []))
            if add_all:
                files_to_commit.extend(status_result.get("untracked_files", []))
        else:
            # Use staged files if any, otherwise use modified files
            files_to_commit = status_result.get("staged_files", [])
            if not files_to_commit:
                files_to_commit = status_result.get("modified_files", [])
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": commit_message,
                "files_to_commit": files_to_commit,
                "files_count": len(files_to_commit)
            }
        
        # Execute commit
        commit_result = execute_git_commit(
            project_path,
            commit_message,
            files_to_commit,
            add_all=add_all
        )
        
        if commit_result["success"]:
            span.set_attributes({
                "autogit.commit_hash": commit_result.get("commit_hash", ""),
                "autogit.files_committed": len(files_to_commit),
                "autogit.message_length": len(commit_message)
            })
        
        return commit_result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Commit generation failed: {str(e)}"
        }


@tracer.start_as_current_span("autogit.sync_repository")
def sync_repository(
    project_path: Path,
    remote: str = "origin",
    branch: Optional[str] = None,
    pull_first: bool = True,
    force: bool = False,
    dry_run: bool = False,
    conflict_strategy: str = "merge"
) -> Dict[str, Any]:
    """
    Intelligently sync repository with remote.
    
    Args:
        project_path: Path to the Git repository
        remote: Remote repository name
        branch: Branch to sync (default: current branch)
        pull_first: Pull changes before pushing
        force: Force push (dangerous)
        dry_run: Preview without executing
        conflict_strategy: How to handle conflicts (merge, rebase, abort)
        
    Returns:
        Dict containing sync results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "autogit.operation": "sync_repository",
        "autogit.remote": remote,
        "autogit.branch": branch or "current",
        "autogit.pull_first": pull_first,
        "autogit.force": force,
        "autogit.dry_run": dry_run,
        "project.path": str(project_path)
    })
    
    try:
        # Get current branch if not specified
        if not branch:
            branch_result = get_git_branch_info(project_path)
            branch = branch_result.get("current_branch", "main")
        
        # Plan sync operations
        planned_operations = []
        
        if pull_first:
            planned_operations.append(f"git pull {remote} {branch}")
        
        planned_operations.append(f"git push {remote} {branch}" + (" --force" if force else ""))
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "planned_operations": planned_operations,
                "remote": remote,
                "branch": branch
            }
        
        # Execute sync operations
        sync_result = execute_git_sync(
            project_path,
            remote,
            branch,
            pull_first=pull_first,
            force=force,
            conflict_strategy=conflict_strategy
        )
        
        if sync_result["success"]:
            span.set_attributes({
                "autogit.operations_count": len(sync_result.get("operations_performed", [])),
                "autogit.commits_pulled": sync_result.get("commits_pulled", 0),
                "autogit.commits_pushed": sync_result.get("commits_pushed", 0)
            })
        
        return sync_result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Repository sync failed: {str(e)}"
        }


def _generate_status_insights(
    project_path: Path,
    status_result: Dict[str, Any],
    file_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate AI-powered insights for git status."""
    insights = {
        "commit_suggestion": "",
        "recommendations": [],
        "patterns_detected": []
    }
    
    try:
        # Analyze change patterns
        modified_files = status_result.get("modified_files", [])
        untracked_files = status_result.get("untracked_files", [])
        
        # Detect patterns
        if any(f.endswith(".py") for f in modified_files):
            insights["patterns_detected"].append("Python code changes")
            
        if any(f.endswith((".md", ".rst", ".txt")) for f in modified_files):
            insights["patterns_detected"].append("Documentation updates")
            
        if any(f.endswith((".yaml", ".yml", ".json", ".toml")) for f in modified_files):
            insights["patterns_detected"].append("Configuration changes")
            
        if any("test" in f.lower() for f in modified_files):
            insights["patterns_detected"].append("Test modifications")
        
        # Generate recommendations
        if len(modified_files) > 10:
            insights["recommendations"].append("Consider breaking changes into smaller commits")
            
        if untracked_files:
            insights["recommendations"].append(f"Review {len(untracked_files)} untracked files for inclusion")
            
        if not status_result.get("staged_files"):
            insights["recommendations"].append("Stage files with 'git add' before committing")
        
        # Suggest commit message based on patterns
        if insights["patterns_detected"]:
            pattern = insights["patterns_detected"][0].lower()
            if "python" in pattern:
                insights["commit_suggestion"] = "feat: improve Python implementation"
            elif "documentation" in pattern:
                insights["commit_suggestion"] = "docs: update documentation"
            elif "test" in pattern:
                insights["commit_suggestion"] = "test: update test suite"
            elif "configuration" in pattern:
                insights["commit_suggestion"] = "config: update configuration"
            else:
                insights["commit_suggestion"] = "chore: general improvements"
        
    except Exception:
        # Graceful fallback if AI analysis fails
        insights["commit_suggestion"] = "chore: update files"
        insights["recommendations"] = ["Review changes before committing"]
    
    return insights


def _generate_fallback_message(status_result: Dict[str, Any], conventional: bool = True) -> str:
    """Generate a simple fallback commit message."""
    modified_count = len(status_result.get("modified_files", []))
    untracked_count = len(status_result.get("untracked_files", []))
    
    if conventional:
        if modified_count > 0 and untracked_count > 0:
            return f"chore: update {modified_count} files and add {untracked_count} new files"
        elif modified_count > 0:
            return f"chore: update {modified_count} files"
        elif untracked_count > 0:
            return f"feat: add {untracked_count} new files"
        else:
            return "chore: general updates"
    else:
        if modified_count > 0 and untracked_count > 0:
            return f"Update {modified_count} files and add {untracked_count} new files"
        elif modified_count > 0:
            return f"Update {modified_count} files"
        elif untracked_count > 0:
            return f"Add {untracked_count} new files"
        else:
            return "General updates"