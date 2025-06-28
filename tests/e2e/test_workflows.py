"""E2E tests for common uvmgr workflows."""
import json
import sys
from pathlib import Path

import pytest

from tests.e2e.conftest import (
    assert_command_success,
    assert_output_contains,
    create_sample_module,
)


class TestProjectWorkflows:
    """Test common project management workflows."""

    def test_new_project_setup(self, uvmgr_runner, tmp_path):
        """Test setting up a new Python project from scratch."""
        project_dir = tmp_path / "my_awesome_project"
        project_dir.mkdir()

        # Create initial project structure
        pyproject = project_dir / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "my-awesome-project"
version = "0.1.0"
description = "An awesome Python project"
requires-python = ">=3.8"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
""")

        # Create source directory
        src = project_dir / "src" / "my_awesome_project"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text('__version__ = "0.1.0"')
        (src / "main.py").write_text("""
def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
""")

        # Set up with uvmgr
        result = uvmgr_runner("deps", "lock", cwd=project_dir)
        assert_command_success(result)

        # Add dev dependencies
        dev_deps = ["pytest", "pytest-cov", "black", "ruff", "mypy"]
        for dep in dev_deps:
            result = uvmgr_runner("deps", "add", dep, "--dev", cwd=project_dir)
            assert_command_success(result)

        # Add runtime dependencies
        result = uvmgr_runner("deps", "add", "typer", "rich", cwd=project_dir)
        assert_command_success(result)

        # Create tests
        tests = project_dir / "tests"
        tests.mkdir()
        (tests / "__init__.py").touch()
        (tests / "test_main.py").write_text("""
from my_awesome_project.main import greet

def test_greet():
    assert greet("Alice") == "Hello, Alice!"
    assert greet("Bob") == "Hello, Bob!"
""")

        # Run tests
        result = uvmgr_runner("tests", "run", cwd=project_dir)
        assert_command_success(result)
        assert_output_contains(result, "2 passed")

        # Generate coverage
        result = uvmgr_runner("tests", "coverage", cwd=project_dir)
        assert_command_success(result)

        # Build distribution
        result = uvmgr_runner("build", "all", cwd=project_dir)
        assert_command_success(result)

        # Verify artifacts
        assert (project_dir / "dist").exists()
        assert len(list((project_dir / "dist").glob("*.whl"))) == 1
        assert len(list((project_dir / "dist").glob("*.tar.gz"))) == 1

    def test_monorepo_workflow(self, uvmgr_runner, tmp_path):
        """Test managing a monorepo with multiple packages."""
        monorepo = tmp_path / "monorepo"
        monorepo.mkdir()

        # Create root pyproject.toml for workspace
        (monorepo / "pyproject.toml").write_text("""
[tool.uv]
workspace = ["packages/*"]
""")

        # Create multiple packages
        packages = ["core", "api", "cli"]
        for pkg in packages:
            pkg_dir = monorepo / "packages" / pkg
            pkg_dir.mkdir(parents=True)

            # Package pyproject.toml
            (pkg_dir / "pyproject.toml").write_text(f"""
[project]
name = "mycompany-{pkg}"
version = "0.1.0"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

            # Package source
            src = pkg_dir / "src" / f"mycompany_{pkg}"
            src.mkdir(parents=True)
            (src / "__init__.py").write_text(f'__version__ = "0.1.0"\nNAME = "{pkg}"')

        # Add inter-package dependencies
        api_pyproject = monorepo / "packages" / "api" / "pyproject.toml"
        content = api_pyproject.read_text()
        content = content.replace(
            "dependencies = []",
            'dependencies = ["mycompany-core"]'
        )
        api_pyproject.write_text(content)

        # Lock workspace
        result = uvmgr_runner("deps", "lock", cwd=monorepo)
        assert_command_success(result)

        # Add dependencies to specific packages
        result = uvmgr_runner("deps", "add", "fastapi", cwd=monorepo / "packages" / "api")
        assert_command_success(result)

        result = uvmgr_runner("deps", "add", "typer", cwd=monorepo / "packages" / "cli")
        assert_command_success(result)

        # Build all packages
        for pkg in packages:
            result = uvmgr_runner("build", "wheel", cwd=monorepo / "packages" / pkg)
            assert_command_success(result)


