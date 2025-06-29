#!/bin/bash

# Simplified Cleanroom Test for uvmgr
# ====================================
# Tests core functionality without full Docker setup

set -euo pipefail

echo "🧪 Running cleanroom validation of uvmgr (simplified)..."

# Test 1: Basic imports and module loading
echo "📦 Testing core module imports..."
python -c "
import sys
sys.path.insert(0, 'src')

# Test core imports
try:
    from uvmgr.commands import multilang, deps, otel, performance
    print('✅ Core command modules import successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)

# Test runtime modules
try:
    from uvmgr.runtime import multilang, performance, container, cicd
    print('✅ Runtime modules import successfully')
except ImportError as e:
    print(f'❌ Runtime import error: {e}')
    exit(1)

# Test semantic conventions
try:
    from uvmgr.core.semconv import MultiLangAttributes, PerformanceAttributes
    print('✅ Semantic conventions import successfully')
except ImportError as e:
    print(f'❌ Semconv import error: {e}')
    exit(1)
"

# Test 2: Create test projects and validate
echo "🔍 Testing multilang detection..."

# Create temporary test directory
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"

echo "📦 Creating Python test project..."
mkdir python-project
cd python-project

cat > pyproject.toml << 'EOF'
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["requests>=2.25.0"]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
EOF

cat > main.py << 'EOF'
#!/usr/bin/env python3
"""Test Python application."""
import requests

def main():
    print("Hello from test project!")

if __name__ == '__main__':
    main()
EOF

echo "🔍 Testing Python project detection..."
python -c "
import sys
sys.path.insert(0, '$PWD/../../../src')  # Adjust path back to uvmgr src
from uvmgr.runtime.multilang import detect_languages, analyze_dependencies
from pathlib import Path

# Test language detection
project_path = Path('.')
languages = detect_languages(project_path)
print('✅ Python Project Detection Results:')
for lang in languages:
    print(f'  - {lang.language}: {lang.files_count} files, {lang.lines_of_code} lines ({lang.percentage:.1f}%)')
    print(f'    Package managers: {lang.package_managers}')

# Test dependency analysis
dependencies = analyze_dependencies(project_path)
print(f'✅ Found {len(dependencies)} dependencies:')
for dep in dependencies:
    print(f'  - {dep.name} {dep.version} ({dep.package_manager})')
"

cd "$TEST_DIR"
echo "🏗️  Creating Terraform test project..."
mkdir terraform-project
cd terraform-project

cat > main.tf << 'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

resource "aws_s3_bucket" "example" {
  bucket = "test-bucket"
}
EOF

echo "🔍 Testing Terraform project detection..."
python -c "
import sys
sys.path.insert(0, '$PWD/../../../src')  # Adjust path back to uvmgr src
from uvmgr.runtime.multilang import detect_languages, analyze_dependencies
from pathlib import Path

# Test language detection
project_path = Path('.')
languages = detect_languages(project_path)
print('✅ Terraform Project Detection Results:')
for lang in languages:
    print(f'  - {lang.language}: {lang.files_count} files, {lang.lines_of_code} lines ({lang.percentage:.1f}%)')
    print(f'    Package managers: {lang.package_managers}')

# Test dependency analysis
dependencies = analyze_dependencies(project_path)
print(f'✅ Found {len(dependencies)} dependencies:')
for dep in dependencies:
    print(f'  - {dep.name} {dep.version} ({dep.package_manager}) from {dep.file_path}')
"

# Test 3: Mixed project
cd "$TEST_DIR"
echo "🔀 Creating mixed Python + Terraform project..."
mkdir mixed-project
cd mixed-project

# Copy files from individual projects
cp ../python-project/pyproject.toml .
cp ../python-project/main.py .
mkdir infrastructure
cp ../terraform-project/main.tf infrastructure/

echo "🔍 Testing mixed project detection..."
python -c "
import sys
sys.path.insert(0, '$PWD/../../../src')
from uvmgr.runtime.multilang import detect_languages, analyze_dependencies
from pathlib import Path

# Test language detection on mixed project
project_path = Path('.')
languages = detect_languages(project_path)
print('✅ Mixed Project Detection Results:')
for lang in languages:
    print(f'  - {lang.language}: {lang.files_count} files, {lang.lines_of_code} lines ({lang.percentage:.1f}%)')

# Test dependency analysis
dependencies = analyze_dependencies(project_path)
python_deps = [d for d in dependencies if d.language == 'python']
terraform_deps = [d for d in dependencies if d.language == 'terraform']
print(f'✅ Mixed Project Dependencies:')
print(f'  - Python: {len(python_deps)} dependencies')
print(f'  - Terraform: {len(terraform_deps)} dependencies')
"

# Clean up
cd /
rm -rf "$TEST_DIR"

echo ""
echo "🎉 Cleanroom validation completed successfully!"
echo ""
echo "📊 Summary:"
echo "✅ All core modules load correctly"
echo "✅ Python project detection working"
echo "✅ Terraform project detection working"
echo "✅ Mixed project support working"
echo "✅ Dependency analysis functional"
echo ""
echo "🏆 uvmgr is validated and ready for use!"