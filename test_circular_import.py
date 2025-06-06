#!/usr/bin/env python3
"""Test script to check if circular imports are fixed."""

import sys
import types

# Mock fastmcp module
fastmcp_mock = types.ModuleType('fastmcp')
fastmcp_mock.FastMCP = lambda *args, **kwargs: type('MockMCP', (), {
    'tool': lambda: lambda f: f,
    'resource': lambda uri: lambda f: f,
    'prompt': lambda name: lambda f: f,
})()
fastmcp_mock.Context = type('Context', (), {})

sys.modules['fastmcp'] = fastmcp_mock

# Add src to path
sys.path.insert(0, 'src')

try:
    # Try importing the MCP modules
    print("Testing imports...")
    
    from uvmgr.mcp._mcp_instance import mcp
    print("✓ _mcp_instance imported")
    
    from uvmgr.mcp.server import OperationResult
    print("✓ server imported")
    
    from uvmgr.mcp.resources import get_project_info
    print("✓ resources imported")
    
    from uvmgr.mcp.tools.ai import ai_fix_tests
    print("✓ tools.ai imported")
    
    from uvmgr.mcp import mcp as mcp_main
    print("✓ main __init__ imported")
    
    print("\n✅ Success! No circular imports detected.")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
