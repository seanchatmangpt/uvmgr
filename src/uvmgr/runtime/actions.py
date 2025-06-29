import urllib.request
import urllib.error
import json
from uvmgr.core.telemetry import span, record_exception, metric_histogram
from uvmgr.core.semconv import GitHubAttributes

def _make_request(url: str, token: str = None, method: str = "GET", data: dict = None):
    """Make a GitHub API request with proper error handling."""
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/vnd.github+json')
    if token:
        req.add_header('Authorization', f'token {token}')
    
    if method != "GET":
        req.method = method
        if data:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode()
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp
    except urllib.error.HTTPError as e:
        record_exception(e, attributes={
            "github.api.endpoint": url,
            "github.api.method": method
        })
        return None
    except Exception as e:
        record_exception(e, attributes={
            "github.api.endpoint": url,
            "github.api.method": method
        })
        return None

def get_workflow_runs(owner, repo, limit=10, token=None):
    """Get GitHub Actions workflow runs from GitHub API with Weaver instrumentation."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              limit=limit,
              endpoint="/repos/{owner}/{repo}/actions/runs"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page={limit}"
        
        try:
            duration_histogram = metric_histogram("github.api.request.duration", unit="ms")
            
            resp = _make_request(url, token)
            if not resp:
                return []
            
            duration_histogram(0)  # Placeholder
            
            data = json.loads(resp.read().decode())
            runs = data.get("workflow_runs", [])
            
            result = []
            
            for run in runs[:limit]:
                result.append({
                    "name": run.get("name", ""),
                    "status": run.get("status", ""),
                    "conclusion": run.get("conclusion", ""),
                    "event": run.get("event", ""),
                    "head_branch": run.get("head_branch", ""),
                    "html_url": run.get("html_url", ""),
                })
            
            with span("github.api.response_processing",
                      runs_count=len(result),
                      total_available=len(runs)):
                pass
            
            return result
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo
            })
            return []

def get_workflows(owner, repo, token=None):
    """Get GitHub Actions workflows from GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              endpoint="/repos/{owner}/{repo}/actions/workflows"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows"
        
        try:
            resp = _make_request(url, token)
            if not resp:
                return []
            
            data = json.loads(resp.read().decode())
            workflows = data.get("workflows", [])
            
            result = []
            for workflow in workflows:
                result.append({
                    "name": workflow.get("name", ""),
                    "state": workflow.get("state", ""),
                    "path": workflow.get("path", ""),
                    "id": workflow.get("id", ""),
                })
            
            return result
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo
            })
            return []

def get_workflow_run(owner, repo, run_id, token=None):
    """Get specific workflow run details from GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              run_id=run_id,
              endpoint="/repos/{owner}/{repo}/actions/runs/{run_id}"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}"
        
        try:
            resp = _make_request(url, token)
            if not resp:
                return None
            
            data = json.loads(resp.read().decode())
            
            return {
                "name": data.get("name", ""),
                "status": data.get("status", ""),
                "conclusion": data.get("conclusion", ""),
                "event": data.get("event", ""),
                "head_branch": data.get("head_branch", ""),
                "head_sha": data.get("head_sha", ""),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "html_url": data.get("html_url", ""),
            }
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo,
                "github.api.run_id": run_id
            })
            return None

def get_workflow_run_jobs(owner, repo, run_id, token=None):
    """Get jobs for a workflow run from GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              run_id=run_id,
              endpoint="/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
        
        try:
            resp = _make_request(url, token)
            if not resp:
                return []
            
            data = json.loads(resp.read().decode())
            jobs = data.get("jobs", [])
            
            result = []
            for job in jobs:
                result.append({
                    "name": job.get("name", ""),
                    "status": job.get("status", ""),
                    "conclusion": job.get("conclusion", ""),
                    "duration": job.get("duration", 0),
                    "id": job.get("id", ""),
                })
            
            return result
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo,
                "github.api.run_id": run_id
            })
            return []

def get_workflow_run_logs(owner, repo, run_id, token=None):
    """Get logs for a workflow run from GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              run_id=run_id,
              endpoint="/repos/{owner}/{repo}/actions/runs/{run_id}/logs"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        
        try:
            resp = _make_request(url, token)
            if not resp:
                return None
            
            return resp.read().decode()
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo,
                "github.api.run_id": run_id
            })
            return None

def get_job_logs(owner, repo, job_id, token=None):
    """Get logs for a specific job from GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              job_id=job_id,
              endpoint="/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        
        try:
            resp = _make_request(url, token)
            if not resp:
                return None
            
            return resp.read().decode()
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo,
                "github.api.job_id": job_id
            })
            return None

