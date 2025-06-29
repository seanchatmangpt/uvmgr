#!/usr/bin/env python3
"""
uvmgr External Project Installer
===============================

This script provides a streamlined way to install uvmgr in external projects
without requiring it to be globally installed.
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional


class UvmgrInstaller:
    """Install uvmgr in external projects."""
    
    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = target_dir or Path.cwd()
        self.uvmgr_repo = "https://github.com/your-org/uvmgr.git"  # Update with actual repo
        
    def detect_project_type(self) -> str:
        """Detect the type of Python project."""
        if (self.target_dir / "pyproject.toml").exists():
            return "modern"
        elif (self.target_dir / "setup.py").exists():
            return "legacy"
        elif (self.target_dir / "requirements.txt").exists():
            return "requirements"
        else:
            return "unknown"
    
    def install_via_uv(self) -> bool:
        """Install uvmgr using uv (fastest method)."""
        try:
            # Check if uv is available
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                return False
            
            # Install uvmgr from PyPI (when published)
            # For now, install from git
            install_cmd = [
                "uv", "add", "--dev", 
                "uvmgr @ git+https://github.com/your-org/uvmgr.git"
            ]
            
            result = subprocess.run(install_cmd, cwd=self.target_dir, capture_output=True, text=True)
            return result.returncode == 0
            
        except FileNotFoundError:
            return False
    
    def install_via_pip(self) -> bool:
        """Install uvmgr using pip (fallback method)."""
        try:
            # Use current Python interpreter
            install_cmd = [
                sys.executable, "-m", "pip", "install",
                "git+https://github.com/your-org/uvmgr.git"
            ]
            
            result = subprocess.run(install_cmd, cwd=self.target_dir, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def install_from_source(self) -> bool:
        """Install uvmgr from source (development method)."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                clone_dir = Path(tmpdir) / "uvmgr"
                
                # Clone repository
                clone_cmd = ["git", "clone", self.uvmgr_repo, str(clone_dir)]
                result = subprocess.run(clone_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return False
                
                # Install in development mode
                install_cmd = [sys.executable, "-m", "pip", "install", "-e", str(clone_dir)]
                result = subprocess.run(install_cmd, cwd=self.target_dir, capture_output=True, text=True)
                return result.returncode == 0
                
        except Exception:
            return False
    
    def create_uvmgr_wrapper(self) -> None:
        """Create a local uvmgr wrapper script."""
        wrapper_path = self.target_dir / "uvmgr"
        wrapper_content = f'''#!/usr/bin/env python3
"""Local uvmgr wrapper for this project."""

import sys
import subprocess
from pathlib import Path

# Try to use uvmgr from current environment
try:
    import uvmgr.cli
    uvmgr.cli.app()
except ImportError:
    print("❌ uvmgr not found in current environment")
    print("Run: pip install uvmgr")
    sys.exit(1)
'''
        
        wrapper_path.write_text(wrapper_content)
        wrapper_path.chmod(0o755)
        print(f"✅ Created uvmgr wrapper at: {wrapper_path}")
    
    def verify_installation(self) -> bool:
        """Verify that uvmgr is properly installed and working."""
        try:
            # Test basic import
            result = subprocess.run(
                [sys.executable, "-c", "import uvmgr; print('OK')"],
                cwd=self.target_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False
            
            # Test CLI functionality
            result = subprocess.run(
                [sys.executable, "-m", "uvmgr", "--version"],
                cwd=self.target_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
            
        except Exception:
            return False
    
    def setup_project_config(self) -> None:
        """Set up uvmgr configuration for the project."""
        config_dir = self.target_dir / ".uvmgr"
        config_dir.mkdir(exist_ok=True)
        
        # Create basic configuration
        config = {
            "version": "1.0",
            "project": {
                "name": self.target_dir.name,
                "type": self.detect_project_type()
            },
            "tools": {
                "dependencies": "uv" if self.has_uv() else "pip",
                "testing": "pytest",
                "linting": "ruff"
            },
            "telemetry": {
                "enabled": True,
                "endpoint": "console"
            }
        }
        
        config_path = config_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Created uvmgr config at: {config_path}")
    
    def has_uv(self) -> bool:
        """Check if uv is available."""
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def install(self) -> bool:
        """Install uvmgr using the best available method."""
        project_type = self.detect_project_type()
        print(f"📁 Detected project type: {project_type}")
        print(f"📂 Installing uvmgr in: {self.target_dir}")
        
        # Try installation methods in order of preference
        methods = [
            ("uv", self.install_via_uv),
            ("pip", self.install_via_pip),
            ("source", self.install_from_source)
        ]
        
        for method_name, method_func in methods:
            print(f"🔄 Trying installation via {method_name}...")
            try:
                if method_func():
                    print(f"✅ Successfully installed via {method_name}")
                    
                    # Verify installation
                    if self.verify_installation():
                        print("✅ Installation verified")
                        
                        # Set up project configuration
                        self.setup_project_config()
                        
                        # Create wrapper script
                        self.create_uvmgr_wrapper()
                        
                        return True
                    else:
                        print(f"❌ Installation verification failed for {method_name}")
                else:
                    print(f"❌ Installation via {method_name} failed")
            except Exception as e:
                print(f"❌ Error during {method_name} installation: {e}")
        
        print("❌ All installation methods failed")
        return False


def main():
    """Main installer function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Install uvmgr in external projects")
    parser.add_argument("--path", type=Path, help="Target project directory", default=Path.cwd())
    parser.add_argument("--force", action="store_true", help="Force reinstallation")
    args = parser.parse_args()
    
    print("🚀 uvmgr External Project Installer")
    print("=" * 40)
    
    installer = UvmgrInstaller(args.path)
    
    # Check if already installed (unless forced)
    if not args.force and installer.verify_installation():
        print("✅ uvmgr is already installed and working")
        return
    
    # Perform installation
    if installer.install():
        print("\n🎉 uvmgr installation completed successfully!")
        print("\nNext steps:")
        print("1. Run: uvmgr --help")
        print("2. Try: uvmgr deps list")
        print("3. See: uvmgr otel validate")
    else:
        print("\n❌ uvmgr installation failed")
        print("\nManual installation options:")
        print("1. pip install uvmgr")
        print("2. uv add uvmgr")
        print("3. pip install git+https://github.com/your-org/uvmgr.git")
        sys.exit(1)


if __name__ == "__main__":
    main()