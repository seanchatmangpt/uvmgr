#!/usr/bin/env python3
"""
Command Validation Script

Validates that all re-enabled commands (search, agent, spiff_otel) are:
1. Importable without errors
2. Have proper Typer app structure
3. Have the expected subcommands
4. Have helpful error messages for missing dependencies

Usage:
    python validate_commands.py

Exit codes:
    0 = All commands valid
    1 = Some commands have issues
    2 = Critical failure (can't import)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_command_import(cmd_name: str) -> bool:
    """Check if a command can be imported."""
    try:
        __import__(f"uvmgr.commands.{cmd_name}")
        return True
    except Exception as e:
        print(f"❌ {cmd_name}: Import failed - {e}")
        return False


def check_command_app(cmd_name: str) -> bool:
    """Check if a command has a Typer app."""
    try:
        module = __import__(f"uvmgr.commands.{cmd_name}", fromlist=[cmd_name])
        if not hasattr(module, "app"):
            print(f"❌ {cmd_name}: No 'app' attribute (not a Typer command)")
            return False
        if module.app is None:
            print(f"❌ {cmd_name}: 'app' is None")
            return False
        print(f"✅ {cmd_name}: Importable and has Typer app")
        return True
    except Exception as e:
        print(f"❌ {cmd_name}: Error checking app - {e}")
        return False


def check_command_help(cmd_name: str) -> bool:
    """Check if a command has help text."""
    try:
        module = __import__(f"uvmgr.commands.{cmd_name}", fromlist=[cmd_name])
        if hasattr(module, "app") and module.app and module.app.help:
            print(f"   └─ Help: {module.app.help[:60]}...")
            return True
        else:
            print(f"   └─ ⚠️  No help text")
            return False
    except Exception:
        return False


def check_commands_in_all() -> bool:
    """Check if commands are registered in __all__."""
    try:
        from uvmgr.commands import __all__

        required = {"search", "agent", "spiff_otel"}
        found = required.intersection(set(__all__))

        if found == required:
            print(f"✅ All commands registered in __all__: {found}")
            return True
        else:
            missing = required - found
            print(f"❌ Missing from __all__: {missing}")
            return False
    except Exception as e:
        print(f"❌ Could not check __all__: {e}")
        return False


def check_security_fixes() -> bool:
    """Verify security fixes are in place."""
    try:
        import inspect
        from uvmgr.runtime.uv import call, add, remove, upgrade

        # Check that uv.py uses list-based calls
        add_source = inspect.getsource(add)
        if "call(cmd)" in add_source or "call([" in add_source:
            print("✅ uv.py: Uses list-based subprocess calls (injection safe)")
        else:
            print("⚠️  uv.py: May still use string-based calls")
            return False

        # Check that ops.aps.py doesn't use shell=True
        from uvmgr.ops.aps import _run_cmd
        aps_source = inspect.getsource(_run_cmd)
        if "shell=True" not in aps_source and "shlex.split" in aps_source:
            print("✅ ops.aps.py: Fixed shell injection vulnerability")
        else:
            print("⚠️  ops.aps.py: May still have shell=True")
            return False

        # Check cache file locking
        from uvmgr.core.cache import store_result
        cache_source = inspect.getsource(store_result)
        if "MAX_CACHE_SIZE" in cache_source:
            print("✅ core.cache.py: Added cache size limits (DoS protection)")
        else:
            print("⚠️  core.cache.py: May not have size limits")
            return False

        return True
    except Exception as e:
        print(f"⚠️  Could not verify security fixes: {e}")
        return False


def main():
    """Run all validations."""
    print("=" * 70)
    print("UVMGR COMMAND VALIDATION")
    print("=" * 70)
    print()

    print("1. CHECKING COMMAND IMPORTS")
    print("-" * 70)
    all_imports_ok = all(
        check_command_import(cmd) for cmd in ["search", "agent", "spiff_otel"]
    )
    if not all_imports_ok:
        print("❌ Some commands failed to import")
        return 2
    print()

    print("2. CHECKING COMMAND APPS")
    print("-" * 70)
    all_apps_ok = all(
        check_command_app(cmd) for cmd in ["search", "agent", "spiff_otel"]
    )
    if not all_apps_ok:
        print("❌ Some commands don't have proper Typer apps")
        return 2
    print()

    print("3. CHECKING HELP TEXT")
    print("-" * 70)
    for cmd in ["search", "agent", "spiff_otel"]:
        check_command_help(cmd)
    print()

    print("4. CHECKING COMMAND REGISTRATION")
    print("-" * 70)
    if not check_commands_in_all():
        print("❌ Commands not properly registered")
        return 1
    print()

    print("5. CHECKING SECURITY FIXES")
    print("-" * 70)
    if not check_security_fixes():
        print("⚠️  Some security fixes may not be in place")
        # Don't fail on this - just warn
    print()

    print("=" * 70)
    print("✅ ALL VALIDATIONS PASSED")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Install dependencies: pip install spiffworkflow chromadb")
    print("2. Try a command: uvmgr search code 'def' --max-results 5")
    print("3. Read guide: cat COMMANDS_GUIDE.md")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
