#!/bin/bash
set -e

echo "🐳 Starting Cleanroom Terraform Integration Tests"
echo "================================================="

# Test environment info
echo "📋 Environment Information:"
echo "Python version: $(python --version)"
echo "Terraform version: $(terraform version | head -1)"
echo "uv version: $(uv --version)"
echo "Working directory: $(pwd)"
echo ""

# Test 1: Basic uvmgr installation
echo "🔧 Test 1: uvmgr Installation Verification"
echo "-------------------------------------------"
python -c "import uvmgr; print('✅ uvmgr imported successfully')" || {
    echo "❌ Failed to import uvmgr"
    exit 1
}

# Test 2: Terraform command availability  
echo ""
echo "🔧 Test 2: Terraform Command Registration"
echo "------------------------------------------"
python -c "
try:
    from uvmgr.commands import terraform
    print('✅ Terraform command module imported')
    
    # Check command functions exist
    commands = ['terraform_init', 'terraform_plan', 'terraform_apply', 'terraform_destroy', 'terraform_workspace', 'terraform_generate', 'terraform_validate']
    for cmd in commands:
        assert hasattr(terraform, cmd), f'Missing command: {cmd}'
    print(f'✅ All {len(commands)} terraform commands available')
    
except Exception as e:
    print(f'❌ Terraform command test failed: {e}')
    exit(1)
" || exit 1

# Test 3: Operations layer functionality
echo ""
echo "🔧 Test 3: Operations Layer Verification"
echo "-----------------------------------------"
python -c "
try:
    from uvmgr.ops import terraform as tf_ops
    
    # Test terraform_validate (doesn't require terraform to be configured)
    config = {'path': '/tmp/test-tf', 'format': 'table'}
    result = tf_ops.terraform_validate(config)
    
    assert isinstance(result, dict), 'Result should be a dictionary'
    assert 'success' in result, 'Result should contain success key'
    print('✅ Operations layer working correctly')
    
except Exception as e:
    print(f'❌ Operations test failed: {e}')
    exit(1)
" || exit 1

# Test 4: Template generation
echo ""
echo "🔧 Test 4: Template Generation"
echo "-------------------------------"
python -c "
import tempfile
from pathlib import Path
from uvmgr.ops import terraform as tf_ops

try:
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {
            'template': 'aws-vpc',
            'name': 'cleanroom-test-vpc',
            'provider': 'aws',
            'output_dir': Path(temp_dir),
            'variables': {'cidr_block': '10.0.0.0/16'},
            'dry_run': False,
        }
        
        result = tf_ops.terraform_generate(config)
        
        assert result.get('success'), f'Template generation failed: {result.get(\"error\")}'
        
        files = result.get('files', [])
        assert len(files) > 0, 'No files generated'
        
        # Check main.tf was created
        main_tf_found = any('main.tf' in f['path'] for f in files)
        assert main_tf_found, 'main.tf not generated'
        
        print(f'✅ Generated {len(files)} template files')
        
        # Verify file contents
        main_tf_path = Path(temp_dir) / 'main.tf'
        if main_tf_path.exists():
            content = main_tf_path.read_text()
            assert 'aws_vpc' in content, 'VPC resource not found in template'
            assert 'cleanroom-test-vpc' in content, 'Resource name not found'
            print('✅ Template content validation passed')
        
except Exception as e:
    print(f'❌ Template generation test failed: {e}')
    exit(1)
" || exit 1

# Test 5: External project simulation
echo ""
echo "🔧 Test 5: External Project Integration"
echo "----------------------------------------"
/test-scripts/test-external-projects.sh

# Test 6: OTEL instrumentation
echo ""
echo "🔧 Test 6: OTEL Instrumentation"
echo "--------------------------------"
python -c "
try:
    from uvmgr.core.instrumentation import add_span_attributes, add_span_event
    from uvmgr.core.telemetry import span
    from uvmgr.core.semconv import CliAttributes
    
    # Test span creation
    with span('cleanroom_test'):
        add_span_attributes(**{
            CliAttributes.COMMAND: 'terraform_cleanroom_test',
            'test.environment': 'docker',
            'test.type': 'cleanroom'
        })
        
        add_span_event('test.completed', {
            'success': True,
            'environment': 'cleanroom'
        })
    
    print('✅ OTEL instrumentation working')
    
except Exception as e:
    print(f'❌ OTEL test failed: {e}')
    exit(1)
" || exit 1

# Test 7: Performance benchmarks
echo ""
echo "🔧 Test 7: Performance Benchmarks"
echo "----------------------------------"
/test-scripts/performance-benchmarks.sh

# Test 8: Error handling
echo ""
echo "🔧 Test 8: Error Handling"
echo "--------------------------"
python -c "
from uvmgr.ops import terraform as tf_ops

try:
    # Test invalid template
    config = {
        'template': 'invalid-template',
        'name': 'test',
        'provider': 'aws',
        'output_dir': '/tmp/test',
        'dry_run': True,
    }
    
    result = tf_ops.terraform_generate(config)
    assert not result.get('success'), 'Invalid template should fail'
    assert 'error' in result, 'Failed operation should include error message'
    print('✅ Error handling working correctly')
    
except Exception as e:
    print(f'❌ Error handling test failed: {e}')
    exit(1
" || exit 1

echo ""
echo "🎉 All Cleanroom Tests Passed!"
echo "=============================="
echo ""
echo "📊 Test Summary:"
echo "- ✅ uvmgr Installation"
echo "- ✅ Terraform Command Registration" 
echo "- ✅ Operations Layer"
echo "- ✅ Template Generation"
echo "- ✅ External Project Integration"
echo "- ✅ OTEL Instrumentation"
echo "- ✅ Performance Benchmarks"
echo "- ✅ Error Handling"
echo ""
echo "🚀 uvmgr Terraform integration is production-ready!"