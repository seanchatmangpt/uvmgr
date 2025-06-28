from uvmgr.core.telemetry import span, metric_counter
from uvmgr.runtime import actions as runtime_actions

def get_github_token(token: str = None) -> str:
    """Get GitHub token from CLI or GitHub CLI."""
    with span("actions.get_github_token", token_provided=token is not None):
        metric_counter("github.actions.token.requests")(1)
        
        if token:
            metric_counter("github.actions.token.source")(1, source="cli")
            return token
        
        try:
            from uvmgr.core.process import run_logged
            token = run_logged(["gh", "auth", "token"], capture=True).strip()
            metric_counter("github.actions.token.source")(1, source="gh_cli")
            return token
        except Exception as e:
            metric_counter("github.actions.token.failed")(1, error=str(e))
            raise RuntimeError(
                "GitHub token is required to access workflow runs. "
                "Please provide a token with --token or install GitHub CLI (gh). "
                "You can create a token at: https://github.com/settings/tokens"
            )

def get_workflow_runs(owner: str, repo: str, limit: int = 10, token: str = None):
    """Get GitHub Actions workflow runs with Weaver instrumentation."""
    with span("actions.get_workflow_runs", 
              owner=owner, 
              repository=repo, 
              limit=limit,
              token_provided=token is not None):
        
        # Record operation metric
        metric_counter("github.actions.api.calls")(1, operation="get_workflow_runs")
        
        runs = runtime_actions.get_workflow_runs(owner, repo, limit, token)
        
        # Record result metrics
        if runs:
            metric_counter("github.actions.runs.retrieved")(len(runs))
            success_count = len([r for r in runs if r.get("conclusion") == "success"])
            failure_count = len([r for r in runs if r.get("conclusion") == "failure"])
            
            if success_count > 0:
                metric_counter("github.actions.runs.success")(success_count)
            if failure_count > 0:
                metric_counter("github.actions.runs.failures")(failure_count)
        
        return runs

def get_workflows(owner: str, repo: str, token: str = None):
    """Get GitHub Actions workflows with Weaver instrumentation."""
    with span("actions.get_workflows", 
              owner=owner, 
              repository=repo,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_workflows")
        
        workflows = runtime_actions.get_workflows(owner, repo, token)
        
        if workflows:
            metric_counter("github.actions.workflows.retrieved")(len(workflows))
        
        return workflows

def get_workflow_run(owner: str, repo: str, run_id: int, token: str = None):
    """Get specific workflow run details with Weaver instrumentation."""
    with span("actions.get_workflow_run", 
              owner=owner, 
              repository=repo,
              run_id=run_id,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_workflow_run")
        
        run_details = runtime_actions.get_workflow_run(owner, repo, run_id, token)
        
        if run_details:
            metric_counter("github.actions.run.details.retrieved")(1)
        
        return run_details

def get_workflow_run_jobs(owner: str, repo: str, run_id: int, token: str = None):
    """Get jobs for a workflow run with Weaver instrumentation."""
    with span("actions.get_workflow_run_jobs", 
              owner=owner, 
              repository=repo,
              run_id=run_id,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_workflow_run_jobs")
        
        jobs = runtime_actions.get_workflow_run_jobs(owner, repo, run_id, token)
        
        if jobs:
            metric_counter("github.actions.jobs.retrieved")(len(jobs))
            success_count = len([j for j in jobs if j.get("conclusion") == "success"])
            failure_count = len([j for j in jobs if j.get("conclusion") == "failure"])
            
            if success_count > 0:
                metric_counter("github.actions.jobs.success")(success_count)
            if failure_count > 0:
                metric_counter("github.actions.jobs.failures")(failure_count)
        
        return jobs

def get_workflow_run_logs(owner: str, repo: str, run_id: int, token: str = None):
    """Get logs for a workflow run with Weaver instrumentation."""
    with span("actions.get_workflow_run_logs", 
              owner=owner, 
              repository=repo,
              run_id=run_id,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_workflow_run_logs")
        
        logs = runtime_actions.get_workflow_run_logs(owner, repo, run_id, token)
        
        if logs:
            metric_counter("github.actions.logs.retrieved")(1)
        
        return logs

def get_job_logs(owner: str, repo: str, job_id: int, token: str = None):
    """Get logs for a specific job with Weaver instrumentation."""
    with span("actions.get_job_logs", 
              owner=owner, 
              repository=repo,
              job_id=job_id,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_job_logs")
        
        logs = runtime_actions.get_job_logs(owner, repo, job_id, token)
        
        if logs:
            metric_counter("github.actions.job.logs.retrieved")(1)
        
        return logs

def cancel_workflow_run(owner: str, repo: str, run_id: int, token: str = None):
    """Cancel a workflow run with Weaver instrumentation."""
    with span("actions.cancel_workflow_run", 
              owner=owner, 
              repository=repo,
              run_id=run_id,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="cancel_workflow_run")
        
        success = runtime_actions.cancel_workflow_run(owner, repo, run_id, token)
        
        if success:
            metric_counter("github.actions.runs.cancelled")(1)
        else:
            metric_counter("github.actions.runs.cancel_failed")(1)
        
        return success

def rerun_workflow(owner: str, repo: str, run_id: int, failed_only: bool = False, token: str = None):
    """Rerun a workflow with Weaver instrumentation."""
    with span("actions.rerun_workflow", 
              owner=owner, 
              repository=repo,
              run_id=run_id,
              failed_only=failed_only,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="rerun_workflow")
        
        success = runtime_actions.rerun_workflow(owner, repo, run_id, failed_only, token)
        
        if success:
            metric_counter("github.actions.runs.rerun_triggered")(1)
        else:
            metric_counter("github.actions.runs.rerun_failed")(1)
        
        return success

def get_workflow_run_artifacts(owner: str, repo: str, run_id: int, token: str = None):
    """Get artifacts for a workflow run with Weaver instrumentation."""
    with span("actions.get_workflow_run_artifacts", 
              owner=owner, 
              repository=repo,
              run_id=run_id,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_workflow_run_artifacts")
        
        artifacts = runtime_actions.get_workflow_run_artifacts(owner, repo, run_id, token)
        
        if artifacts:
            metric_counter("github.actions.artifacts.retrieved")(len(artifacts))
        
        return artifacts

def get_repository_secrets(owner: str, repo: str, token: str = None):
    """Get repository secrets with Weaver instrumentation."""
    with span("actions.get_repository_secrets", 
              owner=owner, 
              repository=repo,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_repository_secrets")
        
        secrets = runtime_actions.get_repository_secrets(owner, repo, token)
        
        if secrets:
            metric_counter("github.actions.secrets.retrieved")(len(secrets))
        
        return secrets

def get_repository_variables(owner: str, repo: str, token: str = None):
    """Get repository variables with Weaver instrumentation."""
    with span("actions.get_repository_variables", 
              owner=owner, 
              repository=repo,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_repository_variables")
        
        variables = runtime_actions.get_repository_variables(owner, repo, token)
        
        if variables:
            metric_counter("github.actions.variables.retrieved")(len(variables))
        
        return variables

def get_repository_usage(owner: str, repo: str, token: str = None):
    """Get repository usage with Weaver instrumentation."""
    with span("actions.get_repository_usage", 
              owner=owner, 
              repository=repo,
              token_provided=token is not None):
        
        metric_counter("github.actions.api.calls")(1, operation="get_repository_usage")
        
        usage = runtime_actions.get_repository_usage(owner, repo, token)
        
        if usage:
            metric_counter("github.actions.usage.retrieved")(1)
        
        return usage

        return runs 