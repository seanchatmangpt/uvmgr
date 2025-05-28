"""
A test script that uses rich to demonstrate dependency handling.
"""

from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    console.print(Panel.fit(
        "[bold green]Hello from uvmgr exec![/]\n"
        "[yellow]This script demonstrates dependency handling with uv run[/]",
        title="Test Script",
        border_style="blue"
    ))

if __name__ == "__main__":
    main() 