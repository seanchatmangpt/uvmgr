import pytest
from unittest import mock
from src.uvmgr.core import shell

def test_colour_prints():
    with mock.patch.object(shell._console, 'print') as mock_print:
        shell.colour('hello', 'red', nl=False)
        mock_print.assert_called_with('hello', style='red', end='')

def test_dump_json_prints():
    with mock.patch.object(shell._console, 'print') as mock_print:
        shell.dump_json({'a': 1})
        assert mock_print.call_count == 1

def test_markdown_prints():
    with mock.patch.object(shell._console, 'print') as mock_print:
        shell.markdown('# Title')
        assert mock_print.call_count == 1

def test_rich_table_prints():
    with mock.patch.object(shell._console, 'print') as mock_print:
        shell.rich_table(['A', 'B'], [[1, 2], [3, 4]])
        assert mock_print.call_count == 1

def test_progress_bar_advances():
    with shell.progress_bar(2) as advance:
        advance()
        advance()

def test_timed_decorator_prints():
    @shell.timed
    def foo():
        return 42
    with mock.patch('src.uvmgr.core.shell.colour') as mock_colour:
        result = foo()
        assert result == 42
        assert mock_colour.call_count == 1 