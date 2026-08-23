"""Behavioral proof for deterministic legacy command import repairs."""

from __future__ import annotations

import importlib

import pytest
from typer.main import get_command


@pytest.mark.parametrize("name", ["automation", "performance", "security"])
def test_repaired_command_module_constructs(name: str) -> None:
    """Direct imports must expose complete constructible Typer applications."""
    module = importlib.import_module(f"uvmgr.commands.{name}")
    command = get_command(module.app)
    assert getattr(command, "commands", {})
