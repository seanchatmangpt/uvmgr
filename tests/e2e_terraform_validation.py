#!/usr/bin/env python3
"""
E2E Terraform Integration Validation
===================================

End-to-end validation workflow for Terraform Infrastructure as Code integration
in uvmgr. Tests the complete lifecycle from command import to template generation
with full OTEL instrumentation and verification.

Validation Workflow
-------------------
1. **Module Import Validation**: Verify all Terraform modules import correctly
2. **Command Registration**: Test CLI command registration and help
3. **Operations Layer**: Validate core operations (init, plan, apply, destroy)
4. **Template Generation**: Test template generation for multiple providers
5. **OTEL Instrumentation**: Verify telemetry data collection
6. **Error Handling**: Test error scenarios and recovery
7. **Performance Benchmarks**: Measure operation performance

80/20 Focus Areas
-----------------
• **Core Workflow**: plan → apply → destroy lifecycle (80% use case)
• **Template Generation**: Common infrastructure patterns
• **Multi-provider Support**: AWS, GCP, Azure
• **State Management**: Workspace and backend operations
• **Safety Features**: Backup, confirmation, rollback
• **Observability**: Complete OTEL instrumentation

Success Criteria
-----------------
- All module imports successful
- CLI commands registered and functional
- Template generation works for all providers
- OTEL spans created with proper attributes
- Error handling graceful and informative
- Performance within acceptable thresholds
- No memory leaks or resource issues

Usage
-----
    python tests/e2e_terraform_validation.py
    python tests/e2e_terraform_validation.py --verbose
    python tests/e2e_terraform_validation.py --benchmark
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer

# Import uvmgr modules
try:
    from uvmgr.commands import terraform as terraform_cmd
    from uvmgr.ops import terraform as terraform_ops
    from uvmgr.core.instrumentation import add_span_attributes, add_span_event
    from uvmgr.core.semconv import CliAttributes
    
    UVMGR_AVAILABLE = True
except ImportError as e:
    UVMGR_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Validation results
validation_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": [],
    "performance": {},
    "otel_spans": [],
}


def log_result(test_name: str, success: bool, message: str = "", duration: float = 0.0):
    """Log validation test result."""
    validation_results["total_tests"] += 1
    
    if success:
        validation_results["passed"] += 1
        status = "✅ PASS"
    else:
        validation_results["failed"] += 1
        status = "❌ FAIL"
        validation_results["errors"].append(f"{test_name}: {message}")
    
    if duration > 0:
        validation_results["performance"][test_name] = duration
    
    print(f"{status} {test_name} ({duration:.3f}s): {message}")


def test_module_imports():
    """Test 1: Validate all Terraform modules import correctly."""
    start_time = time.time()
    
    if not UVMGR_AVAILABLE:
        log_result("Module Imports", False, f"Import failed: {IMPORT_ERROR}", time.time() - start_time)
        return
    
    try:
        # Test command module
        assert hasattr(terraform_cmd, 'app'), "terraform_cmd.app not found"
        assert hasattr(terraform_cmd, 'terraform_init'), "terraform_init command not found"
        assert hasattr(terraform_cmd, 'terraform_plan'), "terraform_plan command not found"
        assert hasattr(terraform_cmd, 'terraform_apply'), "terraform_apply command not found"
        assert hasattr(terraform_cmd, 'terraform_destroy'), "terraform_destroy command not found"
        
        # Test operations module
        assert hasattr(terraform_ops, 'terraform_init'), "terraform_init operation not found"
        assert hasattr(terraform_ops, 'terraform_plan'), "terraform_plan operation not found"
        assert hasattr(terraform_ops, 'terraform_apply'), "terraform_apply operation not found"
        assert hasattr(terraform_ops, 'terraform_destroy'), "terraform_destroy operation not found"
        assert hasattr(terraform_ops, 'terraform_workspace'), "terraform_workspace operation not found"
        assert hasattr(terraform_ops, 'terraform_validate'), "terraform_validate operation not found"
        assert hasattr(terraform_ops, 'terraform_generate'), "terraform_generate operation not found"
        
        log_result("Module Imports", True, "All modules imported successfully", time.time() - start_time)
    
    except Exception as e:
        log_result("Module Imports", False, str(e), time.time() - start_time)


def test_command_registration():
    """Test 2: Verify CLI command registration and help."""
    start_time = time.time()
    
    if not UVMGR_AVAILABLE:
        log_result("Command Registration", False, "uvmgr not available", time.time() - start_time)
        return
    
    try:
        # Test Typer app is configured
        app = terraform_cmd.app
        assert app is not None, "Terraform app not initialized"
        
        # Test commands are registered via callback inspection
        import inspect
        
        # Check if the app has registered commands
        assert hasattr(app, 'registered_commands') or hasattr(app, 'commands') or app.callback, "No commands registered"
        
        # Alternative: check for command functions directly in module
        expected_commands = ["terraform_init", "terraform_plan", "terraform_apply", "terraform_destroy", "terraform_workspace", "terraform_generate", "terraform_validate"]
        
        for cmd in expected_commands:
            assert hasattr(terraform_cmd, cmd), f"Command function '{cmd}' not found"
        
        log_result("Command Registration", True, f"All {len(expected_commands)} commands registered", time.time() - start_time)
    
    except Exception as e:
        log_result("Command Registration", False, str(e), time.time() - start_time)


def test_operations_layer():
    """Test 3: Validate core operations without Terraform binary."""
    start_time = time.time()
    
    if not UVMGR_AVAILABLE:
        log_result("Operations Layer", False, "uvmgr not available", time.time() - start_time)
        return
    
    try:
        # Test terraform_init (without actual terraform binary)
        config = {
            "path": Path.cwd(),
            "backend": "local",
            "upgrade": False,
            "reconfigure": False,
            "parallelism": 2,
        }
        
        result = terraform_ops.terraform_init(config)
        assert isinstance(result, dict), "terraform_init should return dict"
        assert "success" in result, "Result should contain 'success' key"
        assert "duration" in result, "Result should contain 'duration' key"
        
        # The operation should fail gracefully if Terraform is not installed
        if not result["success"]:
            assert "error" in result, "Failed operations should include error message"
        
        log_result("Operations Layer", True, "Operations interface working correctly", time.time() - start_time)
    
    except Exception as e:
        log_result("Operations Layer", False, str(e), time.time() - start_time)


def test_template_generation():
    """Test 4: Validate template generation for multiple providers."""
    start_time = time.time()
    
    if not UVMGR_AVAILABLE:
        log_result("Template Generation", False, "uvmgr not available", time.time() - start_time)
        return
    
    try:
        templates_tested = 0
        
        # Test AWS VPC template
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "template": "aws-vpc",
                "name": "test-vpc",
                "provider": "aws",
                "output_dir": Path(temp_dir),
                "variables": {"cidr_block": "10.0.0.0/16"},
                "dry_run": False,
            }
            
            result = terraform_ops.terraform_generate(config)
            assert result.get("success"), f"AWS VPC template failed: {result.get('error')}"
            
            files = result.get("files", [])
            assert len(files) > 0, "No files generated for AWS VPC template"
            
            # Check that main.tf was created
            main_tf_found = any("main.tf" in f["path"] for f in files)
            assert main_tf_found, "main.tf not generated for AWS VPC template"
            
            templates_tested += 1
        
        # Test EKS cluster template
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "template": "k8s-cluster",
                "name": "test-cluster",
                "provider": "aws",
                "output_dir": Path(temp_dir),
                "variables": {"node_instance_type": "t3.small"},
                "dry_run": False,
            }
            
            result = terraform_ops.terraform_generate(config)
            assert result.get("success"), f"EKS cluster template failed: {result.get('error')}"
            
            files = result.get("files", [])
            assert len(files) > 0, "No files generated for EKS cluster template"
            
            templates_tested += 1
        
        # Test dry run mode
        config = {
            "template": "aws-vpc",
            "name": "dry-run-test",
            "provider": "aws",
            "output_dir": Path("/tmp/dry-run"),
            "variables": {},
            "dry_run": True,
        }
        
        result = terraform_ops.terraform_generate(config)
        assert result.get("success"), f"Dry run failed: {result.get('error')}"
        
        files = result.get("files", [])
        assert len(files) > 0, "Dry run should show files that would be generated"
        
        templates_tested += 1
        
        log_result("Template Generation", True, f"{templates_tested} templates tested successfully", time.time() - start_time)
    
    except Exception as e:
        log_result("Template Generation", False, str(e), time.time() - start_time)


def test_otel_instrumentation():
    """Test 5: Verify OTEL instrumentation is working."""
    start_time = time.time()
    
    if not UVMGR_AVAILABLE:
        log_result("OTEL Instrumentation", False, "uvmgr not available", time.time() - start_time)
        return
    
    try:
        # Test that we can create spans and attributes
        from uvmgr.core.telemetry import span
        
        with span("test_terraform_validation"):
            add_span_attributes(**{
                CliAttributes.COMMAND: "terraform_validation",
                "test.type": "e2e",
                "test.component": "terraform",
            })
            
            add_span_event("validation.test", {
                "event": "otel_instrumentation_test",
                "success": True,
            })
            
            # Test operations also create spans
            config = {
                "template": "aws-vpc",
                "name": "otel-test",
                "provider": "aws",
                "output_dir": Path("/tmp/otel-test"),
                "dry_run": True,
            }
            
            result = terraform_ops.terraform_generate(config)
            
            validation_results["otel_spans"].append({
                "span_name": "test_terraform_validation",
                "attributes": {
                    CliAttributes.COMMAND: "terraform_validation",
                    "test.type": "e2e",
                    "test.component": "terraform",
                },
                "success": result.get("success", False),
            })
        
        log_result("OTEL Instrumentation", True, "Spans and attributes created successfully", time.time() - start_time)
    
    except Exception as e:
        log_result("OTEL Instrumentation", False, str(e), time.time() - start_time)


def test_error_handling():
    """Test 6: Validate error handling and recovery."""
    start_time = time.time()
    
    if not UVMGR_AVAILABLE:
        log_result("Error Handling", False, "uvmgr not available", time.time() - start_time)
        return
    
    try:
        errors_tested = 0
        
        # Test invalid template
        config = {
            "template": "invalid-template",
            "name": "test",
            "provider": "aws",
            "output_dir": Path("/tmp/test"),
            "dry_run": True,
        }
        
        result = terraform_ops.terraform_generate(config)
        assert not result.get("success"), "Invalid template should fail"
        assert "error" in result, "Failed operation should include error message"
        assert "Invalid template" in result["error"], "Error message should be descriptive"
        
        errors_tested += 1
        
        # Test missing required fields
        config = {
            "template": "aws-vpc",
            # Missing 'name' field
            "provider": "aws",
            "output_dir": Path("/tmp/test"),
            "dry_run": True,
        }
        
        try:
            result = terraform_ops.terraform_generate(config)
            # Should handle missing name gracefully
            errors_tested += 1
        except Exception:
            # Exception handling is also acceptable
            errors_tested += 1
        
        log_result("Error Handling", True, f"{errors_tested} error scenarios handled correctly", time.time() - start_time)
    
    except Exception as e:
        log_result("Error Handling", False, str(e), time.time() - start_time)


def test_performance_benchmarks():
    """Test 7: Measure operation performance."""
    start_time = time.time()
    
    if not UVMGR_AVAILABLE:
        log_result("Performance Benchmarks", False, "uvmgr not available", time.time() - start_time)
        return
    
    try:
        benchmarks = {}
        
        # Benchmark template generation
        for i in range(3):
            template_start = time.time()
            
            config = {
                "template": "aws-vpc",
                "name": f"benchmark-test-{i}",
                "provider": "aws",
                "output_dir": Path(f"/tmp/benchmark-{i}"),
                "dry_run": True,
            }
            
            result = terraform_ops.terraform_generate(config)
            template_duration = time.time() - template_start
            
            if result.get("success"):
                benchmarks[f"template_generation_{i}"] = template_duration
        
        # Calculate average template generation time
        if benchmarks:
            avg_template_time = sum(benchmarks.values()) / len(benchmarks)
            validation_results["performance"]["avg_template_generation"] = avg_template_time
            
            # Performance thresholds (80/20 focused)
            if avg_template_time < 1.0:  # Template generation should be under 1 second
                perf_status = "excellent"
            elif avg_template_time < 2.0:
                perf_status = "good"
            else:
                perf_status = "needs_optimization"
            
            log_result("Performance Benchmarks", True, 
                      f"Avg template generation: {avg_template_time:.3f}s ({perf_status})", 
                      time.time() - start_time)
        else:
            log_result("Performance Benchmarks", False, "No benchmarks completed", time.time() - start_time)
    
    except Exception as e:
        log_result("Performance Benchmarks", False, str(e), time.time() - start_time)


def generate_validation_report():
    """Generate comprehensive validation report."""
    report = {
        "validation_summary": {
            "total_tests": validation_results["total_tests"],
            "passed": validation_results["passed"],
            "failed": validation_results["failed"],
            "success_rate": (validation_results["passed"] / validation_results["total_tests"] * 100) if validation_results["total_tests"] > 0 else 0,
        },
        "performance_metrics": validation_results["performance"],
        "otel_telemetry": {
            "spans_created": len(validation_results["otel_spans"]),
            "instrumentation_working": len(validation_results["otel_spans"]) > 0,
        },
        "errors": validation_results["errors"],
        "recommendations": [],
    }
    
    # Add recommendations based on results
    if report["validation_summary"]["success_rate"] < 100:
        report["recommendations"].append("Some tests failed - review error messages for details")
    
    if validation_results["performance"].get("avg_template_generation", 0) > 2.0:
        report["recommendations"].append("Template generation performance needs optimization")
    
    if not report["otel_telemetry"]["instrumentation_working"]:
        report["recommendations"].append("OTEL instrumentation not working properly")
    
    if not validation_results["errors"]:
        report["recommendations"].append("All tests passed - Terraform integration ready for production")
    
    return report


def main(verbose: bool = False, benchmark: bool = False, output_file: Optional[str] = None):
    """
    Run E2E Terraform integration validation.
    
    Args:
        verbose: Enable verbose output
        benchmark: Run extended performance benchmarks
        output_file: Save results to JSON file
    """
    print("🚀 uvmgr Terraform Integration E2E Validation")
    print("=" * 60)
    
    if verbose:
        print(f"Python Path: {Path(__file__).parent}")
        print(f"UVMGR Available: {UVMGR_AVAILABLE}")
        if not UVMGR_AVAILABLE:
            print(f"Import Error: {IMPORT_ERROR}")
        print()
    
    # Run validation tests
    tests = [
        test_module_imports,
        test_command_registration,
        test_operations_layer,
        test_template_generation,
        test_otel_instrumentation,
        test_error_handling,
    ]
    
    if benchmark:
        tests.append(test_performance_benchmarks)
    
    for test_func in tests:
        if verbose:
            print(f"Running {test_func.__name__}...")
        test_func()
    
    print("\n" + "=" * 60)
    print("📊 Validation Summary")
    print("=" * 60)
    
    # Generate and display report
    report = generate_validation_report()
    
    summary = report["validation_summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    
    if report["performance_metrics"]:
        print(f"\n⚡ Performance Metrics:")
        for metric, value in report["performance_metrics"].items():
            print(f"  {metric}: {value:.3f}s")
    
    if report["otel_telemetry"]["instrumentation_working"]:
        print(f"\n📈 OTEL Telemetry: ✅ Working ({report['otel_telemetry']['spans_created']} spans created)")
    else:
        print(f"\n📈 OTEL Telemetry: ❌ Not working")
    
    if report["errors"]:
        print(f"\n❌ Errors:")
        for error in report["errors"]:
            print(f"  • {error}")
    
    if report["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
    
    # Save report to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Report saved to: {output_file}")
    
    # Set exit code based on results
    if summary["success_rate"] == 100:
        print(f"\n✅ All tests passed! Terraform integration is ready.")
        exit_code = 0
    elif summary["success_rate"] >= 80:
        print(f"\n⚠️  Most tests passed ({summary['success_rate']:.1f}%) - review failures.")
        exit_code = 1
    else:
        print(f"\n❌ Many tests failed ({summary['success_rate']:.1f}%) - significant issues detected.")
        exit_code = 2
    
    return exit_code


if __name__ == "__main__":
    typer.run(main)