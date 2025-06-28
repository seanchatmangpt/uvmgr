"""
GitHub Actions commands with validation integration.
"""

import typer
from typing import Optional, List
from uvmgr.ops.actions_ops import GitHubActionsOps
from uvmgr.runtime.actions import get_github_token, get_repo_info
from uvmgr.core.telemetry import span
from uvmgr.core.validation import ValidationLevel

app = typer.Typer(help="GitHub Actions management commands")


@app.command()
def status(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """Check GitHub Actions status with validation."""
    with span("actions.status", owner=owner, repo=repo, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            # Get workflow runs
            runs_result = ops.list_workflow_runs(per_page=10)
            
            # Validate and display results
            if runs_result["validation"].is_valid:
                typer.echo(f"✅ GitHub Actions Status (confidence: {runs_result['validation'].confidence:.2f})")
                
                if runs_result["data"]["workflow_runs"]:
                    typer.echo("\nRecent Workflow Runs:")
                    for run in runs_result["data"]["workflow_runs"]:
                        status_emoji = {
                            "completed": "✅" if run["conclusion"] == "success" else "❌",
                            "in_progress": "🔄",
                            "queued": "⏳",
                            "waiting": "⏳"
                        }.get(run["status"], "❓")
                        
                        typer.echo(f"  {status_emoji} {run['name']} - {run['status']} ({run['id']})")
                else:
                    typer.echo("  No recent workflow runs found.")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {runs_result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(runs_result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  GitHub Actions Status - Validation Issues Detected")
                typer.echo(f"   Confidence: {runs_result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(runs_result['validation'].issues)}")
                
                # Still show data if available, but with warning
                if runs_result["data"]["workflow_runs"]:
                    typer.echo("\n⚠️  Data (may contain hallucinations):")
                    for run in runs_result["data"]["workflow_runs"]:
                        typer.echo(f"  ❓ {run.get('name', 'Unknown')} - {run.get('status', 'Unknown')}")
                
        except Exception as e:
            typer.echo(f"❌ Error checking GitHub Actions status: {e}")
            raise typer.Exit(1)


@app.command()
def workflows(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """List GitHub Actions workflows with validation."""
    with span("actions.workflows", owner=owner, repo=repo, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.list_workflows()
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Workflows (confidence: {result['validation'].confidence:.2f})")
                
                if result["data"]:
                    typer.echo("\nAvailable Workflows:")
                    for workflow in result["data"]:
                        state_emoji = "🟢" if workflow["state"] == "active" else "🔴"
                        typer.echo(f"  {state_emoji} {workflow['name']} ({workflow['state']})")
                        typer.echo(f"     Path: {workflow['path']}")
                        typer.echo(f"     ID: {workflow['id']}")
                        typer.echo()
                else:
                    typer.echo("  No workflows found.")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  Workflows - Validation Issues Detected")
                typer.echo(f"   Confidence: {result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error listing workflows: {e}")
            raise typer.Exit(1)


@app.command()
def runs(
    workflow_id: Optional[str] = typer.Option(None, "--workflow", "-w", help="Workflow ID or name"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """List workflow runs with validation."""
    with span("actions.runs", workflow_id=workflow_id, status=status, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.list_workflow_runs(workflow_id=workflow_id, status=status)
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Workflow Runs (confidence: {result['validation'].confidence:.2f})")
                
                if result["data"]["workflow_runs"]:
                    typer.echo(f"\nWorkflow Runs ({len(result['data']['workflow_runs'])} found):")
                    for run in result["data"]["workflow_runs"]:
                        status_emoji = {
                            "completed": "✅" if run["conclusion"] == "success" else "❌",
                            "in_progress": "🔄",
                            "queued": "⏳",
                            "waiting": "⏳"
                        }.get(run["status"], "❓")
                        
                        typer.echo(f"  {status_emoji} {run['name']}")
                        typer.echo(f"     ID: {run['id']}")
                        typer.echo(f"     Status: {run['status']}")
                        if run.get("conclusion"):
                            typer.echo(f"     Conclusion: {run['conclusion']}")
                        typer.echo(f"     Event: {run['event']}")
                        typer.echo(f"     Branch: {run['head_branch']}")
                        typer.echo(f"     Created: {run['created_at']}")
                        typer.echo()
                else:
                    typer.echo("  No workflow runs found.")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  Workflow Runs - Validation Issues Detected")
                typer.echo(f"   Confidence: {result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error listing workflow runs: {e}")
            raise typer.Exit(1)


@app.command()
def run(
    run_id: str = typer.Argument(..., help="Workflow run ID"),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """Get specific workflow run details with validation."""
    with span("actions.run", run_id=run_id, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.get_workflow_run(run_id)
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Workflow Run Details (confidence: {result['validation'].confidence:.2f})")
                
                run_data = result["data"]
                status_emoji = {
                    "completed": "✅" if run_data["conclusion"] == "success" else "❌",
                    "in_progress": "🔄",
                    "queued": "⏳",
                    "waiting": "⏳"
                }.get(run_data["status"], "❓")
                
                typer.echo(f"\n{status_emoji} {run_data['name']}")
                typer.echo(f"  ID: {run_data['id']}")
                typer.echo(f"  Status: {run_data['status']}")
                if run_data.get("conclusion"):
                    typer.echo(f"  Conclusion: {run_data['conclusion']}")
                typer.echo(f"  Event: {run_data['event']}")
                typer.echo(f"  Branch: {run_data['head_branch']}")
                typer.echo(f"  Created: {run_data['created_at']}")
                typer.echo(f"  Updated: {run_data['updated_at']}")
                if run_data.get("html_url"):
                    typer.echo(f"  URL: {run_data['html_url']}")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  Workflow Run - Validation Issues Detected")
                typer.echo(f"   Confidence: {result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error getting workflow run: {e}")
            raise typer.Exit(1)


@app.command()
def jobs(
    run_id: str = typer.Argument(..., help="Workflow run ID"),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """List jobs for a workflow run with validation."""
    with span("actions.jobs", run_id=run_id, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.list_jobs(run_id)
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Jobs (confidence: {result['validation'].confidence:.2f})")
                
                if result["data"]["jobs"]:
                    typer.echo(f"\nJobs for Run {run_id}:")
                    for job in result["data"]["jobs"]:
                        status_emoji = {
                            "completed": "✅" if job["conclusion"] == "success" else "❌",
                            "in_progress": "🔄",
                            "queued": "⏳",
                            "waiting": "⏳"
                        }.get(job["status"], "❓")
                        
                        typer.echo(f"  {status_emoji} {job['name']}")
                        typer.echo(f"     ID: {job['id']}")
                        typer.echo(f"     Status: {job['status']}")
                        if job.get("conclusion"):
                            typer.echo(f"     Conclusion: {job['conclusion']}")
                        typer.echo(f"     Started: {job['started_at']}")
                        if job.get("completed_at"):
                            typer.echo(f"     Completed: {job['completed_at']}")
                        typer.echo()
                else:
                    typer.echo("  No jobs found.")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  Jobs - Validation Issues Detected")
                typer.echo(f"   Confidence: {result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error listing jobs: {e}")
            raise typer.Exit(1)


@app.command()
def cancel(
    run_id: str = typer.Argument(..., help="Workflow run ID to cancel"),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    )
):
    """Cancel a workflow run with validation."""
    with span("actions.cancel", run_id=run_id, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.cancel_workflow_run(run_id)
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Workflow run {run_id} cancelled successfully")
                typer.echo(f"   Validation confidence: {result['validation'].confidence:.2f}")
            else:
                typer.echo(f"⚠️  Workflow run cancelled but validation issues detected")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error cancelling workflow run: {e}")
            raise typer.Exit(1)


@app.command()
def rerun(
    run_id: str = typer.Argument(..., help="Workflow run ID to rerun"),
    enable_debug_logging: bool = typer.Option(
        False, 
        "--debug", 
        help="Enable debug logging for the rerun"
    ),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    )
):
    """Rerun a workflow with validation."""
    with span("actions.rerun", run_id=run_id, enable_debug_logging=enable_debug_logging, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.rerun_workflow(run_id, enable_debug_logging)
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Workflow run {run_id} rerun initiated successfully")
                if enable_debug_logging:
                    typer.echo("   Debug logging enabled")
                typer.echo(f"   Validation confidence: {result['validation'].confidence:.2f}")
            else:
                typer.echo(f"⚠️  Workflow rerun initiated but validation issues detected")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error rerunning workflow: {e}")
            raise typer.Exit(1)


@app.command()
def artifacts(
    run_id: str = typer.Argument(..., help="Workflow run ID"),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """List artifacts for a workflow run with validation."""
    with span("actions.artifacts", run_id=run_id, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.list_artifacts(run_id)
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Artifacts (confidence: {result['validation'].confidence:.2f})")
                
                if result["data"]["artifacts"]:
                    typer.echo(f"\nArtifacts for Run {run_id}:")
                    for artifact in result["data"]["artifacts"]:
                        typer.echo(f"  📦 {artifact['name']}")
                        typer.echo(f"     ID: {artifact['id']}")
                        typer.echo(f"     Size: {artifact['size_in_bytes']} bytes")
                        typer.echo(f"     Created: {artifact['created_at']}")
                        typer.echo(f"     Expires: {artifact['expires_at']}")
                        typer.echo()
                else:
                    typer.echo("  No artifacts found.")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  Artifacts - Validation Issues Detected")
                typer.echo(f"   Confidence: {result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error listing artifacts: {e}")
            raise typer.Exit(1)


@app.command()
def secrets(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """List repository secrets with validation."""
    with span("actions.secrets", owner=owner, repo=repo, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.list_secrets()
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Secrets (confidence: {result['validation'].confidence:.2f})")
                
                if result["data"]["secrets"]:
                    typer.echo(f"\nRepository Secrets:")
                    for secret in result["data"]["secrets"]:
                        typer.echo(f"  🔐 {secret['name']}")
                        typer.echo(f"     Created: {secret['created_at']}")
                        typer.echo(f"     Updated: {secret['updated_at']}")
                        typer.echo()
                else:
                    typer.echo("  No secrets found.")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  Secrets - Validation Issues Detected")
                typer.echo(f"   Confidence: {result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error listing secrets: {e}")
            raise typer.Exit(1)


@app.command()
def variables(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """List repository variables with validation."""
    with span("actions.variables", owner=owner, repo=repo, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.list_variables()
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Variables (confidence: {result['validation'].confidence:.2f})")
                
                if result["data"]["variables"]:
                    typer.echo(f"\nRepository Variables:")
                    for variable in result["data"]["variables"]:
                        typer.echo(f"  📝 {variable['name']}")
                        typer.echo(f"     Created: {variable['created_at']}")
                        typer.echo(f"     Updated: {variable['updated_at']}")
                        typer.echo()
                else:
                    typer.echo("  No variables found.")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  Variables - Validation Issues Detected")
                typer.echo(f"   Confidence: {result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error listing variables: {e}")
            raise typer.Exit(1)


@app.command()
def usage(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    show_validation: bool = typer.Option(
        False, 
        "--show-validation", 
        help="Show validation details"
    )
):
    """Get repository usage statistics with validation."""
    with span("actions.usage", owner=owner, repo=repo, validation_level=validation_level.value):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            result = ops.get_usage()
            
            if result["validation"].is_valid:
                typer.echo(f"✅ Usage Statistics (confidence: {result['validation'].confidence:.2f})")
                
                usage_data = result["data"]
                typer.echo(f"\nRepository Usage:")
                typer.echo(f"  Full Name: {usage_data.get('full_name', 'N/A')}")
                typer.echo(f"  Active Caches: {usage_data.get('active_caches_count', 0)}")
                typer.echo(f"  Active Caches Size: {usage_data.get('active_caches_size_in_bytes', 0)} bytes")
                
                if show_validation:
                    typer.echo(f"\n📊 Validation Details:")
                    typer.echo(f"  Level: {validation_level.value}")
                    typer.echo(f"  Confidence: {result['validation'].confidence:.2f}")
                    typer.echo(f"  Issues: {len(result['validation'].issues)}")
                    
            else:
                typer.echo(f"⚠️  Usage Statistics - Validation Issues Detected")
                typer.echo(f"   Confidence: {result['validation'].confidence:.2f}")
                typer.echo(f"   Issues: {', '.join(result['validation'].issues)}")
                
        except Exception as e:
            typer.echo(f"❌ Error getting usage statistics: {e}")
            raise typer.Exit(1) 