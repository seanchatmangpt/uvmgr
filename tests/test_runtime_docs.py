"""
Unit tests for runtime/docs.py module.

Tests the actual implementation of documentation generation functions,
including file I/O operations, template processing, and error handling.
"""

from __future__ import annotations

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from uvmgr.runtime.docs import (
    analyze_project_structure,
    create_executive_documentation,
    create_architecture_documentation,
    create_implementation_documentation,
    create_developer_documentation,
    _detect_project_type,
    _extract_dependencies_from_pyproject,
    _extract_dependencies_from_requirements,
    _identify_architecture_patterns
)


class TestProjectStructureAnalysis:
    """Test project structure analysis functions."""
    
    def test_analyze_project_structure_basic_python_project(self):
        """Test analysis of a basic Python project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create basic Python project structure
            src_dir = project_path / "src" / "myproject"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")
            (src_dir / "main.py").write_text("def main(): pass")
            
            tests_dir = project_path / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_main.py").write_text("def test_main(): pass")
            
            # Create pyproject.toml
            pyproject_file = project_path / "pyproject.toml"
            pyproject_file.write_text("""
[project]
name = "myproject"
version = "0.1.0"
dependencies = ["requests", "click"]

[project.optional-dependencies]
dev = ["pytest", "black"]
""")
            
            result = analyze_project_structure(
                project_path=project_path,
                include_dependencies=True,
                include_architecture=True
            )
            
            assert result["project_name"] == temp_dir.split("/")[-1]
            assert result["project_type"] == "python"
            assert result["total_modules"] >= 2  # main.py and test_main.py
            assert "src" in str(result["source_directories"])
            assert len(result["dependencies"]) >= 2  # requests and click
            
    def test_analyze_project_structure_without_dependencies(self):
        """Test analysis without dependency extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create minimal Python project
            (project_path / "main.py").write_text("print('hello')")
            
            result = analyze_project_structure(
                project_path=project_path,
                include_dependencies=False,
                include_architecture=False
            )
            
            assert result["dependencies"] == []
            assert result["architecture_patterns"] == []
            assert result["total_modules"] == 1
            
    def test_detect_project_type_python(self):
        """Test Python project type detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create Python indicators
            (project_path / "pyproject.toml").write_text("[project]\nname = 'test'")
            (project_path / "main.py").write_text("print('hello')")
            
            project_type = _detect_project_type(project_path)
            assert project_type == "python"
            
    def test_detect_project_type_javascript(self):
        """Test JavaScript project type detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create JavaScript indicators
            (project_path / "package.json").write_text('{"name": "test"}')
            (project_path / "index.js").write_text("console.log('hello')")
            
            project_type = _detect_project_type(project_path)
            assert project_type == "nodejs"
            
    def test_detect_project_type_unknown(self):
        """Test unknown project type detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create minimal project without clear indicators
            (project_path / "README.md").write_text("# Test project")
            
            project_type = _detect_project_type(project_path)
            assert project_type == "software"


class TestDependencyExtraction:
    """Test dependency extraction functions."""
    
    def test_extract_dependencies_from_pyproject_full(self):
        """Test extracting dependencies from comprehensive pyproject.toml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            pyproject_file = project_path / "pyproject.toml"
            
            pyproject_content = """
[project]
name = "test-project"
version = "0.1.0"
dependencies = [
    "requests>=2.28.0",
    "click>=8.0.0",
    "pydantic[email]~=1.10.0"
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "black", "mypy"]
docs = ["sphinx", "sphinx-rtd-theme"]
test = ["coverage", "pytest-cov"]

[build-system]
requires = ["setuptools>=65", "wheel"]
build-backend = "setuptools.build_meta"
"""
            pyproject_file.write_text(pyproject_content)
            
            deps = _extract_dependencies_from_pyproject(pyproject_file)
            
            # Check production dependencies
            prod_deps = [d["name"] for d in deps if d["type"] == "production"]
            assert "requests" in prod_deps
            assert "click" in prod_deps
            assert "pydantic" in prod_deps
            
            # Check optional dependencies
            dev_deps = [d["name"] for d in deps if d["type"] == "dev"]
            assert "pytest" in dev_deps
            assert "black" in dev_deps
            
            # Check build dependencies
            build_deps = [d["name"] for d in deps if d["type"] == "build"]
            assert "setuptools" in build_deps
            assert "wheel" in build_deps
            
    def test_extract_dependencies_from_requirements_txt(self):
        """Test extracting dependencies from requirements.txt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            requirements_file = project_path / "requirements.txt"
            
            requirements_content = """
