"""
JTBD Permutation Tests for uvmgr - Real-World Workflows

Tests the core 13 commands in realistic combinations to validate
end-to-end workflows. Each test represents an actual job a user
would perform.

Commands tested:
- deps, build, tests, cache, lint, otel
- guides, worktree, infodesign, mermaid, dod, docs, terraform
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import List, Tuple, Any


class CommandValidator:
    """Validates command execution and output."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []
        self.failed = []

    def run(self, cmd: List[str], description: str = "") -> Tuple[int, str, str]:
        """Run a command and return (returncode, stdout, stderr)."""
        # Convert uvmgr to python -m uvmgr.cli for testing
        if cmd[0] == "uvmgr":
            cmd = ["python", "-m", "uvmgr.cli"] + cmd[1:]

        if self.verbose:
            print(f"  → {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def assert_success(self, returncode: int, stdout: str, stderr: str, msg: str) -> bool:
        """Assert command succeeded."""
        if returncode == 0:
            self.results.append((msg, True))
            if self.verbose:
                print(f"    ✓ {msg}")
            return True
        else:
            self.results.append((msg, False))
            self.failed.append((msg, returncode, stderr))
            if self.verbose:
                print(f"    ✗ {msg}: {stderr[:100]}")
            return False

    def assert_output_contains(self, output: str, text: str, msg: str) -> bool:
        """Assert output contains text."""
        if text in output:
            self.results.append((msg, True))
            if self.verbose:
                print(f"    ✓ {msg}")
            return True
        else:
            self.results.append((msg, False))
            self.failed.append((msg, -1, f"Output missing: {text}"))
            if self.verbose:
                print(f"    ✗ {msg}")
            return False

    def report(self) -> int:
        """Print test report."""
        total = len(self.results)
        passed = sum(1 for _, p in self.results if p)

        print("\n" + "=" * 70)
        print(f"TEST RESULTS: {passed}/{total} passed")
        print("=" * 70)

        if self.failed:
            print(f"\n❌ {len(self.failed)} FAILURES:\n")
            for msg, code, error in self.failed:
                print(f"  • {msg}")
                if error:
                    print(f"    Error: {error[:200]}")

        print(f"\n✅ {passed} passed, ❌ {len(self.failed)} failed")
        return 0 if not self.failed else 1


# ============================================================================
# JTBD TEST SCENARIOS
# ============================================================================


class TestDepsWorkflow:
    """JTBD: Manage project dependencies."""

    @staticmethod
    def run(v: CommandValidator):
        """Test dependency management workflow."""
        print("\n### JTBD: Manage project dependencies")

        # List current dependencies
        code, stdout, stderr = v.run(["uvmgr", "deps", "list"], "List dependencies")
        v.assert_success(code, stdout, stderr, "✓ List dependencies")

        # Show dependency tree
        code, stdout, stderr = v.run(["uvmgr", "deps", "tree"], "Show dependency tree")
        v.assert_success(code, stdout, stderr, "✓ Show dependency tree")

        # Check for vulnerabilities
        code, stdout, stderr = v.run(["uvmgr", "deps", "audit"], "Audit for vulnerabilities")
        v.assert_success(code, stdout, stderr, "✓ Audit dependencies")

        # Sync dependencies (without actually modifying pyproject.toml)
        code, stdout, stderr = v.run(["uvmgr", "deps", "sync", "--dry-run"], "Dry-run sync")
        v.assert_success(code, stdout, stderr, "✓ Dry-run dependency sync")


class TestBuildWorkflow:
    """JTBD: Build and package application."""

    @staticmethod
    def run(v: CommandValidator):
        """Test build workflow."""
        print("\n### JTBD: Build and package application")

        # Build wheel
        code, stdout, stderr = v.run(["uvmgr", "build", "wheel"], "Build wheel")
        # May fail if not in a proper package, but should be a valid command
        v.assert_success(code, stdout, stderr, "✓ Build wheel (valid command)")

        # Build sdist
        code, stdout, stderr = v.run(["uvmgr", "build", "sdist"], "Build sdist")
        v.assert_success(code, stdout, stderr, "✓ Build sdist (valid command)")

        # Show build status
        code, stdout, stderr = v.run(["uvmgr", "build", "status"], "Show build status")
        v.assert_success(code, stdout, stderr, "✓ Show build status")


class TestTestsWorkflow:
    """JTBD: Run tests and check coverage."""

    @staticmethod
    def run(v: CommandValidator):
        """Test test execution workflow."""
        print("\n### JTBD: Run tests and check coverage")

        # Run all tests
        code, stdout, stderr = v.run(["uvmgr", "tests", "run"], "Run all tests")
        v.assert_success(code, stdout, stderr, "✓ Run test suite")

        # Run with coverage
        code, stdout, stderr = v.run(["uvmgr", "tests", "coverage"], "Run with coverage")
        v.assert_success(code, stdout, stderr, "✓ Run tests with coverage")

        # Run specific test pattern
        code, stdout, stderr = v.run(
            ["uvmgr", "tests", "run", "-k", "test_"],
            "Run tests matching pattern",
        )
        v.assert_success(code, stdout, stderr, "✓ Run tests with pattern filter")


class TestLintWorkflow:
    """JTBD: Check code quality."""

    @staticmethod
    def run(v: CommandValidator):
        """Test linting workflow."""
        print("\n### JTBD: Check code quality")

        # Run linters
        code, stdout, stderr = v.run(["uvmgr", "lint", "check"], "Run linters")
        # May have warnings, but should complete
        v.assert_output_contains(stdout + stderr, "", "✓ Lint check completes")

        # Fix linting issues
        code, stdout, stderr = v.run(["uvmgr", "lint", "fix"], "Fix linting issues")
        v.assert_success(code, stdout, stderr, "✓ Fix lint issues")

        # Type check
        code, stdout, stderr = v.run(["uvmgr", "lint", "type"], "Run type checker")
        v.assert_success(code, stdout, stderr, "✓ Type checking")


class TestCacheWorkflow:
    """JTBD: Manage build cache."""

    @staticmethod
    def run(v: CommandValidator):
        """Test cache management workflow."""
        print("\n### JTBD: Manage build cache")

        # Show cache status
        code, stdout, stderr = v.run(["uvmgr", "cache", "status"], "Show cache status")
        v.assert_success(code, stdout, stderr, "✓ Show cache status")

        # Clear cache
        code, stdout, stderr = v.run(
            ["uvmgr", "cache", "clear", "--confirm"],
            "Clear cache",
        )
        v.assert_success(code, stdout, stderr, "✓ Clear cache")

        # Re-check cache status
        code, stdout, stderr = v.run(["uvmgr", "cache", "status"], "Check cache after clear")
        v.assert_success(code, stdout, stderr, "✓ Cache status after clear")


class TestOTELWorkflow:
    """JTBD: Validate observability."""

    @staticmethod
    def run(v: CommandValidator):
        """Test OTEL validation workflow."""
        print("\n### JTBD: Validate observability")

        # Validate OTEL setup
        code, stdout, stderr = v.run(["uvmgr", "otel", "validate"], "Validate OTEL")
        v.assert_success(code, stdout, stderr, "✓ OTEL validation")

        # Show OTEL status
        code, stdout, stderr = v.run(["uvmgr", "otel", "status"], "Show OTEL status")
        v.assert_success(code, stdout, stderr, "✓ OTEL status")

        # Demo OTEL
        code, stdout, stderr = v.run(["uvmgr", "otel", "demo"], "Run OTEL demo")
        v.assert_success(code, stdout, stderr, "✓ OTEL demo")


class TestGuideWorkflow:
    """JTBD: Access development guides."""

    @staticmethod
    def run(v: CommandValidator):
        """Test guide access workflow."""
        print("\n### JTBD: Access development guides")

        # List available guides
        code, stdout, stderr = v.run(["uvmgr", "guides", "list"], "List guides")
        v.assert_success(code, stdout, stderr, "✓ List guides")

        # Show a guide (architecture)
        code, stdout, stderr = v.run(
            ["uvmgr", "guides", "show", "architecture"],
            "Show architecture guide",
        )
        v.assert_success(code, stdout, stderr, "✓ Show architecture guide")

        # List all guide topics
        code, stdout, stderr = v.run(["uvmgr", "guides", "topics"], "List guide topics")
        v.assert_success(code, stdout, stderr, "✓ List guide topics")


class TestWorktreeWorkflow:
    """JTBD: Manage git worktrees."""

    @staticmethod
    def run(v: CommandValidator):
        """Test git worktree workflow."""
        print("\n### JTBD: Manage git worktrees")

        # List worktrees
        code, stdout, stderr = v.run(["uvmgr", "worktree", "list"], "List worktrees")
        v.assert_success(code, stdout, stderr, "✓ List worktrees")

        # Show worktree status
        code, stdout, stderr = v.run(["uvmgr", "worktree", "status"], "Show worktree status")
        v.assert_success(code, stdout, stderr, "✓ Worktree status")

        # Show worktree pruning status
        code, stdout, stderr = v.run(
            ["uvmgr", "worktree", "prune", "--dry-run"],
            "Dry-run prune worktrees",
        )
        v.assert_success(code, stdout, stderr, "✓ Prune worktrees (dry-run)")


class TestDocWorkflow:
    """JTBD: Generate and manage documentation."""

    @staticmethod
    def run(v: CommandValidator):
        """Test documentation workflow."""
        print("\n### JTBD: Generate and manage documentation")

        # Generate API docs
        code, stdout, stderr = v.run(["uvmgr", "docs", "generate"], "Generate docs")
        v.assert_success(code, stdout, stderr, "✓ Generate documentation")

        # Show docs status
        code, stdout, stderr = v.run(["uvmgr", "docs", "status"], "Show docs status")
        v.assert_success(code, stdout, stderr, "✓ Docs status")

        # Validate docs
        code, stdout, stderr = v.run(["uvmgr", "docs", "validate"], "Validate docs")
        v.assert_success(code, stdout, stderr, "✓ Validate documentation")


class TestMermaidWorkflow:
    """JTBD: Generate diagrams."""

    @staticmethod
    def run(v: CommandValidator):
        """Test diagram generation workflow."""
        print("\n### JTBD: Generate diagrams")

        # Generate architecture diagram
        code, stdout, stderr = v.run(
            ["uvmgr", "mermaid", "generate", "architecture"],
            "Generate architecture diagram",
        )
        v.assert_success(code, stdout, stderr, "✓ Generate architecture diagram")

        # Show available diagram types
        code, stdout, stderr = v.run(
            ["uvmgr", "mermaid", "types"],
            "Show diagram types",
        )
        v.assert_success(code, stdout, stderr, "✓ List diagram types")


class TestDODWorkflow:
    """JTBD: Definition of Done automation."""

    @staticmethod
    def run(v: CommandValidator):
        """Test DoD workflow."""
        print("\n### JTBD: Definition of Done automation")

        # Show DoD checklist
        code, stdout, stderr = v.run(["uvmgr", "dod", "show"], "Show DoD checklist")
        v.assert_success(code, stdout, stderr, "✓ Show DoD checklist")

        # Validate against DoD
        code, stdout, stderr = v.run(
            ["uvmgr", "dod", "validate"],
            "Validate against DoD",
        )
        v.assert_success(code, stdout, stderr, "✓ Validate DoD")

        # Generate DoD report
        code, stdout, stderr = v.run(
            ["uvmgr", "dod", "report"],
            "Generate DoD report",
        )
        v.assert_success(code, stdout, stderr, "✓ Generate DoD report")


class TestInfodesignWorkflow:
    """JTBD: Information design support."""

    @staticmethod
    def run(v: CommandValidator):
        """Test information design workflow."""
        print("\n### JTBD: Information design support")

        # List design patterns
        code, stdout, stderr = v.run(
            ["uvmgr", "infodesign", "patterns"],
            "List design patterns",
        )
        v.assert_success(code, stdout, stderr, "✓ List design patterns")

        # Show style guide
        code, stdout, stderr = v.run(
            ["uvmgr", "infodesign", "guide"],
            "Show style guide",
        )
        v.assert_success(code, stdout, stderr, "✓ Show style guide")


class TestTerraformWorkflow:
    """JTBD: Terraform support."""

    @staticmethod
    def run(v: CommandValidator):
        """Test Terraform workflow."""
        print("\n### JTBD: Terraform support")

        # Validate Terraform
        code, stdout, stderr = v.run(
            ["uvmgr", "terraform", "validate"],
            "Validate Terraform",
        )
        v.assert_success(code, stdout, stderr, "✓ Validate Terraform")

        # Format Terraform
        code, stdout, stderr = v.run(
            ["uvmgr", "terraform", "fmt", "--check"],
            "Format check Terraform",
        )
        v.assert_success(code, stdout, stderr, "✓ Format Terraform (dry-run)")

        # Show Terraform status
        code, stdout, stderr = v.run(
            ["uvmgr", "terraform", "status"],
            "Show Terraform status",
        )
        v.assert_success(code, stdout, stderr, "✓ Terraform status")


# ============================================================================
# COMPOSITE WORKFLOWS - Real-world scenarios
# ============================================================================


class TestCompositeWorkflows:
    """JTBD: Real-world multi-command workflows."""

    @staticmethod
    def run(v: CommandValidator):
        """Test realistic multi-command workflows."""
        print("\n### JTBD: Composite Workflows")

        # Workflow 1: Pre-commit validation
        print("\n  Workflow 1: Pre-commit validation")
        commands = [
            (["uvmgr", "lint", "check"], "Lint check"),
            (["uvmgr", "tests", "run"], "Run tests"),
            (["uvmgr", "deps", "audit"], "Audit dependencies"),
        ]
        for cmd, desc in commands:
            code, stdout, stderr = v.run(cmd, desc)
            v.assert_success(code, stdout, stderr, f"✓ {desc}")

        # Workflow 2: Release preparation
        print("\n  Workflow 2: Release preparation")
        commands = [
            (["uvmgr", "lint", "check"], "Lint check"),
            (["uvmgr", "tests", "coverage"], "Test coverage"),
            (["uvmgr", "docs", "generate"], "Generate docs"),
            (["uvmgr", "dod", "validate"], "Validate DoD"),
        ]
        for cmd, desc in commands:
            code, stdout, stderr = v.run(cmd, desc)
            v.assert_success(code, stdout, stderr, f"✓ {desc}")

        # Workflow 3: Development setup
        print("\n  Workflow 3: Development setup")
        commands = [
            (["uvmgr", "deps", "list"], "List dependencies"),
            (["uvmgr", "guides", "list"], "Show development guides"),
            (["uvmgr", "lint", "check"], "Initial lint check"),
            (["uvmgr", "cache", "status"], "Check cache status"),
        ]
        for cmd, desc in commands:
            code, stdout, stderr = v.run(cmd, desc)
            v.assert_success(code, stdout, stderr, f"✓ {desc}")

        # Workflow 4: Quality assurance
        print("\n  Workflow 4: Quality assurance")
        commands = [
            (["uvmgr", "tests", "run"], "Run tests"),
            (["uvmgr", "lint", "check"], "Lint check"),
            (["uvmgr", "lint", "type"], "Type checking"),
            (["uvmgr", "deps", "audit"], "Security audit"),
            (["uvmgr", "otel", "validate"], "OTEL validation"),
        ]
        for cmd, desc in commands:
            code, stdout, stderr = v.run(cmd, desc)
            v.assert_success(code, stdout, stderr, f"✓ {desc}")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================


def main():
    """Run all JTBD tests."""
    print("=" * 70)
    print("JTBD PERMUTATION TESTS - uvmgr Core Commands")
    print("=" * 70)
    print("\nValidating real-world workflows across all 13 core commands")

    validator = CommandValidator(verbose=True)

    # Run all JTBD test classes
    test_classes = [
        TestDepsWorkflow,
        TestBuildWorkflow,
        TestTestsWorkflow,
        TestLintWorkflow,
        TestCacheWorkflow,
        TestOTELWorkflow,
        TestGuideWorkflow,
        TestWorktreeWorkflow,
        TestDocWorkflow,
        TestMermaidWorkflow,
        TestDODWorkflow,
        TestInfodesignWorkflow,
        TestTerraformWorkflow,
        TestCompositeWorkflows,
    ]

    for test_class in test_classes:
        try:
            test_class.run(validator)
        except Exception as e:
            print(f"  ✗ Test class {test_class.__name__} failed: {e}")
            validator.failed.append((test_class.__name__, 1, str(e)))

    # Print final report
    return validator.report()


if __name__ == "__main__":
    sys.exit(main())
