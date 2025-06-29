import pytest
from test_external_project.main import hello_world, add_numbers

def test_hello_world():
    """Test hello_world function."""
    result = hello_world()
    assert result == "Hello, World\!"
    assert isinstance(result, str)

def test_add_numbers():
    """Test add_numbers function."""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0

def test_add_numbers_types():
    """Test add_numbers with different types."""
    assert add_numbers(2.5, 1.5) == 4.0
    with pytest.raises(TypeError):
        add_numbers("hello", "world")
