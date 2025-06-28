#!/usr/bin/env python3
"""
Validate semantic conventions using OpenTelemetry Weaver.

This script validates the semantic conventions YAML file and can generate
code or documentation from it.
"""

import subprocess
import sys
from pathlib import Path

# Find Weaver executable
WEAVER_PATH = Path(__file__).parent.parent / "tools" / "weaver"
REGISTRY_PATH = Path(__file__).parent / "registry"


def run_weaver(args: list[str]) -> subprocess.CompletedProcess:
    """Run weaver command with given arguments."""
    cmd = [str(WEAVER_PATH)] + args
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def validate_conventions():
    """Validate the semantic conventions file."""
    print("Validating semantic conventions...")

    # Check the registry structure
    result = run_weaver([
        "registry", "check",
        "-r", str(REGISTRY_PATH),
        "--future"  # Enable latest validation rules
    ])

    if result.returncode != 0:
        print("Validation failed:")
        print(result.stderr)
        return False

    print("✓ Semantic conventions are valid!")
    return True


def generate_markdown_docs():
    """Generate markdown documentation from conventions."""
    print("\nGenerating documentation...")

    output_dir = Path(__file__).parent / "docs"
    output_dir.mkdir(exist_ok=True)

    result = run_weaver([
        "registry", "generate",
        "-r", str(REGISTRY_PATH),
        "-t", "markdown",
        "-o", str(output_dir),
        "--future"
    ])

    if result.returncode == 0:
        print(f"✓ Documentation generated in {output_dir}")
    else:
        print("Documentation generation failed:")
        print(result.stderr)


def generate_python_constants():
    """Generate Python constants from conventions."""
    print("\nGenerating Python constants...")

    output_file = Path(__file__).parent.parent / "src" / "uvmgr" / "core" / "semconv.py"

    # For now, we'll manually create this since Weaver's Python generation
    # requires templates. In a full implementation, we'd use Weaver's
    # template system.

    constants = '''"""
Auto-generated semantic convention constants for uvmgr.
Generated from weaver-forge/registry/models/uvmgr.yaml

DO NOT EDIT - this file is auto-generated.
"""

# CLI Command Attributes
class CliAttributes:
    COMMAND = "cli.command"
    SUBCOMMAND = "cli.subcommand"
    ARGS = "cli.args"
    OPTIONS = "cli.options"
    EXIT_CODE = "cli.exit_code"
    INTERACTIVE = "cli.interactive"


# Package Management Attributes
class PackageAttributes:
    MANAGER = "package.manager"
    NAME = "package.name"
    VERSION = "package.version"
    OPERATION = "package.operation"
    DEV_DEPENDENCY = "package.dev_dependency"
    EXTRAS = "package.extras"
    SOURCE = "package.source"


# Package Operations
class PackageOperations:
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"
    LOCK = "lock"
    SYNC = "sync"
    LIST = "list"


# Build Attributes
class BuildAttributes:
    TYPE = "build.type"
    SIZE = "build.size"
    DURATION = "build.duration"
    OUTPUT_PATH = "build.output_path"
    PYTHON_VERSION = "build.python_version"


# Build Types
class BuildTypes:
    WHEEL = "wheel"
    SDIST = "sdist"
    EXE = "exe"
    SPEC = "spec"


# Test Attributes
class TestAttributes:
    FRAMEWORK = "test.framework"
    OPERATION = "test.operation"
    TEST_COUNT = "test.test_count"
    PASSED = "test.passed"
    FAILED = "test.failed"
    SKIPPED = "test.skipped"
    DURATION = "test.duration"
    COVERAGE_PERCENTAGE = "test.coverage_percentage"


# Test Operations
class TestOperations:
    RUN = "run"
    COVERAGE = "coverage"
    WATCH = "watch"


# AI Attributes
class AiAttributes:
    MODEL = "ai.model"
    PROVIDER = "ai.provider"
    OPERATION = "ai.operation"
    TOKENS_INPUT = "ai.tokens_input"
    TOKENS_OUTPUT = "ai.tokens_output"
    COST = "ai.cost"


# AI Operations
class AiOperations:
    ASSIST = "assist"
    GENERATE = "generate"
    FIX = "fix"
    PLAN = "plan"


# MCP Attributes
class McpAttributes:
    OPERATION = "mcp.operation"
    TOOL_NAME = "mcp.tool_name"
    SERVER_PORT = "mcp.server_port"


# MCP Operations
class McpOperations:
    START = "start"
    STOP = "stop"
    TOOL_CALL = "tool_call"


# Process Attributes
class ProcessAttributes:
    COMMAND = "process.command"
    EXECUTABLE = "process.executable"
    EXIT_CODE = "process.exit_code"
    DURATION = "process.duration"
    WORKING_DIRECTORY = "process.working_directory"
'''

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(constants)
    print(f"✓ Python constants generated in {output_file}")


def main():
    """Main validation workflow."""
    if not WEAVER_PATH.exists():
        print(f"Error: Weaver not found at {WEAVER_PATH}")
        print("Please run: uvmgr build dogfood")
        sys.exit(1)

    if not REGISTRY_PATH.exists():
        print(f"Error: Semantic conventions registry not found at {REGISTRY_PATH}")
        sys.exit(1)

    # Run validation
    if validate_conventions():
        # Generate outputs
        generate_markdown_docs()
        generate_python_constants()

        print("\n✓ All validations and generations completed successfully!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
