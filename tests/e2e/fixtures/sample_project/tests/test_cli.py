"""Tests for CLI interface."""

from sample_project.cli import main


class TestCLI:
    """Test CLI functionality."""
    
    def test_help(self, capsys):
        """Test help command."""
        assert main(["--help"]) == 0
        captured = capsys.readouterr()
        assert "Sample CLI Commands" in captured.out
        assert "calc" in captured.out
        assert "text" in captured.out
    
    def test_version(self, capsys):
        """Test version command."""
        assert main(["--version"]) == 0
        captured = capsys.readouterr()
        assert "Sample Project" in captured.out
        assert "0.1.0" in captured.out
    
    def test_calc_add(self, capsys):
        """Test calc add command."""
        assert main(["calc", "add", "2", "3"]) == 0
        captured = capsys.readouterr()
        assert "Result: 5" in captured.out
    
    def test_calc_subtract(self, capsys):
        """Test calc subtract command."""
        assert main(["calc", "sub", "10", "3"]) == 0
        captured = capsys.readouterr()
        assert "Result: 7" in captured.out
    
    def test_calc_multiply(self, capsys):
        """Test calc multiply command."""
        assert main(["calc", "mul", "4", "5"]) == 0
        captured = capsys.readouterr()
        assert "Result: 20" in captured.out
    
    def test_calc_divide(self, capsys):
        """Test calc divide command."""
        assert main(["calc", "div", "10", "2"]) == 0
        captured = capsys.readouterr()
        assert "Result: 5" in captured.out
    
    def test_calc_divide_by_zero(self, capsys):
        """Test calc divide by zero."""
        assert main(["calc", "div", "10", "0"]) == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Division by zero" in captured.out
    
    def test_calc_invalid_operation(self, capsys):
        """Test invalid calc operation."""
        assert main(["calc", "pow", "2", "3"]) == 1
        captured = capsys.readouterr()
        assert "Unknown operation: pow" in captured.out
    
    def test_text_upper(self, capsys):
        """Test text upper command."""
        assert main(["text", "upper", "hello", "world"]) == 0
        captured = capsys.readouterr()
        assert "Result: HELLO WORLD" in captured.out
    
    def test_text_lower(self, capsys):
        """Test text lower command."""
        assert main(["text", "lower", "HELLO", "WORLD"]) == 0
        captured = capsys.readouterr()
        assert "Result: hello world" in captured.out
    
    def test_text_reverse(self, capsys):
        """Test text reverse command."""
        assert main(["text", "reverse", "hello"]) == 0
        captured = capsys.readouterr()
        assert "Result: olleh" in captured.out
    
    def test_invalid_command(self, capsys):
        """Test invalid command."""
        assert main(["invalid"]) == 1
        captured = capsys.readouterr()
        assert "Invalid command" in captured.out
    
    def test_no_args(self, capsys):
        """Test no arguments."""
        assert main([]) == 0
        captured = capsys.readouterr()
        assert "Sample CLI Commands" in captured.out