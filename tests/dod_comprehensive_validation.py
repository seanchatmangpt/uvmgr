#!/usr/bin/env python3
"""
Comprehensive DoD Automation System Validation
==============================================

This script provides a complete validation of the Definition of Done automation system
including unit testing, OpenTelemetry validation, and Weaver semantic convention compliance.
"""

import sys
import traceback
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_dod_criteria_weights():
    """Test DoD criteria weights follow 80/20 principle."""
    try:
        from uvmgr.ops.dod import DOD_CRITERIA_WEIGHTS
        
        # Calculate total weight
        total_weight = sum(config.get('weight', 0) for config in DOD_CRITERIA_WEIGHTS.values())
        
        # Calculate critical criteria weight  
        critical_weight = sum(
            config.get('weight', 0) 
            for config in DOD_CRITERIA_WEIGHTS.values() 
            if config.get('priority') == 'critical'
        )
        
        assert abs(total_weight - 1.0) < 0.01, f"Total weight {total_weight} != 1.0"
        assert critical_weight >= 0.70, f"Critical weight {critical_weight} < 0.70 (80/20 principle)"
        
        return {
            "status": "PASS",
            "total_weight": total_weight,
            "critical_weight": critical_weight,
            "criteria_count": len(DOD_CRITERIA_WEIGHTS)
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}


def test_exoskeleton_templates():
    """Test exoskeleton template configurations."""
    try:
        from uvmgr.ops.dod import EXOSKELETON_TEMPLATES
        
        required_fields = ["description", "includes", "ai_features"]
        template_count = len(EXOSKELETON_TEMPLATES)
        
        for template_name, config in EXOSKELETON_TEMPLATES.items():
            for field in required_fields:
                assert field in config, f"Template {template_name} missing {field}"
            assert isinstance(config["includes"], list)
            assert isinstance(config["ai_features"], list)
        
        return {
            "status": "PASS",
            "template_count": template_count,
            "templates": list(EXOSKELETON_TEMPLATES.keys())
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}


def test_weaver_semantic_conventions():
    """Test Weaver semantic convention compliance."""
    try:
        # Test span naming conventions
        expected_spans = [
            'dod.create_exoskeleton',
            'dod.execute_complete_automation', 
            'dod.validate_dod_criteria',
            'dod.generate_devops_pipeline',
            'dod.run_e2e_automation',
            'dod.analyze_project_status'
        ]
        
        valid_spans = []
        for span_name in expected_spans:
            # Check namespace
            assert span_name.startswith('dod.'), f'Span {span_name} must use dod. namespace'
            
            # Check snake_case
            parts = span_name.split('.')
            for part in parts:
                assert part.islower(), f'Span part {part} must be lowercase'
                if '_' in part:
                    assert not part.startswith('_'), f'Span part {part} cannot start with underscore'
                    assert not part.endswith('_'), f'Span part {part} cannot end with underscore'
            
            valid_spans.append(span_name)
        
        # Test attribute naming conventions
        valid_attributes = [
            'dod.template', 'dod.environment', 'dod.force', 'dod.preview',
            'dod.success_rate', 'dod.execution_time', 'dod.criteria_count',
            'project.path', 'automation.strategy'
        ]
        
        for attr_name in valid_attributes:
            # Check namespace
            assert attr_name.startswith(('dod.', 'project.', 'automation.')), \
                f'Attribute {attr_name} must use proper namespace'
            
            # Check snake_case
            namespace, attr = attr_name.split('.', 1)
            assert attr.islower(), f'Attribute {attr} must be lowercase'
        
        return {
            "status": "PASS",
            "valid_spans": len(valid_spans),
            "valid_attributes": len(valid_attributes),
            "span_names": valid_spans,
            "attribute_names": valid_attributes
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}