def cancel_workflow_run(owner, repo, run_id, token=None):
    """Cancel a workflow run via GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              run_id=run_id,
              endpoint="/repos/{owner}/{repo}/actions/runs/{run_id}/cancel"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/cancel"
        
        try:
            resp = _make_request(url, token, method="POST")
            return resp is not None and resp.status == 202
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo,
                "github.api.run_id": run_id
            })
            return False

def rerun_workflow(owner, repo, run_id, failed_only=False, token=None):
    """Rerun a workflow via GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              run_id=run_id,
              failed_only=failed_only,
              endpoint="/repos/{owner}/{repo}/actions/runs/{run_id}/rerun"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/rerun"
        data = {"enable_debug_logging": False}
        
        if failed_only:
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed-jobs"
        
        try:
            resp = _make_request(url, token, method="POST", data=data)
            return resp is not None and resp.status == 201
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo,
                "github.api.run_id": run_id
            })
            return False

def get_workflow_run_artifacts(owner, repo, run_id, token=None):
    """Get artifacts for a workflow run from GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              run_id=run_id,
              endpoint="/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
        
        try:
            resp = _make_request(url, token)
            if not resp:
                return []
            
            data = json.loads(resp.read().decode())
            artifacts = data.get("artifacts", [])
            
            result = []
            for artifact in artifacts:
                result.append({
                    "name": artifact.get("name", ""),
                    "size_in_bytes": artifact.get("size_in_bytes", 0),
                    "expires_at": artifact.get("expires_at", ""),
                    "id": artifact.get("id", ""),
                })
            
            return result
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo,
                "github.api.run_id": run_id
            })
            return []

def get_repository_secrets(owner, repo, token=None):
    """Get repository secrets from GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              endpoint="/repos/{owner}/{repo}/actions/secrets"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets"
        
        try:
            resp = _make_request(url, token)
            if not resp:
                return []
            
            data = json.loads(resp.read().decode())
            secrets = data.get("secrets", [])
            
            result = []
            for secret in secrets:
                result.append({
                    "name": secret.get("name", ""),
                    "updated_at": secret.get("updated_at", ""),
                })
            
            return result
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo
            })
            return []

def get_repository_variables(owner, repo, token=None):
    """Get repository variables from GitHub API."""
    with span("github.api.request",
              owner=owner,
              repository=repo,
              endpoint="/repos/{owner}/{repo}/actions/variables"):
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/variables"
        
        try:
            resp = _make_request(url, token)
            if not resp:
                return []
            
            data = json.loads(resp.read().decode())
            variables = data.get("variables", [])
            
            result = []
            for variable in variables:
                result.append({
                    "name": variable.get("name", ""),
                    "value": variable.get("value", ""),
                    "updated_at": variable.get("updated_at", ""),
                })
            
            return result
            
        except Exception as e:
            record_exception(e, attributes={
                "github.api.endpoint": url,
                "github.api.owner": owner,
                "github.api.repository": repo
            })
            return []

def get_repository_usage(owner, repo, token=None):
    """Get repository usage statistics."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/billing/usage"
    return _make_request(url, token)


def get_github_token():
    """Get GitHub token from environment or keyring."""
    import os
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            import keyring
            token = keyring.get_password("github", "token")
        except ImportError:
            pass
    return token


def get_repo_info(owner=None, repo=None):
    """Get repository owner and name from git remote or arguments."""
    if owner and repo:
        return owner, repo
    
    # Try to get from git remote
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        
        # Parse GitHub URL
        if "github.com" in remote_url:
            # Handle both SSH and HTTPS URLs
            if remote_url.startswith("git@"):
                # SSH format: git@github.com:owner/repo.git
                parts = remote_url.split(":")[-1].replace(".git", "").split("/")
            else:
                # HTTPS format: https://github.com/owner/repo.git
                parts = remote_url.split("/")[-2:]
                parts[-1] = parts[-1].replace(".git", "")
            
            if len(parts) >= 2:
                return parts[-2], parts[-1]
    except (subprocess.CalledProcessError, IndexError):
        pass
    
    # Fallback: prompt user or use defaults
    return owner or "unknown", repo or "unknown"
