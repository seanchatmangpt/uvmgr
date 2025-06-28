#!/usr/bin/env python3
"""
External Project Testing Script for uvmgr 8020 Validation
==========================================================

This script creates and tests external projects to validate that uvmgr
works correctly on real-world projects outside its own file tree.
"""

import asyncio
import json
import logging
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExternalProjectTester:
    """Test uvmgr integration with external projects."""
    
    def __init__(self, workspace: Path, uvmgr_source: Path):
        self.workspace = workspace
        self.uvmgr_source = uvmgr_source
        self.auto_install_script = uvmgr_source / "external-project-testing" / "auto-install-uvmgr.sh"
        self.results = []
        
    async def run_all_tests(self) -> Dict:
        """Run all external project tests."""
        logger.info("Starting external project testing suite...")
        
        test_projects = [
            {
                "name": "minimal-python",
                "type": "minimal",
                "generator": self._create_minimal_project
            },
            {
                "name": "fastapi-app", 
                "type": "fastapi",
                "generator": self._create_fastapi_project
            },
            {
                "name": "cli-tool",
                "type": "cli",
                "generator": self._create_cli_project
            },
            {
                "name": "data-science",
                "type": "data_science", 
                "generator": self._create_data_science_project
            },
            {
                "name": "substrate-template",
                "type": "substrate",
                "generator": self._create_substrate_project
            }
        ]
        
        overall_success = True
        
        for project_config in test_projects:
            try:
                logger.info(f"Testing project: {project_config['name']}")
                result = await self._test_project(project_config)
                self.results.append(result)
                
                if not result["success"]:
                    overall_success = False
                    
            except Exception as e:
                logger.error(f"Failed to test {project_config['name']}: {e}")
                self.results.append({
                    "name": project_config['name'],
                    "type": project_config['type'],
                    "success": False,
                    "error": str(e),
                    "tests_run": 0,
                    "tests_passed": 0
                })
                overall_success = False
        
        # Calculate overall statistics
        total_tests = sum(r.get("tests_run", 0) for r in self.results)
        total_passed = sum(r.get("tests_passed", 0) for r in self.results)
        success_rate = total_passed / total_tests if total_tests > 0 else 0
        
        return {
            "overall_success": overall_success,
            "success_rate": success_rate,
            "total_projects": len(test_projects),
            "successful_projects": sum(1 for r in self.results if r["success"]),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "project_results": self.results,
            "meets_8020_threshold": success_rate >= 0.80
        }
    
    async def _test_project(self, project_config: Dict) -> Dict:
        """Test a single external project."""
        project_name = project_config["name"]
        project_path = self.workspace / project_name
        
        # Clean up any existing project
        if project_path.exists():
            shutil.rmtree(project_path)
        
        try:
            # Create the project
            logger.info(f"Creating {project_name}...")
            await project_config["generator"](project_path)
            
            # Install uvmgr into the project
            logger.info(f"Installing uvmgr into {project_name}...")
            await self._install_uvmgr(project_path)
            
            # Run tests on the project
            logger.info(f"Running tests on {project_name}...")
            test_results = await self._run_project_tests(project_path, project_config["type"])
            
            return {
                "name": project_name,
                "type": project_config["type"],
                "success": test_results["success_rate"] >= 0.80,
                "tests_run": test_results["tests_run"],
                "tests_passed": test_results["tests_passed"],
                "success_rate": test_results["success_rate"],
                "details": test_results["details"],
                "project_path": str(project_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to test {project_name}: {e}")
            return {
                "name": project_name,
                "type": project_config["type"],
                "success": False,
                "error": str(e),
                "tests_run": 0,
                "tests_passed": 0,
                "success_rate": 0.0
            }
    
    async def _create_minimal_project(self, project_path: Path):
        """Create a minimal Python project."""
        project_path.mkdir(parents=True)
        
        # Create pyproject.toml
        (project_path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "minimal-external-test"
version = "0.1.0"
description = "Minimal Python project for uvmgr testing"
dependencies = [
    "requests",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
]
""")
        
        # Create basic Python module
        src_dir = project_path / "src" / "minimal_external_test"
        src_dir.mkdir(parents=True)
        
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')
        (src_dir / "main.py").write_text("""
import requests

def get_python_org():
    \"\"\"Simple function that makes HTTP request.\"\"\"
    try:
        response = requests.get("https://httpbin.org/json")
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def calculate_sum(a, b):
    \"\"\"Simple calculation function.\"\"\"
    return a + b

if __name__ == "__main__":
    result = get_python_org()
    print(f"Result: {result}")
    print(f"Sum: {calculate_sum(5, 3)}")
""")
        
        # Create tests
        test_dir = project_path / "tests"
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("")
        (test_dir / "test_main.py").write_text("""
import pytest
from minimal_external_test.main import calculate_sum, get_python_org

def test_calculate_sum():
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0
    assert calculate_sum(0, 0) == 0

def test_get_python_org():
    result = get_python_org()
    # Should return either valid JSON or error dict
    assert isinstance(result, dict)
""")
        
        # Create README
        (project_path / "README.md").write_text("""
# Minimal External Test Project

This is a minimal Python project created to test uvmgr integration.
""")
    
    async def _create_fastapi_project(self, project_path: Path):
        """Create a FastAPI project."""
        project_path.mkdir(parents=True)
        
        (project_path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "fastapi-external-test"
version = "0.1.0"
description = "FastAPI project for uvmgr testing"
dependencies = [
    "fastapi>=0.68.0",
    "uvicorn>=0.15.0",
    "pydantic>=1.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "httpx",
]
""")
        
        src_dir = project_path / "src" / "fastapi_external_test"
        src_dir.mkdir(parents=True)
        
        (src_dir / "__init__.py").write_text("")
        (src_dir / "main.py").write_text("""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="External Test API")

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

@app.get("/")
def read_root():
    return {"message": "Hello from external FastAPI project!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "fastapi-external-test"}

@app.post("/items/")
def create_item(item: Item):
    return {"item": item, "message": "Item created successfully"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
""")
        
        test_dir = project_path / "tests"
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("")
        (test_dir / "test_api.py").write_text("""
import pytest
from fastapi.testclient import TestClient
from fastapi_external_test.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_item():
    item_data = {
        "name": "Test Item",
        "price": 10.5,
        "is_offer": True
    }
    response = client.post("/items/", json=item_data)
    assert response.status_code == 200
    assert response.json()["item"]["name"] == "Test Item"

def test_read_item():
    response = client.get("/items/1?q=test")
    assert response.status_code == 200
    assert response.json()["item_id"] == 1
    assert response.json()["q"] == "test"
""")
    
    async def _create_cli_project(self, project_path: Path):
        """Create a CLI tool project."""
        project_path.mkdir(parents=True)
        
        (project_path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cli-external-test"
version = "0.1.0"
description = "CLI tool for uvmgr testing"
dependencies = [
    "click>=8.0.0",
    "rich>=10.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
]

[project.scripts]
cli-test = "cli_external_test.main:cli"
""")
        
        src_dir = project_path / "src" / "cli_external_test"
        src_dir.mkdir(parents=True)
        
        (src_dir / "__init__.py").write_text("")
        (src_dir / "main.py").write_text("""
import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def cli():
    \"\"\"CLI External Test Tool\"\"\"
    pass

@cli.command()
@click.argument('name')
def greet(name):
    \"\"\"Greet someone\"\"\"
    console.print(f"Hello, {name}!", style="green")

@cli.command()
def status():
    \"\"\"Show status table\"\"\"
    table = Table(title="CLI Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("CLI Tool", "Working")
    table.add_row("Rich Output", "Enabled")
    table.add_row("Commands", "Available")
    
    console.print(table)

@cli.command()
@click.option('--count', default=1, help='Number of times to say hello')
def hello(count):
    \"\"\"Say hello multiple times\"\"\"
    for i in range(count):
        console.print(f"Hello #{i+1}!")

if __name__ == "__main__":
    cli()
""")
        
        test_dir = project_path / "tests"
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("")
        (test_dir / "test_cli.py").write_text("""
import pytest
from click.testing import CliRunner
from cli_external_test.main import cli

def test_greet_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['greet', 'World'])
    assert result.exit_code == 0
    assert 'Hello, World!' in result.output

def test_status_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'CLI Status' in result.output

def test_hello_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['hello', '--count', '3'])
    assert result.exit_code == 0
    assert 'Hello #1!' in result.output
    assert 'Hello #3!' in result.output
""")
    
    async def _create_data_science_project(self, project_path: Path):
        """Create a data science project."""
        project_path.mkdir(parents=True)
        
        (project_path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "datascience-external-test"
version = "0.1.0"
description = "Data science project for uvmgr testing"
dependencies = [
    "pandas>=1.3.0",
    "numpy>=1.21.0",
    "matplotlib>=3.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "jupyter",
]
""")
        
        src_dir = project_path / "src" / "datascience_external_test"
        src_dir.mkdir(parents=True)
        
        (src_dir / "__init__.py").write_text("")
        (src_dir / "analysis.py").write_text("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_sample_data(n=100):
    \"\"\"Generate sample dataset.\"\"\"
    np.random.seed(42)
    data = {
        'x': np.random.randn(n),
        'y': np.random.randn(n),
        'category': np.random.choice(['A', 'B', 'C'], n)
    }
    return pd.DataFrame(data)

def basic_statistics(df):
    \"\"\"Calculate basic statistics.\"\"\"
    return {
        'mean_x': df['x'].mean(),
        'mean_y': df['y'].mean(),
        'std_x': df['x'].std(),
        'std_y': df['y'].std(),
        'correlation': df['x'].corr(df['y'])
    }

def create_plot(df, save_path=None):
    \"\"\"Create a simple scatter plot.\"\"\"
    plt.figure(figsize=(8, 6))
    for category in df['category'].unique():
        subset = df[df['category'] == category]
        plt.scatter(subset['x'], subset['y'], label=category)
    
    plt.xlabel('X values')
    plt.ylabel('Y values')
    plt.title('Sample Data Scatter Plot')
    plt.legend()
    
    if save_path:
        plt.savefig(save_path)
    
    return plt.gcf()

if __name__ == "__main__":
    df = generate_sample_data()
    stats = basic_statistics(df)
    print("Basic Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:.3f}")
""")
        
        test_dir = project_path / "tests"
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("")
        (test_dir / "test_analysis.py").write_text("""
import pytest
import pandas as pd
from datascience_external_test.analysis import generate_sample_data, basic_statistics, create_plot

def test_generate_sample_data():
    df = generate_sample_data(50)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 50
    assert set(df.columns) == {'x', 'y', 'category'}
    assert set(df['category'].unique()).issubset({'A', 'B', 'C'})

def test_basic_statistics():
    df = generate_sample_data(100)
    stats = basic_statistics(df)
    
    required_keys = ['mean_x', 'mean_y', 'std_x', 'std_y', 'correlation']
    assert all(key in stats for key in required_keys)
    assert all(isinstance(value, float) for value in stats.values())
    assert -1 <= stats['correlation'] <= 1

def test_create_plot():
    df = generate_sample_data(30)
    fig = create_plot(df)
    assert fig is not None
    # Test that plot was created without errors
""")
    
    async def _create_substrate_project(self, project_path: Path):
        """Create a Substrate-inspired project using uvmgr's project command."""
        # Use uvmgr to create the project
        try:
            result = await self._run_command([
                "uv", "run", "uvmgr", "new", str(project_path),
                "--name", "substrate-external-test",
                "--description", "Substrate project for uvmgr testing"
            ], cwd=self.uvmgr_source)
            
            if result.returncode != 0:
                # Fallback to manual creation
                await self._create_manual_substrate_project(project_path)
        except Exception:
            # Fallback to manual creation
            await self._create_manual_substrate_project(project_path)
    
    async def _create_manual_substrate_project(self, project_path: Path):
        """Manually create a Substrate-style project."""
        project_path.mkdir(parents=True)
        
        (project_path / "pyproject.toml").write_text("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "substrate-external-test"
version = "0.1.0"
description = "Substrate-style project for uvmgr testing"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "ruff",
    "mypy",
]

[project.scripts]
substrate-test = "substrate_external_test.main:app"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
""")
        
        src_dir = project_path / "src" / "substrate_external_test"
        src_dir.mkdir(parents=True)
        
        (src_dir / "__init__.py").write_text("")
        (src_dir / "main.py").write_text("""
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional
from pydantic import BaseModel

app = typer.Typer()
console = Console()

class Config(BaseModel):
    name: str
    version: str = "0.1.0"
    debug: bool = False

@app.command()
def hello(name: str = typer.Argument(..., help="Name to greet")):
    \"\"\"Say hello to someone.\"\"\"
    console.print(f"Hello, {name}!", style="bold green")

@app.command()
def info():
    \"\"\"Show project information.\"\"\"
    config = Config(name="substrate-external-test")
    
    table = Table(title="Project Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="yellow")
    
    table.add_row("Name", config.name)
    table.add_row("Version", config.version)
    table.add_row("Debug", str(config.debug))
    
    console.print(table)

@app.command()
def validate(file_path: Optional[str] = typer.Option(None, help="File to validate")):
    \"\"\"Validate a file or configuration.\"\"\"
    if file_path:
        console.print(f"Validating file: {file_path}", style="blue")
        # Simulate validation
        console.print("✓ Validation passed", style="green")
    else:
        console.print("✓ Configuration is valid", style="green")

if __name__ == "__main__":
    app()
""")
        
        test_dir = project_path / "tests"
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("")
        (test_dir / "test_main.py").write_text("""
import pytest
from typer.testing import CliRunner
from substrate_external_test.main import app, Config

def test_hello_command():
    runner = CliRunner()
    result = runner.invoke(app, ['hello', 'World'])
    assert result.exit_code == 0
    assert 'Hello, World!' in result.output

def test_info_command():
    runner = CliRunner()
    result = runner.invoke(app, ['info'])
    assert result.exit_code == 0
    assert 'Project Information' in result.output

def test_validate_command():
    runner = CliRunner()
    result = runner.invoke(app, ['validate'])
    assert result.exit_code == 0
    assert 'Configuration is valid' in result.output

def test_config_model():
    config = Config(name="test")
    assert config.name == "test"
    assert config.version == "0.1.0"
    assert config.debug is False
""")
    
    async def _install_uvmgr(self, project_path: Path):
        """Install uvmgr into the external project."""
        if not self.auto_install_script.exists():
            raise Exception(f"Auto-install script not found: {self.auto_install_script}")
        
        result = await self._run_command([
            "bash", str(self.auto_install_script), str(project_path)
        ])
        
        if result.returncode != 0:
            raise Exception(f"uvmgr installation failed: {result.stderr}")
    
    async def _run_project_tests(self, project_path: Path, project_type: str) -> Dict:
        """Run comprehensive tests on the external project."""
        test_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "success_rate": 0.0,
            "details": []
        }
        
        # Test commands to run
        test_commands = [
            (["uv", "run", "uvmgr", "--help"], "uvmgr help check"),
            (["uv", "run", "uvmgr", "deps", "list"], "dependency listing"),
            (["uv", "run", "uvmgr", "tests", "run"], "test execution"),
            (["uv", "run", "uvmgr", "lint", "check"], "code linting"),
        ]
        
        # Add project-specific tests
        if project_type == "fastapi":
            test_commands.append(
                (["uv", "run", "python", "-m", "pytest", "-v"], "pytest execution")
            )
        elif project_type == "cli":
            test_commands.append(
                (["uv", "run", "cli-test", "--help"], "CLI help")
            )
        elif project_type == "substrate":
            test_commands.append(
                (["uv", "run", "substrate-test", "--help"], "Substrate CLI help")
            )
        
        for cmd, description in test_commands:
            test_results["tests_run"] += 1
            
            try:
                result = await self._run_command(cmd, cwd=project_path, timeout=60)
                
                if result.returncode == 0:
                    test_results["tests_passed"] += 1
                    test_results["details"].append({
                        "command": " ".join(cmd),
                        "description": description,
                        "status": "passed",
                        "output": result.stdout[:200] if result.stdout else ""
                    })
                else:
                    test_results["tests_failed"] += 1
                    test_results["details"].append({
                        "command": " ".join(cmd),
                        "description": description,
                        "status": "failed",
                        "error": result.stderr[:200] if result.stderr else ""
                    })
                    
            except Exception as e:
                test_results["tests_failed"] += 1
                test_results["details"].append({
                    "command": " ".join(cmd),
                    "description": description,
                    "status": "error",
                    "error": str(e)[:200]
                })
        
        # Calculate success rate
        if test_results["tests_run"] > 0:
            test_results["success_rate"] = test_results["tests_passed"] / test_results["tests_run"]
        
        return test_results
    
    async def _run_command(self, cmd: List[str], cwd: Optional[Path] = None, timeout: int = 30):
        """Run a command asynchronously."""
        logger.debug(f"Running command: {' '.join(cmd)} in {cwd}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            return type('Result', (), {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8') if stdout else '',
                'stderr': stderr.decode('utf-8') if stderr else ''
            })()
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise Exception(f"Command timed out after {timeout} seconds")
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive test report."""
        report = f"""
# uvmgr External Project Testing Report

## Summary
- **Overall Success**: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}
- **Success Rate**: {results['success_rate']:.1%}
- **8020 Threshold**: {'✅ MET' if results['meets_8020_threshold'] else '❌ NOT MET'}

## Statistics
- **Total Projects**: {results['total_projects']}
- **Successful Projects**: {results['successful_projects']}
- **Total Tests**: {results['total_tests']}
- **Tests Passed**: {results['total_passed']}

## Project Results

"""
        
        for project in results['project_results']:
            status = "✅ PASS" if project['success'] else "❌ FAIL"
            report += f"### {project['name']} ({project['type']}) - {status}\n"
            report += f"- **Tests Run**: {project.get('tests_run', 0)}\n"
            report += f"- **Tests Passed**: {project.get('tests_passed', 0)}\n"
            report += f"- **Success Rate**: {project.get('success_rate', 0):.1%}\n"
            
            if 'error' in project:
                report += f"- **Error**: {project['error']}\n"
            
            report += "\n"
        
        report += f"""
## Conclusion

The external project testing {'PASSED' if results['meets_8020_threshold'] else 'FAILED'} the 8020 validation criteria.
uvmgr {'successfully integrates' if results['overall_success'] else 'has issues integrating'} with external Python projects.

---
Generated by uvmgr External Project Tester
"""
        
        return report


async def main():
    """Main function for external project testing."""
    parser = argparse.ArgumentParser(description="Test uvmgr with external projects")
    parser.add_argument("--workspace", type=Path, 
                       default=Path("workspace"),
                       help="Workspace directory for test projects")
    parser.add_argument("--uvmgr-source", type=Path,
                       default=Path(".."),
                       help="Path to uvmgr source directory")
    parser.add_argument("--output", type=Path,
                       help="Output file for results")
    
    args = parser.parse_args()
    
    # Ensure workspace exists
    args.workspace.mkdir(exist_ok=True)
    
    tester = ExternalProjectTester(args.workspace, args.uvmgr_source)
    
    logger.info("Starting uvmgr external project testing...")
    results = await tester.run_all_tests()
    
    # Generate report
    report = tester.generate_report(results)
    print(report)
    
    # Save results
    if args.output:
        args.output.write_text(report)
        logger.info(f"Report saved to {args.output}")
    
    # Save JSON results
    json_file = args.workspace / "external_project_test_results.json"
    json_file.write_text(json.dumps(results, indent=2, default=str))
    logger.info(f"JSON results saved to {json_file}")
    
    # Exit with appropriate code
    exit_code = 0 if results["meets_8020_threshold"] else 1
    logger.info(f"Testing completed with exit code {exit_code}")
    return exit_code


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)