"""Core functionality for sample project."""
from typing import Union


class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        """Initialize calculator."""
        self.history: list[tuple[str, float, float, float]] = []
    
    def add(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(("add", a, b, result))
        return result
    
    def subtract(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Subtract b from a."""
        result = a - b
        self.history.append(("subtract", a, b, result))
        return result
    
    def multiply(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(("multiply", a, b, result))
        return result
    
    def divide(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Division by zero")
        result = a / b
        self.history.append(("divide", a, b, result))
        return result
    
    def get_history(self) -> list[tuple[str, float, float, float]]:
        """Get calculation history."""
        return self.history.copy()


class TextProcessor:
    """Text processing utilities."""
    
    def to_upper(self, text: str) -> str:
        """Convert text to uppercase."""
        return text.upper()
    
    def to_lower(self, text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()
    
    def reverse(self, text: str) -> str:
        """Reverse text."""
        return text[::-1]
    
    def count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def count_chars(self, text: str, include_spaces: bool = True) -> int:
        """Count characters in text."""
        if include_spaces:
            return len(text)
        return len(text.replace(" ", ""))