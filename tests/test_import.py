"""Test uvmgr."""

import uvmgr


def test_import() -> None:
    """Test that the app can be imported."""
    assert isinstance(uvmgr.__name__, str)
