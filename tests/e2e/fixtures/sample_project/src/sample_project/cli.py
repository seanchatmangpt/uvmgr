"""Sample CLI application."""
import sys
from typing import Optional

from rich.console import Console
from rich.table import Table

from . import __version__
from .core import Calculator, TextProcessor

console = Console()


def print_version():
    """Print version information."""
    console.print(f"[bold blue]Sample Project[/bold blue] v{__version__}")


def print_help():
    """Print help information."""
    table = Table(title="Sample CLI Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    
    table.add_row("--version", "Show version information")
    table.add_row("--help", "Show this help message")
    table.add_row("calc <operation>", "Perform calculation (add/sub/mul/div)")
    table.add_row("text <operation>", "Process text (upper/lower/reverse)")
    
    console.print(table)


def main(args: Optional[list] = None) -> int:
    """Main CLI entry point."""
    if args is None:
        args = sys.argv[1:]
    
    if not args or "--help" in args:
        print_help()
        return 0
    
    if "--version" in args:
        print_version()
        return 0
    
    if args[0] == "calc" and len(args) >= 4:
        calc = Calculator()
        op = args[1]
        try:
            a = float(args[2])
            b = float(args[3])
            
            if op == "add":
                result = calc.add(a, b)
            elif op == "sub":
                result = calc.subtract(a, b)
            elif op == "mul":
                result = calc.multiply(a, b)
            elif op == "div":
                result = calc.divide(a, b)
            else:
                console.print(f"[red]Unknown operation: {op}[/red]")
                return 1
            
            console.print(f"[green]Result: {result}[/green]")
            return 0
            
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1
    
    elif args[0] == "text" and len(args) >= 3:
        processor = TextProcessor()
        op = args[1]
        text = " ".join(args[2:])
        
        if op == "upper":
            result = processor.to_upper(text)
        elif op == "lower":
            result = processor.to_lower(text)
        elif op == "reverse":
            result = processor.reverse(text)
        else:
            console.print(f"[red]Unknown operation: {op}[/red]")
            return 1
        
        console.print(f"[green]Result: {result}[/green]")
        return 0
    
    console.print("[red]Invalid command. Use --help for usage.[/red]")
    return 1


if __name__ == "__main__":
    sys.exit(main())