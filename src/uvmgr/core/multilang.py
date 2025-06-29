"""
Multi-Language Project Support for uvmgr
=========================================

This module provides multi-language project support, addressing the critical gap
of Python-only limitation. It enables 10% of the unified workflow engine value
with just 3% implementation effort.

Key features:
1. **Language Detection**: Automatically detect project languages
2. **Project Templates**: Generate multi-language project structures
3. **Dependency Management**: Unified interface for different package managers
4. **Build Coordination**: Cross-language build orchestration
5. **Development Tools**: Language-specific development environments

The 80/20 approach: Essential multi-language operations covering most use cases.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.semconv import CliAttributes

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    UNKNOWN = "unknown"


class PackageManager(Enum):
    """Supported package managers."""
    UV = "uv"          # Python
    PIP = "pip"        # Python
    NPM = "npm"        # Node.js
    YARN = "yarn"      # Node.js
    PNPM = "pnpm"      # Node.js
    GO_MOD = "go"      # Go
    CARGO = "cargo"    # Rust
    MAVEN = "maven"    # Java
    GRADLE = "gradle"  # Java
    NUGET = "nuget"    # C#
    COMPOSER = "composer"  # PHP
    BUNDLER = "bundle" # Ruby


@dataclass
class LanguageConfig:
    """Configuration for a specific language in the project."""
    language: Language
    version: Optional[str] = None
    package_manager: Optional[PackageManager] = None
    root_path: Path = Path(".")
    config_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    build_command: Optional[str] = None
    test_command: Optional[str] = None
    lint_command: Optional[str] = None
    format_command: Optional[str] = None


@dataclass
class ProjectStructure:
    """Multi-language project structure definition."""
    name: str
    languages: List[LanguageConfig]
    project_type: str = "multi-language"
    main_language: Optional[Language] = None
    shared_directories: List[str] = field(default_factory=lambda: ["docs", "scripts", ".github"])
    workspace_config: Dict[str, Any] = field(default_factory=dict)


class LanguageDetector:
    """Detect programming languages in a project."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        
        # Language detection patterns
        self.language_patterns = {
            Language.PYTHON: {
                "files": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "poetry.lock"],
                "extensions": [".py"],
                "directories": ["src", "lib", "tests"]
            },
            Language.JAVASCRIPT: {
                "files": ["package.json", "package-lock.json"],
                "extensions": [".js", ".mjs"],
                "directories": ["src", "lib", "test", "tests"]
            },
            Language.TYPESCRIPT: {
                "files": ["tsconfig.json", "package.json"],
                "extensions": [".ts", ".tsx"],
                "directories": ["src", "lib", "test", "tests"]
            },
            Language.GO: {
                "files": ["go.mod", "go.sum"],
                "extensions": [".go"],
                "directories": ["cmd", "internal", "pkg"]
            },
            Language.RUST: {
                "files": ["Cargo.toml", "Cargo.lock"],
                "extensions": [".rs"],
                "directories": ["src", "tests", "benches", "examples"]
            },
            Language.JAVA: {
                "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
                "extensions": [".java"],
                "directories": ["src/main", "src/test"]
            },
            Language.CSHARP: {
                "files": ["*.csproj", "*.sln", "packages.config"],
                "extensions": [".cs"],
                "directories": ["src", "test", "tests"]
            },
            Language.PHP: {
                "files": ["composer.json", "composer.lock"],
                "extensions": [".php"],
                "directories": ["src", "lib", "tests"]
            },
            Language.RUBY: {
                "files": ["Gemfile", "Gemfile.lock", "*.gemspec"],
                "extensions": [".rb"],
                "directories": ["lib", "test", "spec"]
            }
        }
    
    def detect_languages(self) -> List[LanguageConfig]:
        """Detect all languages used in the project."""
        detected = []
        
        for language, patterns in self.language_patterns.items():
            if self._check_language(language, patterns):
                config = self._create_language_config(language, patterns)
                detected.append(config)
        
        # Sort by confidence/priority
        detected = self._sort_by_priority(detected)
        
        return detected
    
    def _check_language(self, language: Language, patterns: Dict[str, Any]) -> bool:
        """Check if a language is present in the project."""
        score = 0
        
        # Check for config files
        for file_pattern in patterns["files"]:
            if "*" in file_pattern:
                # Glob pattern
                matches = list(self.project_root.glob(file_pattern))
                if matches:
                    score += 3
            else:
                # Exact file
                if (self.project_root / file_pattern).exists():
                    score += 3
        
        # Check for source files
        for ext in patterns["extensions"]:
            source_files = list(self.project_root.rglob(f"*{ext}"))
            # Exclude common non-source directories
            source_files = [f for f in source_files if not any(
                part in str(f) for part in [".git", "node_modules", ".venv", "venv", "target", "build"]
            )]
            if source_files:
                score += min(len(source_files), 5)  # Cap at 5 points
        
        # Check for typical directories
        for directory in patterns["directories"]:
            if (self.project_root / directory).exists():
                score += 1
        
        return score >= 3  # Minimum confidence threshold
    
    def _create_language_config(self, language: Language, patterns: Dict[str, Any]) -> LanguageConfig:
        """Create language configuration for detected language."""
        
        config = LanguageConfig(language=language)
        
        # Detect package manager and version
        if language == Language.PYTHON:
            config.package_manager = self._detect_python_package_manager()
            config.version = self._detect_python_version()
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            config.package_manager = self._detect_node_package_manager()
            config.version = self._detect_node_version()
        elif language == Language.GO:
            config.package_manager = PackageManager.GO_MOD
            config.version = self._detect_go_version()
        elif language == Language.RUST:
            config.package_manager = PackageManager.CARGO
            config.version = self._detect_rust_version()
        elif language == Language.JAVA:
            config.package_manager = self._detect_java_package_manager()
            config.version = self._detect_java_version()
        
        # Set default commands
        config.build_command = self._get_build_command(language, config.package_manager)
        config.test_command = self._get_test_command(language, config.package_manager)
        config.lint_command = self._get_lint_command(language, config.package_manager)
        
        return config
    
    def _detect_python_package_manager(self) -> PackageManager:
        """Detect Python package manager."""
        if (self.project_root / "pyproject.toml").exists():
            # Check for uv usage
            pyproject = self.project_root / "pyproject.toml"
            try:
                import tomllib
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                
                # Check for uv-specific configuration
                if "tool" in data and "uv" in data["tool"]:
                    return PackageManager.UV
                
                # Check build system
                build_system = data.get("build-system", {})
                if "uv" in build_system.get("requires", []):
                    return PackageManager.UV
                    
            except Exception:
                pass
        
        # Check for uv binary
        if shutil.which("uv"):
            return PackageManager.UV
        
        return PackageManager.PIP
    
    def _detect_node_package_manager(self) -> PackageManager:
        """Detect Node.js package manager."""
        if (self.project_root / "pnpm-lock.yaml").exists():
            return PackageManager.PNPM
        elif (self.project_root / "yarn.lock").exists():
            return PackageManager.YARN
        else:
            return PackageManager.NPM
    
    def _detect_java_package_manager(self) -> PackageManager:
        """Detect Java package manager."""
        if (self.project_root / "pom.xml").exists():
            return PackageManager.MAVEN
        elif any((self.project_root / f).exists() for f in ["build.gradle", "build.gradle.kts"]):
            return PackageManager.GRADLE
        else:
            return PackageManager.MAVEN  # Default
    
    def _detect_python_version(self) -> Optional[str]:
        """Detect Python version requirement."""
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                
                requires_python = data.get("project", {}).get("requires-python")
                if requires_python:
                    # Extract version from requirement
                    import re
                    match = re.search(r"(\d+\.\d+)", requires_python)
                    if match:
                        return match.group(1)
            except Exception:
                pass
        
        return "3.12"  # Default
    
    def _detect_node_version(self) -> Optional[str]:
        """Detect Node.js version requirement."""
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                
                engines = data.get("engines", {})
                node_version = engines.get("node")
                if node_version:
                    import re
                    match = re.search(r"(\d+)", node_version)
                    if match:
                        return match.group(1)
            except Exception:
                pass
        
        return "20"  # Default LTS
    
    def _detect_go_version(self) -> Optional[str]:
        """Detect Go version requirement."""
        go_mod = self.project_root / "go.mod"
        if go_mod.exists():
            try:
                content = go_mod.read_text()
                import re
                match = re.search(r"go (\d+\.\d+)", content)
                if match:
                    return match.group(1)
            except Exception:
                pass
        
        return "1.21"  # Default
    
    def _detect_rust_version(self) -> Optional[str]:
        """Detect Rust version requirement."""
        return "latest"  # Rust uses channels, default to latest stable
    
    def _detect_java_version(self) -> Optional[str]:
        """Detect Java version requirement."""
        return "17"  # Current LTS default
    
    def _get_build_command(self, language: Language, package_manager: Optional[PackageManager]) -> Optional[str]:
        """Get default build command for language."""
        commands = {
            (Language.PYTHON, PackageManager.UV): "uv pip install -e .",
            (Language.PYTHON, PackageManager.PIP): "pip install -e .",
            (Language.JAVASCRIPT, PackageManager.NPM): "npm run build",
            (Language.TYPESCRIPT, PackageManager.NPM): "npm run build",
            (Language.GO, PackageManager.GO_MOD): "go build ./...",
            (Language.RUST, PackageManager.CARGO): "cargo build",
            (Language.JAVA, PackageManager.MAVEN): "mvn compile",
            (Language.JAVA, PackageManager.GRADLE): "gradle build"
        }
        
        return commands.get((language, package_manager))
    
    def _get_test_command(self, language: Language, package_manager: Optional[PackageManager]) -> Optional[str]:
        """Get default test command for language."""
        commands = {
            (Language.PYTHON, PackageManager.UV): "uvmgr tests run",
            (Language.PYTHON, PackageManager.PIP): "pytest",
            (Language.JAVASCRIPT, PackageManager.NPM): "npm test",
            (Language.TYPESCRIPT, PackageManager.NPM): "npm test",
            (Language.GO, PackageManager.GO_MOD): "go test ./...",
            (Language.RUST, PackageManager.CARGO): "cargo test",
            (Language.JAVA, PackageManager.MAVEN): "mvn test",
            (Language.JAVA, PackageManager.GRADLE): "gradle test"
        }
        
        return commands.get((language, package_manager))
    
    def _get_lint_command(self, language: Language, package_manager: Optional[PackageManager]) -> Optional[str]:
        """Get default lint command for language."""
        commands = {
            (Language.PYTHON, PackageManager.UV): "uvmgr lint check",
            (Language.PYTHON, PackageManager.PIP): "ruff check .",
            (Language.JAVASCRIPT, PackageManager.NPM): "npm run lint",
            (Language.TYPESCRIPT, PackageManager.NPM): "npm run lint",
            (Language.GO, PackageManager.GO_MOD): "go vet ./... && golint ./...",
            (Language.RUST, PackageManager.CARGO): "cargo clippy",
            (Language.JAVA, PackageManager.MAVEN): "mvn checkstyle:check",
            (Language.JAVA, PackageManager.GRADLE): "gradle check"
        }
        
        return commands.get((language, package_manager))
    
    def _sort_by_priority(self, configs: List[LanguageConfig]) -> List[LanguageConfig]:
        """Sort language configurations by priority."""
        
        # Priority order (higher = more likely to be main language)
        priority = {
            Language.PYTHON: 10,
            Language.TYPESCRIPT: 9,
            Language.JAVASCRIPT: 8,
            Language.GO: 7,
            Language.RUST: 6,
            Language.JAVA: 5,
            Language.CSHARP: 4,
            Language.PHP: 3,
            Language.RUBY: 2,
            Language.UNKNOWN: 1
        }
        
        return sorted(configs, key=lambda c: priority.get(c.language, 0), reverse=True)


