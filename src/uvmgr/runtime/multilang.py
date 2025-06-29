"""
Multi-Language Runtime Operations
==================================

This module provides multi-language project support operations for Python and Terraform.
Implements the 80/20 principle: focuses on the most essential language integrations
that provide 80% of the value for uvmgr development workflows.

Supported Languages:
- Python: Full dependency management with uv, pip, poetry, pipenv
- Terraform: Infrastructure as Code with provider dependency analysis

Key Features:
- Language detection and analysis
- Dependency management (Python packages, Terraform providers)
- Build tool integration (uv build, terraform validate)
- Configuration file analysis
- Unified testing across languages
- Package manager abstractions
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.process import run_logged
from uvmgr.core.semconv import MultiLangAttributes, MultiLangOperations
from uvmgr.core.telemetry import metric_counter, metric_histogram, span, record_exception


@dataclass
class LanguageInfo:
    """Language detection information."""
    language: str
    files_count: int
    lines_of_code: int
    percentage: float
    config_files: List[str]
    package_managers: List[str]
    entry_points: List[str]


@dataclass
class DependencyInfo:
    """Cross-language dependency information."""
    name: str
    version: str
    language: str
    package_manager: str
    file_path: str
    is_dev: bool


@dataclass
class BuildTarget:
    """Build target information."""
    language: str
    build_tool: str
    target_name: str
    commands: List[str]
    artifacts: List[str]


# Language detection patterns
LANGUAGE_PATTERNS = {
    "python": {
        "extensions": [".py", ".pyi", ".pyw"],
        "config_files": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "poetry.lock"],
        "package_managers": ["pip", "poetry", "pipenv", "uv"],
        "entry_patterns": ["__main__.py", "main.py", "app.py"]
    },
    "terraform": {
        "extensions": [".tf", ".tfvars", ".hcl"],
        "config_files": ["main.tf", "variables.tf", "outputs.tf", "versions.tf", "terraform.tfvars", ".terraform.lock.hcl"],
        "package_managers": ["terraform"],
        "entry_patterns": ["main.tf", "provider.tf"]
    }
}


@instrument_command("multilang_detect_languages")
def detect_languages(project_path: Path) -> List[LanguageInfo]:
    """Detect programming languages used in a project."""
    with span("multilang.detect_languages",
              **{MultiLangAttributes.OPERATION: MultiLangOperations.DETECT_LANGUAGES,
                 "project.path": str(project_path)}):
        
        languages = {}
        total_files = 0
        total_lines = 0
        
        # Scan all files in the project
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and not _should_ignore_file(file_path):
                extension = file_path.suffix.lower()
                
                # Check against language patterns
                for lang, patterns in LANGUAGE_PATTERNS.items():
                    if extension in patterns["extensions"]:
                        if lang not in languages:
                            languages[lang] = {
                                "files": [],
                                "lines": 0,
                                "config_files": [],
                                "package_managers": set(),
                                "entry_points": []
                            }
                        
                        languages[lang]["files"].append(file_path)
                        
                        # Count lines of code
                        try:
                            lines = len(file_path.read_text(encoding="utf-8", errors="ignore").splitlines())
                            languages[lang]["lines"] += lines
                            total_lines += lines
                        except Exception:
                            pass
                        
                        total_files += 1
                        break
        
        # Find config files and determine package managers
        for lang, data in languages.items():
            patterns = LANGUAGE_PATTERNS[lang]
            
            # Look for config files
            for config_pattern in patterns["config_files"]:
                if "*" in config_pattern:
                    # Handle glob patterns
                    config_files = list(project_path.glob(config_pattern))
                else:
                    config_file = project_path / config_pattern
                    config_files = [config_file] if config_file.exists() else []
                
                for config_file in config_files:
                    data["config_files"].append(str(config_file.relative_to(project_path)))
            
            # Determine available package managers
            data["package_managers"] = _detect_package_managers(lang, project_path)
            
            # Find entry points
            for entry_pattern in patterns["entry_patterns"]:
                entry_files = list(project_path.rglob(entry_pattern))
                for entry_file in entry_files:
                    data["entry_points"].append(str(entry_file.relative_to(project_path)))
        
        # Convert to LanguageInfo objects
        language_infos = []
        for lang, data in languages.items():
            files_count = len(data["files"])
            lines_of_code = data["lines"]
            percentage = (lines_of_code / total_lines * 100) if total_lines > 0 else 0
            
            language_infos.append(LanguageInfo(
                language=lang,
                files_count=files_count,
                lines_of_code=lines_of_code,
                percentage=percentage,
                config_files=data["config_files"],
                package_managers=list(data["package_managers"]),
                entry_points=data["entry_points"]
            ))
        
        # Sort by percentage (most used first)
        language_infos.sort(key=lambda x: x.percentage, reverse=True)
        
        add_span_attributes(**{
            "languages.detected": len(language_infos),
            "languages.primary": language_infos[0].language if language_infos else "none",
            "files.total": total_files,
            "lines.total": total_lines
        })
        
        metric_counter("multilang.detections")(1)
        
        return language_infos


def _should_ignore_file(file_path: Path) -> bool:
    """Check if file should be ignored during language detection."""
    ignore_patterns = {
        ".git", "__pycache__", "node_modules", "target", "dist", "build",
        ".venv", "venv", ".env", ".DS_Store", "Thumbs.db"
    }
    
    return any(pattern in str(file_path) for pattern in ignore_patterns)


def _detect_package_managers(language: str, project_path: Path) -> List[str]:
    """Detect available package managers for a language."""
    managers = []
    
    if language == "python":
        if (project_path / "pyproject.toml").exists():
            # Check if it's using uv, poetry, or other tools
            try:
                import tomllib
                with open(project_path / "pyproject.toml", "rb") as f:
                    data = tomllib.load(f)
                    if "tool" in data:
                        if "uv" in data["tool"]:
                            managers.append("uv")
                        if "poetry" in data["tool"]:
                            managers.append("poetry")
                        if "setuptools" in data["tool"]:
                            managers.append("pip")
            except Exception:
                managers.append("pip")
        
        if (project_path / "Pipfile").exists():
            managers.append("pipenv")
        if (project_path / "requirements.txt").exists():
            managers.append("pip")
        
        # Check if tools are actually available
        available_managers = []
        for manager in ["uv", "poetry", "pipenv", "pip"]:
            if manager in managers or not managers:
                try:
                    subprocess.run([manager, "--version"], 
                                 capture_output=True, timeout=5, check=True)
                    available_managers.append(manager)
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass
        
        return available_managers or ["pip"]  # Fallback to pip
    
    elif language == "terraform":
        # Check if terraform is available
        try:
            subprocess.run(["terraform", "version"], 
                         capture_output=True, timeout=5, check=True)
            managers.append("terraform")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return managers or ["terraform"]  # Always return terraform as fallback
    
    return []


@instrument_command("multilang_analyze_dependencies")
def analyze_dependencies(project_path: Path, languages: Optional[List[str]] = None) -> List[DependencyInfo]:
    """Analyze dependencies across all languages in the project."""
    if languages is None:
        detected_languages = detect_languages(project_path)
        languages = [lang.language for lang in detected_languages]
    
    with span("multilang.analyze_dependencies",
              **{MultiLangAttributes.OPERATION: MultiLangOperations.ANALYZE_DEPENDENCIES,
                 "project.path": str(project_path),
                 "languages": ",".join(languages)}):
        
        all_dependencies = []
        
        for language in languages:
            try:
                deps = _analyze_language_dependencies(language, project_path)
                all_dependencies.extend(deps)
            except Exception as e:
                record_exception(e, attributes={
                    "multilang.language": language,
                    "multilang.operation": "analyze_dependencies"
                })
        
        add_span_attributes(**{
            "dependencies.total": len(all_dependencies),
            "dependencies.languages": len(set(dep.language for dep in all_dependencies))
        })
        
        return all_dependencies


def _analyze_language_dependencies(language: str, project_path: Path) -> List[DependencyInfo]:
    """Analyze dependencies for a specific language."""
    dependencies = []
    
    if language == "python":
        dependencies.extend(_analyze_python_dependencies(project_path))
    elif language == "terraform":
        dependencies.extend(_analyze_terraform_dependencies(project_path))
    
    return dependencies


def _analyze_python_dependencies(project_path: Path) -> List[DependencyInfo]:
    """Analyze Python dependencies."""
    dependencies = []
    
    # Check pyproject.toml
    pyproject_file = project_path / "pyproject.toml"
    if pyproject_file.exists():
        try:
            import tomllib
            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)
                
                # Main dependencies
                if "project" in data and "dependencies" in data["project"]:
                    for dep in data["project"]["dependencies"]:
                        name, version = _parse_dependency_spec(dep)
                        dependencies.append(DependencyInfo(
                            name=name,
                            version=version,
                            language="python",
                            package_manager="pip",
                            file_path="pyproject.toml",
                            is_dev=False
                        ))
                
                # Dev dependencies
                if "project" in data and "optional-dependencies" in data["project"]:
                    for group_name, deps in data["project"]["optional-dependencies"].items():
                        for dep in deps:
                            name, version = _parse_dependency_spec(dep)
                            dependencies.append(DependencyInfo(
                                name=name,
                                version=version,
                                language="python",
                                package_manager="pip",
                                file_path="pyproject.toml",
                                is_dev=True
                            ))
        except Exception:
            pass
    
    # Check requirements.txt
    req_file = project_path / "requirements.txt"
    if req_file.exists():
        try:
            for line in req_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    name, version = _parse_dependency_spec(line)
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        language="python",
                        package_manager="pip",
                        file_path="requirements.txt",
                        is_dev=False
                    ))
        except Exception:
            pass
    
    return dependencies


def _analyze_terraform_dependencies(project_path: Path) -> List[DependencyInfo]:
    """Analyze Terraform dependencies."""
    dependencies = []
    
    # Check for terraform configuration files
    for tf_file in project_path.rglob("*.tf"):
        try:
            content = tf_file.read_text()
            
            # Look for provider blocks
            lines = content.splitlines()
            in_terraform_block = False
            in_required_providers = False
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("terraform {"):
                    in_terraform_block = True
                    continue
                elif line.startswith("required_providers {"):
                    in_required_providers = True
                    continue
                elif line == "}":
                    if in_required_providers:
                        in_required_providers = False
                    elif in_terraform_block:
                        in_terraform_block = False
                    continue
                
                # Parse provider requirements
                if in_required_providers and "=" in line:
                    # Simple parsing for provider = { source = "...", version = "..." }
                    if "source" in line and "version" in line:
                        # Extract provider name (before =)
                        provider_name = line.split("=")[0].strip()
                        
                        # Try to extract version (simplified)
                        if "version" in line:
                            version_part = line.split("version")[1]
                            if '"' in version_part:
                                version = version_part.split('"')[1]
                            else:
                                version = "*"
                        else:
                            version = "*"
                        
                        dependencies.append(DependencyInfo(
                            name=provider_name,
                            version=version,
                            language="terraform",
                            package_manager="terraform",
                            file_path=str(tf_file.relative_to(project_path)),
                            is_dev=False
                        ))
                
                # Also look for simple provider blocks
                elif line.startswith("provider "):
                    # Extract provider name from 'provider "aws" {'
                    if '"' in line:
                        provider_name = line.split('"')[1]
                        dependencies.append(DependencyInfo(
                            name=provider_name,
                            version="*",
                            language="terraform",
                            package_manager="terraform",
                            file_path=str(tf_file.relative_to(project_path)),
                            is_dev=False
                        ))
        
        except Exception:
            continue
    
    # Check terraform.lock.hcl for exact versions
    lock_file = project_path / ".terraform.lock.hcl"
    if lock_file.exists():
        try:
            content = lock_file.read_text()
            lines = content.splitlines()
            
            for line in lines:
                line = line.strip()
                if line.startswith("provider "):
                    # Extract provider from 'provider "registry.terraform.io/hashicorp/aws" {'
                    if '"' in line:
                        provider_full = line.split('"')[1]
                        provider_name = provider_full.split("/")[-1]  # Get last part
                        
                        # Look for version in next few lines
                        # This is a simplified parser
                        dependencies.append(DependencyInfo(
                            name=provider_name,
                            version="locked",
                            language="terraform",
                            package_manager="terraform",
                            file_path=".terraform.lock.hcl",
                            is_dev=False
                        ))
        except Exception:
            pass
    
    return dependencies


def _parse_dependency_spec(spec: str) -> tuple[str, str]:
    """Parse dependency specification to extract name and version."""
    spec = spec.strip()
    
    # Handle common formats: "package==1.0.0", "package>=1.0.0", "package~=1.0.0"
    for op in ["==", ">=", "<=", "~=", ">", "<"]:
        if op in spec:
            name, version = spec.split(op, 1)
            return name.strip(), version.strip()
    
    # No version specified
    return spec, "*"


@instrument_command("multilang_run_builds")
def run_builds(project_path: Path, languages: Optional[List[str]] = None,
               parallel: bool = True) -> Dict[str, Any]:
    """Run builds for all languages in the project."""
    if languages is None:
        detected_languages = detect_languages(project_path)
        languages = [lang.language for lang in detected_languages]
    
    with span("multilang.run_builds",
              **{MultiLangAttributes.OPERATION: MultiLangOperations.BUILD,
                 "project.path": str(project_path),
                 "languages": ",".join(languages),
                 "parallel": parallel}):
        
        build_results = {}
        
        for language in languages:
            try:
                result = _run_language_build(language, project_path)
                build_results[language] = result
            except Exception as e:
                build_results[language] = {
                    "success": False,
                    "error": str(e),
                    "duration": 0
                }
                record_exception(e, attributes={
                    "multilang.language": language,
                    "multilang.operation": "build"
                })
        
        success_count = sum(1 for result in build_results.values() if result.get("success"))
        total_duration = sum(result.get("duration", 0) for result in build_results.values())
        
        add_span_attributes(**{
            "builds.total": len(build_results),
            "builds.successful": success_count,
            "builds.duration_total": total_duration
        })
        
        metric_counter("multilang.builds")(1)
        
        return {
            "success": success_count == len(build_results),
            "results": build_results,
            "summary": {
                "total": len(build_results),
                "successful": success_count,
                "failed": len(build_results) - success_count,
                "duration": total_duration
            }
        }


def _run_language_build(language: str, project_path: Path) -> Dict[str, Any]:
    """Run build for a specific language."""
    start_time = time.time()
    
    if language == "python":
        # Use uv build if available, fallback to pip
        try:
            result = subprocess.run(
                ["uv", "build"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
                check=True
            )
            return {
                "success": True,
                "output": result.stdout,
                "duration": time.time() - start_time,
                "tool": "uv"
            }
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to setup.py
            try:
                result = subprocess.run(
                    ["python", "setup.py", "build"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=True
                )
                return {
                    "success": True,
                    "output": result.stdout,
                    "duration": time.time() - start_time,
                    "tool": "setuptools"
                }
            except subprocess.CalledProcessError as e:
                return {
                    "success": False,
                    "error": e.stderr,
                    "duration": time.time() - start_time
                }
    
    elif language == "terraform":
        try:
            # Terraform validate (most common "build" operation)
            result = subprocess.run(
                ["terraform", "validate"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
                check=True
            )
            return {
                "success": True,
                "output": result.stdout,
                "duration": time.time() - start_time,
                "tool": "terraform"
            }
        except subprocess.CalledProcessError as e:
            # Try terraform init first, then validate
            try:
                subprocess.run(
                    ["terraform", "init"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=True
                )
                result = subprocess.run(
                    ["terraform", "validate"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=True
                )
                return {
                    "success": True,
                    "output": f"Initialized and validated\n{result.stdout}",
                    "duration": time.time() - start_time,
                    "tool": "terraform"
                }
            except subprocess.CalledProcessError as init_error:
                return {
                    "success": False,
                    "error": f"Init failed: {init_error.stderr}\nValidate failed: {e.stderr}",
                    "duration": time.time() - start_time
                }
    
    return {
        "success": False,
        "error": f"Build not supported for language: {language}",
        "duration": time.time() - start_time
    }