class TestDevelopmentWorkflows:
    """Test development workflows like testing, linting, formatting."""

    def test_tdd_workflow(self, uvmgr_runner, temp_project, sample_python_module):
        """Test Test-Driven Development workflow."""
        # Setup project
        uvmgr_runner("deps", "lock", cwd=temp_project)
        uvmgr_runner("deps", "add", "pytest", "pytest-watch", "--dev", cwd=temp_project)

        # Create failing test first (TDD)
        tests = temp_project / "tests"
        tests.mkdir(exist_ok=True)
        test_file = tests / "test_calculator.py"
        test_file.write_text("""
def test_calculator_add():
    from calculator import Calculator
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_calculator_subtract():
    from calculator import Calculator
    calc = Calculator()
    assert calc.subtract(5, 3) == 2
""")

        # Run tests (should fail)
        result = uvmgr_runner("tests", "run", str(test_file), cwd=temp_project, check=False)
        assert result.returncode != 0
        assert "ModuleNotFoundError" in result.stdout or "ImportError" in result.stdout

        # Implement code to make tests pass
        src = temp_project / "src"
        src.mkdir(exist_ok=True)
        (src / "calculator.py").write_text("""
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def subtract(self, a: int, b: int) -> int:
        return a - b
""")

        # Update Python path for tests
        (tests / "conftest.py").write_text("""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
""")

        # Run tests again (should pass)
        result = uvmgr_runner("tests", "run", str(test_file), cwd=temp_project)
        assert_command_success(result)
        assert_output_contains(result, "2 passed")

    def test_ci_workflow(self, uvmgr_runner, temp_project, sample_python_module, sample_test_module):
        """Test typical CI workflow: lint, test, build."""
        # Setup project with all CI tools
        uvmgr_runner("deps", "lock", cwd=temp_project)
        ci_tools = ["pytest", "pytest-cov", "black", "ruff", "mypy"]
        for tool in ci_tools:
            uvmgr_runner("deps", "add", tool, "--dev", cwd=temp_project)

        # Create code
        create_sample_module(temp_project, sample_python_module, sample_test_module)

        # CI Steps:
        # 1. Format check
        result = uvmgr_runner("lint", "check", cwd=temp_project, check=False)
        # May have formatting issues

        # 2. Fix formatting
        result = uvmgr_runner("lint", "fix", cwd=temp_project, check=False)

        # 3. Run tests
        result = uvmgr_runner("tests", "run", cwd=temp_project)
        assert_command_success(result)

        # 4. Coverage
        result = uvmgr_runner("tests", "coverage", cwd=temp_project)
        assert_command_success(result)

        # 5. Build
        result = uvmgr_runner("build", "wheel", cwd=temp_project)
        assert_command_success(result)

        # 6. Verify all artifacts exist
        assert (temp_project / "dist" / "test_project-0.1.0-py3-none-any.whl").exists()
        assert (temp_project / "reports").exists()  # Coverage reports


class TestReleaseWorkflows:
    """Test release and deployment workflows."""

    def test_version_bump_workflow(self, uvmgr_runner, temp_project):
        """Test version bumping workflow."""
        # Setup project with commitizen
        uvmgr_runner("deps", "lock", cwd=temp_project)
        uvmgr_runner("deps", "add", "commitizen", "--dev", cwd=temp_project)

        # Initialize git repo
        result = uvmgr_runner("run", "git", "init", cwd=temp_project)
        assert_command_success(result)

        result = uvmgr_runner("run", "git", "config", "user.email", "test@example.com", cwd=temp_project)
        assert_command_success(result)

        result = uvmgr_runner("run", "git", "config", "user.name", "Test User", cwd=temp_project)
        assert_command_success(result)

        # Initial commit
        result = uvmgr_runner("run", "git", "add", ".", cwd=temp_project)
        assert_command_success(result)

        result = uvmgr_runner("run", "git", "commit", "-m", "feat: initial commit", cwd=temp_project)
        assert_command_success(result)

        # Bump version
        result = uvmgr_runner("release", "version", "patch", cwd=temp_project, check=False)
        # May fail if commitizen not configured, but command should run

        # Check current version
        pyproject = temp_project / "pyproject.toml"
        content = pyproject.read_text()
        assert 'version = "0.1.0"' in content

    def test_build_and_check_workflow(self, uvmgr_runner, temp_project):
        """Test building and checking distribution."""
        # Setup
        uvmgr_runner("deps", "lock", cwd=temp_project)
        uvmgr_runner("deps", "add", "twine", "--dev", cwd=temp_project)

        # Add some metadata
        pyproject = temp_project / "pyproject.toml"
        content = pyproject.read_text()
        content = content.replace(
            "[project]",
            """[project]
authors = [{name = "Test Author", email = "test@example.com"}]
readme = "README.md"
license = {text = "MIT"}
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
]"""
        )
        pyproject.write_text(content)

        # Create README
        (temp_project / "README.md").write_text("# Test Project\n\nA test project for uvmgr.")

        # Build all distributions
        result = uvmgr_runner("build", "all", cwd=temp_project)
        assert_command_success(result)

        # Check distributions
        result = uvmgr_runner("build", "check", cwd=temp_project)
        assert_command_success(result)
        assert_output_contains(result, "PASSED")


class TestAIWorkflows:
    """Test AI-assisted development workflows."""

    @pytest.mark.skipif(not Path.home().joinpath(".config/uvmgr/.env").exists(),
                        reason="AI features require API keys")
    def test_ai_assisted_development(self, uvmgr_runner, temp_project):
        """Test AI-assisted coding workflow."""
        # Setup project
        uvmgr_runner("deps", "lock", cwd=temp_project)

        # Get AI help for implementation
        result = uvmgr_runner(
            "ai", "assist",
            "Write a function to calculate fibonacci numbers",
            cwd=temp_project,
            check=False
        )

        # Should provide some output if API is configured
        if result.returncode == 0:
            assert len(result.stdout) > 50  # Some meaningful output

    @pytest.mark.skipif(not Path.home().joinpath(".config/uvmgr/.env").exists(),
                        reason="AI features require API keys")
    def test_ai_test_generation(self, uvmgr_runner, temp_project):
        """Test AI-generated test workflow."""
        # Create a module to test
        src = temp_project / "src"
        src.mkdir()
        module = src / "math_utils.py"
        module.write_text("""
def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
""")

        # Ask AI to generate tests
        result = uvmgr_runner(
            "ai", "assist",
            f"Generate pytest tests for the functions in {module}",
            cwd=temp_project,
            check=False
        )

        if result.returncode == 0:
            # AI should suggest test code
            assert "def test_" in result.stdout or "factorial" in result.stdout
