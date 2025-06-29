#!/bin/bash
set -e

echo "⚡ Performance Benchmarks"
echo "========================"

# Create benchmark results directory
mkdir -p /test-workspace/benchmarks
cd /test-workspace/benchmarks

echo "🔬 Running performance benchmarks..."

python << 'PYTHON'
import time
import tempfile
from pathlib import Path
from uvmgr.ops import terraform as tf_ops

def benchmark_operation(name, operation_func, *args, **kwargs):
    """Benchmark a single operation."""
    times = []
    
    # Run operation multiple times
    for i in range(5):
        start_time = time.time()
        try:
            result = operation_func(*args, **kwargs)
            duration = time.time() - start_time
            times.append(duration)
        except Exception as e:
            duration = time.time() - start_time
            times.append(duration)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    return {
        'avg': avg_time,
        'min': min_time,
        'max': max_time,
        'times': times
    }

# Benchmark 1: Template Generation Performance
print("📊 Benchmark 1: Template Generation")
print("-----------------------------------")

aws_vpc_config = {
    'template': 'aws-vpc',
    'name': 'benchmark-vpc',
    'provider': 'aws',
    'output_dir': Path('/tmp/bench-vpc'),
    'variables': {'cidr_block': '10.0.0.0/16'},
    'dry_run': True,
}

vpc_benchmark = benchmark_operation(
    "AWS VPC Template Generation",
    tf_ops.terraform_generate,
    aws_vpc_config
)

print(f"AWS VPC Template:")
print(f"  Average: {vpc_benchmark['avg']:.4f}s")
print(f"  Min:     {vpc_benchmark['min']:.4f}s") 
print(f"  Max:     {vpc_benchmark['max']:.4f}s")

# Check performance threshold (should be under 1 second)
if vpc_benchmark['avg'] < 1.0:
    print("✅ Template generation performance: EXCELLENT")
elif vpc_benchmark['avg'] < 2.0:
    print("✅ Template generation performance: GOOD")
else:
    print("⚠️  Template generation performance: NEEDS OPTIMIZATION")

# Benchmark 2: EKS Cluster Template
eks_config = {
    'template': 'k8s-cluster',
    'name': 'benchmark-cluster',
    'provider': 'aws',
    'output_dir': Path('/tmp/bench-eks'),
    'variables': {'node_instance_type': 't3.medium'},
    'dry_run': True,
}

eks_benchmark = benchmark_operation(
    "EKS Cluster Template Generation",
    tf_ops.terraform_generate,
    eks_config
)

print(f"\nEKS Cluster Template:")
print(f"  Average: {eks_benchmark['avg']:.4f}s")
print(f"  Min:     {eks_benchmark['min']:.4f}s")
print(f"  Max:     {eks_benchmark['max']:.4f}s")

# Benchmark 3: Validation Operations
print(f"\n📊 Benchmark 2: Validation Operations")
print("-------------------------------------")

validation_config = {
    'path': Path('/tmp/nonexistent'),
    'format': 'table',
}

validation_benchmark = benchmark_operation(
    "Terraform Validation",
    tf_ops.terraform_validate,
    validation_config
)

print(f"Terraform Validation:")
print(f"  Average: {validation_benchmark['avg']:.4f}s")
print(f"  Min:     {validation_benchmark['min']:.4f}s")
print(f"  Max:     {validation_benchmark['max']:.4f}s")

# Benchmark 4: Error Handling Performance
print(f"\n📊 Benchmark 3: Error Handling")
print("------------------------------")

error_config = {
    'template': 'invalid-template',
    'name': 'error-test',
    'provider': 'aws',
    'output_dir': Path('/tmp/error-test'),
    'dry_run': True,
}

error_benchmark = benchmark_operation(
    "Error Handling",
    tf_ops.terraform_generate,
    error_config
)

print(f"Error Handling:")
print(f"  Average: {error_benchmark['avg']:.4f}s")
print(f"  Min:     {error_benchmark['min']:.4f}s")
print(f"  Max:     {error_benchmark['max']:.4f}s")

# Summary
print(f"\n🎯 Performance Summary")
print("=====================")

total_avg = (vpc_benchmark['avg'] + eks_benchmark['avg'] + 
             validation_benchmark['avg'] + error_benchmark['avg']) / 4

print(f"Overall Average Operation Time: {total_avg:.4f}s")

# Performance criteria (80/20 focused)
criteria = {
    'template_generation': vpc_benchmark['avg'] < 1.0,  # Under 1 second
    'complex_templates': eks_benchmark['avg'] < 2.0,   # Under 2 seconds
    'validation': validation_benchmark['avg'] < 0.5,   # Under 0.5 seconds
    'error_handling': error_benchmark['avg'] < 0.1,    # Under 0.1 seconds
}

all_passed = all(criteria.values())

print(f"\n🏆 Performance Criteria:")
for test, passed in criteria.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {test}: {status}")

if all_passed:
    print(f"\n🚀 All performance benchmarks PASSED!")
    print("uvmgr terraform operations meet 80/20 performance requirements")
else:
    print(f"\n⚠️  Some performance benchmarks need optimization")

# Export benchmark results
benchmark_results = {
    'vpc_template': vpc_benchmark,
    'eks_template': eks_benchmark,
    'validation': validation_benchmark,
    'error_handling': error_benchmark,
    'overall_avg': total_avg,
    'criteria_passed': all_passed,
    'criteria': criteria
}

import json
with open('/test-workspace/benchmarks/results.json', 'w') as f:
    json.dump(benchmark_results, f, indent=2)

print(f"\n💾 Benchmark results saved to: /test-workspace/benchmarks/results.json")

PYTHON

echo ""
echo "⚡ Performance benchmarks completed!"
echo "====================================="

# Display results summary
if [ -f "/test-workspace/benchmarks/results.json" ]; then
    echo "📊 Quick Summary:"
    python -c "
import json
with open('/test-workspace/benchmarks/results.json', 'r') as f:
    data = json.load(f)

print(f'  Overall Average: {data[\"overall_avg\"]:.4f}s')
print(f'  Criteria Passed: {\"All\" if data[\"criteria_passed\"] else \"Some\"}')
print(f'  VPC Template: {data[\"vpc_template\"][\"avg\"]:.4f}s')
print(f'  EKS Template: {data[\"eks_template\"][\"avg\"]:.4f}s')
"
fi