"""
Basic tests for uvmgr core functionality.

These tests ensure the basic functionality works and pytest can discover tests.
"""

import asyncio
import pytest
from pathlib import Path


def test_import_uvmgr():
    """Test that uvmgr can be imported."""
    import uvmgr
    assert uvmgr is not None


def test_cli_import():
    """Test that CLI can be imported."""
    from uvmgr.cli import app
    assert app is not None


def test_telemetry_import():
    """Test that telemetry can be imported."""
    from uvmgr.core.telemetry import span
    assert span is not None


def test_project_structure():
    """Test that project structure is correct."""
    project_root = Path(__file__).parent.parent.parent
    assert (project_root / "src" / "uvmgr").exists()
    assert (project_root / "tests").exists()
    assert (project_root / "pyproject.toml").exists()


def test_basic_math():
    """Basic math test to ensure pytest works."""
    assert 2 + 2 == 4
    assert 3 * 3 == 9


@pytest.mark.asyncio
async def test_async_basic():
    """Basic async test."""
    result = await asyncio.sleep(0.001)
    assert result is None


if __name__ == "__main__":
    pytest.main([__file__]) 