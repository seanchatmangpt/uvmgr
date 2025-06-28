"""
GitHub Actions operations with comprehensive validation.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uvmgr.core.telemetry import span, record_exception
from uvmgr.core.validation import ValidationOrchestrator, ValidationLevel

logger = logging.getLogger(__name__)


class GitHubActionsOps:
    """GitHub Actions operations with validation."""
    
    def __init__(self, token: str, owner: str, repo: str, validation_level: ValidationLevel = ValidationLevel.STRICT):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.validator = ValidationOrchestrator(validation_level)
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to GitHub API with validation."""
        with span("github.request", endpoint=endpoint, method=method):
            url = f"{self.base_url}/{endpoint}"
            
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "uvmgr/1.0"
            }
            
            if data:
                headers["Content-Type"] = "application/json"
                request_data = json.dumps(data).encode('utf-8')
            else:
                request_data = None
            
            try:
                request = Request(url, data=request_data, headers=headers, method=method)
                with urlopen(request) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    
                    # Validate response
                    validation_result = self.validator.validate_github_actions_response(
                        response_data, 
                        {"endpoint": endpoint, "method": method},
                        self._get_response_type(endpoint)
                    )
                    
                    if not validation_result.is_valid:
                        logger.warning(f"Validation failed for {endpoint}: {validation_result.issues}")
                        record_exception(
                            Exception(f"API response validation failed: {validation_result.issues}"),
                            attributes={
                                "endpoint": endpoint,
                                "confidence": validation_result.confidence,
                                "validation_issues": validation_result.issues
                            }
                        )
                    
                    return {
                        "data": response_data,
                        "validation": validation_result,
                        "status_code": response.status
                    }
                    
            except HTTPError as e:
                logger.error(f"HTTP error for {endpoint}: {e.code} - {e.reason}")
                record_exception(e, attributes={"endpoint": endpoint, "status_code": e.code})
                raise
            except URLError as e:
                logger.error(f"URL error for {endpoint}: {e.reason}")
                record_exception(e, attributes={"endpoint": endpoint})
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {endpoint}: {e}")
                record_exception(e, attributes={"endpoint": endpoint})
                raise
    
    def _get_response_type(self, endpoint: str) -> str:
        """Determine response type based on endpoint."""
        if "workflows" in endpoint:
            return "workflows"
        elif "runs" in endpoint:
            return "workflow_runs"
        elif "jobs" in endpoint:
            return "jobs"
        else:
            return "unknown"
    
    def list_workflows(self, per_page: int = 30) -> Dict[str, Any]:
        """List workflows with validation."""
        with span("actions.list_workflows", per_page=per_page):
            endpoint = f"actions/workflows?per_page={per_page}"
            return self._make_request(endpoint)
    
    def list_workflow_runs(self, workflow_id: Optional[str] = None, 
                          status: Optional[str] = None, 
                          per_page: int = 30) -> Dict[str, Any]:
        """List workflow runs with validation."""
        with span("actions.list_workflow_runs", workflow_id=workflow_id, status=status):
            endpoint = "actions/runs"
            params = [f"per_page={per_page}"]
            
            if workflow_id:
                params.append(f"workflow_id={workflow_id}")
            if status:
                params.append(f"status={status}")
            
            if params:
                endpoint += "?" + "&".join(params)
            
            return self._make_request(endpoint)
    
    def get_workflow_run(self, run_id: str) -> Dict[str, Any]:
        """Get specific workflow run with validation."""
        with span("actions.get_workflow_run", run_id=run_id):
            endpoint = f"actions/runs/{run_id}"
            return self._make_request(endpoint)
    
    def list_jobs(self, run_id: str) -> Dict[str, Any]:
        """List jobs for a workflow run with validation."""
        with span("actions.list_jobs", run_id=run_id):
            endpoint = f"actions/runs/{run_id}/jobs"
            return self._make_request(endpoint)
    
    def get_job_logs(self, job_id: str) -> Dict[str, Any]:
        """Get job logs with validation."""
        with span("actions.get_job_logs", job_id=job_id):
            endpoint = f"actions/jobs/{job_id}/logs"
            return self._make_request(endpoint)
    
    def cancel_workflow_run(self, run_id: str) -> Dict[str, Any]:
        """Cancel workflow run with validation."""
        with span("actions.cancel_workflow_run", run_id=run_id):
            endpoint = f"actions/runs/{run_id}/cancel"
            return self._make_request(endpoint, method="POST")
    
    def rerun_workflow(self, run_id: str, enable_debug_logging: bool = False) -> Dict[str, Any]:
        """Rerun workflow with validation."""
        with span("actions.rerun_workflow", run_id=run_id, enable_debug_logging=enable_debug_logging):
            endpoint = f"actions/runs/{run_id}/rerun"
            data = {"enable_debug_logging": enable_debug_logging} if enable_debug_logging else None
            return self._make_request(endpoint, method="POST", data=data)
    
    def list_artifacts(self, run_id: str) -> Dict[str, Any]:
        """List artifacts for a workflow run with validation."""
        with span("actions.list_artifacts", run_id=run_id):
            endpoint = f"actions/runs/{run_id}/artifacts"
            return self._make_request(endpoint)
    
    def download_artifact(self, artifact_id: str, archive_format: str = "zip") -> Dict[str, Any]:
        """Download artifact with validation."""
        with span("actions.download_artifact", artifact_id=artifact_id, archive_format=archive_format):
            endpoint = f"actions/artifacts/{artifact_id}/{archive_format}"
            return self._make_request(endpoint)
    
    def list_secrets(self) -> Dict[str, Any]:
        """List repository secrets with validation."""
        with span("actions.list_secrets"):
            endpoint = "actions/secrets"
            return self._make_request(endpoint)
    
    def list_variables(self) -> Dict[str, Any]:
        """List repository variables with validation."""
        with span("actions.list_variables"):
            endpoint = "actions/variables"
            return self._make_request(endpoint)
    
    def get_usage(self) -> Dict[str, Any]:
        """Get repository usage with validation."""
        with span("actions.get_usage"):
            endpoint = "actions/cache/usage"
            return self._make_request(endpoint)
    
    def get_workflow_usage(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow usage with validation."""
        with span("actions.get_workflow_usage", workflow_id=workflow_id):
            endpoint = f"actions/workflows/{workflow_id}/timing"
            return self._make_request(endpoint) 