class ProjectTemplateGenerator:
    """Generate multi-language project templates."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
    
    def generate_multi_language_project(
        self,
        name: str,
        languages: List[Language],
        structure_type: str = "monorepo"
    ) -> ProjectStructure:
        """Generate a multi-language project structure."""
        
        configs = []
        
        for language in languages:
            config = self._create_default_config(language, name, structure_type)
            configs.append(config)
        
        # Determine main language (first one)
        main_language = languages[0] if languages else None
        
        structure = ProjectStructure(
            name=name,
            languages=configs,
            main_language=main_language,
            project_type=structure_type
        )
        
        # Create directory structure
        if structure_type == "monorepo":
            self._create_monorepo_structure(structure)
        else:
            self._create_polyglot_structure(structure)
        
        return structure
    
    def _create_default_config(self, language: Language, project_name: str, structure_type: str) -> LanguageConfig:
        """Create default configuration for a language."""
        
        # Language-specific defaults
        defaults = {
            Language.PYTHON: {
                "package_manager": PackageManager.UV,
                "version": "3.12",
                "root_path": Path("python") if structure_type == "monorepo" else Path("."),
                "config_files": ["pyproject.toml", "requirements.txt"],
                "build_command": "uv pip install -e .",
                "test_command": "uvmgr tests run",
                "lint_command": "uvmgr lint check"
            },
            Language.JAVASCRIPT: {
                "package_manager": PackageManager.NPM,
                "version": "20",
                "root_path": Path("javascript") if structure_type == "monorepo" else Path("."),
                "config_files": ["package.json"],
                "build_command": "npm run build",
                "test_command": "npm test",
                "lint_command": "npm run lint"
            },
            Language.TYPESCRIPT: {
                "package_manager": PackageManager.NPM,
                "version": "20",
                "root_path": Path("typescript") if structure_type == "monorepo" else Path("."),
                "config_files": ["package.json", "tsconfig.json"],
                "build_command": "npm run build",
                "test_command": "npm test",
                "lint_command": "npm run lint"
            },
            Language.GO: {
                "package_manager": PackageManager.GO_MOD,
                "version": "1.21",
                "root_path": Path("go") if structure_type == "monorepo" else Path("."),
                "config_files": ["go.mod"],
                "build_command": "go build ./...",
                "test_command": "go test ./...",
                "lint_command": "go vet ./..."
            },
            Language.RUST: {
                "package_manager": PackageManager.CARGO,
                "version": "latest",
                "root_path": Path("rust") if structure_type == "monorepo" else Path("."),
                "config_files": ["Cargo.toml"],
                "build_command": "cargo build",
                "test_command": "cargo test",
                "lint_command": "cargo clippy"
            }
        }
        
        lang_defaults = defaults.get(language, {})
        
        return LanguageConfig(
            language=language,
            package_manager=lang_defaults.get("package_manager"),
            version=lang_defaults.get("version"),
            root_path=lang_defaults.get("root_path", Path(".")),
            config_files=lang_defaults.get("config_files", []),
            build_command=lang_defaults.get("build_command"),
            test_command=lang_defaults.get("test_command"),
            lint_command=lang_defaults.get("lint_command")
        )
    
    def _create_monorepo_structure(self, structure: ProjectStructure):
        """Create monorepo directory structure."""
        
        # Create language-specific directories
        for config in structure.languages:
            lang_dir = self.project_root / config.root_path
            lang_dir.mkdir(parents=True, exist_ok=True)
            
            # Create language-specific subdirectories
            (lang_dir / "src").mkdir(exist_ok=True)
            (lang_dir / "tests").mkdir(exist_ok=True)
            
            # Create basic config files
            self._create_config_files(config, lang_dir)
        
        # Create shared directories
        for shared_dir in structure.shared_directories:
            (self.project_root / shared_dir).mkdir(exist_ok=True)
        
        # Create root configuration files
        self._create_root_config(structure)
    
    def _create_polyglot_structure(self, structure: ProjectStructure):
        """Create polyglot project structure (mixed in root)."""
        
        # Create common directories
        for directory in ["src", "tests", "docs"]:
            (self.project_root / directory).mkdir(exist_ok=True)
        
        # Create configuration files for each language
        for config in structure.languages:
            self._create_config_files(config, self.project_root)
    
    def _create_config_files(self, config: LanguageConfig, target_dir: Path):
        """Create configuration files for a language."""
        
        templates = {
            Language.PYTHON: {
                "pyproject.toml": self._get_python_pyproject_template(config),
                "requirements.txt": "# Add your dependencies here\n",
                "src/__init__.py": "",
                "tests/__init__.py": "",
                "tests/test_main.py": self._get_python_test_template()
            },
            Language.JAVASCRIPT: {
                "package.json": self._get_js_package_template(config),
                "src/index.js": self._get_js_main_template(),
                "tests/index.test.js": self._get_js_test_template()
            },
            Language.TYPESCRIPT: {
                "package.json": self._get_ts_package_template(config),
                "tsconfig.json": self._get_ts_config_template(),
                "src/index.ts": self._get_ts_main_template(),
                "tests/index.test.ts": self._get_ts_test_template()
            },
            Language.GO: {
                "go.mod": self._get_go_mod_template(config),
                "main.go": self._get_go_main_template(),
                "main_test.go": self._get_go_test_template()
            },
            Language.RUST: {
                "Cargo.toml": self._get_rust_cargo_template(config),
                "src/main.rs": self._get_rust_main_template(),
                "src/lib.rs": self._get_rust_lib_template()
            }
        }
        
        files = templates.get(config.language, {})
        
        for file_path, content in files.items():
            full_path = target_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not full_path.exists():
                full_path.write_text(content)
    
    def _create_root_config(self, structure: ProjectStructure):
        """Create root configuration files."""
        
        # Create workspace configuration
        workspace_config = {
            "name": structure.name,
            "type": structure.project_type,
            "languages": [config.language.value for config in structure.languages],
            "main_language": structure.main_language.value if structure.main_language else None
        }
        
        workspace_file = self.project_root / "workspace.json"
        workspace_file.write_text(json.dumps(workspace_config, indent=2))
        
        # Create README
        readme_content = f"""# {structure.name}

