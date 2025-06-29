#!/usr/bin/env python3
"""
Simple test script for MCP functionality.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test basic imports."""
    try:
        from uvmgr.mcp.server import UvmgrMCPServer
        print("✅ MCP Server import successful")
        
        from uvmgr.mcp.client import UvmgrMCPClient
        print("✅ MCP Client import successful")
        
        from uvmgr.mcp.config import MCPConfig
        print("✅ MCP Config import successful")
        
        from uvmgr.mcp.models import UvmgrDSPyModels
        print("✅ MCP Models import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_server_creation():
    """Test server creation."""
    try:
        from uvmgr.mcp.server import UvmgrMCPServer
        
        server = UvmgrMCPServer()
        print("✅ MCP Server creation successful")
        
        # Check that tools are registered
        tools = server.server.get_tools()
        print(f"✅ Found {len(tools)} tools registered")
        
        return True
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        return False

def test_client_creation():
    """Test client creation."""
    try:
        from uvmgr.mcp.client import UvmgrMCPClient
        
        client = UvmgrMCPClient("http://localhost:8000")
        print("✅ MCP Client creation successful")
        
        return True
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        return False

def test_config():
    """Test configuration."""
    try:
        from uvmgr.mcp.config import MCPConfig, validate_mcp_config
        
        config = MCPConfig()
        print("✅ MCP Config creation successful")
        
        validation = validate_mcp_config()
        print(f"✅ Config validation: {validation['is_valid']}")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_dspy_models():
    """Test DSPy models."""
    try:
        from uvmgr.mcp.models import UvmgrDSPyModels
        
        models = UvmgrDSPyModels()
        print("✅ DSPy Models creation successful")
        
        available_models = models.get_available_models()
        print(f"✅ Found {len(available_models)} DSPy models")
        
        return True
    except Exception as e:
        print(f"❌ DSPy models test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing MCP functionality...\n")
    
    tests = [
        ("Basic Imports", test_imports),
        ("Server Creation", test_server_creation),
        ("Client Creation", test_client_creation),
        ("Configuration", test_config),
        ("DSPy Models", test_dspy_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP functionality is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 