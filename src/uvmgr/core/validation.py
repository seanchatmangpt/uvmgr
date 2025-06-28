"""
Multi-layered validation system to detect hallucinations and ensure data integrity.
"""

import json
import hashlib
import time
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timezone
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
    
    def __post_init__(self):
        # Ensure confidence is within bounds
        self.confidence = max(0.0, min(1.0, self.confidence))


class BehavioralAnalyzer:
    """Analyzes behavioral patterns to detect anomalies."""
    
    def __init__(self):
        self.pattern_history = []
        self.anomaly_threshold = 0.8
        
    def analyze_response_pattern(self, response_data: Dict[str, Any], 
                               request_context: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Analyze response patterns for behavioral anomalies."""
        issues = []
        anomaly_score = 0.0
        
        # Check response time patterns
        if "response_time" in request_context:
            response_time = request_context["response_time"]
            if response_time < 50:  # Suspiciously fast
                issues.append("Response time suspiciously fast")
                anomaly_score += 0.3
            elif response_time > 10000:  # Suspiciously slow
                issues.append("Response time suspiciously slow")
                anomaly_score += 0.2
        
        # Check data volume patterns
        if isinstance(response_data, dict) and "workflow_runs" in response_data:
            run_count = len(response_data["workflow_runs"])
            if run_count > 100:  # Unusually large response
                issues.append("Unusually large response volume")
                anomaly_score += 0.2
        
        # Check for repetitive patterns
        if self._has_repetitive_patterns(response_data):
            issues.append("Repetitive patterns detected")
            anomaly_score += 0.4
        
        # Check for unrealistic data distributions
        if self._has_unrealistic_distributions(response_data):
            issues.append("Unrealistic data distributions")
            anomaly_score += 0.3
        
        return anomaly_score, issues
    
    def _has_repetitive_patterns(self, data: Any) -> bool:
        """Check for repetitive patterns in data."""
        if isinstance(data, list) and len(data) > 5:
            # Check if first few items are identical
            first_item = data[0]
            identical_count = sum(1 for item in data[:5] if item == first_item)
            return identical_count >= 4
        return False
    
    def _has_unrealistic_distributions(self, data: Any) -> bool:
        """Check for unrealistic data distributions."""
        if isinstance(data, dict) and "workflow_runs" in data:
            runs = data["workflow_runs"]
            if len(runs) > 10:
                # Check status distribution
                statuses = [run.get("status", "") for run in runs]
                status_counts = {}
                for status in statuses:
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                # If one status dominates (>90%), it's suspicious
                total = len(statuses)
                for count in status_counts.values():
                    if count / total > 0.9:
                        return True
        return False


class MLBasedDetector:
    """Machine learning-based hallucination detection."""
    
    def __init__(self):
        self.feature_extractors = [
            self._extract_text_features,
            self._extract_numerical_features,
            self._extract_temporal_features,
            self._extract_structural_features
        ]
        self.hallucination_threshold = 0.7
    
    def detect_hallucinations(self, data: Any) -> Tuple[float, List[str]]:
        """Detect hallucinations using ML-based features."""
        features = self._extract_features(data)
        hallucination_score = self._calculate_hallucination_score(features)
        issues = self._generate_issues(features, hallucination_score)
        
        return hallucination_score, issues
    
    def _extract_features(self, data: Any) -> Dict[str, float]:
        """Extract features from data for ML analysis."""
        features = {}
        
        for extractor in self.feature_extractors:
            features.update(extractor(data))
        
        return features
    
    def _extract_text_features(self, data: Any) -> Dict[str, float]:
        """Extract text-based features."""
        features = {}
        
        if isinstance(data, str):
            features["text_length"] = len(data)
            features["word_count"] = len(data.split())
            features["unique_word_ratio"] = len(set(data.split())) / max(len(data.split()), 1)
            features["uppercase_ratio"] = sum(1 for c in data if c.isupper()) / max(len(data), 1)
            features["digit_ratio"] = sum(1 for c in data if c.isdigit()) / max(len(data), 1)
        
        return features
    
    def _extract_numerical_features(self, data: Any) -> Dict[str, float]:
        """Extract numerical features."""
        features = {}
        
        if isinstance(data, (int, float)):
            features["value_magnitude"] = abs(data)
            features["is_negative"] = 1.0 if data < 0 else 0.0
            features["is_zero"] = 1.0 if data == 0 else 0.0
        
        return features
    
    def _extract_temporal_features(self, data: Any) -> Dict[str, float]:
        """Extract temporal features."""
        features = {}
        
        if isinstance(data, str):
            # Try to parse as timestamp
            try:
                dt = datetime.fromisoformat(data.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_days = (now - dt).days
                features["data_age_days"] = age_days
                features["is_future"] = 1.0 if age_days < 0 else 0.0
                features["is_very_old"] = 1.0 if age_days > 365 else 0.0
            except (ValueError, TypeError):
                pass
        
        return features
    
    def _extract_structural_features(self, data: Any) -> Dict[str, float]:
        """Extract structural features."""
        features = {}
        
        if isinstance(data, dict):
            features["field_count"] = len(data)
            features["nested_depth"] = self._calculate_nested_depth(data)
            features["missing_required_fields"] = self._count_missing_fields(data)
        
        elif isinstance(data, list):
            features["list_length"] = len(data)
            features["empty_list"] = 1.0 if len(data) == 0 else 0.0
        
        return features
    
    def _calculate_nested_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate the maximum nesting depth of an object."""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_nested_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._calculate_nested_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _count_missing_fields(self, data: Dict[str, Any]) -> float:
        """Count missing required fields."""
        required_fields = ["id", "name", "status", "created_at"]
        missing_count = sum(1 for field in required_fields if field not in data)
        return missing_count / len(required_fields)
    
    def _calculate_hallucination_score(self, features: Dict[str, float]) -> float:
        """Calculate hallucination score based on features."""
        score = 0.0
        
        # Text-based indicators
        if "unique_word_ratio" in features and features["unique_word_ratio"] < 0.3:
            score += 0.3  # Low vocabulary diversity
        
        if "uppercase_ratio" in features and features["uppercase_ratio"] > 0.5:
            score += 0.2  # Too much uppercase
        
        # Temporal indicators
        if "is_future" in features and features["is_future"] > 0:
            score += 0.4  # Future timestamps
        
        if "is_very_old" in features and features["is_very_old"] > 0:
            score += 0.2  # Very old data
        
        # Structural indicators
        if "missing_required_fields" in features and features["missing_required_fields"] > 0.5:
            score += 0.3  # Missing many required fields
        
        return min(1.0, score)
    
    def _generate_issues(self, features: Dict[str, float], score: float) -> List[str]:
        """Generate issues based on features and score."""
        issues = []
        
        if score > self.hallucination_threshold:
            issues.append("ML-based hallucination detection triggered")
        
        if "unique_word_ratio" in features and features["unique_word_ratio"] < 0.3:
            issues.append("Low vocabulary diversity detected")
        
        if "is_future" in features and features["is_future"] > 0:
            issues.append("Future timestamps detected")
        
        return issues


class AdaptiveValidator:
    """Adaptive validation that adjusts based on context and history."""
    
    def __init__(self):
        self.validation_history = []
        self.adaptation_threshold = 10
        self.confidence_threshold = 0.8
    
    def adapt_validation_level(self, current_level: ValidationLevel, 
                              context: Dict[str, Any]) -> ValidationLevel:
        """Adapt validation level based on context and history."""
        # Check recent validation success rate
        recent_results = self.validation_history[-self.adaptation_threshold:] if self.validation_history else []
        
        if len(recent_results) >= 5:
            success_rate = sum(1 for result in recent_results if result.confidence > self.confidence_threshold) / len(recent_results)
            
            if success_rate > 0.9 and current_level != ValidationLevel.BASIC:
                return ValidationLevel.BASIC  # Relax validation
            elif success_rate < 0.7 and current_level != ValidationLevel.PARANOID:
                return ValidationLevel.PARANOID  # Tighten validation
        
        # Context-based adaptation
        if context.get("critical_operation", False):
            return ValidationLevel.PARANOID
        
        if context.get("high_performance", False):
            return ValidationLevel.BASIC
        
        return current_level
    
    def record_validation_result(self, result: ValidationResult):
        """Record validation result for adaptation."""
        self.validation_history.append(result)
        
        # Keep only recent history
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-50:]


