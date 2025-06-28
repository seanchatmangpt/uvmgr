"""Command line interface for real external test."""

import click
from . import greet, calculate_sum


@click.group()
def cli():
    """Real external test CLI."""
    pass


@cli.command()
@click.argument("name")
def hello(name: str):
    """Say hello to someone."""
    click.echo(greet(name))


@cli.command()
@click.argument("numbers", nargs=-1, type=int)
def sum_numbers(numbers: tuple[int, ...]):
    """Calculate sum of numbers."""
    result = calculate_sum(list(numbers))
    click.echo(f"Sum: {result}")


if __name__ == "__main__":
    cli()