# Production dependencies
requests>=2.28.0
click==8.1.0
pydantic[email]

# Comments should be ignored
numpy  # Scientific computing
pandas>=1.5.0  # Data analysis

# Empty lines and comments
flask-sqlalchemy
"""
            requirements_file.write_text(requirements_content)
            
            deps = _extract_dependencies_from_requirements(requirements_file)
            
            dep_names = [d["name"] for d in deps]
            assert "requests" in dep_names
            assert "click" in dep_names
            assert "pydantic" in dep_names
            assert "numpy" in dep_names
            assert "pandas" in dep_names
            assert "flask-sqlalchemy" in dep_names
            
            # All should be production type
            assert all(d["type"] == "production" for d in deps)


class TestArchitecturePatternIdentification:
    """Test architecture pattern identification."""
    
    def test_identify_architecture_patterns_mvc(self):
        """Test identification of MVC pattern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create MVC structure
            (project_path / "models").mkdir()
            (project_path / "models" / "__init__.py").write_text("")
            (project_path / "models" / "user.py").write_text("class User: pass")
            
            (project_path / "views").mkdir()
            (project_path / "views" / "__init__.py").write_text("")
            (project_path / "views" / "user_view.py").write_text("def user_view(): pass")
            
            (project_path / "controllers").mkdir()
            (project_path / "controllers" / "__init__.py").write_text("")
            (project_path / "controllers" / "user_controller.py").write_text("def handle_user(): pass")
            
            patterns = _identify_architecture_patterns(project_path)
            assert "MVC" in patterns
            
    def test_identify_architecture_patterns_microservices(self):
        """Test identification of microservices pattern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create microservices structure
            (project_path / "services").mkdir()
            (project_path / "services" / "user_service").mkdir()
            (project_path / "services" / "auth_service").mkdir()
            (project_path / "services" / "payment_service").mkdir()
            
            # Create docker files
            (project_path / "docker-compose.yml").write_text("version: '3'")
            (project_path / "services" / "user_service" / "Dockerfile").write_text("FROM python:3.11")
            
            patterns = _identify_architecture_patterns(project_path)
            assert "Microservices" in patterns
            
    def test_identify_architecture_patterns_layered(self):
        """Test identification of layered architecture."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create layered structure
            src_dir = project_path / "src"
            src_dir.mkdir()
            
            (src_dir / "presentation").mkdir()
            (src_dir / "business").mkdir()
            (src_dir / "data").mkdir()
            
            patterns = _identify_architecture_patterns(project_path)
            assert "Layered Architecture" in patterns or "Layered" in patterns


