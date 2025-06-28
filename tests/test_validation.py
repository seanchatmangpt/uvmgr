"""
Tests for the multi-layered validation system.
"""

import pytest
from datetime import datetime, timezone
from uvmgr.core.validation import (
    ValidationOrchestrator, 
    ValidationLevel, 
    ValidationResult,
    HallucinationDetector,
    DataIntegrityValidator,
    CrossValidationChecker
)


class TestHallucinationDetector:
    """Test hallucination detection capabilities."""
    
    def setup_method(self):
        self.detector = HallucinationDetector(ValidationLevel.STRICT)
    
    def test_valid_workflow_run(self):
        """Test validation of a valid workflow run."""
        valid_run = {
            "id": 123456789,
            "name": "CI/CD Pipeline",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:35:00Z",
            "html_url": "https://github.com/owner/repo/actions/runs/123456789"
        }
        
        result = self.detector.validate_workflow_run(valid_run)
        assert result.is_valid
        assert result.confidence > 0.9
        assert len(result.issues) == 0
    
    def test_invalid_workflow_run_missing_fields(self):
        """Test validation of workflow run with missing required fields."""
        invalid_run = {
            "id": 123456789,
            "name": "CI/CD Pipeline"
            # Missing required fields
        }
        
        result = self.detector.validate_workflow_run(invalid_run)
        assert not result.is_valid
        assert result.confidence < 0.8
        assert len(result.issues) > 0
        assert any("Missing required field" in issue for issue in result.issues)
    
    def test_invalid_workflow_run_suspicious_patterns(self):
        """Test detection of suspicious patterns."""
        suspicious_run = {
            "id": 123456789,
            "name": "lorem ipsum test pipeline",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:35:00Z"
        }
        
        result = self.detector.validate_workflow_run(suspicious_run)
        assert not result.is_valid
        assert result.confidence < 0.7
        assert any("Suspicious pattern" in issue for issue in result.issues)
    
    def test_invalid_workflow_run_bad_status(self):
        """Test validation with invalid status values."""
        invalid_run = {
            "id": 123456789,
            "name": "CI/CD Pipeline",
            "status": "invalid_status",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:35:00Z"
        }
        
        result = self.detector.validate_workflow_run(invalid_run)
        assert not result.is_valid
        assert any("Invalid status value" in issue for issue in result.issues)
    
    def test_invalid_workflow_run_bad_id(self):
        """Test validation with non-numeric ID."""
        invalid_run = {
            "id": "not_a_number",
            "name": "CI/CD Pipeline",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:35:00Z"
        }
        
        result = self.detector.validate_workflow_run(invalid_run)
        assert not result.is_valid
        assert any("Invalid ID format" in issue for issue in result.issues)
    
    def test_invalid_timestamp(self):
        """Test validation of invalid timestamps."""
        invalid_run = {
            "id": 123456789,
            "name": "CI/CD Pipeline",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": "invalid_timestamp",
            "updated_at": "2024-01-15T10:35:00Z"
        }
        
        result = self.detector.validate_workflow_run(invalid_run)
        assert not result.is_valid
        assert any("Invalid created_at timestamp" in issue for issue in result.issues)
    
    def test_workflow_list_validation(self):
        """Test validation of workflow list."""
        valid_workflows = [
            {
                "id": 123,
                "name": "CI Pipeline",
                "state": "active",
                "path": ".github/workflows/ci.yml"
            },
            {
                "id": 124,
                "name": "Deploy Pipeline",
                "state": "active",
                "path": ".github/workflows/deploy.yml"
            }
        ]
        
        result = self.detector.validate_workflow_list(valid_workflows)
        assert result.is_valid
        assert result.confidence > 0.9
    
    def test_workflow_list_too_large(self):
        """Test validation of unreasonably large workflow list."""
        large_list = [{"id": i, "name": f"Workflow {i}", "state": "active", "path": ".github/workflows/test.yml"} 
                     for i in range(1500)]
        
        result = self.detector.validate_workflow_list(large_list)
        assert not result.is_valid
        assert any("Unreasonably large list" in issue for issue in result.issues)


