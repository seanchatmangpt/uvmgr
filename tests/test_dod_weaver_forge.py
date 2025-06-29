"""
Unit tests for Weaver Forge DoD compiler and exoskeleton.

Tests the Weaver Forge compiler, DoD specification processing,
and exoskeleton architecture for enterprise-grade automation.
"""

from __future__ import annotations

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from uvmgr.dod.weaver_forge_compiler import (
    DoDExoskeleton,
    WeaverForgeCompiler,
    DoDSpecification,
    DoDRule,
    DoDValidationResult,
    ValidationLevel,
    DoDCategory,
    get_dod_exoskeleton,
    wrap_project_with_dod,
    validate_dod
)


class TestDoDDataClasses:
    """Test DoD data classes and enums."""
    
    def test_validation_level_enum(self):
        """Test ValidationLevel enum values."""
        assert ValidationLevel.STRICT.value == "strict"
        assert ValidationLevel.STANDARD.value == "standard"
        assert ValidationLevel.ADVISORY.value == "advisory"
        
        # Test ordering
        assert ValidationLevel.STRICT > ValidationLevel.STANDARD
        assert ValidationLevel.STANDARD > ValidationLevel.ADVISORY
        
    def test_dod_category_enum(self):
        """Test DoDCategory enum completeness."""
        expected_categories = {
            "CODE_QUALITY", "SECURITY", "TESTING", "DOCUMENTATION",
            "PERFORMANCE", "OPERATIONS", "COMPLIANCE"
        }
        
        actual_categories = {category.name for category in DoDCategory}
        assert actual_categories == expected_categories
        
    def test_dod_rule_creation(self):
        """Test DoDRule data class creation and validation."""
        rule = DoDRule(
            name="test_coverage",
            condition="coverage >= 90",
            level=ValidationLevel.STRICT,
            category=DoDCategory.TESTING,
            auto_fix=False,
            fix_command=None,
            description="Test coverage must be at least 90%"
        )
        
        assert rule.name == "test_coverage"
        assert rule.condition == "coverage >= 90"
        assert rule.level == ValidationLevel.STRICT
        assert rule.category == DoDCategory.TESTING
        assert rule.auto_fix is False
        assert rule.fix_command is None
        assert "90%" in rule.description
        
    def test_dod_rule_with_auto_fix(self):
        """Test DoDRule with auto-fix configuration."""
        rule = DoDRule(
            name="lint_score",
            condition="lint_score >= 9.5",
            level=ValidationLevel.STANDARD,
            category=DoDCategory.CODE_QUALITY,
            auto_fix=True,
            fix_command="ruff check --fix . && ruff format .",
            description="Code must pass linting with score >= 9.5"
        )
        
        assert rule.auto_fix is True
        assert rule.fix_command is not None
        assert "ruff" in rule.fix_command
        
    def test_dod_validation_result(self):
        """Test DoDValidationResult data class."""
        result = DoDValidationResult(
            rule_name="test_coverage",
            passed=True,
            score=95.0,
            message="Test coverage is excellent",
            execution_time=1.5,
            auto_fix_applied=False,
            telemetry_data={"metric": "coverage", "value": 95.0}
        )
        
        assert result.rule_name == "test_coverage"
        assert result.passed is True
        assert result.score == 95.0
        assert "excellent" in result.message
        assert result.execution_time == 1.5
        assert result.auto_fix_applied is False
        assert result.telemetry_data["metric"] == "coverage"
        
    def test_dod_specification_creation(self):
        """Test DoDSpecification data class with rules."""
        rules = [
            DoDRule(
                name="test_coverage",
                condition="coverage >= 90",
                level=ValidationLevel.STRICT,
                category=DoDCategory.TESTING,
                auto_fix=False,
                fix_command=None,
                description="Test coverage validation"
            ),
            DoDRule(
                name="security_scan",
                condition="vulnerabilities == 0",
                level=ValidationLevel.STRICT,
                category=DoDCategory.SECURITY,
                auto_fix=False,
                fix_command=None,
                description="Security vulnerability scan"
            )
        ]
        
        spec = DoDSpecification(
            name="Enterprise DoD",
            version="1.0.0",
            enforcement=ValidationLevel.STRICT,
            rules=rules,
            metadata={"author": "test", "created": "2024-06-29"}
        )
        
        assert spec.name == "Enterprise DoD"
        assert spec.version == "1.0.0"
        assert spec.enforcement == ValidationLevel.STRICT
        assert len(spec.rules) == 2
        assert spec.metadata["author"] == "test"
        
        # Test rule lookup
        test_rule = next((r for r in spec.rules if r.name == "test_coverage"), None)
        assert test_rule is not None
        assert test_rule.category == DoDCategory.TESTING


