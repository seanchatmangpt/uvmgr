
import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def cli():
    """CLI External Test Tool"""
    pass

@cli.command()
@click.argument('name')
def greet(name):
    """Greet someone"""
    console.print(f"Hello, {name}!", style="green")

@cli.command()
def status():
    """Show status table"""
    table = Table(title="CLI Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("CLI Tool", "Working")
    table.add_row("Rich Output", "Enabled")
    table.add_row("Commands", "Available")
    
    console.print(table)

@cli.command()
@click.option('--count', default=1, help='Number of times to say hello')
def hello(count):
    """Say hello multiple times"""
    for i in range(count):
        console.print(f"Hello #{i+1}!")

if __name__ == "__main__":
    cli()
