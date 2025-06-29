#!/usr/bin/env python3
"""
Exponential Technology Validation Script
========================================

Validates all exponential technology capabilities in a cleanroom environment:
- Exponential command functionality
- Democratization platform
- Convergence engine detection
- AGI reasoning enhancements
- External project validation
"""

import subprocess
import sys
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    success: bool
    details: str
    execution_time: float
    output: str = ""
    error: str = ""

class ExponentialValidator:
    """Validates exponential technology capabilities."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        
        # Ensure we're in the right directory
        if not Path("pyproject.toml").exists():
            print("❌ Not in uvmgr project directory!")
            sys.exit(1)
    
    def run_command(self, cmd: List[str], timeout: float = 30) -> ValidationResult:
        """Run a command and capture result."""
        test_name = " ".join(cmd)
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd()
            )
            
            execution_time = time.time() - start_time
            success = result.returncode == 0
            
            return ValidationResult(
                test_name=test_name,
                success=success,
                details=f"Exit code: {result.returncode}",
                execution_time=execution_time,
                output=result.stdout,
                error=result.stderr
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ValidationResult(
                test_name=test_name,
                success=False,
                details=f"Command timed out after {timeout}s",
                execution_time=execution_time,
                error="Timeout"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ValidationResult(
                test_name=test_name,
                success=False,
                details=f"Exception: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
    
    def validate_basic_installation(self) -> ValidationResult:
        """Validate basic uvmgr installation."""
        print("🔧 Validating basic installation...")
        
        # Install dependencies first
        install_result = self.run_command(["uv", "sync"], timeout=300)
        if not install_result.success:
            return ValidationResult(
                test_name="basic_installation",
                success=False,
                details="Failed to install dependencies",
                execution_time=install_result.execution_time,
                error=install_result.error
            )
        
        # Test basic uvmgr import
        test_result = self.run_command([
            "python", "-c", 
            "import uvmgr; print('✅ uvmgr imported successfully')"
        ])
        
        return ValidationResult(
            test_name="basic_installation",
            success=test_result.success,
            details="uvmgr installation and import test",
            execution_time=test_result.execution_time,
            output=test_result.output,
            error=test_result.error
        )
    
    def validate_exponential_commands(self) -> List[ValidationResult]:
        """Validate exponential command functionality."""
        print("🚀 Validating exponential commands...")
        
        results = []
        
        # Test exponential status
        result = self.run_command(["python", "-m", "uvmgr.cli", "exponential", "status"])
        results.append(ValidationResult(
            test_name="exponential_status",
            success=result.success,
            details="Exponential status command",
            execution_time=result.execution_time,
            output=result.output,
            error=result.error
        ))
        
        # Test exponential generate-workflow
        result = self.run_command([
            "python", "-m", "uvmgr.cli", "exponential", "generate-workflow",
            "Create a simple test automation workflow"
        ])
        results.append(ValidationResult(
            test_name="exponential_generate_workflow",
            success=result.success,
            details="AI workflow generation command",
            execution_time=result.execution_time,
            output=result.output,
            error=result.error
        ))
        
        # Test convergence analysis
        result = self.run_command([
            "python", "-m", "uvmgr.cli", "exponential", "analyze-convergences"
        ])
        results.append(ValidationResult(
            test_name="exponential_analyze_convergences",
            success=result.success,
            details="Technology convergence analysis",
            execution_time=result.execution_time,
            output=result.output,
            error=result.error
        ))
        
        return results
    
    def validate_democratization_platform(self) -> List[ValidationResult]:
        """Validate democratization platform functionality."""
        print("🌍 Validating democratization platform...")
        
        results = []
        
        # Test democratize templates
        result = self.run_command(["python", "-m", "uvmgr.cli", "democratize", "templates"])
        results.append(ValidationResult(
            test_name="democratize_templates",
            success=result.success,
            details="Democratization templates listing",
            execution_time=result.execution_time,
            output=result.output,
            error=result.error
        ))
        
        # Test democratize status
        result = self.run_command(["python", "-m", "uvmgr.cli", "democratize", "status"])
        results.append(ValidationResult(
            test_name="democratize_status",
            success=result.success,
            details="Democratization platform status",
            execution_time=result.execution_time,
            output=result.output,
            error=result.error
        ))
        
        return results
    
    def validate_agi_reasoning(self) -> ValidationResult:
        """Validate AGI reasoning enhancements."""
        print("🧠 Validating AGI reasoning...")
        
        # Test AGI reasoning import and functionality
        test_code = """
