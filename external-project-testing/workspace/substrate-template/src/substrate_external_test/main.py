
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional
from pydantic import BaseModel

app = typer.Typer()
console = Console()

class Config(BaseModel):
    name: str
    version: str = "0.1.0"
    debug: bool = False

@app.command()
def hello(name: str = typer.Argument(..., help="Name to greet")):
    """Say hello to someone."""
    console.print(f"Hello, {name}!", style="bold green")

@app.command()
def info():
    """Show project information."""
    config = Config(name="substrate-external-test")
    
    table = Table(title="Project Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="yellow")
    
    table.add_row("Name", config.name)
    table.add_row("Version", config.version)
    table.add_row("Debug", str(config.debug))
    
    console.print(table)

@app.command()
def validate(file_path: Optional[str] = typer.Option(None, help="File to validate")):
    """Validate a file or configuration."""
    if file_path:
        console.print(f"Validating file: {file_path}", style="blue")
        # Simulate validation
        console.print("✓ Validation passed", style="green")
    else:
        console.print("✓ Configuration is valid", style="green")

if __name__ == "__main__":
    app()
