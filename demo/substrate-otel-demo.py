#!/usr/bin/env python3
"""
Substrate + OTEL Demo
====================

This demonstrates a complete workflow for creating and using a Substrate project
with full OTEL instrumentation via uvmgr.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, cwd: Path = None) -> bool:
    """Run a command and return success status."""
    print(f"\n🚀 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Success")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print(f"❌ Failed with code {result.returncode}")
        if result.stderr:
            print(result.stderr)
        return False


def main():
    """Run the complete Substrate + OTEL demo."""
    print("=" * 60)
    print("🎯 Substrate + OTEL Integration Demo")
    print("=" * 60)
    
    # Step 1: Create project
    project_name = "demo-otel-app"
    project_dir = Path.cwd() / "demo" / project_name
    
    print(f"\n📦 Step 1: Creating Substrate project '{project_name}'...")
    if not run_command(f"python -m uvmgr substrate create {project_name} --type cli --output demo"):
        print("Failed to create project")
        return 1
    
    print(f"\n✅ Project created at: {project_dir}")
    
    # Step 2: Show project structure
    print("\n📁 Step 2: Project Structure:")
    run_command(f"ls -la {project_dir}")
    
    # Step 3: Show OTEL features
    print("\n🔍 Step 3: OTEL Features Added:")
    
    print("\n📄 pyproject.toml OTEL dependencies:")
    run_command(f"grep -A 5 'opentelemetry' {project_dir}/pyproject.toml")
    
    print("\n🛠️ uvmgr Poe tasks:")
    run_command(f"grep -E 'otel-|spiff-|telemetry-' {project_dir}/pyproject.toml -A 2")
    
    print("\n📊 Telemetry module:")
    if (project_dir / "src" / "demo_otel_app" / "_telemetry.py").exists():
        print("✅ _telemetry.py created")
        run_command(f"head -20 {project_dir}/src/demo_otel_app/_telemetry.py")
    
    print("\n💡 CLI Example:")
    if (project_dir / "examples" / "cli_with_otel.py").exists():
        print("✅ examples/cli_with_otel.py created")
        run_command(f"cat {project_dir}/examples/cli_with_otel.py")
    
    # Step 4: Show how to use
    print("\n📚 Step 4: How to Use:")
    print("""
    # 1. Navigate to project
    cd demo/demo-otel-app
    
    # 2. Install dependencies
    uv sync --all-extras
    
    # 3. Test telemetry
    python -c "from src.demo_otel_app import tracer, meter; print('✅ OTEL Ready')"
    
    # 4. Run example CLI
    python examples/cli_with_otel.py --name "OTEL User"
    
    # 5. Validate with uvmgr
    uvmgr spiff-otel external-validate . --mode 8020
    
    # 6. Use Poe tasks
    poe otel-validate
    poe telemetry-test
    """)
    
    print("\n🎉 Demo Complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())