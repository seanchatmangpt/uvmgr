"""
Multi-layered validation system to detect hallucinations and ensure data integrity.
"""

import json
import hashlib
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
from uvmgr.core.telemetry import span, record_exception

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation levels for different types of checks."""
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    issues: List[str]
    metadata: Dict[str, Any]
    validation_level: ValidationLevel


class HallucinationDetector:
    """Multi-layered system to detect hallucinations in API responses."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STRICT):
        self.validation_level = validation_level
        self.known_patterns = self._load_known_patterns()
        self.suspicious_patterns = self._load_suspicious_patterns()
    
    def _load_known_patterns(self) -> Dict[str, Any]:
        """Load known valid patterns for GitHub API responses."""
        return {
            "workflow_run": {
                "required_fields": ["id", "name", "status", "conclusion", "event", "head_branch"],
                "status_values": ["queued", "in_progress", "completed", "waiting"],
                "conclusion_values": ["success", "failure", "cancelled", "skipped", "neutral", None],
                "event_values": ["push", "pull_request", "schedule", "workflow_dispatch", "repository_dispatch"],
                "id_pattern": r"^\d+$",
                "name_max_length": 100,
                "branch_max_length": 50
            },
            "workflow": {
                "required_fields": ["id", "name", "state", "path"],
                "state_values": ["active", "deleted", "disabled_fork", "disabled_inactivity", "disabled_manually"],
                "id_pattern": r"^\d+$",
                "name_max_length": 100,
                "path_pattern": r"^\.github/workflows/.*\.ya?ml$"
            },
            "job": {
                "required_fields": ["id", "name", "status", "conclusion"],
                "status_values": ["queued", "in_progress", "completed", "waiting"],
                "conclusion_values": ["success", "failure", "cancelled", "skipped", "neutral", None],
                "id_pattern": r"^\d+$",
                "name_max_length": 100
            }
        }
    
    def _load_suspicious_patterns(self) -> List[str]:
        """Load patterns that indicate potential hallucinations."""
        return [
            "lorem ipsum",
            "test data",
            "placeholder",
            "sample",
            "example",
            "dummy",
            "fake",
            "mock",
            "stub",
            "TODO",
            "FIXME",
            "XXX",
            "TBD"
        ]
    
    def validate_workflow_run(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate workflow run data for hallucinations."""
        with span("validation.workflow_run", validation_level=self.validation_level.value):
            issues = []
            confidence = 1.0
            
            # Basic field validation
            pattern = self.known_patterns["workflow_run"]
            
            # Check required fields
            for field in pattern["required_fields"]:
                if field not in data:
                    issues.append(f"Missing required field: {field}")
                    confidence -= 0.2
            
            # Check field values
            if "status" in data and data["status"] not in pattern["status_values"]:
                issues.append(f"Invalid status value: {data['status']}")
                confidence -= 0.3
            
            if "conclusion" in data and data["conclusion"] not in pattern["conclusion_values"]:
                issues.append(f"Invalid conclusion value: {data['conclusion']}")
                confidence -= 0.3
            
            if "event" in data and data["event"] not in pattern["event_values"]:
                issues.append(f"Invalid event value: {data['event']}")
                confidence -= 0.2
            
            # Check ID format
            if "id" in data and not str(data["id"]).isdigit():
                issues.append(f"Invalid ID format: {data['id']}")
                confidence -= 0.5
            
            # Check string lengths
            if "name" in data and len(str(data["name"])) > pattern["name_max_length"]:
                issues.append(f"Name too long: {len(str(data['name']))} chars")
                confidence -= 0.1
            
            if "head_branch" in data and len(str(data["head_branch"])) > pattern["branch_max_length"]:
                issues.append(f"Branch name too long: {len(str(data['head_branch']))} chars")
                confidence -= 0.1
            
            # Check for suspicious patterns
            for field, value in data.items():
                if isinstance(value, str):
                    for pattern in self.suspicious_patterns:
                        if pattern.lower() in value.lower():
                            issues.append(f"Suspicious pattern in {field}: {pattern}")
                            confidence -= 0.4
            
            # Timestamp validation
            if "created_at" in data:
                if not self._is_valid_timestamp(data["created_at"]):
                    issues.append("Invalid created_at timestamp")
                    confidence -= 0.3
            
            if "updated_at" in data:
                if not self._is_valid_timestamp(data["updated_at"]):
                    issues.append("Invalid updated_at timestamp")
                    confidence -= 0.3
            
            # URL validation
            if "html_url" in data:
                if not self._is_valid_github_url(data["html_url"]):
                    issues.append("Invalid GitHub URL format")
                    confidence -= 0.4
            
            return ValidationResult(
                is_valid=confidence > 0.5,
                confidence=max(0.0, confidence),
                issues=issues,
                metadata={"validation_level": self.validation_level.value},
                validation_level=self.validation_level
            )
    
    def validate_workflow_list(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """Validate a list of workflows."""
        with span("validation.workflow_list", count=len(data)):
            issues = []
            confidence = 1.0
            
            if not isinstance(data, list):
                issues.append("Data is not a list")
                confidence = 0.0
                return ValidationResult(
                    is_valid=False,
                    confidence=confidence,
                    issues=issues,
                    metadata={"validation_level": self.validation_level.value},
                    validation_level=self.validation_level
                )
            
            # Check for reasonable list size
            if len(data) > 1000:
                issues.append(f"Unreasonably large list: {len(data)} items")
                confidence -= 0.3
            
            # Validate each workflow
            for i, workflow in enumerate(data):
                result = self.validate_workflow(workflow)
                if not result.is_valid:
                    issues.append(f"Invalid workflow at index {i}: {', '.join(result.issues)}")
                    confidence -= 0.2
            
            return ValidationResult(
                is_valid=confidence > 0.5,
                confidence=max(0.0, confidence),
                issues=issues,
                metadata={"validation_level": self.validation_level.value, "count": len(data)},
                validation_level=self.validation_level
            )
    
    def validate_workflow(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate individual workflow data."""
        with span("validation.workflow"):
            issues = []
            confidence = 1.0
            
            pattern = self.known_patterns["workflow"]
            
            # Check required fields
            for field in pattern["required_fields"]:
                if field not in data:
                    issues.append(f"Missing required field: {field}")
                    confidence -= 0.2
            
            # Check state values
            if "state" in data and data["state"] not in pattern["state_values"]:
                issues.append(f"Invalid state value: {data['state']}")
                confidence -= 0.3
            
            # Check ID format
            if "id" in data and not str(data["id"]).isdigit():
                issues.append(f"Invalid ID format: {data['id']}")
                confidence -= 0.5
            
            # Check path format
            if "path" in data and not data["path"].startswith(".github/workflows/"):
                issues.append(f"Invalid workflow path: {data['path']}")
                confidence -= 0.4
            
            return ValidationResult(
                is_valid=confidence > 0.5,
                confidence=max(0.0, confidence),
                issues=issues,
                metadata={"validation_level": self.validation_level.value},
                validation_level=self.validation_level
            )
    
    def _is_valid_timestamp(self, timestamp: str) -> bool:
        """Validate GitHub API timestamp format."""
        try:
            import datetime
            # GitHub uses ISO 8601 format
            datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_valid_github_url(self, url: str) -> bool:
        """Validate GitHub URL format."""
        return url.startswith("https://github.com/") and "/actions/runs/" in url


class DataIntegrityValidator:
    """Validates data integrity and consistency."""
    
    def __init__(self):
        self.checksums = {}
    
    def validate_response_consistency(self, response_data: Dict[str, Any], 
                                    request_params: Dict[str, Any]) -> ValidationResult:
        """Validate that response data is consistent with request parameters."""
        with span("validation.response_consistency"):
            issues = []
            confidence = 1.0
            
            # Check owner/repo consistency
            if "owner" in request_params and "repository" in response_data:
                if not self._validate_owner_repo_consistency(request_params["owner"], response_data):
                    issues.append("Owner/repo mismatch in response")
                    confidence -= 0.5
            
            # Check pagination consistency
            if "per_page" in request_params and "workflow_runs" in response_data:
                per_page = request_params.get("per_page", 30)
                actual_count = len(response_data["workflow_runs"])
                if actual_count > per_page:
                    issues.append(f"Response contains more items than requested: {actual_count} > {per_page}")
                    confidence -= 0.3
            
            # Check data freshness
            if "workflow_runs" in response_data:
                for run in response_data["workflow_runs"]:
                    if "updated_at" in run:
                        if not self._is_recent_timestamp(run["updated_at"]):
                            issues.append("Stale data detected")
                            confidence -= 0.2
            
            return ValidationResult(
                is_valid=confidence > 0.5,
                confidence=max(0.0, confidence),
                issues=issues,
                metadata={"validation_level": "consistency"},
                validation_level=ValidationLevel.STRICT
            )
    
    def _validate_owner_repo_consistency(self, owner: str, response_data: Dict[str, Any]) -> bool:
        """Validate that response data belongs to the requested owner/repo."""
        # This would need to be implemented based on actual GitHub API response structure
        return True
    
    def _is_recent_timestamp(self, timestamp: str) -> bool:
        """Check if timestamp is reasonably recent (within last year)."""
        try:
            import datetime
            ts = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.datetime.now(datetime.timezone.utc)
            return (now - ts).days < 365
        except (ValueError, TypeError):
            return False


class CrossValidationChecker:
    """Performs cross-validation between different API endpoints."""
    
    def __init__(self):
        self.cache = {}
    
    def cross_validate_workflow_data(self, workflow_runs: List[Dict[str, Any]], 
                                   workflows: List[Dict[str, Any]]) -> ValidationResult:
        """Cross-validate workflow runs against workflow definitions."""
        with span("validation.cross_validate"):
            issues = []
            confidence = 1.0
            
            # Create workflow name mapping
            workflow_names = {w["name"] for w in workflows}
            
            # Check that all workflow runs reference valid workflows
            for run in workflow_runs:
                if "name" in run and run["name"] not in workflow_names:
                    issues.append(f"Workflow run references unknown workflow: {run['name']}")
                    confidence -= 0.3
            
            # Check for orphaned workflows (no recent runs)
            recent_workflow_names = {run["name"] for run in workflow_runs if "name" in run}
            orphaned_workflows = workflow_names - recent_workflow_names
            if len(orphaned_workflows) > len(workflow_names) * 0.8:
                issues.append("Too many orphaned workflows detected")
                confidence -= 0.2
            
            return ValidationResult(
                is_valid=confidence > 0.5,
                confidence=max(0.0, confidence),
                issues=issues,
                metadata={"validation_level": "cross_validation"},
                validation_level=ValidationLevel.STRICT
            )


class ValidationOrchestrator:
    """Orchestrates multiple validation strategies."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STRICT):
        self.hallucination_detector = HallucinationDetector(validation_level)
        self.integrity_validator = DataIntegrityValidator()
        self.cross_validator = CrossValidationChecker()
        self.validation_level = validation_level
    
    def validate_github_actions_response(self, response_data: Any, 
                                       request_params: Dict[str, Any],
                                       response_type: str) -> ValidationResult:
        """Comprehensive validation of GitHub Actions API response."""
        with span("validation.orchestrator", response_type=response_type):
            all_issues = []
            total_confidence = 0.0
            validation_count = 0
            
            # Basic hallucination detection
            if response_type == "workflow_runs" and isinstance(response_data, dict):
                if "workflow_runs" in response_data:
                    for run in response_data["workflow_runs"]:
                        result = self.hallucination_detector.validate_workflow_run(run)
                        all_issues.extend(result.issues)
                        total_confidence += result.confidence
                        validation_count += 1
            
            elif response_type == "workflows" and isinstance(response_data, list):
                result = self.hallucination_detector.validate_workflow_list(response_data)
                all_issues.extend(result.issues)
                total_confidence += result.confidence
                validation_count += 1
            
            # Data integrity validation
            if isinstance(response_data, dict):
                result = self.integrity_validator.validate_response_consistency(response_data, request_params)
                all_issues.extend(result.issues)
                total_confidence += result.confidence
                validation_count += 1
            
            # Calculate average confidence
            avg_confidence = total_confidence / max(validation_count, 1)
            
            # Log validation results
            if all_issues:
                logger.warning(f"Validation issues detected: {all_issues}")
                record_exception(Exception(f"Validation failed: {all_issues}"), 
                               attributes={"validation_issues": all_issues})
            
            return ValidationResult(
                is_valid=avg_confidence > 0.7,
                confidence=avg_confidence,
                issues=all_issues,
                metadata={
                    "validation_level": self.validation_level.value,
                    "validation_count": validation_count,
                    "response_type": response_type
                },
                validation_level=self.validation_level
            ) 