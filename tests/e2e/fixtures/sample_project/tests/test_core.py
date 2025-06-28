"""Tests for core functionality."""
import pytest

from sample_project.core import Calculator, TextProcessor


class TestCalculator:
    """Test Calculator class."""
    
    def test_add(self):
        """Test addition."""
        calc = Calculator()
        assert calc.add(2, 3) == 5
        assert calc.add(-1, 1) == 0
        assert calc.add(0.5, 0.5) == 1.0
    
    def test_subtract(self):
        """Test subtraction."""
        calc = Calculator()
        assert calc.subtract(5, 3) == 2
        assert calc.subtract(0, 5) == -5
        assert calc.subtract(1.5, 0.5) == 1.0
    
    def test_multiply(self):
        """Test multiplication."""
        calc = Calculator()
        assert calc.multiply(3, 4) == 12
        assert calc.multiply(-2, 3) == -6
        assert calc.multiply(0, 100) == 0
    
    def test_divide(self):
        """Test division."""
        calc = Calculator()
        assert calc.divide(10, 2) == 5
        assert calc.divide(7, 2) == 3.5
        assert calc.divide(-10, 2) == -5
    
    def test_divide_by_zero(self):
        """Test division by zero."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Division by zero"):
            calc.divide(10, 0)
    
    def test_history(self):
        """Test calculation history."""
        calc = Calculator()
        calc.add(2, 3)
        calc.multiply(4, 5)
        
        history = calc.get_history()
        assert len(history) == 2
        assert history[0] == ("add", 2, 3, 5)
        assert history[1] == ("multiply", 4, 5, 20)


class TestTextProcessor:
    """Test TextProcessor class."""
    
    def test_to_upper(self):
        """Test uppercase conversion."""
        processor = TextProcessor()
        assert processor.to_upper("hello") == "HELLO"
        assert processor.to_upper("Hello World") == "HELLO WORLD"
        assert processor.to_upper("123abc") == "123ABC"
    
    def test_to_lower(self):
        """Test lowercase conversion."""
        processor = TextProcessor()
        assert processor.to_lower("HELLO") == "hello"
        assert processor.to_lower("Hello World") == "hello world"
        assert processor.to_lower("123ABC") == "123abc"
    
    def test_reverse(self):
        """Test text reversal."""
        processor = TextProcessor()
        assert processor.reverse("hello") == "olleh"
        assert processor.reverse("12345") == "54321"
        assert processor.reverse("") == ""
    
    def test_count_words(self):
        """Test word counting."""
        processor = TextProcessor()
        assert processor.count_words("hello world") == 2
        assert processor.count_words("one two three four") == 4
        assert processor.count_words("") == 0
        assert processor.count_words("   spaced   out   ") == 2
    
    def test_count_chars(self):
        """Test character counting."""
        processor = TextProcessor()
        assert processor.count_chars("hello") == 5
        assert processor.count_chars("hello world") == 11
        assert processor.count_chars("hello world", include_spaces=False) == 10