"""
Advanced tests for the multi-layered validation system.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uvmgr.core.validation import (
    ValidationOrchestrator, 
    ValidationLevel, 
    ValidationResult,
    HallucinationDetector,
    BehavioralAnalyzer,
    MLBasedDetector,
    AdaptiveValidator
)


class TestBehavioralAnalyzer:
    """Test behavioral analysis capabilities."""
    
    def setup_method(self):
        self.analyzer = BehavioralAnalyzer()
    
    def test_suspiciously_fast_response(self):
        """Test detection of suspiciously fast responses."""
        response_data = {"workflow_runs": [{"id": 1, "name": "test"}]}
        context = {"response_time": 25}  # Very fast
        
        score, issues = self.analyzer.analyze_response_pattern(response_data, context)
        
        assert score > 0.2
        assert any("suspiciously fast" in issue for issue in issues)
    
    def test_suspiciously_slow_response(self):
        """Test detection of suspiciously slow responses."""
        response_data = {"workflow_runs": [{"id": 1, "name": "test"}]}
        context = {"response_time": 15000}  # Very slow
        
        score, issues = self.analyzer.analyze_response_pattern(response_data, context)
        
        assert score > 0.1
        assert any("suspiciously slow" in issue for issue in issues)
    
    def test_large_response_volume(self):
        """Test detection of unusually large response volumes."""
        response_data = {
            "workflow_runs": [{"id": i, "name": f"test_{i}"} for i in range(150)]
        }
        context = {}
        
        score, issues = self.analyzer.analyze_response_pattern(response_data, context)
        
        assert score > 0.1
        assert any("large response volume" in issue for issue in issues)
    
    def test_repetitive_patterns(self):
        """Test detection of repetitive patterns."""
        response_data = [
            {"id": 1, "name": "test", "status": "completed"},
            {"id": 1, "name": "test", "status": "completed"},
            {"id": 1, "name": "test", "status": "completed"},
            {"id": 1, "name": "test", "status": "completed"},
            {"id": 1, "name": "test", "status": "completed"}
        ]
        context = {}
        
        score, issues = self.analyzer.analyze_response_pattern(response_data, context)
        
        assert score > 0.3
        assert any("Repetitive patterns" in issue for issue in issues)
    
    def test_unrealistic_distributions(self):
        """Test detection of unrealistic data distributions."""
        response_data = {
            "workflow_runs": [
                {"id": i, "name": f"test_{i}", "status": "completed"} 
                for i in range(20)
            ]
        }
        context = {}
        
        score, issues = self.analyzer.analyze_response_pattern(response_data, context)
        
        assert score > 0.2
        assert any("unrealistic distributions" in issue for issue in issues)
    
    def test_normal_response_pattern(self):
        """Test that normal response patterns don't trigger alerts."""
        response_data = {
            "workflow_runs": [
                {"id": 1, "name": "test1", "status": "completed"},
                {"id": 2, "name": "test2", "status": "in_progress"},
                {"id": 3, "name": "test3", "status": "queued"}
            ]
        }
        context = {"response_time": 500}  # Normal response time
        
        score, issues = self.analyzer.analyze_response_pattern(response_data, context)
        
        assert score < 0.3
        assert len(issues) == 0


