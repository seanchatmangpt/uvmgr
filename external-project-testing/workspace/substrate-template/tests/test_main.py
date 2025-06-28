
import pytest
from typer.testing import CliRunner
from substrate_external_test.main import app, Config

def test_hello_command():
    runner = CliRunner()
    result = runner.invoke(app, ['hello', 'World'])
    assert result.exit_code == 0
    assert 'Hello, World!' in result.output

def test_info_command():
    runner = CliRunner()
    result = runner.invoke(app, ['info'])
    assert result.exit_code == 0
    assert 'Project Information' in result.output

def test_validate_command():
    runner = CliRunner()
    result = runner.invoke(app, ['validate'])
    assert result.exit_code == 0
    assert 'Configuration is valid' in result.output

def test_config_model():
    config = Config(name="test")
    assert config.name == "test"
    assert config.version == "0.1.0"
    assert config.debug is False
