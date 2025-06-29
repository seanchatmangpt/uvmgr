"""Global test configuration and fixtures."""

import sys
import types
from unittest.mock import MagicMock
import pytest


@pytest.fixture(scope="session", autouse=True)
def mock_weaver_dependencies():
    """Mock weaver dependencies for all tests."""
    # Create a mock weaver module
    mock_weaver = types.ModuleType("weaver")
    mock_instrumentation = types.ModuleType("weaver.instrumentation")
    
    # Mock the required functions
    mock_instrumentation.instrument_command = lambda *a, **kw: (lambda f: f)
    mock_instrumentation.span = lambda *a, **kw: (lambda f: f)
    mock_instrumentation.add_span_event = lambda *a, **kw: None
    mock_instrumentation.metric_counter = lambda *a, **kw: (lambda *a, **kw: None)
    mock_instrumentation.metric_histogram = lambda *a, **kw: (lambda *a, **kw: None)
    
    # Attach instrumentation to weaver
    mock_weaver.instrumentation = mock_instrumentation
    
    # Patch sys.modules at session level
    original_weaver = sys.modules.get("weaver")
    original_weaver_instr = sys.modules.get("weaver.instrumentation")
    
    sys.modules["weaver"] = mock_weaver
    sys.modules["weaver.instrumentation"] = mock_instrumentation
    
    yield
    
    # Restore original modules if they existed
    if original_weaver is not None:
        sys.modules["weaver"] = original_weaver
    else:
        sys.modules.pop("weaver", None)
        
    if original_weaver_instr is not None:
        sys.modules["weaver.instrumentation"] = original_weaver_instr
    else:
        sys.modules.pop("weaver.instrumentation", None) 