class TestMLBasedDetector:
    """Test machine learning-based detection capabilities."""
    
    def setup_method(self):
        self.detector = MLBasedDetector()
    
    def test_text_feature_extraction(self):
        """Test text feature extraction."""
        text_data = "This is a test workflow with some UPPERCASE and 123 numbers"
        
        features = self.detector._extract_text_features(text_data)
        
        assert "text_length" in features
        assert "word_count" in features
        assert "unique_word_ratio" in features
        assert "uppercase_ratio" in features
        assert "digit_ratio" in features
        
        assert features["text_length"] == len(text_data)
        assert features["word_count"] == 10
        assert features["uppercase_ratio"] > 0
        assert features["digit_ratio"] > 0
    
    def test_numerical_feature_extraction(self):
        """Test numerical feature extraction."""
        number_data = -42
        
        features = self.detector._extract_numerical_features(number_data)
        
        assert "value_magnitude" in features
        assert "is_negative" in features
        assert "is_zero" in features
        
        assert features["value_magnitude"] == 42
        assert features["is_negative"] == 1.0
        assert features["is_zero"] == 0.0
    
    def test_temporal_feature_extraction(self):
        """Test temporal feature extraction."""
        # Future timestamp
        future_timestamp = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        features = self.detector._extract_temporal_features(future_timestamp)
        
        assert "is_future" in features
        assert features["is_future"] == 1.0
        
        # Past timestamp
        past_timestamp = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        features = self.detector._extract_temporal_features(past_timestamp)
        
        assert "is_future" in features
        assert features["is_future"] == 0.0
    
    def test_structural_feature_extraction(self):
        """Test structural feature extraction."""
        dict_data = {
            "id": 1,
            "name": "test",
            "nested": {"level1": {"level2": "value"}}
        }
        
        features = self.detector._extract_structural_features(dict_data)
        
        assert "field_count" in features
        assert "nested_depth" in features
        assert "missing_required_fields" in features
        
        assert features["field_count"] == 3
        assert features["nested_depth"] == 3
        assert features["missing_required_fields"] > 0  # Missing some required fields
    
    def test_hallucination_detection_low_vocabulary(self):
        """Test detection of low vocabulary diversity."""
        low_vocab_data = "test test test test test test test test test test"
        
        score, issues = self.detector.detect_hallucinations(low_vocab_data)
        
        assert score > 0.2
        assert any("Low vocabulary diversity" in issue for issue in issues)
    
    def test_hallucination_detection_future_timestamp(self):
        """Test detection of future timestamps."""
        future_data = {
            "id": 1,
            "name": "test",
            "created_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        
        score, issues = self.detector.detect_hallucinations(future_data)
        
        assert score > 0.3
        assert any("Future timestamps" in issue for issue in issues)
    
    def test_hallucination_detection_missing_fields(self):
        """Test detection of missing required fields."""
        incomplete_data = {"id": 1}  # Missing name, status, created_at
        
        score, issues = self.detector.detect_hallucinations(incomplete_data)
        
        assert score > 0.2
        assert any("ML-based hallucination detection" in issue for issue in issues)
    
    def test_normal_data_detection(self):
        """Test that normal data doesn't trigger hallucination detection."""
        normal_data = {
            "id": 123456789,
            "name": "CI/CD Pipeline",
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        score, issues = self.detector.detect_hallucinations(normal_data)
        
        assert score < 0.5
        assert len(issues) == 0


class TestAdaptiveValidator:
    """Test adaptive validation capabilities."""
    
    def setup_method(self):
        self.validator = AdaptiveValidator()
    
    def test_adaptation_to_high_success_rate(self):
        """Test adaptation to high success rate."""
        # Create history with high success rate
        for i in range(10):
            result = ValidationResult(
                is_valid=True,
                confidence=0.95,
                issues=[],
                metadata={},
                validation_level=ValidationLevel.STRICT
            )
            self.validator.record_validation_result(result)
        
        adapted_level = self.validator.adapt_validation_level(
            ValidationLevel.STRICT, {}
        )
        
        assert adapted_level == ValidationLevel.BASIC
    
    def test_adaptation_to_low_success_rate(self):
        """Test adaptation to low success rate."""
        # Create history with low success rate
        for i in range(10):
            result = ValidationResult(
                is_valid=False,
                confidence=0.3,
                issues=["test issue"],
                metadata={},
                validation_level=ValidationLevel.STRICT
            )
            self.validator.record_validation_result(result)
        
        adapted_level = self.validator.adapt_validation_level(
            ValidationLevel.STRICT, {}
        )
        
        assert adapted_level == ValidationLevel.PARANOID
    
    def test_critical_operation_adaptation(self):
        """Test adaptation for critical operations."""
        context = {"critical_operation": True}
        
        adapted_level = self.validator.adapt_validation_level(
            ValidationLevel.STRICT, context
        )
        
        assert adapted_level == ValidationLevel.PARANOID
    
    def test_high_performance_adaptation(self):
        """Test adaptation for high performance requirements."""
        context = {"high_performance": True}
        
        adapted_level = self.validator.adapt_validation_level(
            ValidationLevel.STRICT, context
        )
        
        assert adapted_level == ValidationLevel.BASIC
    
    def test_no_adaptation_for_insufficient_history(self):
        """Test that adaptation doesn't occur with insufficient history."""
        # Only 3 results, not enough for adaptation
        for i in range(3):
            result = ValidationResult(
                is_valid=True,
                confidence=0.95,
                issues=[],
                metadata={},
                validation_level=ValidationLevel.STRICT
            )
            self.validator.record_validation_result(result)
        
        adapted_level = self.validator.adapt_validation_level(
            ValidationLevel.STRICT, {}
        )
        
        assert adapted_level == ValidationLevel.STRICT  # No change
    
    def test_history_limiting(self):
        """Test that history is limited to prevent memory issues."""
        # Add more than 100 results
        for i in range(150):
            result = ValidationResult(
                is_valid=True,
                confidence=0.95,
                issues=[],
                metadata={},
                validation_level=ValidationLevel.STRICT
            )
            self.validator.record_validation_result(result)
        
        # Should only keep recent 50 results
        assert len(self.validator.validation_history) <= 50


class TestAdvancedHallucinationDetector:
    """Test advanced hallucination detection with ML and behavioral analysis."""
    
    def setup_method(self):
        self.detector = HallucinationDetector(ValidationLevel.STRICT)
    
    def test_ml_based_detection_integration(self):
        """Test integration of ML-based detection."""
        suspicious_data = {
            "id": "not_a_number",
            "name": "lorem ipsum test pipeline",
            "status": "completed",
            "created_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        
        result = self.detector.validate_workflow_run(suspicious_data)
        
        assert not result.is_valid
        assert result.confidence < 0.5
        assert "ml_score" in result.metadata
        assert result.metadata["ml_score"] > 0.3
    
    def test_behavioral_analysis_integration(self):
        """Test integration of behavioral analysis."""
        normal_data = {
            "id": 123456789,
            "name": "CI/CD Pipeline",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        context = {"response_time": 25}  # Suspiciously fast
        
        result = self.detector.validate_workflow_run(normal_data, context)
        
        assert not result.is_valid
        assert "behavior_score" in result.metadata
        assert result.metadata["behavior_score"] > 0.2
    
    def test_adaptive_validation_integration(self):
        """Test integration of adaptive validation."""
        # Create history for adaptation
        for i in range(10):
            result = ValidationResult(
                is_valid=True,
                confidence=0.95,
                issues=[],
                metadata={},
                validation_level=ValidationLevel.STRICT
            )
            self.detector.adaptive_validator.record_validation_result(result)
        
        normal_data = {
            "id": 123456789,
            "name": "CI/CD Pipeline",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "main",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = self.detector.validate_workflow_run(normal_data)
        
        # Should adapt to BASIC level due to high success rate
        assert result.validation_level == ValidationLevel.BASIC
    
    def test_comprehensive_validation_scenario(self):
        """Test comprehensive validation with all features."""
        # Suspicious data with multiple issues
        suspicious_data = {
            "id": "not_a_number",
            "name": "lorem ipsum test pipeline with UPPERCASE and 123 numbers",
            "status": "invalid_status",
            "created_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        
        context = {
            "response_time": 25,  # Suspiciously fast
            "critical_operation": True
        }
        
        result = self.detector.validate_workflow_run(suspicious_data, context)
        
        assert not result.is_valid
        assert result.confidence < 0.3
        assert len(result.issues) > 5  # Multiple issues detected
        assert "ml_score" in result.metadata
        assert "behavior_score" in result.metadata
        assert result.validation_level == ValidationLevel.PARANOID  # Critical operation


class TestValidationOrchestratorAdvanced:
    """Test advanced validation orchestrator features."""
    
    def setup_method(self):
        self.orchestrator = ValidationOrchestrator(ValidationLevel.STRICT)
    
    def test_context_aware_validation(self):
        """Test context-aware validation."""
        response_data = {
            "workflow_runs": [
                {
                    "id": 123456789,
                    "name": "CI/CD Pipeline",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "head_branch": "main",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        request_params = {"endpoint": "actions/runs", "method": "GET"}
        context = {"critical_operation": True}
        
        result = self.orchestrator.validate_github_actions_response(
            response_data, request_params, "workflow_runs", context
        )
        
        assert result.is_valid
        assert result.metadata["validation_level"] == "paranoid"  # Critical operation
    
    def test_ml_and_behavioral_integration(self):
        """Test integration of ML and behavioral analysis in orchestrator."""
        response_data = {
            "workflow_runs": [
                {
                    "id": "not_a_number",
                    "name": "lorem ipsum test",
                    "status": "completed",
                    "created_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
                }
            ]
        }
        
        request_params = {"endpoint": "actions/runs", "method": "GET"}
        context = {"response_time": 25}
        
        result = self.orchestrator.validate_github_actions_response(
            response_data, request_params, "workflow_runs", context
        )
        
        assert not result.is_valid
        assert result.confidence < 0.5
        assert len(result.issues) > 3  # Multiple validation issues
    
    def test_validation_metadata_enrichment(self):
        """Test that validation metadata is properly enriched."""
        response_data = {
            "workflow_runs": [
                {
                    "id": 123456789,
                    "name": "CI/CD Pipeline",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "head_branch": "main",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        
        request_params = {"endpoint": "actions/runs", "method": "GET"}
        
        result = self.orchestrator.validate_github_actions_response(
            response_data, request_params, "workflow_runs"
        )
        
        assert "validation_level" in result.metadata
        assert "validation_count" in result.metadata
        assert "response_type" in result.metadata
        assert result.metadata["response_type"] == "workflow_runs"
        assert result.metadata["validation_count"] > 0 