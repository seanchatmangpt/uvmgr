"""Test demo-otel-app."""

import demo_otel_app


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(demo_otel_app.__name__, str)
