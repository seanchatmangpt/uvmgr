"""Basic tests for the external project."""

import pytest
from test_external_project import hello_world, add_numbers


def test_hello_world():
    """Test hello world function."""
    assert hello_world() == "Hello, World!"


def test_add_numbers():
    """Test addition function."""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0


def test_add_numbers_types():
    """Test addition with different types."""
    assert add_numbers(2.5, 3.5) == 6.0
    assert add_numbers("hello", " world") == "hello world"