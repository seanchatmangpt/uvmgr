import typer
from uvmgr.core.instrumentation import instrument_command, add_span_attributes
from uvmgr.core.semconv import CliAttributes, GitHubAttributes
from uvmgr.ops import actions as actions_ops

app = typer.Typer(help="GitHub Actions utilities")

def _get_token(token: str = None) -> str:
    """Get GitHub token from CLI or GitHub CLI."""
    try:
        return actions_ops.get_github_token(token)
    except RuntimeError as e:
        typer.echo("❌ " + str(e))
        raise typer.Exit(1)

@app.command("status")
@instrument_command("actions_status", track_args=True)
def status(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    limit: int = typer.Option(10, help="Number of runs to show"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """Show recent GitHub Actions workflow runs for a repo."""
    # Add Weaver semantic convention attributes
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            "github.actions.limit": limit,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    runs = actions_ops.get_workflow_runs(owner, repo, limit, token)
    if not runs:
        typer.echo("No workflow runs found.")
        raise typer.Exit(1)
    
    # Add result metrics
    add_span_attributes(
        **{
            "github.actions.runs_count": len(runs),
            "github.actions.success_count": len([r for r in runs if r.get("conclusion") == "success"]),
            "github.actions.failure_count": len([r for r in runs if r.get("conclusion") == "failure"]),
        }
    )
    
    typer.echo(f"📊 Recent workflow runs for {owner}/{repo}:")
    typer.echo(f"{'Workflow':30} {'Status':12} {'Conclusion':12} {'Event':10} {'Branch':10}")
    typer.echo("-" * 80)
    
    for run in runs:
        conclusion = run.get("conclusion", "running") if run.get("status") == "completed" else run.get("status", "unknown")
        typer.echo(f"{run['name'][:28]:30} {run['status'][:10]:12} {str(conclusion)[:10]:12} {run['event'][:8]:10} {run['head_branch'][:8]:10}")

@app.command("workflows")
@instrument_command("actions_workflows", track_args=True)
def workflows(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """List all workflows in a repository."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    workflow_list = actions_ops.get_workflows(owner, repo, token)
    if not workflow_list:
        typer.echo("No workflows found.")
        raise typer.Exit(1)
    
    add_span_attributes(
        **{
            "github.actions.workflows_count": len(workflow_list),
        }
    )
    
    typer.echo(f"🔧 Workflows in {owner}/{repo}:")
    typer.echo(f"{'Name':40} {'State':10} {'Path':30}")
    typer.echo("-" * 80)
    
    for workflow in workflow_list:
        typer.echo(f"{workflow['name'][:38]:40} {workflow['state'][:8]:10} {workflow['path'][:28]:30}")

@app.command("run")
@instrument_command("actions_run", track_args=True)
def run(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    run_id: int = typer.Option(..., help="Workflow run ID"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """Get detailed information about a specific workflow run."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            GitHubAttributes.WORKFLOW_RUN_ID: run_id,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    run_details = actions_ops.get_workflow_run(owner, repo, run_id, token)
    if not run_details:
        typer.echo("Workflow run not found.")
        raise typer.Exit(1)
    
    typer.echo(f"🔍 Workflow Run Details:")
    typer.echo(f"  Name: {run_details['name']}")
    typer.echo(f"  Status: {run_details['status']}")
    typer.echo(f"  Conclusion: {run_details.get('conclusion', 'N/A')}")
    typer.echo(f"  Event: {run_details['event']}")
    typer.echo(f"  Branch: {run_details['head_branch']}")
    typer.echo(f"  Commit: {run_details['head_sha'][:8]}")
    typer.echo(f"  Created: {run_details['created_at']}")
    typer.echo(f"  Updated: {run_details['updated_at']}")
    typer.echo(f"  URL: {run_details['html_url']}")

@app.command("jobs")
@instrument_command("actions_jobs", track_args=True)
def jobs(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    run_id: int = typer.Option(..., help="Workflow run ID"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """List jobs for a specific workflow run."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            GitHubAttributes.WORKFLOW_RUN_ID: run_id,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    job_list = actions_ops.get_workflow_run_jobs(owner, repo, run_id, token)
    if not job_list:
        typer.echo("No jobs found for this workflow run.")
        raise typer.Exit(1)
    
    add_span_attributes(
        **{
            "github.actions.jobs_count": len(job_list),
        }
    )
    
    typer.echo(f"⚙️  Jobs for workflow run {run_id}:")
    typer.echo(f"{'Name':30} {'Status':12} {'Conclusion':12} {'Duration':10}")
    typer.echo("-" * 70)
    
    for job in job_list:
        duration = job.get('duration', 0)
        duration_str = f"{duration//60}m{duration%60}s" if duration else "N/A"
        conclusion = job.get("conclusion", "running") if job.get("status") == "completed" else job.get("status", "unknown")
        typer.echo(f"{job['name'][:28]:30} {job['status'][:10]:12} {str(conclusion)[:10]:12} {duration_str:10}")

@app.command("logs")
@instrument_command("actions_logs", track_args=True)
def logs(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    run_id: int = typer.Option(..., help="Workflow run ID"),
    job_id: int = typer.Option(None, help="Specific job ID (optional)"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """Get logs for a workflow run or specific job."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            GitHubAttributes.WORKFLOW_RUN_ID: run_id,
            "github.actions.job_id": job_id,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    if job_id:
        log_data = actions_ops.get_job_logs(owner, repo, job_id, token)
        typer.echo(f"📋 Logs for job {job_id}:")
    else:
        log_data = actions_ops.get_workflow_run_logs(owner, repo, run_id, token)
        typer.echo(f"📋 Logs for workflow run {run_id}:")
    
    if not log_data:
        typer.echo("No logs found.")
        raise typer.Exit(1)
    
    typer.echo(log_data)

@app.command("cancel")
@instrument_command("actions_cancel", track_args=True)
def cancel(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    run_id: int = typer.Option(..., help="Workflow run ID"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """Cancel a running workflow."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            GitHubAttributes.WORKFLOW_RUN_ID: run_id,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    success = actions_ops.cancel_workflow_run(owner, repo, run_id, token)
    if success:
        typer.echo(f"✅ Successfully cancelled workflow run {run_id}")
    else:
        typer.echo(f"❌ Failed to cancel workflow run {run_id}")
        raise typer.Exit(1)

@app.command("rerun")
@instrument_command("actions_rerun", track_args=True)
def rerun(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    run_id: int = typer.Option(..., help="Workflow run ID"),
    failed_only: bool = typer.Option(False, help="Rerun only failed jobs"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """Rerun a workflow."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            GitHubAttributes.WORKFLOW_RUN_ID: run_id,
            "github.actions.failed_only": failed_only,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    success = actions_ops.rerun_workflow(owner, repo, run_id, failed_only, token)
    if success:
        typer.echo(f"✅ Successfully triggered rerun for workflow run {run_id}")
    else:
        typer.echo(f"❌ Failed to rerun workflow run {run_id}")
        raise typer.Exit(1)

@app.command("artifacts")
@instrument_command("actions_artifacts", track_args=True)
def artifacts(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    run_id: int = typer.Option(..., help="Workflow run ID"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """List artifacts for a workflow run."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            GitHubAttributes.WORKFLOW_RUN_ID: run_id,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    artifact_list = actions_ops.get_workflow_run_artifacts(owner, repo, run_id, token)
    if not artifact_list:
        typer.echo("No artifacts found for this workflow run.")
        raise typer.Exit(1)
    
    add_span_attributes(
        **{
            "github.actions.artifacts_count": len(artifact_list),
        }
    )
    
    typer.echo(f"📦 Artifacts for workflow run {run_id}:")
    typer.echo(f"{'Name':30} {'Size':12} {'Expires':15}")
    typer.echo("-" * 60)
    
    for artifact in artifact_list:
        size_mb = artifact.get('size_in_bytes', 0) / (1024 * 1024)
        typer.echo(f"{artifact['name'][:28]:30} {size_mb:.1f}MB{'':8} {artifact.get('expires_at', 'N/A')[:10]:15}")

@app.command("secrets")
@instrument_command("actions_secrets", track_args=True)
def secrets(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """List repository secrets (names only, not values)."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    secret_list = actions_ops.get_repository_secrets(owner, repo, token)
    if not secret_list:
        typer.echo("No secrets found.")
        raise typer.Exit(1)
    
    add_span_attributes(
        **{
            "github.actions.secrets_count": len(secret_list),
        }
    )
    
    typer.echo(f"🔐 Repository secrets for {owner}/{repo}:")
    typer.echo(f"{'Name':30} {'Updated':15}")
    typer.echo("-" * 50)
    
    for secret in secret_list:
        typer.echo(f"{secret['name'][:28]:30} {secret.get('updated_at', 'N/A')[:10]:15}")

@app.command("variables")
@instrument_command("actions_variables", track_args=True)
def variables(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """List repository variables."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    variable_list = actions_ops.get_repository_variables(owner, repo, token)
    if not variable_list:
        typer.echo("No variables found.")
        raise typer.Exit(1)
    
    add_span_attributes(
        **{
            "github.actions.variables_count": len(variable_list),
        }
    )
    
    typer.echo(f"📝 Repository variables for {owner}/{repo}:")
    typer.echo(f"{'Name':30} {'Value':20} {'Updated':15}")
    typer.echo("-" * 70)
    
    for variable in variable_list:
        value_preview = variable.get('value', '')[:18] + '..' if len(variable.get('value', '')) > 20 else variable.get('value', '')
        typer.echo(f"{variable['name'][:28]:30} {value_preview:20} {variable.get('updated_at', 'N/A')[:10]:15}")

@app.command("usage")
@instrument_command("actions_usage", track_args=True)
def usage(
    owner: str = typer.Option(..., help="GitHub owner/org name"),
    repo: str = typer.Option(..., help="GitHub repository name"),
    token: str = typer.Option(None, help="GitHub token (will use gh auth token if not provided)"),
):
    """Show GitHub Actions usage for a repository."""
    add_span_attributes(
        **{
            GitHubAttributes.OWNER: owner,
            GitHubAttributes.REPOSITORY: repo,
            "github.actions.token_provided": token is not None,
        }
    )
    
    token = _get_token(token)
    
    usage_data = actions_ops.get_repository_usage(owner, repo, token)
    if not usage_data:
        typer.echo("No usage data found.")
        raise typer.Exit(1)
    
    typer.echo(f"📊 GitHub Actions usage for {owner}/{repo}:")
    typer.echo(f"  Billable minutes: {usage_data.get('billable_minutes', 'N/A')}")
    typer.echo(f"  Total minutes: {usage_data.get('total_minutes', 'N/A')}")
    typer.echo(f"  Included minutes: {usage_data.get('included_minutes', 'N/A')}")
    typer.echo(f"  Period: {usage_data.get('period', 'N/A')}") 