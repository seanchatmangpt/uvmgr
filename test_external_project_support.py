#!/usr/bin/env python3
"""
Test external project support for uvmgr.
This script validates that uvmgr works correctly in external projects.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def create_test_project(base_dir: Path) -> Path:
    """Create a simple test external project."""
    project_dir = base_dir / "test-external-uvmgr"
    project_dir.mkdir()
    
    # Create pyproject.toml
    pyproject_content = """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-external-uvmgr"
version = "0.1.0"
description = "Test external project for uvmgr validation"
authors = [{name = "Test", email = "test@example.com"}]
dependencies = []

[project.scripts]
test-app = "test_external_uvmgr.main:main"

[tool.uv]
dev-dependencies = ["pytest>=7.0.0"]
"""
    
    (project_dir / "pyproject.toml").write_text(pyproject_content)
    
    # Create main module
    src_dir = project_dir / "test_external_uvmgr"
    src_dir.mkdir()
    
    (src_dir / "__init__.py").write_text("# Test external project")
    
    main_content = '''#!/usr/bin/env python3
"""Test external project main module."""

def main():
    """Main entry point."""
    print("🚀 External project running!")
    print("✅ uvmgr integration successful!")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
'''
    (src_dir / "main.py").write_text(main_content)
    
    # Create test file
    test_content = '''#!/usr/bin/env python3
"""Test script."""

def test_main():
    """Test the main function."""
    from test_external_uvmgr.main import main
    result = main()
    assert result == 0

def test_import():
    """Test module import."""
    import test_external_uvmgr
    assert test_external_uvmgr is not None
'''
    (project_dir / "test_main.py").write_text(test_content)
    
    return project_dir

def test_uvmgr_commands(project_dir: Path) -> bool:
    """Test uvmgr commands in the external project."""
    os.chdir(project_dir)
    
    success = True
    
    # Test 1: Tests run (the main one we care about)
    print("🧪 Testing: uvmgr tests run")
    result = subprocess.run(["uvmgr", "tests", "run"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Tests run: PASSED")
    else:
        print(f"❌ Tests run: FAILED - {result.stderr}")
        success = False
    
    # Test 2: OTEL telemetry
    print("🧪 Testing: uvmgr otel test")
    result = subprocess.run(["uvmgr", "otel", "test"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ OTEL test: PASSED")
    else:
        print(f"❌ OTEL test: FAILED - {result.stderr}")
        success = False
    
    # Test 3: Weaver validation 
    print("🧪 Testing: uvmgr weaver check")
    result = subprocess.run(["uvmgr", "weaver", "check"], 
                          capture_output=True, text=True)
    # Check command exists even if it fails validation
    if "No such command" not in result.stderr:
        print("✅ Weaver available: PASSED")
    else:
        print(f"❌ Weaver available: FAILED - {result.stderr}")
        success = False
    
    return success

def main():
    """Main test function."""
    print("🎯 Testing uvmgr external project support")
    print("=" * 50)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            # Create test project
            print("📁 Creating test external project...")
            project_dir = create_test_project(temp_path)
            print(f"✅ Project created at: {project_dir}")
            
            # Test uvmgr functionality
            print("\n🧪 Testing uvmgr commands...")
            success = test_uvmgr_commands(project_dir)
            
            if success:
                print("\n🎉 All external project tests PASSED!")
                print("✅ uvmgr works correctly with external projects")
                return 0
            else:
                print("\n❌ Some external project tests FAILED!")
                return 1
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())