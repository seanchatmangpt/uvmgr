"""Executable capability inventory for uvmgr command surfaces."""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import asdict, dataclass
from enum import StrEnum
from types import ModuleType
from typing import Iterable

import typer

import uvmgr.commands as commands_package


class CapabilityStanding(StrEnum):
    """Typed capability standing."""

    ALIVE = "ALIVE"
    PARTIAL_ALIVE = "PARTIAL_ALIVE"
    UNSUPPORTED = "UNSUPPORTED"
    REFUSED = "REFUSED:EXCLUDED_BY_LEAN_CORE"
    BUILD_BROKEN = "BUILD_BROKEN"


@dataclass(frozen=True)
class CapabilityRecord:
    """One observed command capability and its layer closure."""

    name: str
    standing: str
    enabled: bool
    command_module: bool
    typer_app: bool
    operations_module: bool
    runtime_module: bool
    detail: str


def _has_typer_app(module: ModuleType) -> bool:
    """Return whether a command module exposes a Typer application."""
    return any(isinstance(value, typer.Typer) for value in vars(module).values())


def _module_exists(package: str, name: str) -> bool:
    """Check a package module without importing optional dependencies."""
    module = importlib.util.find_spec(f"{package}.{name}")
    return module is not None


def discover_command_names() -> tuple[str, ...]:
    """Return all command modules physically present in the package."""
    names = {
        module.name
        for module in pkgutil.iter_modules(commands_package.__path__)
        if module.name != "__init__" and not module.name.startswith("_")
    }
    return tuple(sorted(names))


def inspect_capabilities(
    *,
    enabled: Iterable[str] | None = None,
    excluded: Iterable[str] | None = None,
) -> tuple[CapabilityRecord, ...]:
    """Import enabled commands and classify every physical command surface."""
    enabled_names = set(enabled or commands_package.__all__)
    excluded_names = set(excluded or commands_package.EXCLUDED_COMMANDS)
    records: list[CapabilityRecord] = []

    for name in sorted(set(discover_command_names()) | enabled_names | excluded_names):
        command_module = _module_exists("uvmgr.commands", name)
        operations_module = _module_exists("uvmgr.ops", name)
        runtime_module = _module_exists("uvmgr.runtime", name)
        is_enabled = name in enabled_names

        if name in excluded_names:
            records.append(
                CapabilityRecord(
                    name=name,
                    standing=CapabilityStanding.REFUSED,
                    enabled=False,
                    command_module=command_module,
                    typer_app=False,
                    operations_module=operations_module,
                    runtime_module=runtime_module,
                    detail="Deliberately excluded from the lean core; source presence is not admission.",
                )
            )
            continue

        if not command_module:
            records.append(
                CapabilityRecord(
                    name=name,
                    standing=CapabilityStanding.UNSUPPORTED,
                    enabled=is_enabled,
                    command_module=False,
                    typer_app=False,
                    operations_module=operations_module,
                    runtime_module=runtime_module,
                    detail="Command module is absent.",
                )
            )
            continue

        typer_app = False
        detail = ""
        try:
            module = importlib.import_module(f"uvmgr.commands.{name}")
            typer_app = _has_typer_app(module)
        except Exception as exc:  # capability verifier must report, not hide, imports
            detail = f"{type(exc).__name__}: {exc}"
            standing = CapabilityStanding.BUILD_BROKEN
        else:
            if not typer_app:
                standing = CapabilityStanding.BUILD_BROKEN
                detail = "No Typer application found."
            elif is_enabled and operations_module and runtime_module:
                standing = CapabilityStanding.ALIVE
                detail = "Enabled command has Command → Ops → Runtime closure."
            elif is_enabled:
                standing = CapabilityStanding.PARTIAL_ALIVE
                detail = "Enabled and importable; dedicated Ops/Runtime closure is incomplete."
            else:
                standing = CapabilityStanding.PARTIAL_ALIVE
                detail = "Importable candidate exists but is not admitted into the CLI."

        records.append(
            CapabilityRecord(
                name=name,
                standing=standing,
                enabled=is_enabled,
                command_module=True,
                typer_app=typer_app,
                operations_module=operations_module,
                runtime_module=runtime_module,
                detail=detail,
            )
        )

    return tuple(records)


def capabilities_as_dict(records: Iterable[CapabilityRecord]) -> list[dict[str, object]]:
    """Return a stable JSON-compatible capability projection."""
    return [asdict(record) for record in records]
