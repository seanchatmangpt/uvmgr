"""
A test script that uses termcolor to demonstrate dependency handling.
"""

from termcolor import colored

def main():
    print(colored("Hello from uvmgr exec!", "green", attrs=["bold"]))
    print(colored("This script demonstrates dependency handling with uv run", "yellow"))

if __name__ == "__main__":
    main() 