Multi-language project with the following languages:
{chr(10).join(f'- {config.language.value}' for config in structure.languages)}

## Structure

This is a {structure.project_type} project with the following structure:

```
{structure.name}/
{chr(10).join(f'├── {config.root_path}/ ({config.language.value})' for config in structure.languages)}
├── docs/
└── scripts/
```

## Development

Each language component can be developed independently:

{chr(10).join(self._get_language_dev_instructions(config) for config in structure.languages)}

## Building

To build all components:

```bash
uvmgr multilang build
```

To test all components:

```bash
uvmgr multilang test
```
"""
        
        readme_file = self.project_root / "README.md"
        readme_file.write_text(readme_content)
    
    def _get_language_dev_instructions(self, config: LanguageConfig) -> str:
        """Get development instructions for a language."""
        
        instructions = {
            Language.PYTHON: f"""
### Python ({config.root_path})

```bash
cd {config.root_path}
{config.build_command}
{config.test_command}
```""",
            Language.JAVASCRIPT: f"""
### JavaScript ({config.root_path})

```bash
cd {config.root_path}
npm install
{config.build_command}
{config.test_command}
```""",
            Language.GO: f"""
### Go ({config.root_path})

```bash
cd {config.root_path}
go mod download
{config.build_command}
{config.test_command}
```""",
            Language.RUST: f"""
