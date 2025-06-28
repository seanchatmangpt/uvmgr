"""Test uvmgr integration in external project."""
import subprocess
import sys

def test_uvmgr_available():
    """Test that uvmgr is available."""
    result = subprocess.run([sys.executable, "-m", "uvmgr", "--help"], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert "uvmgr" in result.stdout

def test_uvmgr_help():
    """Test that uvmgr help works."""
    result = subprocess.run([sys.executable, "-m", "uvmgr", "--help"], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert "Usage:" in result.stdout

def test_uvmgr_deps_list():
    """Test that uvmgr deps list works."""
    result = subprocess.run([sys.executable, "-m", "uvmgr", "deps", "list"], 
                          capture_output=True, text=True)
    # Should work even if no dependencies installed
    assert result.returncode == 0
