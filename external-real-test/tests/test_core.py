"""Tests for the real external test project."""

import pytest
from real_external_test import greet, calculate_sum


def test_greet():
    """Test greeting function."""
    assert greet("World") == "Hello, World!"
    assert greet("Python") == "Hello, Python!"


def test_calculate_sum():
    """Test sum calculation."""
    assert calculate_sum([1, 2, 3]) == 6
    assert calculate_sum([]) == 0
    assert calculate_sum([10]) == 10
    assert calculate_sum([-1, 1]) == 0


def test_calculate_sum_large_numbers():
    """Test sum with large numbers."""
    numbers = list(range(1, 101))  # 1 to 100
    expected = sum(numbers)
    assert calculate_sum(numbers) == expected


@pytest.mark.parametrize("numbers,expected", [
    ([1, 2, 3], 6),
    ([0, 0, 0], 0),
    ([-5, 5], 0),
    ([100, 200, 300], 600),
])
def test_calculate_sum_parametrized(numbers, expected):
    """Parametrized test for sum calculation."""
    assert calculate_sum(numbers) == expected