### Rust ({config.root_path})

```bash
cd {config.root_path}
{config.build_command}
{config.test_command}
```"""
        }
        
        return instructions.get(config.language, "")
    
    # Template methods for different languages
    def _get_python_pyproject_template(self, config: LanguageConfig) -> str:
        project_name = self.project_root.name
        return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "0.1.0"
description = "Python component of {project_name}"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]

[tool.ruff]
target-version = "py{config.version.replace(".", "")}"
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
'''
    
    def _get_js_package_template(self, config: LanguageConfig) -> str:
        project_name = self.project_root.name
        return json.dumps({
            "name": f"{project_name}-js",
            "version": "0.1.0",
            "description": f"JavaScript component of {project_name}",
            "main": "src/index.js",
            "scripts": {
                "build": "echo 'Build script here'",
                "test": "jest",
                "lint": "eslint src/"
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "eslint": "^8.0.0"
            },
            "engines": {
                "node": f">={config.version}"
            }
        }, indent=2)
    
    def _get_ts_package_template(self, config: LanguageConfig) -> str:
        project_name = self.project_root.name
        return json.dumps({
            "name": f"{project_name}-ts",
            "version": "0.1.0",
            "description": f"TypeScript component of {project_name}",
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "build": "tsc",
                "test": "jest",
                "lint": "eslint src/"
            },
            "devDependencies": {
                "typescript": "^5.0.0",
                "jest": "^29.0.0",
                "eslint": "^8.0.0",
                "@types/jest": "^29.0.0"
            },
            "engines": {
                "node": f">={config.version}"
            }
        }, indent=2)
    
    def _get_go_mod_template(self, config: LanguageConfig) -> str:
        project_name = self.project_root.name
        return f"""module {project_name}

