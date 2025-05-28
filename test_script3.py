"""
A test script that uses a very obscure package.
"""

from pyfiglet import figlet_format

def main():
    print(figlet_format("Hello from uvmgr exec!"))
    print("This script demonstrates dependency handling with uv run")

if __name__ == "__main__":
    main() 