#!/usr/bin/env python3
"""
Apply Weaver Forge instrumentation templates to uvmgr source code.

This script reads the forge YAML files and extracts the Python code
to create the actual instrumentation modules.
"""

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ForgeApplicator:
    """Apply Weaver Forge templates to generate instrumentation code."""

    def __init__(self, forge_dir: Path, target_dir: Path):
        """Initialize with forge directory and target source directory."""
        self.forge_dir = forge_dir
        self.target_dir = target_dir
        self.applied_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def extract_template_content(self, forge_file: Path) -> str | None:
        """Extract the Python code from a forge YAML template."""
        try:
            with open(forge_file) as f:
                forge_data = yaml.safe_load(f)

            # Look for outputs with template content
            if "outputs" in forge_data:
                for output in forge_data["outputs"]:
                    if "template" in output:
                        # Extract the template content
                        template = output["template"]
                        # Remove leading | if present
                        template = template.removeprefix("|")
                        # Remove common leading whitespace
                        lines = template.strip().split("\n")
                        if lines:
                            # Find minimum indentation
                            min_indent = min(
                                len(line) - len(line.lstrip())
                                for line in lines
                                if line.strip()
                            )
                            # Remove that indentation from all lines
                            cleaned_lines = [
                                line[min_indent:] if len(line) > min_indent else line
                                for line in lines
                            ]
                            return "\n".join(cleaned_lines)

            return None

        except Exception as e:
            print(f"❌ Error reading {forge_file}: {e}")
            return None

    def apply_core_infrastructure(self):
        """Apply core infrastructure templates."""
        print("\n🏗️  Applying Core Infrastructure")
        print("=" * 40)

        core_templates = [
            ("instrumentation.forge.yaml", "src/uvmgr/core/instrumentation.py"),
            ("semantic-conventions.forge.yaml", "src/uvmgr/core/semconv.py"),
        ]

        for forge_name, target_path in core_templates:
            forge_file = self.forge_dir / "core-infrastructure" / forge_name
            target_file = self.target_dir / target_path

            if target_file.exists():
                print(f"✅ {target_path} already exists, skipping")
                self.skipped_count += 1
                continue

            if not forge_file.exists():
                print(f"❌ Forge template not found: {forge_file}")
                self.error_count += 1
                continue

            content = self.extract_template_content(forge_file)
            if content:
                # Ensure directory exists
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # Write the file
                with open(target_file, "w") as f:
                    f.write(content)

                print(f"✅ Created {target_path}")
                self.applied_count += 1
            else:
                print(f"❌ No template content found in {forge_name}")
                self.error_count += 1

    def check_command_instrumentation(self):
        """Check which commands need instrumentation."""
        print("\n🎯 Checking Command Instrumentation")
        print("=" * 40)

        commands_dir = self.target_dir / "src/uvmgr/commands"

        if not commands_dir.exists():
            print(f"❌ Commands directory not found: {commands_dir}")
            return

        # Get all command modules
        command_files = list(commands_dir.glob("*.py"))
        command_files = [f for f in command_files if f.name != "__init__.py"]

        instrumented = []
        not_instrumented = []

        for cmd_file in sorted(command_files):
            content = cmd_file.read_text()

            # Check if already instrumented
            if "instrument_command" in content:
                instrumented.append(cmd_file.stem)
            else:
                not_instrumented.append(cmd_file.stem)

        print(f"\n✅ Already instrumented ({len(instrumented)}):")
        for cmd in instrumented:
            print(f"   - {cmd}")

        print(f"\n⚠️  Need instrumentation ({len(not_instrumented)}):")
        for cmd in not_instrumented:
            print(f"   - {cmd}")

            # Check if forge template exists
            forge_file = self.forge_dir / "command-instrumentation" / "commands" / f"{cmd}.forge.yaml"
            if forge_file.exists():
                print("     → Forge template available")
            else:
                print("     → No forge template yet")

        # Calculate coverage
        total = len(command_files)
        coverage = (len(instrumented) / total * 100) if total > 0 else 0

        print(f"\n📊 Command instrumentation coverage: {coverage:.1f}% ({len(instrumented)}/{total})")

    def check_subprocess_usage(self):
        """Check for direct subprocess usage that needs fixing."""
        print("\n🔧 Checking for Direct Subprocess Usage")
        print("=" * 40)

        # Commands known to use subprocess directly
        subprocess_commands = ["tests.py", "lint.py"]

        for cmd_name in subprocess_commands:
            cmd_file = self.target_dir / "src/uvmgr/commands" / cmd_name

            if not cmd_file.exists():
                continue

            content = cmd_file.read_text()

            # Check for subprocess usage
            if "subprocess.run" in content:
                if "run_logged" in content:
                    print(f"✅ {cmd_name} - subprocess usage already fixed")
                else:
                    print(f"⚠️  {cmd_name} - uses subprocess.run directly, needs fixing")
            else:
                print(f"✅ {cmd_name} - no direct subprocess usage")

    def generate_summary(self):
        """Generate a summary of the application process."""
        print("\n📊 Summary")
        print("=" * 40)
        print(f"Applied: {self.applied_count}")
        print(f"Skipped: {self.skipped_count}")
        print(f"Errors: {self.error_count}")

        print("\n🚀 Next Steps:")
        print("1. Review generated files in src/uvmgr/core/")
        print("2. Apply command-specific instrumentation manually or with patches")
        print("3. Fix subprocess usage in tests.py and lint.py")
        print("4. Test with: OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 uvmgr <command>")
        print("5. Run validation: python scripts/validate-coverage.py")


def main():
    """Main entry point."""
    # Determine paths
    script_path = Path(__file__).resolve()
    forge_dir = script_path.parent.parent  # weaver-forge directory
    project_root = forge_dir.parent  # uvmgr project root

    print("🔨 Weaver Forge Instrumentation Applicator")
    print(f"Project root: {project_root}")
    print(f"Forge directory: {forge_dir}")

    # Create applicator
    applicator = ForgeApplicator(forge_dir, project_root)

    # Apply core infrastructure
    applicator.apply_core_infrastructure()

    # Check command instrumentation status
    applicator.check_command_instrumentation()

    # Check subprocess usage
    applicator.check_subprocess_usage()

    # Generate summary
    applicator.generate_summary()

    # Return exit code based on errors
    return 1 if applicator.error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
