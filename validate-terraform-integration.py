#!/usr/bin/env python3
"""
Terraform Integration Validation
================================

Validate the uvmgr Terraform integration without Docker dependencies.
This tests the core functionality, template generation, and error handling.
"""

import tempfile
import time
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all Terraform modules import correctly."""
    try:
        from uvmgr.commands import terraform as terraform_cmd
        from uvmgr.ops import terraform as terraform_ops
        from uvmgr.core.instrumentation import add_span_attributes, add_span_event
        from uvmgr.core.semconv import CliAttributes
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_command_functions():
    """Test that command functions exist."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        expected_operations = [
            "terraform_init", "terraform_plan", "terraform_apply", 
            "terraform_destroy", "terraform_workspace", "terraform_generate", 
            "terraform_validate"
        ]
        
        for op in expected_operations:
            assert hasattr(terraform_ops, op), f"Missing operation: {op}"
        
        print(f"✅ All {len(expected_operations)} operation functions exist")
        return True
    except Exception as e:
        print(f"❌ Operation functions test failed: {e}")
        return False

def test_template_generation():
    """Test Terraform template generation."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'template': 'aws-vpc',
                'name': 'test-vpc',
                'provider': 'aws',
                'output_dir': Path(temp_dir),
                'variables': {'cidr_block': '10.0.0.0/16'},
                'dry_run': False,
            }
            
            result = terraform_ops.terraform_generate(config)
            
            assert result.get('success'), f"Template generation failed: {result.get('error')}"
            
            files = result.get('files', [])
            assert len(files) > 0, "No files generated"
            
            # Check main.tf was created
            main_tf_found = any('main.tf' in f['path'] for f in files)
            assert main_tf_found, "main.tf not generated"
            
            # Verify file contents
            main_tf_path = Path(temp_dir) / 'main.tf'
            if main_tf_path.exists():
                content = main_tf_path.read_text()
                assert 'aws_vpc' in content, "VPC resource not found"
                assert 'test-vpc' in content, "VPC name not found"
        
        print("✅ Template generation successful")
        return True
    except Exception as e:
        print(f"❌ Template generation failed: {e}")
        return False

def test_multiple_templates():
    """Test multiple template types."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        templates = [
            ('aws-vpc', 'aws'),
            ('k8s-cluster', 'aws'),
        ]
        
        for template, provider in templates:
            with tempfile.TemporaryDirectory() as temp_dir:
                config = {
                    'template': template,
                    'name': f'test-{template}',
                    'provider': provider,
                    'output_dir': Path(temp_dir),
                    'variables': {},
                    'dry_run': True,
                }
                
                result = terraform_ops.terraform_generate(config)
                assert result.get('success'), f"{template} template failed: {result.get('error')}"
        
        print(f"✅ Multiple template types tested successfully")
        return True
    except Exception as e:
        print(f"❌ Multiple templates test failed: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid inputs."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        # Test invalid template
        config = {
            'template': 'invalid-template',
            'name': 'test',
            'provider': 'aws',
            'output_dir': Path('/tmp'),
            'dry_run': True,
        }
        
        result = terraform_ops.terraform_generate(config)
        assert not result.get('success'), "Invalid template should fail"
        assert 'error' in result, "Error should be reported"
        
        print("✅ Error handling working correctly")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_performance():
    """Test performance of operations."""
    try:
        from uvmgr.ops import terraform as terraform_ops
        
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'template': 'aws-vpc',
                'name': 'perf-test',
                'provider': 'aws',
                'output_dir': Path(temp_dir),
                'variables': {},
                'dry_run': True,
            }
            
            result = terraform_ops.terraform_generate(config)
            
        duration = time.time() - start_time
        
        assert result.get('success'), "Performance test operation failed"
        assert duration < 2.0, f"Operation too slow: {duration:.3f}s"
        
        print(f"✅ Performance test passed ({duration:.3f}s)")
        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def test_otel_instrumentation():
    """Test OTEL instrumentation."""
    try:
        from uvmgr.core.instrumentation import add_span_attributes, add_span_event
        from uvmgr.core.telemetry import span
        from uvmgr.core.semconv import CliAttributes
        
        # Test span creation
        with span('terraform_validation_test'):
            add_span_attributes(**{
                CliAttributes.COMMAND: 'terraform_validation',
                'test.type': 'integration',
            })
            
            add_span_event('test.completed', {
                'success': True,
                'test_name': 'otel_instrumentation'
            })
        
        print("✅ OTEL instrumentation working")
        return True
    except Exception as e:
        print(f"❌ OTEL instrumentation failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 uvmgr Terraform Integration Validation")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Command Functions Test", test_command_functions),
        ("Template Generation Test", test_template_generation),
        ("Multiple Templates Test", test_multiple_templates),
        ("Error Handling Test", test_error_handling),
        ("Performance Test", test_performance),
        ("OTEL Instrumentation Test", test_otel_instrumentation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Validation Summary")
    print("=" * 50)
    
    success_rate = (passed / total) * 100
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ✅ All tests passed!")
        print("🚀 uvmgr Terraform integration is ready for production!")
        return 0
    elif success_rate >= 80:
        print(f"\n⚠️  Most tests passed ({success_rate:.1f}%)")
        print("Review failures and re-test")
        return 1
    else:
        print(f"\n❌ Many tests failed ({success_rate:.1f}%)")
        print("Significant issues need to be addressed")
        return 2

if __name__ == "__main__":
    exit(main())