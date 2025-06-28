"""
uvmgr.logging_config - Logging Configuration
===========================================

Basic logging configuration for the uvmgr application.

This module provides a simple logging setup function that configures
the Python logging system with a standard format and configurable log level.
"""

import logging
import os


def setup_logging():
    """
    Set up basic logging configuration for the uvmgr application.
    
    Configures logging with:
    - Log level from UVMGR_LOGLEVEL environment variable (default: INFO)
    - Standard timestamp format: YYYY-MM-DD HH:MM:SS
    - Log format: timestamp [level] logger_name: message
    
    Environment Variables
    ---------------------
    UVMGR_LOGLEVEL : str, optional
        Log level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        Defaults to "INFO" if not set
        
    Examples
    --------
    >>> setup_logging()
    >>> logging.info("Application started")
    2024-01-15 10:30:45 [INFO] root: Application started
    """
    loglevel = os.getenv("UVMGR_LOGLEVEL", "INFO").upper()
    logging.basicConfig(
        level=loglevel,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