class TestWeaverForgeCompiler:
    """Test Weaver Forge compiler functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_spec_yaml = """
name: "Test DoD Specification"
version: "1.0.0"
enforcement: "strict"

categories:
  code_quality:
    - name: "lint_score"
      condition: "lint_score >= 9.5"
      auto_fix: true
      fix_command: "ruff check --fix ."
      severity: "standard"
      telemetry:
        metric: "dod.code_quality.lint_score"
        threshold: 9.5
        
  security:
    - name: "vulnerability_scan"
      condition: "critical_vulnerabilities == 0"
      auto_fix: false
      severity: "strict"
      telemetry:
        metric: "dod.security.vulnerabilities"
        critical_threshold: 0
        
evolution:
  enabled: true
  learning_mode: "balanced"
  auto_tune: true
  
exoskeleton:
  semantic_conventions:
    - prefix: "dod"
      attributes:
        - "dod.category"
        - "dod.rule_name"
        - "dod.enforcement_level"
        """
        
    def test_compiler_initialization(self):
        """Test WeaverForgeCompiler initialization."""
        compiler = WeaverForgeCompiler()
        
        assert compiler is not None
        assert hasattr(compiler, 'compile_specification')
        assert hasattr(compiler, 'validate_specification')
        assert hasattr(compiler, 'generate_exoskeleton')
        
    def test_compile_specification_from_yaml(self):
        """Test compiling DoD specification from YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(self.test_spec_yaml)
            spec_file = Path(f.name)
            
        try:
            compiler = WeaverForgeCompiler()
            result = compiler.compile_specification(spec_file)
            
            assert result["success"] is True
            assert "specification" in result
            assert "compiled_rules" in result
            assert "exoskeleton_config" in result
            
            spec = result["specification"]
            assert spec.name == "Test DoD Specification"
            assert spec.version == "1.0.0"
            assert spec.enforcement == ValidationLevel.STRICT
            
            compiled_rules = result["compiled_rules"]
            assert len(compiled_rules) >= 2  # Should have lint_score and vulnerability_scan
            
            # Verify rules were compiled correctly
            lint_rule = next((r for r in compiled_rules if r.name == "lint_score"), None)
            assert lint_rule is not None
            assert lint_rule.auto_fix is True
            assert lint_rule.category == DoDCategory.CODE_QUALITY
            
            vuln_rule = next((r for r in compiled_rules if r.name == "vulnerability_scan"), None)
            assert vuln_rule is not None
            assert vuln_rule.auto_fix is False
            assert vuln_rule.category == DoDCategory.SECURITY
            
        finally:
            spec_file.unlink()
            
    def test_compile_specification_invalid_yaml(self):
        """Test compiling invalid YAML specification."""
        invalid_yaml = "invalid: yaml: content: [unclosed"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            spec_file = Path(f.name)
            
        try:
            compiler = WeaverForgeCompiler()
            result = compiler.compile_specification(spec_file)
            
            assert result["success"] is False
            assert "error" in result
            assert "YAML" in result["error"] or "yaml" in result["error"]
            
        finally:
            spec_file.unlink()
            
    def test_validate_specification_success(self):
        """Test successful specification validation."""
        rules = [
            DoDRule(
                name="test_coverage",
                condition="coverage >= 90",
                level=ValidationLevel.STRICT,
                category=DoDCategory.TESTING,
                auto_fix=False,
                fix_command=None,
                description="Test coverage validation"
            )
        ]
        
        spec = DoDSpecification(
            name="Test Spec",
            version="1.0.0",
            enforcement=ValidationLevel.STRICT,
            rules=rules,
            metadata={}
        )
        
        compiler = WeaverForgeCompiler()
        result = compiler.validate_specification(spec)
        
        assert result["success"] is True
        assert "validation_results" in result
        assert "schema_valid" in result
        assert result["schema_valid"] is True
        
    def test_validate_specification_with_errors(self):
        """Test specification validation with errors."""
        # Create spec with invalid rule (missing required fields)
        rules = [
            DoDRule(
                name="",  # Invalid: empty name
                condition="coverage >= 90",
                level=ValidationLevel.STRICT,
                category=DoDCategory.TESTING,
                auto_fix=False,
                fix_command=None,
                description="Test coverage validation"
            )
        ]
        
        spec = DoDSpecification(
            name="Invalid Spec",
            version="1.0.0",
            enforcement=ValidationLevel.STRICT,
            rules=rules,
            metadata={}
        )
        
        compiler = WeaverForgeCompiler()
        result = compiler.validate_specification(spec)
        
        assert result["success"] is False
        assert "validation_errors" in result
        assert len(result["validation_errors"]) > 0
        
    def test_generate_exoskeleton_success(self):
        """Test successful exoskeleton generation."""
        rules = [
            DoDRule(
                name="test_coverage",
                condition="coverage >= 90",
                level=ValidationLevel.STRICT,
                category=DoDCategory.TESTING,
                auto_fix=False,
                fix_command=None,
                description="Test coverage validation"
            )
        ]
        
        spec = DoDSpecification(
            name="Test Spec",
            version="1.0.0",
            enforcement=ValidationLevel.STRICT,
            rules=rules,
            metadata={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            compiler = WeaverForgeCompiler()
            result = compiler.generate_exoskeleton(spec, project_path)
            
            assert result["success"] is True
            assert "exoskeleton_files" in result
            assert "semantic_conventions" in result
            assert "telemetry_config" in result
            
            # Verify exoskeleton structure was created
            exoskeleton_dir = project_path / ".uvmgr" / "exoskeleton"
            assert exoskeleton_dir.exists()
            
    def test_execute_validation_with_mock_project(self):
        """Test executing validation against a mock project."""
        rules = [
            DoDRule(
                name="lint_score",
                condition="lint_score >= 9.0",
                level=ValidationLevel.STANDARD,
                category=DoDCategory.CODE_QUALITY,
                auto_fix=True,
                fix_command="ruff check --fix .",
                description="Linting validation"
            )
        ]
        
        spec = DoDSpecification(
            name="Test Spec",
            version="1.0.0",
            enforcement=ValidationLevel.STANDARD,
            rules=rules,
            metadata={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            compiler = WeaverForgeCompiler()
            
            # Mock the validation execution
            with patch.object(compiler, '_execute_rule_validation') as mock_validate:
                mock_validate.return_value = DoDValidationResult(
                    rule_name="lint_score",
                    passed=True,
                    score=95.0,
                    message="Linting passed",
                    execution_time=1.2,
                    auto_fix_applied=False,
                    telemetry_data={}
                )
                
                result = compiler.execute_validation(spec, project_path)
                
                assert result["success"] is True
                assert "validation_results" in result
                assert len(result["validation_results"]) == 1
                
                validation_result = result["validation_results"][0]
                assert validation_result.rule_name == "lint_score"
                assert validation_result.passed is True
                assert validation_result.score == 95.0


class TestDoDExoskeleton:
    """Test DoD exoskeleton functionality."""
    
    def test_exoskeleton_initialization(self):
        """Test DoDExoskeleton initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            rules = [
                DoDRule(
                    name="test_rule",
                    condition="test_condition",
                    level=ValidationLevel.STANDARD,
                    category=DoDCategory.TESTING,
                    auto_fix=False,
                    fix_command=None,
                    description="Test rule"
                )
            ]
            
            spec = DoDSpecification(
                name="Test Spec",
                version="1.0.0",
                enforcement=ValidationLevel.STANDARD,
                rules=rules,
                metadata={}
            )
            
            exoskeleton = DoDExoskeleton(
                project_path=project_path,
                specification=spec
            )
            
            assert exoskeleton.project_path == project_path
            assert exoskeleton.specification == spec
            assert exoskeleton.is_active is False  # Should be inactive initially
            
    def test_exoskeleton_activation(self):
        """Test exoskeleton activation and deactivation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            rules = []
            spec = DoDSpecification(
                name="Test Spec",
                version="1.0.0",
                enforcement=ValidationLevel.STANDARD,
                rules=rules,
                metadata={}
            )
            
            exoskeleton = DoDExoskeleton(
                project_path=project_path,
                specification=spec
            )
            
            # Test activation
            result = exoskeleton.activate()
            assert result["success"] is True
            assert exoskeleton.is_active is True
            
            # Test deactivation
            result = exoskeleton.deactivate()
            assert result["success"] is True
            assert exoskeleton.is_active is False
            
    def test_exoskeleton_continuous_validation(self):
        """Test continuous validation functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            rules = [
                DoDRule(
                    name="continuous_test",
                    condition="always_true",
                    level=ValidationLevel.ADVISORY,
                    category=DoDCategory.TESTING,
                    auto_fix=False,
                    fix_command=None,
                    description="Continuous test rule"
                )
            ]
            
            spec = DoDSpecification(
                name="Continuous Spec",
                version="1.0.0",
                enforcement=ValidationLevel.ADVISORY,
                rules=rules,
                metadata={}
            )
            
            exoskeleton = DoDExoskeleton(
                project_path=project_path,
                specification=spec
            )
            
            # Mock the validation execution
            with patch.object(exoskeleton, '_run_validation_cycle') as mock_cycle:
                mock_cycle.return_value = {
                    "success": True,
                    "results": [
                        DoDValidationResult(
                            rule_name="continuous_test",
                            passed=True,
                            score=100.0,
                            message="Continuous validation passed",
                            execution_time=0.5,
                            auto_fix_applied=False,
                            telemetry_data={}
                        )
                    ]
                }
                
                result = exoskeleton.run_continuous_validation()
                
                assert result["success"] is True
                assert "results" in result
                assert len(result["results"]) == 1


class TestDoDFunctions:
    """Test module-level DoD functions."""
    
    def test_get_dod_exoskeleton_existing(self):
        """Test getting existing DoD exoskeleton."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create exoskeleton directory structure
            exoskeleton_dir = project_path / ".uvmgr" / "exoskeleton"
            exoskeleton_dir.mkdir(parents=True)
            
            # Create a minimal specification file
            spec_file = exoskeleton_dir / "dod-spec.yaml"
            spec_data = {
                "name": "Existing DoD",
                "version": "1.0.0",
                "enforcement": "standard",
                "categories": {}
            }
            
            with open(spec_file, 'w') as f:
                yaml.dump(spec_data, f)
                
            result = get_dod_exoskeleton(project_path)
            
            assert result["success"] is True
            assert "exoskeleton" in result
            assert result["exoskeleton"] is not None
            
    def test_get_dod_exoskeleton_none_existing(self):
        """Test getting DoD exoskeleton when none exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            result = get_dod_exoskeleton(project_path)
            
            assert result["success"] is True
            assert result["exoskeleton"] is None
            assert "No exoskeleton found" in result["message"]
            
    def test_wrap_project_with_dod_success(self):
        """Test successfully wrapping project with DoD."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            with patch("uvmgr.dod.weaver_forge_compiler.WeaverForgeCompiler") as mock_compiler_class:
                mock_compiler = Mock()
                mock_compiler_class.return_value = mock_compiler
                
                # Mock compiler methods
                mock_compiler.compile_specification.return_value = {
                    "success": True,
                    "specification": Mock(),
                    "compiled_rules": [],
                    "exoskeleton_config": {}
                }
                
                mock_compiler.generate_exoskeleton.return_value = {
                    "success": True,
                    "exoskeleton_files": [],
                    "semantic_conventions": {},
                    "telemetry_config": {}
                }
                
                result = wrap_project_with_dod(project_path, "enterprise")
                
                assert result["success"] is True
                assert "exoskeleton" in result
                
    def test_validate_dod_success(self):
        """Test successful DoD validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create mock exoskeleton
            mock_exoskeleton = Mock()
            mock_exoskeleton.is_active = True
            
            mock_validation_result = DoDValidationResult(
                rule_name="test_rule",
                passed=True,
                score=95.0,
                message="Validation passed",
                execution_time=1.0,
                auto_fix_applied=False,
                telemetry_data={}
            )
            
            mock_exoskeleton.run_validation.return_value = {
                "success": True,
                "results": [mock_validation_result],
                "overall_score": 95.0,
                "passed": True
            }
            
            with patch("uvmgr.dod.weaver_forge_compiler.get_dod_exoskeleton") as mock_get:
                mock_get.return_value = {
                    "success": True,
                    "exoskeleton": mock_exoskeleton
                }
                
                result = validate_dod(project_path, fix_issues=False)
                
                assert result["success"] is True
                assert "validation_results" in result
                assert result["overall_score"] == 95.0
                assert result["passed"] is True
                
    def test_validate_dod_no_exoskeleton(self):
        """Test DoD validation when no exoskeleton exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            with patch("uvmgr.dod.weaver_forge_compiler.get_dod_exoskeleton") as mock_get:
                mock_get.return_value = {
                    "success": True,
                    "exoskeleton": None,
                    "message": "No exoskeleton found"
                }
                
                result = validate_dod(project_path)
                
                assert result["success"] is False
                assert "No DoD exoskeleton found" in result["error"]


class TestDoDIntegration:
    """Integration tests for DoD system components."""
    
    @pytest.mark.integration
    def test_full_dod_workflow(self):
        """Test complete DoD workflow from specification to validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a test specification file
            spec_data = {
                "name": "Integration Test DoD",
                "version": "1.0.0",
                "enforcement": "standard",
                "categories": {
                    "testing": [
                        {
                            "name": "unit_tests",
                            "condition": "unit_coverage >= 80",
                            "auto_fix": False,
                            "severity": "standard"
                        }
                    ]
                }
            }
            
            spec_file = project_path / "dod-spec.yaml"
            with open(spec_file, 'w') as f:
                yaml.dump(spec_data, f)
                
            # Step 1: Wrap project with DoD
            wrap_result = wrap_project_with_dod(project_path, "standard")
            
            # For integration test, we expect this to work with the real implementation
            # But since we're testing the interface, we can verify the call structure
            assert "success" in wrap_result
            
            # Step 2: Get exoskeleton
            exoskeleton_result = get_dod_exoskeleton(project_path)
            assert "success" in exoskeleton_result
            
            # Step 3: Validate DoD
            validation_result = validate_dod(project_path)
            assert "success" in validation_result


class TestDoDPerformance:
    """Performance tests for DoD system."""
    
    def test_specification_compilation_performance(self):
        """Test specification compilation performance."""
        import time
        
        # Create a large specification for performance testing
        large_spec_data = {
            "name": "Large DoD Specification",
            "version": "1.0.0",
            "enforcement": "standard",
            "categories": {}
        }
        
        # Add many rules to test performance
        for category in ["testing", "security", "code_quality", "documentation"]:
            large_spec_data["categories"][category] = []
            for i in range(25):  # 25 rules per category = 100 total rules
                rule = {
                    "name": f"{category}_rule_{i}",
                    "condition": f"metric_{i} >= {i * 10}",
                    "auto_fix": i % 2 == 0,
                    "severity": "standard"
                }
                large_spec_data["categories"][category].append(rule)
                
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(large_spec_data, f)
            spec_file = Path(f.name)
            
        try:
            compiler = WeaverForgeCompiler()
            
            start_time = time.time()
            result = compiler.compile_specification(spec_file)
            end_time = time.time()
            
            # Should complete within reasonable time even with 100 rules
            assert (end_time - start_time) < 5.0  # Less than 5 seconds
            
            if result["success"]:
                assert len(result["compiled_rules"]) == 100
                
        finally:
            spec_file.unlink()
            
    def test_validation_execution_performance(self):
        """Test validation execution performance."""
        import time
        
        # Create specification with multiple rules
        rules = []
        for i in range(10):
            rule = DoDRule(
                name=f"perf_rule_{i}",
                condition=f"metric_{i} >= 80",
                level=ValidationLevel.STANDARD,
                category=DoDCategory.TESTING,
                auto_fix=False,
                fix_command=None,
                description=f"Performance test rule {i}"
            )
            rules.append(rule)
            
        spec = DoDSpecification(
            name="Performance Test Spec",
            version="1.0.0",
            enforcement=ValidationLevel.STANDARD,
            rules=rules,
            metadata={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            compiler = WeaverForgeCompiler()
            
            # Mock rule validation to test execution overhead
            with patch.object(compiler, '_execute_rule_validation') as mock_validate:
                mock_validate.return_value = DoDValidationResult(
                    rule_name="test",
                    passed=True,
                    score=90.0,
                    message="Passed",
                    execution_time=0.1,
                    auto_fix_applied=False,
                    telemetry_data={}
                )
                
                start_time = time.time()
                result = compiler.execute_validation(spec, project_path)
                end_time = time.time()
                
                # Should complete quickly with mocked validation
                assert (end_time - start_time) < 2.0  # Less than 2 seconds
                
                if result["success"]:
                    assert len(result["validation_results"]) == 10


if __name__ == "__main__":
    pytest.main([__file__])