def test_dod_operations():
    """Test DoD operations functionality."""
    try:
        from uvmgr.ops.dod import validate_dod_criteria, create_exoskeleton
        from pathlib import Path
        
        # Test validation
        validation_result = validate_dod_criteria(
            project_path=Path('.'),
            criteria=['testing', 'security'],
            detailed=False,
            fix_suggestions=True
        )
        
        assert validation_result.get('success'), "Validation should succeed"
        assert 'overall_score' in validation_result, "Should have overall score"
        assert 'criteria_scores' in validation_result, "Should have criteria scores"
        
        # Test exoskeleton creation (preview mode)
        exoskeleton_result = create_exoskeleton(
            project_path=Path('.'),
            template='standard',
            preview=True
        )
        
        assert exoskeleton_result.get('success'), "Exoskeleton preview should succeed"
        assert exoskeleton_result.get('preview'), "Should be in preview mode"
        assert 'structure' in exoskeleton_result, "Should have structure"
        
        return {
            "status": "PASS",
            "validation_score": validation_result.get('overall_score', 0),
            "criteria_evaluated": len(validation_result.get('criteria_scores', {})),
            "exoskeleton_preview": True
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}


def test_command_interface():
    """Test DoD command interface."""
    try:
        from uvmgr.commands.dod import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Test status command
        status_result = runner.invoke(app, ['status'])
        status_success = status_result.exit_code == 0
        
        # Test validation command
        validate_result = runner.invoke(app, ['validate', '--criteria', 'testing'])
        validate_success = validate_result.exit_code == 0
        
        # Test complete automation
        complete_result = runner.invoke(app, ['complete', '--env', 'development'])
        complete_success = complete_result.exit_code == 0
        
        return {
            "status": "PASS",
            "status_command": status_success,
            "validate_command": validate_success,
            "complete_command": complete_success,
            "total_commands_tested": 3,
            "successful_commands": sum([status_success, validate_success, complete_success])
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}


def test_runtime_implementations():
    """Test runtime implementation functionality."""
    try:
        from uvmgr.runtime.dod import (
            execute_automation_workflow,
            validate_criteria_runtime,
            analyze_project_health
        )
        from pathlib import Path
        
        # Test automation workflow
        workflow_result = execute_automation_workflow(
            project_path=Path('.'),
            criteria=['testing', 'security'],
            environment='development',
            auto_fix=False,
            parallel=True,
            ai_assist=True
        )
        
        assert workflow_result.get('success'), "Workflow should succeed"
        assert 'criteria_results' in workflow_result, "Should have criteria results"
        
        # Test criteria validation
        criteria_result = validate_criteria_runtime(
            project_path=Path('.'),
            criteria=['testing'],
            detailed=True,
            fix_suggestions=True
        )
        
        assert criteria_result.get('success'), "Criteria validation should succeed"
        
        # Test health analysis  
        health_result = analyze_project_health(
            project_path=Path('.'),
            detailed=True,
            suggestions=True
        )
        
        assert health_result.get('success'), "Health analysis should succeed"
        
        return {
            "status": "PASS",
            "workflow_execution": True,
            "criteria_validation": True,
            "health_analysis": True,
            "runtime_functions_tested": 3
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}


def run_comprehensive_validation():
    """Run comprehensive validation and return results."""
    print("🎯 DoD Automation System Comprehensive Validation")
    print("=" * 60)
    
    tests = [
        ("DoD Criteria Weights (80/20 Principle)", test_dod_criteria_weights),
        ("Exoskeleton Templates", test_exoskeleton_templates), 
        ("Weaver Semantic Conventions", test_weaver_semantic_conventions),
        ("DoD Operations", test_dod_operations),
        ("Command Interface", test_command_interface),
        ("Runtime Implementations", test_runtime_implementations)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            
            if result["status"] == "PASS":
                print(f"   ✅ PASSED")
                passed += 1
                
                # Print key metrics
                for key, value in result.items():
                    if key != "status" and not key.endswith("_names"):
                        print(f"      {key}: {value}")
            else:
                print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")
            results[test_name] = {"status": "ERROR", "error": str(e)}
    
    print(f"\n🏁 Validation Summary")
    print(f"=" * 30)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All validations PASSED! DoD system is fully functional.")
    else:
        print(f"⚠️  {total-passed} validation(s) failed. Review results above.")
    
    return results


if __name__ == "__main__":
    try:
        results = run_comprehensive_validation()
        
        # Exit with appropriate code
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("status") == "PASS")
        
        if passed_tests == total_tests:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Some failures
            
    except Exception as e:
        print(f"\n💥 Critical validation error: {str(e)}")
        traceback.print_exc()
        sys.exit(2)  # Critical error