import sys
sys.path.insert(0, '/workspace/src')

try:
    from uvmgr.core.agi_reasoning import (
        observe_with_agi_reasoning, 
        get_agi_insights, 
        get_exponential_agi_insights,
        trigger_learning_acceleration
    )
    
    # Test observation
    observation = observe_with_agi_reasoning(
        attributes={"cli.command": "test", "test.framework": "validation"},
        context={"validation_test": True}
    )
    
    # Test insights
    insights = get_agi_insights()
    exp_insights = get_exponential_agi_insights()
    
    # Test learning acceleration
    acceleration = trigger_learning_acceleration()
    
    print(f"✅ AGI Reasoning: Observation confidence: {observation.confidence:.2f}")
    print(f"✅ AGI Insights: {len(insights.get('improvement_suggestions', []))} suggestions")
    print(f"✅ Exponential: Learning acceleration: {acceleration:.2f}x")
    print(f"✅ AGI reasoning validation successful")
    
except Exception as e:
    print(f"❌ AGI reasoning validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
        
        result = self.run_command(["python", "-c", test_code])
        
        return ValidationResult(
            test_name="agi_reasoning_validation",
            success=result.success,
            details="AGI reasoning and exponential learning validation",
            execution_time=result.execution_time,
            output=result.output,
            error=result.error
        )
    
    def validate_convergence_engine(self) -> ValidationResult:
        """Validate convergence engine functionality."""
        print("🔄 Validating convergence engine...")
        
        test_code = """
import sys
sys.path.insert(0, '/workspace/src')

try:
    from uvmgr.core.convergence_engine import (
        get_convergence_engine,
        analyze_convergences,
        get_convergence_recommendations
    )
    
    # Get convergence engine
    engine = get_convergence_engine()
    
    # Run convergence analysis
    analysis = analyze_convergences({"test_context": True})
    
    # Get recommendations
    recommendations = get_convergence_recommendations()
    
    print(f"✅ Convergence Engine: {analysis['total_capabilities']} capabilities detected")
    print(f"✅ Convergence Analysis: {analysis['active_convergences']} active convergences")
    print(f"✅ Recommendations: {len(recommendations)} convergence recommendations")
    print(f"✅ Convergence Score: {analysis['convergence_score']:.2f}")
    print("✅ Convergence engine validation successful")
    
except Exception as e:
    print(f"❌ Convergence engine validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
        
        result = self.run_command(["python", "-c", test_code])
        
        return ValidationResult(
            test_name="convergence_engine_validation",
            success=result.success,
            details="Technology convergence detection validation",
            execution_time=result.execution_time,
            output=result.output,
            error=result.error
        )
    
    def validate_external_project_capability(self) -> ValidationResult:
        """Test capability to work with external projects."""
        print("🌐 Validating external project capability...")
        
        # Create a simple test project
        test_project = Path("/tmp/test-exponential-project")
        test_project.mkdir(exist_ok=True)
        
        # Create a simple Python project
        (test_project / "main.py").write_text('''
def hello_world():
    """Simple test function."""
    return "Hello, Exponential World!"

if __name__ == "__main__":
    print(hello_world())
''')
        
        (test_project / "requirements.txt").write_text("# No dependencies needed\n")
        
        # Test uvmgr functionality on external project
        test_code = f"""
import os
import sys
os.chdir('{test_project}')
sys.path.insert(0, '/workspace/src')

try:
    from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
    from uvmgr.core.convergence_engine import analyze_convergences
    
    # Test observation in external context
    observation = observe_with_agi_reasoning(
        attributes={{"cli.command": "external_test", "project.path": str('{test_project}')}},
        context={{"external_project": True, "validation": True}}
    )
    
    # Test convergence analysis in external context
    analysis = analyze_convergences({{"external_project": str('{test_project}')}})
    
    print(f"✅ External Project: Observed with confidence {observation.confidence:.2f}")
    print(f"✅ External Analysis: {analysis['total_capabilities']} capabilities available")
    print("✅ External project validation successful")
    
except Exception as e:
    print(f"❌ External project validation failed: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
        
        result = self.run_command(["python", "-c", test_code])
        
        return ValidationResult(
            test_name="external_project_validation",
            success=result.success,
            details="External project capability validation",
            execution_time=result.execution_time,
            output=result.output,
            error=result.error
        )
    
    def validate_cli_integration(self) -> List[ValidationResult]:
        """Validate CLI integration of all exponential features."""
        print("⚡ Validating CLI integration...")
        
        results = []
        
        # Test help commands
        commands_to_test = [
            ["python", "-m", "uvmgr.cli", "--help"],
            ["python", "-m", "uvmgr.cli", "exponential", "--help"],
            ["python", "-m", "uvmgr.cli", "democratize", "--help"],
        ]
        
        for cmd in commands_to_test:
            result = self.run_command(cmd)
            results.append(ValidationResult(
                test_name=f"cli_help_{cmd[-2] if len(cmd) > 4 else 'main'}",
                success=result.success,
                details=f"CLI help for {' '.join(cmd[-2:])}",
                execution_time=result.execution_time,
                output=result.output,
                error=result.error
            ))
        
        return results
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🚀 Starting Exponential Technology Validation\n")
        
        # Run all validation tests
        validation_methods = [
            ("Basic Installation", self.validate_basic_installation),
            ("AGI Reasoning", self.validate_agi_reasoning), 
            ("Convergence Engine", self.validate_convergence_engine),
            ("External Project Capability", self.validate_external_project_capability),
        ]
        
        # Run methods that return single results
        for name, method in validation_methods:
            print(f"\n--- {name} ---")
            result = method()
            self.results.append(result)
            
            if result.success:
                print(f"✅ {name}: PASSED")
                if result.output:
                    for line in result.output.strip().split('\n'):
                        if line.strip():
                            print(f"   {line}")
            else:
                print(f"❌ {name}: FAILED")
                print(f"   Details: {result.details}")
                if result.error:
                    print(f"   Error: {result.error}")
        
        # Run methods that return multiple results
        multi_result_methods = [
            ("Exponential Commands", self.validate_exponential_commands),
            ("Democratization Platform", self.validate_democratization_platform),
            ("CLI Integration", self.validate_cli_integration),
        ]
        
        for name, method in multi_result_methods:
            print(f"\n--- {name} ---")
            results = method()
            self.results.extend(results)
            
            passed = sum(1 for r in results if r.success)
            total = len(results)
            print(f"✅ {name}: {passed}/{total} tests passed")
            
            for result in results:
                status = "✅" if result.success else "❌"
                print(f"   {status} {result.test_name}")
                if not result.success and result.error:
                    print(f"      Error: {result.error}")
        
        # Generate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        total_time = time.time() - self.start_time
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "total_execution_time": total_time,
            "avg_test_time": sum(r.execution_time for r in self.results) / total_tests if total_tests > 0 else 0,
            "all_passed": passed_tests == total_tests
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "="*60)
        print("🚀 EXPONENTIAL TECHNOLOGY VALIDATION SUMMARY")
        print("="*60)
        
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Total Time: {summary['total_execution_time']:.2f}s")
        print(f"Average Test Time: {summary['avg_test_time']:.2f}s")
        
        if summary['all_passed']:
            print("\n🎉 ALL EXPONENTIAL CAPABILITIES VALIDATED SUCCESSFULLY!")
            print("The Future Is Faster Than You Think - Implementation Complete! 🚀")
        else:
            print(f"\n⚠️  {summary['failed_tests']} tests failed. See details above.")
            
            # Show failed tests
            failed_tests = [r for r in self.results if not r.success]
            if failed_tests:
                print("\nFailed Tests:")
                for test in failed_tests:
                    print(f"  ❌ {test.test_name}: {test.details}")
        
        print("="*60)
        
        return summary['all_passed']

def main():
    """Main validation function."""
    validator = ExponentialValidator()
    
    try:
        summary = validator.run_all_validations()
        success = validator.print_summary(summary)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()