#!/usr/bin/env python3
"""
Current State Validation for uvmgr Exponential Technology Capabilities
====================================================================

This script validates the current implementation state of uvmgr's exponential
technology capabilities as outlined in "The Future Is Faster Than You Think".

It provides a comprehensive report on:
- Available core modules and their functionality
- Command availability and import status
- OpenTelemetry integration status
- Technology convergence engine status
- AGI reasoning capabilities
- External project integration readiness
"""

import sys
import os
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add src to path for imports
workspace_src = Path("/workspace/src")
if workspace_src.exists():
    sys.path.insert(0, str(workspace_src))

@dataclass
class ValidationResult:
    """Result of a validation test."""
    name: str
    status: str  # "PASS", "FAIL", "WARN", "SKIP"
    message: str
    details: Optional[Dict[str, Any]] = None

class ExponentialStateValidator:
    """Validates current state of exponential technology implementation."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🚀 uvmgr Exponential Technology State Validation")
        print("=" * 60)
        
        # Core infrastructure tests
        self._test_python_environment()
        self._test_core_dependencies()
        self._test_core_modules()
        
        # Technology convergence tests
        self._test_convergence_engine()
        self._test_agi_reasoning()
        self._test_telemetry_integration()
        
        # Command system tests
        self._test_command_system()
        self._test_available_commands()
        
        # External integration readiness
        self._test_external_readiness()
        
        return self._generate_report()
    
    def _test_python_environment(self):
        """Test Python environment setup."""
        try:
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            if sys.version_info >= (3, 11):
                self.results.append(ValidationResult(
                    "Python Environment",
                    "PASS",
                    f"Python {python_version} - Compatible version"
                ))
            else:
                self.results.append(ValidationResult(
                    "Python Environment", 
                    "WARN",
                    f"Python {python_version} - May have compatibility issues"
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                "Python Environment",
                "FAIL", 
                f"Environment check failed: {e}"
            ))
    
    def _test_core_dependencies(self):
        """Test availability of core dependencies."""
        core_deps = [
            ("rich", "Rich terminal output"),
            ("typer", "CLI framework"),
            ("pydantic", "Data validation"),
            ("opentelemetry", "Observability framework"),
        ]
        
        for dep_name, description in core_deps:
            try:
                importlib.import_module(dep_name)
                self.results.append(ValidationResult(
                    f"Dependency: {dep_name}",
                    "PASS",
                    f"{description} - Available"
                ))
            except ImportError as e:
                self.results.append(ValidationResult(
                    f"Dependency: {dep_name}",
                    "FAIL",
                    f"{description} - Missing: {e}"
                ))
    
    def _test_core_modules(self):
        """Test uvmgr core module availability."""
        core_modules = [
            ("uvmgr.core", "Core utilities"),
            ("uvmgr.core.semconv", "Semantic conventions"),
            ("uvmgr.core.telemetry", "Telemetry system"),
            ("uvmgr.core.instrumentation", "Instrumentation decorators"),
        ]
        
        for module_name, description in core_modules:
            try:
                module = importlib.import_module(module_name)
                self.results.append(ValidationResult(
                    f"Core Module: {module_name}",
                    "PASS",
                    f"{description} - Imported successfully",
                    {"module_attrs": len(dir(module))}
                ))
            except Exception as e:
                self.results.append(ValidationResult(
                    f"Core Module: {module_name}",
                    "FAIL",
                    f"{description} - Import failed: {e}"
                ))
    
    def _test_convergence_engine(self):
        """Test technology convergence engine."""
        try:
            from uvmgr.core.convergence_engine import (
                ConvergenceEngine, 
                get_convergence_engine,
                TechnologyDomain,
                ConvergenceLevel
            )
            
            engine = get_convergence_engine()
            status = engine.get_convergence_status()
            
            self.results.append(ValidationResult(
                "Convergence Engine",
                "PASS",
                "Technology convergence engine operational",
                {
                    "capabilities": status.get("total_capabilities", 0),
                    "convergences": status.get("total_convergences", 0),
                    "score": status.get("convergence_score", 0.0)
                }
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Convergence Engine",
                "FAIL",
                f"Convergence engine failed: {e}"
            ))
    
    def _test_agi_reasoning(self):
        """Test AGI reasoning capabilities."""
        try:
            from uvmgr.core.agi_reasoning import (
                observe_with_agi_reasoning,
                get_agi_insights,
                AGIReasoningEngine
            )
            
            # Test basic functionality
            insights = get_agi_insights()
            
            self.results.append(ValidationResult(
                "AGI Reasoning",
                "PASS",
                "AGI reasoning system operational",
                {"insights_available": len(insights)}
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "AGI Reasoning",
                "FAIL",
                f"AGI reasoning failed: {e}"
            ))
    
    def _test_telemetry_integration(self):
        """Test OpenTelemetry integration."""
        try:
            from uvmgr.core.telemetry import span, metric_counter
            from uvmgr.core.instrumentation import instrument_command
            
            # Test basic telemetry functionality
            with span("test_span", operation_type="validation"):
                counter = metric_counter("test.validation.counter")
                counter(1)
            
            self.results.append(ValidationResult(
                "Telemetry Integration", 
                "PASS",
                "OpenTelemetry integration working"
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Telemetry Integration",
                "FAIL",
                f"Telemetry integration failed: {e}"
            ))
    
    def _test_command_system(self):
        """Test command system infrastructure."""
        try:
            from uvmgr.commands import __all__ as available_commands
            
            self.results.append(ValidationResult(
                "Command System",
                "PASS",
                f"Command system operational - {len(available_commands)} commands available",
                {"available_commands": available_commands}
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Command System",
                "FAIL",
                f"Command system failed: {e}"
            ))
    
    def _test_available_commands(self):
        """Test individual command availability."""
        try:
            from uvmgr.commands import __all__ as available_commands
            
            working_commands = []
            failed_commands = []
            
            for cmd_name in available_commands:
                try:
                    # Try to import each command
                    cmd_module = importlib.import_module(f"uvmgr.commands.{cmd_name}")
                    working_commands.append(cmd_name)
                except Exception as e:
                    failed_commands.append((cmd_name, str(e)))
            
            if working_commands:
                self.results.append(ValidationResult(
                    "Available Commands",
                    "PASS" if not failed_commands else "WARN",
                    f"Working: {len(working_commands)}, Failed: {len(failed_commands)}",
                    {
                        "working_commands": working_commands,
                        "failed_commands": failed_commands
                    }
                ))
            else:
                self.results.append(ValidationResult(
                    "Available Commands",
                    "FAIL",
                    "No commands are importable"
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                "Available Commands",
                "FAIL",
                f"Command testing failed: {e}"
            ))
    
    def _test_external_readiness(self):
        """Test readiness for external project integration."""
        try:
            # Check if we can handle external project workflows
            from uvmgr.core.semconv import (
                CliAttributes, 
                WorkflowAttributes,
                ProcessAttributes
            )
            
            # Test semantic convention availability
            test_attrs = [
                CliAttributes.COMMAND,
                WorkflowAttributes.OPERATION,
                ProcessAttributes.COMMAND
            ]
            
            self.results.append(ValidationResult(
                "External Integration Readiness",
                "PASS", 
                "Semantic conventions available for external projects",
                {"semantic_attributes": len(test_attrs)}
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "External Integration Readiness",
                "WARN",
                f"Limited external integration: {e}"
            ))
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL") 
        warned = sum(1 for r in self.results if r.status == "WARN")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        report = {
            "validation_summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "warned": warned,
                "skipped": skipped,
                "success_rate": success_rate
            },
            "results": self.results,
            "status": "READY" if failed == 0 else "NEEDS_WORK" if success_rate > 50 else "NOT_READY"
        }
        
        # Print detailed report
        print(f"\n📊 Validation Results")
        print(f"{'='*40}")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warned: {warned}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Overall Status: {report['status']}")
        
        print(f"\n📋 Detailed Results")
        print(f"{'='*40}")
        
        for result in self.results:
            status_emoji = {
                "PASS": "✅",
                "FAIL": "❌", 
                "WARN": "⚠️",
                "SKIP": "⏭️"
            }.get(result.status, "❓")
            
            print(f"{status_emoji} {result.name}: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    print(f"   └─ {key}: {value}")
        
        return report

def main():
    """Main validation function."""
    try:
        validator = ExponentialStateValidator()
        report = validator.validate_all()
        
        print(f"\n🎯 Next Steps")
        print(f"{'='*40}")
        
        if report["status"] == "READY":
            print("🚀 System is ready for external project validation!")
            print("   • Core exponential capabilities are operational")
            print("   • Ready for end-to-end telemetry testing")
            print("   • Can proceed with external project integration")
        elif report["status"] == "NEEDS_WORK":
            print("🔧 System needs some fixes but core functionality works")
            print("   • Address failed tests before full deployment")
            print("   • Core capabilities are mostly operational")
        else:
            print("⚠️  System needs significant work before deployment")
            print("   • Critical failures need to be addressed")
            print("   • Not ready for external validation")
        
        return 0 if report["status"] in ["READY", "NEEDS_WORK"] else 1
        
    except Exception as e:
        print(f"❌ Validation script failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())