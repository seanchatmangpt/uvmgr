"""Deterministic import repairs for legacy command modules.

The repaired modules remain the canonical source surfaces.  This loader applies
small, identity-checked source rewrites before Python executes them, so direct
imports and CLI discovery see the same corrected modules without duplicating
command implementations.
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Final


@dataclass(frozen=True)
class SourceRewrite:
    """One exact, bounded source rewrite."""

    old: str
    new: str
    count: int = 1


_REWRITES: Final[dict[str, tuple[SourceRewrite, ...]]] = {
    "uvmgr.commands.automation": (
        SourceRewrite(
            '@app.command("rules")\ndef rules_commands():\n'
            '    """Automation rules management."""\n    pass\n',
            'rules_app = typer.Typer(help="Automation rules management.")\n',
        ),
        SourceRewrite("@rules_commands.command(", "@rules_app.command(", count=4),
        SourceRewrite(
            'app.add_typer(rules_commands, name="rules")',
            'app.add_typer(rules_app, name="rules")',
        ),
    ),
    "uvmgr.commands.performance": (
        SourceRewrite(
            '@app.command("profile")\n@instrument_command\n',
            '@app.command("profile")\n'
            '@instrument_command("performance_profile", track_args=True)\n',
        ),
        SourceRewrite(
            '@app.command("benchmark")\n@instrument_command\n',
            '@app.command("benchmark")\n'
            '@instrument_command("performance_benchmark", track_args=True)\n',
        ),
        SourceRewrite(
            '@app.command("optimize")\n@instrument_command\n',
            '@app.command("optimize")\n'
            '@instrument_command("performance_optimize", track_args=True)\n',
        ),
        SourceRewrite(
            '@app.command("monitor")\n@instrument_command\n',
            '@app.command("monitor")\n'
            '@instrument_command("performance_monitor", track_args=True)\n',
        ),
    ),
    "uvmgr.commands.security": (
        SourceRewrite(
            '@app.command("scan")\n@instrument_command\n',
            '@app.command("scan")\n'
            '@instrument_command("security_scan", track_args=True)\n',
        ),
        SourceRewrite(
            '@app.command("audit")\n@instrument_command  \n',
            '@app.command("audit")\n'
            '@instrument_command("security_audit", track_args=True)\n',
        ),
        SourceRewrite(
            '@app.command("secrets")\n@instrument_command\n',
            '@app.command("secrets")\n'
            '@instrument_command("security_secrets", track_args=True)\n',
        ),
        SourceRewrite(
            '@app.command("config")\n@instrument_command\n',
            '@app.command("config")\n'
            '@instrument_command("security_config", track_args=True)\n',
        ),
    ),
}


def _rewrite_source(fullname: str, source: str) -> str:
    """Apply all admitted rewrites and refuse source drift."""
    for rewrite in _REWRITES[fullname]:
        observed = source.count(rewrite.old)
        if observed != rewrite.count:
            raise ImportError(
                f"COMMAND_SOURCE_DRIFT_REFUSED module={fullname} "
                f"expected={rewrite.count} observed={observed}"
            )
        source = source.replace(rewrite.old, rewrite.new)
    return source


class _RepairLoader(importlib.abc.Loader):
    """Execute one module after exact source admission."""

    def __init__(self, fullname: str, origin: str) -> None:
        self.fullname = fullname
        self.origin = origin

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType | None:
        """Use Python's standard module manufacture."""
        return None

    def exec_module(self, module: ModuleType) -> None:
        """Compile and execute the admitted repaired source."""
        with open(self.origin, encoding="utf-8") as source_file:
            source = source_file.read()
        repaired = _rewrite_source(self.fullname, source)
        module.__file__ = self.origin
        module.__package__ = self.fullname.rpartition(".")[0]
        exec(compile(repaired, self.origin, "exec"), module.__dict__)


class _RepairFinder(importlib.abc.MetaPathFinder):
    """Intercept only the explicitly admitted legacy command modules."""

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        """Return a repair loader for an admitted module name."""
        del target
        if fullname not in _REWRITES:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.origin is None:
            raise ImportError(f"COMMAND_SOURCE_UNAVAILABLE module={fullname}")
        return importlib.machinery.ModuleSpec(
            fullname,
            _RepairLoader(fullname, spec.origin),
            origin=spec.origin,
        )


_FINDER = _RepairFinder()


def install_command_repairs() -> None:
    """Install the bounded finder once, ahead of the default path finder."""
    if _FINDER not in sys.meta_path:
        sys.meta_path.insert(0, _FINDER)