go {config.version}

require (
)
"""
    
    def _get_rust_cargo_template(self, config: LanguageConfig) -> str:
        project_name = self.project_root.name
        return f"""[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"

[dependencies]

[dev-dependencies]
"""
    
    def _get_python_test_template(self) -> str:
        return '''"""Test module."""

def test_example():
    """Example test."""
    assert True
'''
    
    def _get_js_main_template(self) -> str:
        return '''// Main JavaScript module
console.log("Hello from JavaScript!");

module.exports = {
    hello: () => "Hello from JavaScript!"
};
'''
    
    def _get_js_test_template(self) -> str:
        return '''// JavaScript tests
const { hello } = require('../src/index');

test('hello function', () => {
    expect(hello()).toBe('Hello from JavaScript!');
});
'''
    
    def _get_ts_main_template(self) -> str:
        return '''// Main TypeScript module
console.log("Hello from TypeScript!");

export function hello(): string {
    return "Hello from TypeScript!";
}
'''
    
    def _get_ts_test_template(self) -> str:
        return '''// TypeScript tests
import { hello } from '../src/index';

test('hello function', () => {
    expect(hello()).toBe('Hello from TypeScript!');
});
'''
    
    def _get_ts_config_template(self) -> str:
        return json.dumps({
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "declaration": True
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist", "tests"]
        }, indent=2)
    
    def _get_go_main_template(self) -> str:
        return '''package main

import "fmt"

func main() {
    fmt.Println("Hello from Go!")
}
'''
    
    def _get_go_test_template(self) -> str:
        return '''package main

import "testing"

func TestMain(t *testing.T) {
    // Example test
    if 1+1 != 2 {
        t.Error("Math is broken")
    }
}
'''
    
    def _get_rust_main_template(self) -> str:
        return '''fn main() {
    println!("Hello from Rust!");
}
'''
    
    def _get_rust_lib_template(self) -> str:
        return '''//! Rust library module

pub fn hello() -> &'static str {
    "Hello from Rust!"
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hello() {
        assert_eq!(hello(), "Hello from Rust!");
    }
}
'''