#!/usr/bin/env python3
"""
External Project Workflow Validation
===================================

This script validates that uvmgr can successfully integrate with and enhance
external Python projects across the complete development lifecycle.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


class WorkflowValidator:
    """Validates uvmgr external project workflow integration."""
    
    def __init__(self):
        self.results = {
            "start_time": time.time(),
            "validator": "external_workflow",
            "validations": {},
            "summary": {}
        }
    
    def validate_auto_install(self, project_path: Path) -> Dict[str, Any]:
        """Validate auto-install script functionality."""
        validation = {
            "name": "auto_install",
            "description": "Validate uvmgr auto-install script",
            "success": False,
            "details": {}
        }
        
        try:
            # Test auto-install script
            script_path = Path(__file__).parent / "auto-install-uvmgr.sh"
            
            if not script_path.exists():
                validation["error"] = "Auto-install script not found"
                return validation
            
            # Run auto-install
            result = subprocess.run(
                ["bash", str(script_path), str(project_path)],
                capture_output=True, text=True, timeout=300
            )
            
            validation["details"]["returncode"] = result.returncode
            validation["details"]["stdout"] = result.stdout[:1000]
            validation["details"]["stderr"] = result.stderr[:1000]
            
            # Check if uvmgr was installed
            uvmgr_result = subprocess.run(
                ["uvmgr", "--version"],
                cwd=project_path,
                capture_output=True, text=True
            )
            
            validation["details"]["uvmgr_available"] = uvmgr_result.returncode == 0
            
            if uvmgr_result.returncode == 0:
                validation["details"]["uvmgr_version"] = uvmgr_result.stdout.strip()
            
            # Check for configuration files
            config_files = [".uvmgr.toml", ".uvmgr/examples/dev-workflow.sh"]
            validation["details"]["config_files"] = {}
            
            for config_file in config_files:
                file_path = project_path / config_file
                validation["details"]["config_files"][config_file] = file_path.exists()
            
            validation["success"] = (
                result.returncode == 0 and
                validation["details"]["uvmgr_available"] and
                validation["details"]["config_files"][".uvmgr.toml"]
            )
            
        except Exception as e:
            validation["error"] = str(e)
        
        return validation
    
    def validate_substrate_integration(self) -> Dict[str, Any]:
        """Validate Substrate template integration."""
        validation = {
            "name": "substrate_integration",
            "description": "Validate Substrate template integration with uvmgr",
            "success": False,
            "details": {}
        }
        
        try:
            # Test Substrate integration script
            script_path = Path(__file__).parent / "test-substrate-integration.sh"
            
            if not script_path.exists():
                validation["error"] = "Substrate integration script not found"
                return validation
            
            # Run with dry-run to validate script structure
            result = subprocess.run(
                ["bash", "-n", str(script_path)],  # Syntax check only
                capture_output=True, text=True
            )
            
            validation["details"]["syntax_check"] = result.returncode == 0
            
            if result.returncode != 0:
                validation["details"]["syntax_errors"] = result.stderr
            
            # Check for copier availability
            copier_result = subprocess.run(
                ["copier", "--version"],
                capture_output=True, text=True
            )
            
            validation["details"]["copier_available"] = copier_result.returncode == 0
            
            # Validate script has all required phases
            script_content = script_path.read_text()
            required_phases = [
                "Phase 1: Creating project with Substrate template",
                "Phase 2: Installing and configuring uvmgr",
                "Phase 3: Analyzing Substrate project configuration",
                "Phase 4: Enhancing Substrate project with uvmgr",
                "Phase 5: Testing complete Substrate + uvmgr workflow",
                "Phase 6: Workflow Comparison",
                "Phase 7: Integration Report"
            ]
            
            validation["details"]["required_phases"] = {}
            for phase in required_phases:
                validation["details"]["required_phases"][phase] = phase in script_content
            
            validation["success"] = (
                validation["details"]["syntax_check"] and
                all(validation["details"]["required_phases"].values())
            )
            
        except Exception as e:
            validation["error"] = str(e)
        
        return validation
    
    def validate_lifecycle_testing(self) -> Dict[str, Any]:
        """Validate lifecycle testing script."""
        validation = {
            "name": "lifecycle_testing",
            "description": "Validate comprehensive lifecycle testing",
            "success": False,
            "details": {}
        }
        
        try:
            # Test lifecycle script
            script_path = Path(__file__).parent / "test-lifecycle.py"
            
            if not script_path.exists():
                validation["error"] = "Lifecycle testing script not found"
                return validation
            
            # Validate script imports and syntax
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(script_path)],
                capture_output=True, text=True
            )
            
            validation["details"]["syntax_check"] = result.returncode == 0
            
            if result.returncode != 0:
                validation["details"]["syntax_errors"] = result.stderr
            
            # Test help functionality
            help_result = subprocess.run(
                [sys.executable, str(script_path), "--help"],
                capture_output=True, text=True
            )
            
            validation["details"]["help_available"] = help_result.returncode == 0
            
            # Check for required classes and methods
            script_content = script_path.read_text()
            required_components = [
                "class LifecycleTestRunner",
                "def test_project_setup",
                "def test_dependencies_phase",
                "def test_development_phase",
                "def test_testing_phase",
                "def test_building_phase",
                "def test_ai_integration_phase",
                "def test_observability_phase",
                "def test_release_phase"
            ]
            
            validation["details"]["required_components"] = {}
            for component in required_components:
                validation["details"]["required_components"][component] = component in script_content
            
            validation["success"] = (
                validation["details"]["syntax_check"] and
                validation["details"]["help_available"] and
                all(validation["details"]["required_components"].values())
            )
            
        except Exception as e:
            validation["error"] = str(e)
        
        return validation
    
    def validate_docker_compose(self) -> Dict[str, Any]:
        """Validate Docker Compose configuration."""
        validation = {
            "name": "docker_compose",
            "description": "Validate Docker Compose external testing setup",
            "success": False,
            "details": {}
        }
        
        try:
            # Check Docker Compose file
            compose_path = Path(__file__).parent / "docker-compose.external.yml"
            
            if not compose_path.exists():
                validation["error"] = "Docker Compose file not found"
                return validation
            
            # Parse and validate compose file
            import yaml
            
            with open(compose_path) as f:
                compose_config = yaml.safe_load(f)
            
            validation["details"]["version"] = compose_config.get("version")
            
            # Check required services
            required_services = [
                "uvmgr-external",
                "otel-collector", 
                "jaeger",
                "prometheus",
                "grafana"
            ]
            
            services = compose_config.get("services", {})
            validation["details"]["services"] = {}
            
            for service in required_services:
                validation["details"]["services"][service] = service in services
            
            # Check for required volumes and networks
            validation["details"]["has_volumes"] = "volumes" in compose_config
            validation["details"]["has_networks"] = "networks" in compose_config
            
            # Check Dockerfile
            dockerfile_path = Path(__file__).parent / "Dockerfile.external"
            validation["details"]["dockerfile_exists"] = dockerfile_path.exists()
            
            validation["success"] = (
                all(validation["details"]["services"].values()) and
                validation["details"]["has_volumes"] and
                validation["details"]["has_networks"] and
                validation["details"]["dockerfile_exists"]
            )
            
        except Exception as e:
            validation["error"] = str(e)
        
        return validation
    
    def validate_runner_script(self) -> Dict[str, Any]:
        """Validate the main runner script."""
        validation = {
            "name": "runner_script", 
            "description": "Validate main lifecycle test runner",
            "success": False,
            "details": {}
        }
        
        try:
            # Test runner script
            script_path = Path(__file__).parent / "run-lifecycle-tests.sh"
            
            if not script_path.exists():
                validation["error"] = "Runner script not found"
                return validation
            
            # Check syntax
            result = subprocess.run(
                ["bash", "-n", str(script_path)],
                capture_output=True, text=True
            )
            
            validation["details"]["syntax_check"] = result.returncode == 0
            
            if result.returncode != 0:
                validation["details"]["syntax_errors"] = result.stderr
            
            # Test help functionality
            help_result = subprocess.run(
                ["bash", str(script_path), "--help"],
                capture_output=True, text=True
            )
            
            validation["details"]["help_available"] = help_result.returncode == 0
            
            # Check for required functions
            script_content = script_path.read_text()
            required_functions = [
                "run_quick_test",
                "run_full_test", 
                "run_docker_tests",
                "run_substrate_test",
                "run_benchmark_test",
                "check_prerequisites",
                "setup_workspace"
            ]
            
            validation["details"]["required_functions"] = {}
            for func in required_functions:
                validation["details"]["required_functions"][func] = func in script_content
            
            validation["success"] = (
                validation["details"]["syntax_check"] and
                validation["details"]["help_available"] and
                all(validation["details"]["required_functions"].values())
            )
            
        except Exception as e:
            validation["error"] = str(e)
        
        return validation
    
    def validate_project_initialization(self) -> Dict[str, Any]:
        """Validate project initialization capabilities."""
        validation = {
            "name": "project_initialization",
            "description": "Validate uvmgr can initialize various project types",
            "success": False,
            "details": {}
        }
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                project_path = Path(tmpdir) / "test-project"
                project_path.mkdir()
                
                # Test auto-install in empty directory
                auto_install_result = self.validate_auto_install(project_path)
                validation["details"]["auto_install"] = auto_install_result["success"]
                
                # Test various project types can be created
                project_types = ["minimal", "fastapi"]
                validation["details"]["project_types"] = {}
                
                for proj_type in project_types:
                    type_dir = Path(tmpdir) / f"test-{proj_type}"
                    type_dir.mkdir()
                    
                    # Create minimal project structure
                    (type_dir / "pyproject.toml").write_text(f'''
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-{proj_type}"
version = "0.1.0"
''')
                    
                    # Test auto-install
                    result = self.validate_auto_install(type_dir)
                    validation["details"]["project_types"][proj_type] = result["success"]
                
                validation["success"] = (
                    validation["details"]["auto_install"] and
                    all(validation["details"]["project_types"].values())
                )
                
        except Exception as e:
            validation["error"] = str(e)
        
        return validation
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🔍 Running External Project Workflow Validations")
        print("=" * 50)
        
        validations = [
            ("substrate_integration", self.validate_substrate_integration),
            ("lifecycle_testing", self.validate_lifecycle_testing),
            ("docker_compose", self.validate_docker_compose),
            ("runner_script", self.validate_runner_script),
            ("project_initialization", self.validate_project_initialization)
        ]
        
        for name, validator in validations:
            print(f"\n🧪 Validating: {name}")
            result = validator()
            self.results["validations"][name] = result
            
            if result["success"]:
                print(f"✅ {result['description']}: PASS")
            else:
                print(f"❌ {result['description']}: FAIL")
                if "error" in result:
                    print(f"   Error: {result['error']}")
        
        # Generate summary
        total_validations = len(self.results["validations"])
        successful_validations = sum(
            1 for v in self.results["validations"].values() if v["success"]
        )
        
        self.results["summary"] = {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0,
            "overall_success": successful_validations == total_validations,
            "duration": time.time() - self.results["start_time"]
        }
        
        print(f"\n📊 Validation Summary")
        print(f"   Total: {total_validations}")
        print(f"   Passed: {successful_validations}")
        print(f"   Success Rate: {self.results['summary']['success_rate']:.1%}")
        print(f"   Overall: {'✅ PASS' if self.results['summary']['overall_success'] else '❌ FAIL'}")
        
        return self.results
    
    def save_results(self, output_path: Optional[Path] = None):
        """Save validation results to file."""
        if output_path is None:
            output_path = Path("external-workflow-validation-results.json")
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Validation results saved to: {output_path}")


def main():
    """Main validation entry point."""
    validator = WorkflowValidator()
    
    try:
        results = validator.run_all_validations()
        validator.save_results()
        
        # Exit with appropriate code
        success = results["summary"]["overall_success"]
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()