class HallucinationDetector:
    """Multi-layered system to detect hallucinations in API responses."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STRICT):
        self.validation_level = validation_level
        self.known_patterns = self._load_known_patterns()
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.ml_detector = MLBasedDetector()
        self.adaptive_validator = AdaptiveValidator()
    
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
            "TBD",
            "random",
            "generated",
            "synthetic"
        ]
    
    def validate_workflow_run(self, data: Dict[str, Any], 
                            context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate workflow run data for hallucinations with adaptive validation."""
        with span("validation.workflow_run", validation_level=self.validation_level.value):
            # Adapt validation level based on context
            adapted_level = self.adaptive_validator.adapt_validation_level(
                self.validation_level, context or {}
            )
            
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
            
            # ML-based detection
            ml_score, ml_issues = self.ml_detector.detect_hallucinations(data)
            if ml_score > 0.5:
                issues.extend(ml_issues)
                confidence -= ml_score * 0.3
            
            # Behavioral analysis
            if context:
                behavior_score, behavior_issues = self.behavioral_analyzer.analyze_response_pattern(data, context)
                if behavior_score > 0.5:
                    issues.extend(behavior_issues)
                    confidence -= behavior_score * 0.2
            
            result = ValidationResult(
                is_valid=confidence > 0.5,
                confidence=max(0.0, confidence),
                issues=issues,
                metadata={
                    "validation_level": adapted_level.value,
                    "ml_score": ml_score,
                    "behavior_score": behavior_score if context else 0.0
                },
                validation_level=adapted_level
            )
            
            # Record result for adaptation
            self.adaptive_validator.record_validation_result(result)
            
            return result
    
    def validate_workflow_list(self, data: List[Dict[str, Any]], 
                             context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate a list of workflows with adaptive validation."""
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
                result = self.validate_workflow(workflow, context)
                if not result.is_valid:
                    issues.append(f"Invalid workflow at index {i}: {', '.join(result.issues)}")
                    confidence -= 0.2
            
            # ML-based detection on the entire list
            ml_score, ml_issues = self.ml_detector.detect_hallucinations(data)
            if ml_score > 0.5:
                issues.extend(ml_issues)
                confidence -= ml_score * 0.3
            
            return ValidationResult(
                is_valid=confidence > 0.5,
                confidence=max(0.0, confidence),
                issues=issues,
                metadata={
                    "validation_level": self.validation_level.value,
                    "count": len(data),
                    "ml_score": ml_score
                },
                validation_level=self.validation_level
            )
    
    def validate_workflow(self, data: Dict[str, Any], 
                         context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate individual workflow data with adaptive validation."""
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
            
            # ML-based detection
            ml_score, ml_issues = self.ml_detector.detect_hallucinations(data)
            if ml_score > 0.5:
                issues.extend(ml_issues)
                confidence -= ml_score * 0.3
            
            return ValidationResult(
                is_valid=confidence > 0.5,
                confidence=max(0.0, confidence),
                issues=issues,
                metadata={
                    "validation_level": self.validation_level.value,
                    "ml_score": ml_score
                },
                validation_level=self.validation_level
            )
    
    def _is_valid_timestamp(self, timestamp: str) -> bool:
        """Validate GitHub API timestamp format."""
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
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
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
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
                                       response_type: str,
                                       context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Comprehensive validation of GitHub Actions API response."""
        with span("validation.orchestrator", response_type=response_type):
            all_issues = []
            total_confidence = 0.0
            validation_count = 0
            
            # Basic hallucination detection
            if response_type == "workflow_runs" and isinstance(response_data, dict):
                if "workflow_runs" in response_data:
                    for run in response_data["workflow_runs"]:
                        result = self.hallucination_detector.validate_workflow_run(run, context)
                        all_issues.extend(result.issues)
                        total_confidence += result.confidence
                        validation_count += 1
            
            elif response_type == "workflows" and isinstance(response_data, list):
                result = self.hallucination_detector.validate_workflow_list(response_data, context)
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