class TestDocumentationGeneration:
    """Test documentation generation functions."""
    
    def test_create_executive_documentation_basic(self):
        """Test basic executive documentation creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            project_analysis = {
                "project_name": "test-project",
                "project_type": "python",
                "total_modules": 10,
                "dependencies": [
                    {"name": "requests", "version": "2.28.0", "type": "production"},
                    {"name": "pytest", "version": "7.0.0", "type": "dev"}
                ]
            }
            
            result = create_executive_documentation(
                project_path=project_path,
                project_analysis=project_analysis,
                output_format="markdown",
                include_metrics=True,
                ai_enhance=False
            )
            
            assert result["success"] is True
            assert "output_file" in result
            assert "sections_generated" in result
            assert "business_value" in result["sections_generated"]
            assert "risks" in result["sections_generated"]
            
            # Verify file was created
            output_file = Path(result["output_file"])
            assert output_file.exists()
            
            # Verify content
            content = output_file.read_text()
            assert "test-project" in content
            assert "Executive Summary" in content
            assert "Business Value" in content
            
    def test_create_architecture_documentation_with_patterns(self):
        """Test architecture documentation with detected patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            project_analysis = {
                "project_name": "arch-project",
                "project_type": "python",
                "architecture_patterns": ["MVC", "Repository"],
                "dependencies": [
                    {"name": "flask", "version": "2.3.0", "type": "production"},
                    {"name": "sqlalchemy", "version": "2.0.0", "type": "production"}
                ]
            }
            
            result = create_architecture_documentation(
                project_path=project_path,
                project_analysis=project_analysis,
                output_format="markdown",
                include_diagrams=False,  # Skip diagrams for testing
                detail_level="basic"
            )
            
            assert result["success"] is True
            assert "architecture_components" in result
            assert "diagrams_included" in result
            assert result["diagrams_included"] is False
            
            # Verify file content
            output_file = Path(result["output_file"])
            content = output_file.read_text()
            assert "Solution Architecture" in content
            assert "MVC" in content
            assert "Repository" in content
            
    def test_create_implementation_documentation_with_modules(self):
        """Test implementation documentation with module extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create some Python modules
            src_dir = project_path / "src" / "myproject"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")
            (src_dir / "core.py").write_text('''
"""Core module with important functions."""

def process_data(data):
    """Process input data and return results."""
    return data.upper()

class DataProcessor:
    """Main data processing class."""
    
    def __init__(self):
        self.processed = 0
        
    def process(self, item):
        """Process a single item."""
        self.processed += 1
        return item
''')
            
            project_analysis = {
                "project_name": "myproject",
                "project_type": "python",
                "total_modules": 2
            }
            
            result = create_implementation_documentation(
                project_path=project_path,
                project_analysis=project_analysis,
                output_format="markdown",
                auto_extract=True,
                include_examples=True,
                ai_enhance=False
            )
            
            if not result["success"]:
                print("Error:", result.get("error"))
            assert result["success"] is True
            assert "modules_documented" in result
            assert result["auto_extracted"] is True
            assert result["examples_included"] is True
            
            # Should have extracted modules from the project
            modules = result["modules_documented"]
            assert len(modules) > 0
            assert any("core" in module for module in modules)
            
    def test_create_developer_documentation_comprehensive(self):
        """Test comprehensive developer documentation creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            project_analysis = {
                "project_name": "dev-project",
                "project_type": "python",
                "dependencies": [
                    {"name": "fastapi", "version": "0.104.0", "type": "production"},
                    {"name": "pytest", "version": "7.4.0", "type": "dev"}
                ]
            }
            
            result = create_developer_documentation(
                project_path=project_path,
                project_analysis=project_analysis,
                output_format="markdown",
                include_setup=True,
                include_workflows=True
            )
            
            assert result["success"] is True
            assert "setup_included" in result
            assert "workflows_included" in result
            assert result["setup_included"] is True
            assert result["workflows_included"] is True
            
            # Verify file content
            output_file = Path(result["output_file"])
            content = output_file.read_text()
            assert "Developer Guide" in content
            assert "Quick Start" in content
            assert "Prerequisites" in content
            assert "Development Workflow" in content


class TestDocumentationErrorHandling:
    """Test error handling in documentation functions."""
    
    def test_analyze_project_structure_invalid_path(self):
        """Test error handling for invalid project path."""
        invalid_path = Path("/nonexistent/path/that/does/not/exist")
        
        result = analyze_project_structure(
            project_path=invalid_path,
            include_dependencies=True,
            include_architecture=True
        )
        
        # Should return a basic result even for invalid paths
        assert "project_name" in result
        assert result["total_modules"] == 0
        assert result["dependencies"] == []
        
    def test_create_executive_documentation_write_error(self):
        """Test error handling when unable to write documentation files."""
        # Try to write to a read-only location
        invalid_path = Path("/proc")  # Read-only on most systems
        
        project_analysis = {
            "project_name": "test-project",
            "project_type": "python",
            "total_modules": 5
        }
        
        result = create_executive_documentation(
            project_path=invalid_path,
            project_analysis=project_analysis,
            output_format="markdown",
            include_metrics=True,
            ai_enhance=False
        )
        
        # Should handle error gracefully
        if not result["success"]:
            assert "error" in result
            assert isinstance(result["error"], str)
        
    def test_dependency_extraction_malformed_pyproject(self):
        """Test error handling for malformed pyproject.toml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            pyproject_file = project_path / "pyproject.toml"
            
            # Create malformed TOML
            pyproject_file.write_text("""
