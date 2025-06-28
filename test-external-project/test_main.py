#!/usr/bin/env python3
"""Test script for external project."""

import pytest

def test_main_function():
    """Test the main function works."""
    from test_external_project.main import main
    result = main()
    assert result == 0

def test_import():
    """Test that the module can be imported."""
    import test_external_project
    assert test_external_project is not None