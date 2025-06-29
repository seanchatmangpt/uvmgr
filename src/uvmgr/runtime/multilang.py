"""
Multi-Language Runtime Operations
==================================

This module provides multi-language project support operations.
Implements the 80/20 principle: focuses on the most common language integrations
that provide 80% of the value for typical polyglot development workflows.

Key Features:
- Language detection and analysis
- Dependency management across languages
- Build tool integration (npm, cargo, go mod, etc.)
- Cross-language import analysis
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
    "javascript": {
        "extensions": [".js", ".mjs", ".cjs"],
        "config_files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "package_managers": ["npm", "yarn", "pnpm"],
        "entry_patterns": ["index.js", "main.js", "app.js", "server.js"]
    },
    "typescript": {
        "extensions": [".ts", ".tsx", ".d.ts"],
        "config_files": ["tsconfig.json", "package.json"],
        "package_managers": ["npm", "yarn", "pnpm"],
        "entry_patterns": ["index.ts", "main.ts", "app.ts", "server.ts"]
    },
    "rust": {
        "extensions": [".rs"],
        "config_files": ["Cargo.toml", "Cargo.lock"],
        "package_managers": ["cargo"],
        "entry_patterns": ["main.rs", "lib.rs"]
    },
    "go": {
        "extensions": [".go"],
        "config_files": ["go.mod", "go.sum"],
        "package_managers": ["go mod"],
        "entry_patterns": ["main.go"]
    },
    "java": {
        "extensions": [".java"],
        "config_files": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "package_managers": ["maven", "gradle"],
        "entry_patterns": ["Main.java", "Application.java"]
    },
    "csharp": {
        "extensions": [".cs"],
        "config_files": ["*.csproj", "*.sln", "packages.config"],
        "package_managers": ["nuget", "dotnet"],
        "entry_patterns": ["Program.cs", "Main.cs"]
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
        
        metric_counter("multilang.detections")(1, {
            "languages_count": len(language_infos)
        })
        
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
    
    elif language in ["javascript", "typescript"]:
        if (project_path / "package-lock.json").exists():
            managers.append("npm")
        if (project_path / "yarn.lock").exists():
            managers.append("yarn")
        if (project_path / "pnpm-lock.yaml").exists():
            managers.append("pnpm")
        
        return managers or ["npm"]
    
    elif language == "rust":
        return ["cargo"] if (project_path / "Cargo.toml").exists() else []
    
    elif language == "go":
        return ["go mod"] if (project_path / "go.mod").exists() else []
    
    elif language == "java":
        managers = []
        if (project_path / "pom.xml").exists():
            managers.append("maven")
        if any((project_path / f).exists() for f in ["build.gradle", "build.gradle.kts"]):
            managers.append("gradle")
        return managers
    
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
    elif language in ["javascript", "typescript"]:
        dependencies.extend(_analyze_node_dependencies(project_path))
    elif language == "rust":
        dependencies.extend(_analyze_rust_dependencies(project_path))
    elif language == "go":
        dependencies.extend(_analyze_go_dependencies(project_path))
    elif language == "java":
        dependencies.extend(_analyze_java_dependencies(project_path))
    
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


def _analyze_node_dependencies(project_path: Path) -> List[DependencyInfo]:
    """Analyze Node.js dependencies."""
    dependencies = []
    
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text())
            
            # Main dependencies
            if "dependencies" in data:
                for name, version in data["dependencies"].items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        language="javascript",
                        package_manager="npm",
                        file_path="package.json",
                        is_dev=False
                    ))
            
            # Dev dependencies
            if "devDependencies" in data:
                for name, version in data["devDependencies"].items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        language="javascript",
                        package_manager="npm",
                        file_path="package.json",
                        is_dev=True
                    ))
        except Exception:
            pass
    
    return dependencies


def _analyze_rust_dependencies(project_path: Path) -> List[DependencyInfo]:
    """Analyze Rust dependencies."""
    dependencies = []
    
    cargo_toml = project_path / "Cargo.toml"
    if cargo_toml.exists():
        try:
            import tomllib
            with open(cargo_toml, "rb") as f:
                data = tomllib.load(f)
                
                # Main dependencies
                if "dependencies" in data:
                    for name, spec in data["dependencies"].items():
                        version = spec if isinstance(spec, str) else spec.get("version", "*")
                        dependencies.append(DependencyInfo(
                            name=name,
                            version=version,
                            language="rust",
                            package_manager="cargo",
                            file_path="Cargo.toml",
                            is_dev=False
                        ))
                
                # Dev dependencies
                if "dev-dependencies" in data:
                    for name, spec in data["dev-dependencies"].items():
                        version = spec if isinstance(spec, str) else spec.get("version", "*")
                        dependencies.append(DependencyInfo(
                            name=name,
                            version=version,
                            language="rust",
                            package_manager="cargo",
                            file_path="Cargo.toml",
                            is_dev=True
                        ))
        except Exception:
            pass
    
    return dependencies


def _analyze_go_dependencies(project_path: Path) -> List[DependencyInfo]:
    """Analyze Go dependencies."""
    dependencies = []
    
    go_mod = project_path / "go.mod"
    if go_mod.exists():
        try:
            content = go_mod.read_text()
            in_require = False
            
            for line in content.splitlines():
                line = line.strip()
                
                if line.startswith("require ("):
                    in_require = True
                    continue
                elif line == ")":
                    in_require = False
                    continue
                elif line.startswith("require "):
                    # Single line require
                    parts = line.replace("require ", "").split()
                    if len(parts) >= 2:
                        dependencies.append(DependencyInfo(
                            name=parts[0],
                            version=parts[1],
                            language="go",
                            package_manager="go mod",
                            file_path="go.mod",
                            is_dev=False
                        ))
                elif in_require and line:
                    # Multi-line require
                    parts = line.split()
                    if len(parts) >= 2:
                        dependencies.append(DependencyInfo(
                            name=parts[0],
                            version=parts[1],
                            language="go",
                            package_manager="go mod",
                            file_path="go.mod",
                            is_dev=False
                        ))
        except Exception:
            pass
    
    return dependencies


def _analyze_java_dependencies(project_path: Path) -> List[DependencyInfo]:
    """Analyze Java dependencies."""
    dependencies = []
    
    # Check Maven pom.xml
    pom_xml = project_path / "pom.xml"
    if pom_xml.exists():
        try:
            # This would require XML parsing
            # Simplified implementation for now
            content = pom_xml.read_text()
            if "<dependencies>" in content:
                # Basic regex-like parsing would go here
                # For now, just mark that dependencies exist
                dependencies.append(DependencyInfo(
                    name="maven-dependencies",
                    version="*",
                    language="java",
                    package_manager="maven",
                    file_path="pom.xml",
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
        
        metric_counter("multilang.builds")(1, {
            "languages_count": len(languages),
            "success_rate": success_count / len(build_results) if build_results else 0
        })
        
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
    
    elif language in ["javascript", "typescript"]:
        try:
            # Try npm run build
            result = subprocess.run(
                ["npm", "run", "build"],
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
                "tool": "npm"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr,
                "duration": time.time() - start_time
            }
    
    elif language == "rust":
        try:
            result = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=600,
                check=True
            )
            return {
                "success": True,
                "output": result.stdout,
                "duration": time.time() - start_time,
                "tool": "cargo"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr,
                "duration": time.time() - start_time
            }
    
    elif language == "go":
        try:
            result = subprocess.run(
                ["go", "build", "./..."],
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
                "tool": "go"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr,
                "duration": time.time() - start_time
            }
    
    return {
        "success": False,
        "error": f"Build not supported for language: {language}",
        "duration": time.time() - start_time
    }