import sys
import logging
import traceback

def handle_cli_exception(e, debug=False):
    logger = logging.getLogger("uvmgr.cli")
    logger.error(f"An error occurred: {e}")
    if debug:
        traceback.print_exc()
    sys.exit(1) 