"""
uvmgr.__main__ - Module Entry Point
==================================

Entry point for running uvmgr as a module: python -m uvmgr

This module allows uvmgr to be executed directly as a Python module,
providing the same functionality as the command-line interface.

Usage
-----
    $ python -m uvmgr --help
    $ python -m uvmgr deps install
    $ python -m uvmgr tests run

See Also
--------
- :mod:`uvmgr.cli` : Main CLI application
- :mod:`uvmgr.main` : Application entry point
"""

from uvmgr.cli import app

if __name__ == "__main__":
    app()
