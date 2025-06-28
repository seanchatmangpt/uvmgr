
import pytest
from click.testing import CliRunner
from cli_external_test.main import cli

def test_greet_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['greet', 'World'])
    assert result.exit_code == 0
    assert 'Hello, World!' in result.output

def test_status_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'CLI Status' in result.output

def test_hello_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['hello', '--count', '3'])
    assert result.exit_code == 0
    assert 'Hello #1!' in result.output
    assert 'Hello #3!' in result.output
