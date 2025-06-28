"""
uvmgr.cli_utils - CLI Utility Functions
======================================

Utility functions for the command-line interface, providing common functionality
for error handling, JSON output, and CLI operations.

This module contains helper functions that are used across multiple CLI commands
to ensure consistent behavior and reduce code duplication.
"""

import logging
import sys
import traceback
from typing import Any

import typer

from uvmgr.core.shell import dump_json


def handle_cli_exception(e, debug=False, exit_code=1):
    """
    Handle CLI exceptions with proper logging and exit behavior.
    
    Parameters
    ----------
    e : Exception
        The exception that occurred
    debug : bool, optional
        Whether to print full traceback, by default False
    exit_code : int, optional
        Exit code to use when terminating, by default 1
        
    Notes
    -----
    This function logs the error and optionally prints the full traceback
    before exiting with the specified exit code.
    """
    logger = logging.getLogger("uvmgr.cli")
    logger.error(f"An error occurred: {e}")
    if debug:
        traceback.print_exc()
    sys.exit(exit_code)


def maybe_json(ctx: typer.Context, payload: Any, exit_code: int = 0) -> None:
    """
    Utility: in sub-commands call **maybe_json(ctx, data, exit_code)**; if the user
    passed --json we dump the object and exit early.
    
    Parameters
    ----------
    ctx : typer.Context
        The Typer context containing CLI options
    payload : Any
        The data to output as JSON
    exit_code : int, optional
        Exit code to use when terminating, by default 0
        
    Raises
    ------
    typer.Exit
        When --json flag is present, exits with the specified code
        
    Notes
    -----
    This function checks if the --json flag was passed in the context.
    If so, it outputs the payload as JSON and exits immediately.
    """
    if ctx.meta.get("json"):
        dump_json(payload)
        raise typer.Exit(exit_code)
