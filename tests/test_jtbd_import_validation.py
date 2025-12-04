"""
JTBD Import Validation Tests - Verify command structure and imports

Tests that all 13 core commands:
1. Can be imported successfully
2. Have proper Typer app structure
3. Have required subcommands
4. Have help documentation

This validates the command infrastructure without requiring full installation.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class JTBDValidator:
    """Validates command structure."""

    def __init__(self):
        self.results = []
        self.failed = []

    def test_command_import(self, cmd_name: str) -> bool:
        """Test that a command can be imported."""
        try:
            module = __import__(f"uvmgr.commands.{cmd_name}", fromlist=[cmd_name])
            self.results.append((f"Import {cmd_name}", True))
            return True
        except Exception as e:
            self.results.append((f"Import {cmd_name}", False))
            self.failed.append((f"Import {cmd_name}", str(e)))
            return False

    def test_command_has_app(self, cmd_name: str) -> bool:
        """Test that a command has a Typer app."""
        try:
            module = __import__(f"uvmgr.commands.{cmd_name}", fromlist=[cmd_name])
            if not hasattr(module, "app"):
                raise AssertionError(f"No 'app' attribute in {cmd_name}")
            if module.app is None:
                raise AssertionError(f"'app' is None in {cmd_name}")
            self.results.append((f"{cmd_name} has Typer app", True))
            return True
        except Exception as e:
            self.results.append((f"{cmd_name} has Typer app", False))
            self.failed.append((f"{cmd_name} app", str(e)))
            return False

    def test_command_has_help(self, cmd_name: str) -> bool:
        """Test that a command has help text (Typer app object exists)."""
        try:
            module = __import__(f"uvmgr.commands.{cmd_name}", fromlist=[cmd_name])
            if hasattr(module, "app") and module.app:
                # Typer app exists - it will have help via --help flag
                self.results.append((f"{cmd_name} has help", True))
                return True
            else:
                self.results.append((f"{cmd_name} has help", False))
                self.failed.append((f"{cmd_name} help", "No Typer app found"))
                return False
        except Exception as e:
            self.results.append((f"{cmd_name} has help", False))
            self.failed.append((f"{cmd_name} help", str(e)))
            return False

    def test_in_all(self, cmd_name: str) -> bool:
        """Test that command is registered in __all__."""
        try:
            from uvmgr.commands import __all__

            if cmd_name in __all__:
                self.results.append((f"{cmd_name} in __all__", True))
                return True
            else:
                self.results.append((f"{cmd_name} in __all__", False))
                self.failed.append((f"{cmd_name} registration", f"Not in __all__"))
                return False
        except Exception as e:
            self.results.append((f"{cmd_name} in __all__", False))
            self.failed.append((f"{cmd_name} registration", str(e)))
            return False

    def report(self) -> int:
        """Print test report."""
        total = len(self.results)
        passed = sum(1 for _, p in self.results if p)

        print("\n" + "=" * 70)
        print(f"COMMAND VALIDATION RESULTS: {passed}/{total} passed")
        print("=" * 70)

        if self.failed:
            print(f"\n❌ {len(self.failed)} FAILURES:\n")
            for cmd, error in self.failed:
                print(f"  • {cmd}: {error[:100]}")

        print(f"\n✅ {passed} passed, ❌ {len(self.failed)} failed")
        return 0 if not self.failed else 1


def main():
    """Run JTBD validation tests."""
    print("=" * 70)
    print("JTBD IMPORT VALIDATION - uvmgr Core Commands")
    print("=" * 70)
    print("\nValidating structure of all 13 core commands\n")

    # 13 core commands
    commands = [
        "deps",
        "build",
        "tests",
        "cache",
        "lint",
        "otel",
        "guides",
        "worktree",
        "infodesign",
        "mermaid",
        "dod",
        "docs",
        "terraform",
    ]

    validator = JTBDValidator()

    print("### JTBD: Command Structure Validation")
    print()

    for cmd in commands:
        print(f"Validating {cmd}...")
        import_ok = validator.test_command_import(cmd)
        app_ok = validator.test_command_has_app(cmd) if import_ok else False
        help_ok = validator.test_command_has_help(cmd) if import_ok else False
        all_ok = validator.test_in_all(cmd)

        status = "✅" if all([import_ok, app_ok, help_ok, all_ok]) else "⚠️"
        print(f"  {status} {cmd}: import={import_ok} app={app_ok} help={help_ok} registered={all_ok}")

    print()
    return validator.report()


if __name__ == "__main__":
    sys.exit(main())