[project
name = "invalid-toml"  # Missing closing bracket
dependencies = [
""")
            
            # Should handle error gracefully and return empty list
            deps = _extract_dependencies_from_pyproject(pyproject_file)
            assert deps == []
            
    def test_dependency_extraction_nonexistent_file(self):
        """Test error handling for nonexistent requirements file."""
        nonexistent_file = Path("/nonexistent/requirements.txt")
        
        deps = _extract_dependencies_from_requirements(nonexistent_file)
        assert deps == []


class TestDocumentationIntegration:
    """Integration tests for documentation workflow."""
    
    def test_full_documentation_workflow(self):
        """Test complete documentation generation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a realistic project structure
            src_dir = project_path / "src" / "webapp"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")
            (src_dir / "app.py").write_text("""
'''Main application module.'''

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    '''Home page route.'''
    return 'Hello World'

if __name__ == '__main__':
    app.run()
""")
            
            # Create models directory (MVC pattern)
            models_dir = src_dir / "models"
            models_dir.mkdir()
            (models_dir / "__init__.py").write_text("")
            (models_dir / "user.py").write_text("""
'''User model.'''

class User:
    '''User entity class.'''
    
    def __init__(self, name, email):
        self.name = name
        self.email = email
""")
            
            # Create pyproject.toml
            pyproject_file = project_path / "pyproject.toml"
            pyproject_file.write_text("""
[project]
name = "webapp"
version = "1.0.0"
description = "A sample web application"
dependencies = [
    "flask>=2.3.0",
    "sqlalchemy>=2.0.0"
]

[project.optional-dependencies]
dev = ["pytest>=7.4.0", "black", "mypy"]
""")
            
            # Step 1: Analyze project structure
            analysis = analyze_project_structure(
                project_path=project_path,
                include_dependencies=True,
                include_architecture=True
            )
            
            assert analysis["project_type"] == "python"
            assert analysis["total_modules"] >= 3  # app.py, user.py, __init__.py files
            assert len(analysis["dependencies"]) >= 2  # flask, sqlalchemy
            
            # Step 2: Generate executive documentation
            exec_result = create_executive_documentation(
                project_path=project_path,
                project_analysis=analysis,
                output_format="markdown",
                include_metrics=True,
                ai_enhance=False
            )
            
            assert exec_result["success"] is True
            
            # Step 3: Generate architecture documentation
            arch_result = create_architecture_documentation(
                project_path=project_path,
                project_analysis=analysis,
                output_format="markdown",
                include_diagrams=False,
                detail_level="basic"
            )
            
            assert arch_result["success"] is True
            
            # Step 4: Generate implementation documentation
            impl_result = create_implementation_documentation(
                project_path=project_path,
                project_analysis=analysis,
                output_format="markdown",
                auto_extract=True,
                include_examples=True,
                ai_enhance=False
            )
            
            assert impl_result["success"] is True
            assert len(impl_result["modules_documented"]) > 0
            
            # Step 5: Generate developer documentation
            dev_result = create_developer_documentation(
                project_path=project_path,
                project_analysis=analysis,
                output_format="markdown",
                include_setup=True,
                include_workflows=True
            )
            
            assert dev_result["success"] is True
            
            # Verify all documentation files were created
            docs_dir = project_path / "docs"
            assert docs_dir.exists()
            
            expected_files = [
                "docs/executive/executive-summary.md",
                "docs/architecture/solution-architecture.md", 
                "docs/implementation/implementation-guide.md",
                "docs/developer/developer-guide.md"
            ]
            
            for file_path in expected_files:
                full_path = project_path / file_path
                assert full_path.exists(), f"Expected file not found: {file_path}"
                
                # Verify files have content
                content = full_path.read_text()
                assert len(content) > 100, f"File too short: {file_path}"
                assert "webapp" in content, f"Project name not found in: {file_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])