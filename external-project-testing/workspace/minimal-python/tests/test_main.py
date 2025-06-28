
import pytest
from minimal_external_test.main import calculate_sum, get_python_org


def test_calculate_sum():
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0
    assert calculate_sum(0, 0) == 0

def test_get_python_org():
    result = get_python_org()
    # Should return either valid JSON or error dict
    assert isinstance(result, dict)
