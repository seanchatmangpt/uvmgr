"""Non-actuating capability inventory for uvmgr command surfaces."""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from enum import StrEnum
from types import ModuleType

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
    """Observed capability state without promoting inspection to execution."""

    name: str
    standing: str
    observed: bool
    admitted: bool
    executed: bool
    imported: bool
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
    return importlib.util.find_spec(f"{package}.{name}") is not None


def discover_command_names() -> tuple[str, ...]:
    """Return all command modules physically present in the package."""
    names = {
        module.name
        for module in pkgutil.iter_modules(commands_package.__path__)
        if module.name != "__init__" and not module.name.startswith("_")
    }
    return tuple(sorted(names))


def _record(
    *,
    name: str,
    standing: CapabilityStanding,
    admitted: bool,
    imported: bool,
    command_module: bool,
    typer_app: bool,
    operations_module: bool,
    runtime_module: bool,
    detail: str,
) -> CapabilityRecord:
    """Construct an inspection record with execution held false."""
    return CapabilityRecord(
        name=name,
        standing=standing,
        observed=True,
        admitted=admitted,
        executed=False,
        imported=imported,
        command_module=command_module,
        typer_app=typer_app,
        operations_module=operations_module,
        runtime_module=runtime_module,
        detail=detail,
    )


def inspect_capabilities(
    *,
    enabled: Iterable[str] | None = None,
    excluded: Iterable[str] | None = None,
) -> tuple[CapabilityRecord, ...]:
    """Import only admitted commands and classify all physical command surfaces."""
    enabled_names = set(commands_package.__all__ if enabled is None else enabled)
    excluded_names = set(
        commands_package.EXCLUDED_COMMANDS if excluded is None else excluded
    )
    records: list[CapabilityRecord] = []

    for name in sorted(set(discover_command_names()) | enabled_names | excluded_names):
        command_module = _module_exists("uvmgr.commands", name)
        operations_module = _module_exists("uvmgr.ops", name)
        runtime_module = _module_exists("uvmgr.runtime", name)
        is_admitted = name in enabled_names

        if name in excluded_names:
            records.append(
                _record(
                    name=name,
                    standing=CapabilityStanding.REFUSED,
                    admitted=False,
                    imported=False,
                    command_module=command_module,
                    typer_app=False,
                    operations_module=operations_module,
                    runtime_module=runtime_module,
                    detail=(
                        "Deliberately excluded from the lean core; source presence "
                        "does not grant execution authority."
                    ),
                )
            )
            continue

        if not command_module:
            records.append(
                _record(
                    name=name,
                    standing=CapabilityStanding.UNSUPPORTED,
                    admitted=is_admitted,
                    imported=False,
                    command_module=False,
                    typer_app=False,
                    operations_module=operations_module,
                    runtime_module=runtime_module,
                    detail="Command module is absent.",
                )
            )
            continue

        if not is_admitted:
            records.append(
                _record(
                    name=name,
                    standing=CapabilityStanding.PARTIAL_ALIVE,
                    admitted=False,
                    imported=False,
                    command_module=True,
                    typer_app=False,
                    operations_module=operations_module,
                    runtime_module=runtime_module,
                    detail=(
                        "Physical candidate observed but not admitted or imported; "
                        "behavior remains unexecuted."
                    ),
                )
            )
            continue

        try:
            module = importlib.import_module(f"uvmgr.commands.{name}")
        except Exception as exc:  # verifier must expose enabled-command failures
            records.append(
                _record(
                    name=name,
                    standing=CapabilityStanding.BUILD_BROKEN,
                    admitted=True,
                    imported=False,
                    command_module=True,
                    typer_app=False,
                    operations_module=operations_module,
                    runtime_module=runtime_module,
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        typer_app = _has_typer_app(module)
        if not typer_app:
            records.append(
                _record(
                    name=name,
                    standing=CapabilityStanding.BUILD_BROKEN,
                    admitted=True,
                    imported=True,
                    command_module=True,
                    typer_app=False,
                    operations_module=operations_module,
                    runtime_module=runtime_module,
                    detail="Admitted module imports but exposes no Typer application.",
                )
            )
            continue

        has_layer_closure = operations_module and runtime_module
        detail = (
            "Import and Command → Ops → Runtime closure observed; exact behavior "
            "has not executed."
            if has_layer_closure
            else (
                "Admitted command imports, but dedicated Ops/Runtime closure is "
                "incomplete and exact behavior has not executed."
            )
        )
        records.append(
            _record(
                name=name,
                standing=CapabilityStanding.PARTIAL_ALIVE,
                admitted=True,
                imported=True,
                command_module=True,
                typer_app=True,
                operations_module=operations_module,
                runtime_module=runtime_module,
                detail=detail,
            )
        )

    return tuple(records)


def capabilities_as_dict(
    records: Iterable[CapabilityRecord],
) -> list[dict[str, object]]:
    """Return a stable JSON-compatible capability projection."""
    return [asdict(record) for record in records]
