"""Complete lazy command registry for the uvmgr CLI surface."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from types import ModuleType
from typing import Final

from uvmgr.core.command_repairs import install_command_repairs
from uvmgr.core.command_registry import (
    EXCLUDED_COMMANDS,
    LEGACY_COMMANDS,
    OPTIONAL_COMMANDS,
    admitted_command_names,
)

# Source discovery extends the canonical ontology reversibly. Source presence
# alone never grants authority when the name is explicitly excluded.
install_command_repairs()


def _discover_source_commands() -> set[str]:
    """Discover command modules present in a source checkout."""
    return {
        module.name
        for module in pkgutil.iter_modules(__path__)
        if module.name != "__init__"
        and not module.name.startswith("_")
        and not module.name.endswith("_backup")
    }


# The registry is intentionally derived from installed/source modules; every
# element is a module-name string by construction even though Ruff cannot prove
# that statically for the special __all__ variable.
__all__: Final[list[str]] = list(  # noqa: PLE0605
    admitted_command_names(_discover_source_commands())
)
_PACKAGE_PREFIX = f"{__name__}."


def __getattr__(name: str) -> ModuleType:
    """Lazy-import an admitted command module."""
    if name not in __all__:
        raise AttributeError(name)
    module = importlib.import_module(_PACKAGE_PREFIX + name)
    setattr(sys.modules[__name__], name, module)
    return module
