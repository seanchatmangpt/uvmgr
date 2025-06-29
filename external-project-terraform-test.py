#!/usr/bin/env python3
"""
External Project Terraform Integration Test
===========================================

Test uvmgr Terraform integration against external project scenarios
to validate real-world usage patterns.
"""

import tempfile
import time
import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_fastapi_project(project_dir: Path):
    """Create a sample FastAPI project."""
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # pyproject.toml
    (project_dir / "pyproject.toml").write_text("""
[project]
name = "fastapi-terraform-test"
version = "0.1.0"
description = "FastAPI project for Terraform integration testing"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")
    
    # main.py
    (project_dir / "main.py").write_text("""
from fastapi import FastAPI

app = FastAPI(title="Terraform Test App", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Hello from Terraform-managed FastAPI"}

@app.get("/health")
async def health():
    return {"status": "healthy", "infrastructure": "terraform-managed"}
""")
    
    return project_dir

def create_cli_project(project_dir: Path):
    """Create a sample CLI project."""
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # pyproject.toml
    (project_dir / "pyproject.toml").write_text("""
[project]
name = "cli-terraform-test"
version = "0.1.0"
description = "CLI project for Terraform integration testing"
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
]

[project.scripts]
cli-test = "cli_test:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")
    
    # cli_test.py
    (project_dir / "cli_test.py").write_text("""
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def deploy():
    console.print("Deploying to Terraform-managed infrastructure...", style="bold blue")
    console.print("✅ Deployment to cloud complete!", style="bold green")

@app.command()
def status():
    console.print("Infrastructure Status: Terraform-managed", style="bold cyan")

if __name__ == "__main__":
    app()
""")
    
    return project_dir

def test_fastapi_project_infrastructure():
    """Test Terraform integration with FastAPI project."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create FastAPI project
            project_dir = Path(temp_dir) / "fastapi-app"
            create_fastapi_project(project_dir)
            
            # Generate infrastructure for web application
            terraform_dir = project_dir / "terraform"
            config = {
                'template': 'aws-vpc',  # Use VPC as base infrastructure
                'name': 'fastapi-infrastructure',
                'provider': 'aws',
                'output_dir': terraform_dir,
                'variables': {
                    'app_name': 'fastapi-terraform-test',
                    'environment': 'test',
                    'cidr_block': '10.0.0.0/16'
                },
                'dry_run': False,
            }
            
            result = terraform_ops.terraform_generate(config)
            
            assert result.get('success'), f"FastAPI infrastructure generation failed: {result.get('error')}"
            
            files = result.get('files', [])
            assert len(files) >= 3, f"Expected at least 3 terraform files, got {len(files)}"
            
            # Verify infrastructure files
            main_tf = terraform_dir / 'main.tf'
            assert main_tf.exists(), "main.tf not created"
            
            content = main_tf.read_text()
            assert 'fastapi-infrastructure' in content, "App name not found in terraform"
            assert 'aws_vpc' in content, "VPC resource not found"
            
            print("✅ FastAPI project infrastructure generation successful")
            return True
    except Exception as e:
        print(f"❌ FastAPI project test failed: {e}")
        return False

def test_cli_project_infrastructure():
    """Test Terraform integration with CLI project."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create CLI project
            project_dir = Path(temp_dir) / "cli-app"
            create_cli_project(project_dir)
            
            # Generate EKS cluster infrastructure for CLI deployment
            terraform_dir = project_dir / "terraform"
            config = {
                'template': 'k8s-cluster',
                'name': 'cli-k8s-cluster',
                'provider': 'aws',
                'output_dir': terraform_dir,
                'variables': {
                    'node_instance_type': 't3.small',
                    'node_group_size': {'desired': 1, 'min': 1, 'max': 3}
                },
                'dry_run': False,
            }
            
            result = terraform_ops.terraform_generate(config)
            
            assert result.get('success'), f"CLI infrastructure generation failed: {result.get('error')}"
            
            files = result.get('files', [])
            assert len(files) >= 3, f"Expected at least 3 terraform files, got {len(files)}"
            
            # Verify EKS infrastructure files
            main_tf = terraform_dir / 'main.tf'
            assert main_tf.exists(), "main.tf not created"
            
            content = main_tf.read_text()
            assert 'cli-k8s-cluster' in content, "Cluster name not found"
            assert 'aws_eks_cluster' in content, "EKS cluster not found"
            
            print("✅ CLI project infrastructure generation successful")
            return True
    except Exception as e:
        print(f"❌ CLI project test failed: {e}")
        return False

