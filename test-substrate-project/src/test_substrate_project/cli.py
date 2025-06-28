'''Command-line interface for test_substrate_project.'''

import typer
from rich.console import Console

from . import __version__

app = typer.Typer(help="Command-line interface for test_substrate_project")
console = Console()


@app.command()
def version():
    '''Show version information.'''
    console.print(f"{__version__}")


@app.command()
def hello(name: str = "World"):
    '''Say hello to someone.'''
    console.print(f"Hello {name}!")


def main():
    '''Entry point for the CLI.'''
    app()


if __name__ == "__main__":
    main()