class TestDataIntegrityValidator:
    """Test data integrity validation."""
    
    def setup_method(self):
        self.validator = DataIntegrityValidator()
    
    def test_response_consistency(self):
        """Test response consistency validation."""
        request_params = {"owner": "test-owner", "per_page": 30}
        response_data = {
            "workflow_runs": [
                {
                    "id": 123,
                    "name": "CI Pipeline",
                    "status": "completed",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        result = self.validator.validate_response_consistency(response_data, request_params)
        assert result.is_valid
        assert result.confidence > 0.8
    
    def test_response_consistency_too_many_items(self):
        """Test validation when response contains more items than requested."""
        request_params = {"per_page": 5}
        response_data = {
            "workflow_runs": [
                {"id": i, "name": f"Pipeline {i}", "status": "completed"} 
                for i in range(10)
            ]
        }
        
        result = self.validator.validate_response_consistency(response_data, request_params)
        assert not result.is_valid
        assert any("more items than requested" in issue for issue in result.issues)
    
    def test_stale_data_detection(self):
        """Test detection of stale data."""
        request_params = {"owner": "test-owner"}
        response_data = {
            "workflow_runs": [
                {
                    "id": 123,
                    "name": "CI Pipeline",
                    "status": "completed",
                    "updated_at": "2020-01-15T10:30:00Z"  # Very old
                }
            ]
        }
        
        result = self.validator.validate_response_consistency(response_data, request_params)
        assert not result.is_valid
        assert any("Stale data" in issue for issue in result.issues)


class TestCrossValidationChecker:
    """Test cross-validation capabilities."""
    
    def setup_method(self):
        self.checker = CrossValidationChecker()
    
    def test_cross_validate_workflow_data(self):
        """Test cross-validation between workflows and workflow runs."""
        workflows = [
            {"id": 123, "name": "CI Pipeline", "state": "active", "path": ".github/workflows/ci.yml"},
            {"id": 124, "name": "Deploy Pipeline", "state": "active", "path": ".github/workflows/deploy.yml"}
        ]
        
        workflow_runs = [
            {"id": 456, "name": "CI Pipeline", "status": "completed"},
            {"id": 457, "name": "Deploy Pipeline", "status": "completed"}
        ]
        
        result = self.checker.cross_validate_workflow_data(workflow_runs, workflows)
        assert result.is_valid
        assert result.confidence > 0.9
    
    def test_cross_validate_unknown_workflow(self):
        """Test cross-validation with unknown workflow reference."""
        workflows = [
            {"id": 123, "name": "CI Pipeline", "state": "active", "path": ".github/workflows/ci.yml"}
        ]
        
        workflow_runs = [
            {"id": 456, "name": "CI Pipeline", "status": "completed"},
            {"id": 457, "name": "Unknown Pipeline", "status": "completed"}  # Unknown workflow
        ]
        
        result = self.checker.cross_validate_workflow_data(workflow_runs, workflows)
        assert not result.is_valid
        assert any("unknown workflow" in issue for issue in result.issues)
    
    def test_cross_validate_too_many_orphaned_workflows(self):
        """Test cross-validation with too many orphaned workflows."""
        workflows = [
            {"id": i, "name": f"Workflow {i}", "state": "active", "path": ".github/workflows/test.yml"}
            for i in range(100)
        ]
        
        workflow_runs = [
            {"id": 456, "name": "Workflow 1", "status": "completed"}  # Only one workflow has runs
        ]
        
        result = self.checker.cross_validate_workflow_data(workflow_runs, workflows)
        assert not result.is_valid
        assert any("orphaned workflows" in issue for issue in result.issues)


class TestValidationOrchestrator:
    """Test the main validation orchestrator."""
    
    def setup_method(self):
        self.orchestrator = ValidationOrchestrator(ValidationLevel.STRICT)
    
    def test_validate_github_actions_response_workflow_runs(self):
        """Test validation of workflow runs response."""
        response_data = {
            "workflow_runs": [
                {
                    "id": 123456789,
                    "name": "CI/CD Pipeline",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "head_branch": "main",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:35:00Z"
                }
            ]
        }
        
        request_params = {"endpoint": "actions/runs", "method": "GET"}
        
        result = self.orchestrator.validate_github_actions_response(
            response_data, request_params, "workflow_runs"
        )
        assert result.is_valid
        assert result.confidence > 0.8
        assert result.metadata["response_type"] == "workflow_runs"
    
    def test_validate_github_actions_response_workflows(self):
        """Test validation of workflows response."""
        response_data = [
            {
                "id": 123,
                "name": "CI Pipeline",
                "state": "active",
                "path": ".github/workflows/ci.yml"
            }
        ]
        
        request_params = {"endpoint": "actions/workflows", "method": "GET"}
        
        result = self.orchestrator.validate_github_actions_response(
            response_data, request_params, "workflows"
        )
        assert result.is_valid
        assert result.confidence > 0.8
        assert result.metadata["response_type"] == "workflows"
    
    def test_validate_github_actions_response_invalid_data(self):
        """Test validation of invalid response data."""
        response_data = {
            "workflow_runs": [
                {
                    "id": "not_a_number",
                    "name": "lorem ipsum pipeline",
                    "status": "invalid_status",
                    "created_at": "invalid_timestamp"
                }
            ]
        }
        
        request_params = {"endpoint": "actions/runs", "method": "GET"}
        
        result = self.orchestrator.validate_github_actions_response(
            response_data, request_params, "workflow_runs"
        )
        assert not result.is_valid
        assert result.confidence < 0.5
        assert len(result.issues) > 0


class TestValidationLevels:
    """Test different validation levels."""
    
    def test_basic_validation_level(self):
        """Test basic validation level."""
        detector = HallucinationDetector(ValidationLevel.BASIC)
        
        # Basic level should be more permissive
        minimal_run = {"id": 123, "name": "Test"}
        result = detector.validate_workflow_run(minimal_run)
        assert result.validation_level == ValidationLevel.BASIC
    
    def test_strict_validation_level(self):
        """Test strict validation level."""
        detector = HallucinationDetector(ValidationLevel.STRICT)
        
        # Strict level should catch more issues
        suspicious_run = {
            "id": 123,
            "name": "lorem ipsum test",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": "2024-01-15T10:30:00Z"
        }
        
        result = detector.validate_workflow_run(suspicious_run)
        assert result.validation_level == ValidationLevel.STRICT
        assert not result.is_valid
    
    def test_paranoid_validation_level(self):
        """Test paranoid validation level."""
        detector = HallucinationDetector(ValidationLevel.PARANOID)
        
        # Paranoid level should be very strict
        valid_run = {
            "id": 123456789,
            "name": "CI/CD Pipeline",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:35:00Z",
            "html_url": "https://github.com/owner/repo/actions/runs/123456789"
        }
        
        result = detector.validate_workflow_run(valid_run)
        assert result.validation_level == ValidationLevel.PARANOID
        # Paranoid level might flag even valid data as suspicious
        assert result.confidence < 1.0


class TestValidationResult:
    """Test validation result data structure."""
    
    def test_validation_result_creation(self):
        """Test creating validation results."""
        result = ValidationResult(
            is_valid=True,
            confidence=0.95,
            issues=["Minor formatting issue"],
            metadata={"test": "data"},
            validation_level=ValidationLevel.STRICT
        )
        
        assert result.is_valid
        assert result.confidence == 0.95
        assert len(result.issues) == 1
        assert result.metadata["test"] == "data"
        assert result.validation_level == ValidationLevel.STRICT
    
    def test_validation_result_confidence_bounds(self):
        """Test confidence bounds enforcement."""
        result = ValidationResult(
            is_valid=False,
            confidence=1.5,  # Should be clamped to 1.0
            issues=[],
            metadata={},
            validation_level=ValidationLevel.STRICT
        )
        
        assert result.confidence == 1.0
        
        result = ValidationResult(
            is_valid=False,
            confidence=-0.5,  # Should be clamped to 0.0
            issues=[],
            metadata={},
            validation_level=ValidationLevel.STRICT
        )
        
        assert result.confidence == 0.0 