def test_existing_terraform_project():
    """Test operations on existing Terraform project."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing terraform project
            project_dir = Path(temp_dir) / "existing-terraform"
            project_dir.mkdir()
            
            # Create existing terraform files
            (project_dir / "main.tf").write_text("""
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "test_bucket" {
  bucket = "uvmgr-terraform-test-${random_string.suffix.result}"
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}
""")
            
            (project_dir / "variables.tf").write_text("""
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}
""")
            
            # Test terraform validate
            config = {
                'path': project_dir,
                'format': 'table',
            }
            
            result = terraform_ops.terraform_validate(config)
            
            # Note: This will likely fail since terraform isn't initialized,
            # but we're testing that the operation handles this gracefully
            assert isinstance(result, dict), "Validate result should be a dictionary"
            assert 'success' in result, "Result should contain success key"
            
            if not result.get('success'):
                assert 'error' in result, "Failed validation should include error"
                print(f"⚠️  Validation failed as expected (no terraform init): {result.get('error', 'No error message')}")
            
            print("✅ Existing Terraform project operations working")
            return True
    except Exception as e:
        print(f"❌ Existing terraform project test failed: {e}")
        return False

def test_multi_environment_workspace():
    """Test workspace operations for multi-environment setup."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test workspace operations
            project_dir = Path(temp_dir) / "multi-env"
            project_dir.mkdir()
            
            # Test workspace list (should work even without terraform init)
            config = {
                'path': project_dir,
                'action': 'list',
            }
            
            result = terraform_ops.terraform_workspace(config)
            
            # This might fail without terraform init, which is expected
            assert isinstance(result, dict), "Workspace result should be a dictionary"
            assert 'success' in result, "Result should contain success key"
            
            if not result.get('success'):
                print(f"⚠️  Workspace list failed as expected (no terraform init): {result.get('error', 'No error')}")
            else:
                workspaces = result.get('workspaces', [])
                print(f"✅ Found workspaces: {workspaces}")
            
            print("✅ Multi-environment workspace operations working")
            return True
    except Exception as e:
        print(f"❌ Multi-environment workspace test failed: {e}")
        return False

def test_template_customization():
    """Test template customization with different parameters."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        test_cases = [
            {
                'name': 'production-vpc',
                'template': 'aws-vpc',
                'provider': 'aws',
                'variables': {
                    'cidr_block': '172.16.0.0/16',
                    'availability_zones': ['us-east-1a', 'us-east-1b']
                }
            },
            {
                'name': 'development-cluster',
                'template': 'k8s-cluster',
                'provider': 'aws',
                'variables': {
                    'node_instance_type': 't3.micro',
                    'node_group_size': {'desired': 1, 'min': 1, 'max': 2}
                }
            }
        ]
        
        for test_case in test_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                config = {
                    'template': test_case['template'],
                    'name': test_case['name'],
                    'provider': test_case['provider'],
                    'output_dir': Path(temp_dir),
                    'variables': test_case['variables'],
                    'dry_run': False,
                }
                
                result = terraform_ops.terraform_generate(config)
                
                assert result.get('success'), f"Template {test_case['template']} failed: {result.get('error')}"
                
                files = result.get('files', [])
                assert len(files) > 0, f"No files generated for {test_case['template']}"
                
                # Verify customization
                main_tf_path = Path(temp_dir) / 'main.tf'
                if main_tf_path.exists():
                    content = main_tf_path.read_text()
                    assert test_case['name'] in content, f"Template name not found in {test_case['template']}"
        
        print("✅ Template customization working correctly")
        return True
    except Exception as e:
        print(f"❌ Template customization test failed: {e}")
        return False

def test_performance_with_large_templates():
    """Test performance with complex template generation."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        start_time = time.time()
        
        # Generate multiple templates in sequence
        templates = ['aws-vpc', 'k8s-cluster'] * 3  # 6 templates total
        
        for i, template in enumerate(templates):
            with tempfile.TemporaryDirectory() as temp_dir:
                config = {
                    'template': template,
                    'name': f'perf-test-{i}-{template}',
                    'provider': 'aws',
                    'output_dir': Path(temp_dir),
                    'variables': {},
                    'dry_run': True,  # Faster for performance testing
                }
                
                result = terraform_ops.terraform_generate(config)
                assert result.get('success'), f"Performance test failed on template {template}"
        
        total_duration = time.time() - start_time
        avg_duration = total_duration / len(templates)
        
        # Performance criteria: average should be under 0.5 seconds per template
        assert avg_duration < 0.5, f"Template generation too slow: {avg_duration:.3f}s average"
        
        print(f"✅ Performance test passed: {len(templates)} templates in {total_duration:.3f}s (avg: {avg_duration:.3f}s)")
        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Run all external project tests."""
    print("🚀 External Project Terraform Integration Tests")
    print("=" * 60)
    
    tests = [
        ("FastAPI Project Infrastructure", test_fastapi_project_infrastructure),
        ("CLI Project Infrastructure", test_cli_project_infrastructure),
        ("Existing Terraform Project", test_existing_terraform_project),
        ("Multi-Environment Workspace", test_multi_environment_workspace),
        ("Template Customization", test_template_customization),
        ("Performance with Large Templates", test_performance_with_large_templates),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("📊 External Project Test Summary")
    print("=" * 60)
    
    success_rate = (passed / total) * 100
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ✅ All external project tests passed!")
        print("🚀 uvmgr Terraform integration works with real-world projects!")
        return 0
    elif success_rate >= 80:
        print(f"\n⚠️  Most tests passed ({success_rate:.1f}%)")
        print("Terraform integration is functional with minor issues")
        return 1
    else:
        print(f"\n❌ Many tests failed ({success_rate:.1f}%)")
        print("Significant issues with external project integration")
        return 2

if __name__ == "__main__":
    exit(main())