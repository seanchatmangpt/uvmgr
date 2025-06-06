import sys
import logging
import pytest
from unittest import mock
from src.uvmgr import cli_utils

def test_handle_cli_exception_exits_and_logs():
    with mock.patch.object(sys, 'exit') as mock_exit, \
         mock.patch.object(logging, 'getLogger') as mock_get_logger:
        mock_logger = mock.Mock()
        mock_get_logger.return_value = mock_logger
        e = Exception("test error")
        cli_utils.handle_cli_exception(e, debug=False)
        mock_logger.error.assert_called_with("An error occurred: test error")
        mock_exit.assert_called_once_with(1)

def test_handle_cli_exception_debug_prints_traceback():
    with mock.patch.object(sys, 'exit') as mock_exit, \
         mock.patch.object(logging, 'getLogger') as mock_get_logger, \
         mock.patch('traceback.print_exc') as mock_print_exc:
        mock_logger = mock.Mock()
        mock_get_logger.return_value = mock_logger
        e = Exception("debug error")
        cli_utils.handle_cli_exception(e, debug=True)
        mock_logger.error.assert_called_with("An error occurred: debug error")
        mock_print_exc.assert_called_once()
        mock_exit.assert_called_once_with(1) 