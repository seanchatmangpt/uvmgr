"""
Progressive Command Discovery Engine
===================================

This module addresses the critical UX gap by providing intelligent command discovery and guidance.

Key features:
1. **Interactive Command Exploration**: Context-aware command suggestions
2. **Smart Command Completion**: Auto-complete with project context
3. **Guided Workflows**: Step-by-step guidance for common tasks
4. **Usage Pattern Learning**: Learns from user behavior to improve suggestions

The 80/20 approach: 20% of discovery features that solve 80% of UX friction.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import difflib

from uvmgr.core.semconv import CliAttributes, ProjectAttributes
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning, get_agi_insights
from uvmgr.core.workspace import get_workspace_config, get_workspace_manager
from uvmgr.core.knowledge import get_knowledge_base


@dataclass
class CommandSuggestion:
    """A suggested command with context and rationale."""
    
    command: str
    description: str
    confidence: float
    rationale: str
    category: str
    examples: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


@dataclass
class UserContext:
    """Current user context for intelligent suggestions."""
    
    project_type: str
    current_directory: str
    recent_commands: List[str] = field(default_factory=list)
    project_files: List[str] = field(default_factory=list)
    git_status: Optional[str] = None
    environment: str = "development"
    user_level: str = "beginner"  # beginner, intermediate, advanced


@dataclass
class WorkflowGuide:
    """Guided workflow for accomplishing specific tasks."""
    
    name: str
    description: str
    category: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: str = "5-10 minutes"
    difficulty: str = "beginner"


class ProjectAnalyzer:
    """Analyzes project context for intelligent command suggestions."""
    
    @staticmethod
    def analyze_current_context() -> UserContext:
        """Analyze current project context."""
        
        cwd = Path.cwd()
        
        # Basic project detection
        project_type = ProjectAnalyzer._detect_project_type(cwd)
        
        # Get workspace config if available
        try:
            workspace_config = get_workspace_config()
            environment = get_workspace_manager().load_state().current_environment
        except Exception:
            environment = "development"
        
        # Get recent command history
        recent_commands = ProjectAnalyzer._get_recent_commands()
        
        # Get project files
        project_files = ProjectAnalyzer._get_project_files(cwd)
        
        # Get git status
        git_status = ProjectAnalyzer._get_git_status(cwd)
        
        # Determine user level from command history
        user_level = ProjectAnalyzer._determine_user_level(recent_commands)
        
        return UserContext(
            project_type=project_type,
            current_directory=str(cwd),
            recent_commands=recent_commands,
            project_files=project_files,
            git_status=git_status,
            environment=environment,
            user_level=user_level
        )
    
    @staticmethod
    def _detect_project_type(path: Path) -> str:
        """Detect project type from directory contents."""
        
        # Check for specific markers
        if (path / "pyproject.toml").exists():
            content = (path / "pyproject.toml").read_text()
            if "fastapi" in content.lower():
                return "fastapi"
            elif "flask" in content.lower():
                return "flask"
            elif "django" in content.lower():
                return "django"
            elif "typer" in content.lower():
                return "cli"
            else:
                return "python"
        
        if (path / "setup.py").exists():
            return "python"
        
        if (path / "requirements.txt").exists():
            return "python"
        
        if (path / "Dockerfile").exists():
            return "containerized"
        
        if (path / ".github" / "workflows").exists():
            return "ci_cd"
        
        return "general"
    
    @staticmethod
    def _get_recent_commands() -> List[str]:
        """Get recent command history."""
        
        try:
            manager = get_workspace_manager()
            state = manager.load_state()
            return [cmd["command"] for cmd in state.command_history[-10:]]
        except Exception:
            return []
    
    @staticmethod
    def _get_project_files(path: Path) -> List[str]:
        """Get relevant project files."""
        
        important_files = []
        
        # Configuration files
        for pattern in ["*.toml", "*.yaml", "*.yml", "*.json", "requirements*.txt", "Dockerfile", "*.md"]:
            important_files.extend([str(f.name) for f in path.glob(pattern)])
        
        # Source directories
        for src_dir in ["src", "lib", "app", "tests"]:
            if (path / src_dir).exists():
                important_files.append(f"{src_dir}/")
        
        return important_files[:20]  # Limit to most relevant
    
    @staticmethod
    def _get_git_status(path: Path) -> Optional[str]:
        """Get git repository status."""
        
        if not (path / ".git").exists():
            return None
        
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if not lines or lines == ['']:
                    return "clean"
                else:
                    return f"{len(lines)} changes"
            
        except Exception:
            pass
        
        return "unknown"
    
    @staticmethod
    def _determine_user_level(recent_commands: List[str]) -> str:
        """Determine user experience level from command history."""
        
        if len(recent_commands) < 3:
            return "beginner"
        
        # Advanced indicators
        advanced_commands = {"workflow", "knowledge", "agent", "ai", "forge", "otel"}
        if any(cmd in advanced_commands for cmd in recent_commands):
            return "advanced"
        
        # Intermediate indicators
        intermediate_commands = {"build", "release", "lint", "serve"}
        if any(cmd in intermediate_commands for cmd in recent_commands):
            return "intermediate"
        
        return "beginner"


class CommandDiscoveryEngine:
    """
    Intelligent command discovery engine that provides context-aware suggestions.
    
    Addresses the critical UX gap of command discoverability and learning curve.
    """
    
    def __init__(self):
        self.command_registry = self._build_command_registry()
        self.workflow_guides = self._build_workflow_guides()
        
    def _build_command_registry(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive command registry with metadata."""
        
        return {
            # Core commands
            "workspace": {
                "category": "configuration",
                "description": "Manage workspace configuration and environments",
                "keywords": ["config", "environment", "settings", "setup"],
                "beginner_friendly": True,
                "examples": ["workspace init", "workspace status", "workspace env switch staging"],
                "when_to_use": ["Starting new project", "Switching environments", "Checking project status"]
            },
            
            "deps": {
                "category": "dependencies",
                "description": "Manage project dependencies with uv",
                "keywords": ["dependencies", "packages", "install", "requirements"],
                "beginner_friendly": True,
                "examples": ["deps add requests", "deps list", "deps update"],
                "when_to_use": ["Adding new packages", "Updating dependencies", "Checking installed packages"]
            },
            
            "tests": {
                "category": "quality",
                "description": "Run test suite with coverage",
                "keywords": ["testing", "pytest", "coverage", "quality"],
                "beginner_friendly": True,
                "examples": ["tests run", "tests coverage", "tests run --verbose"],
                "when_to_use": ["After code changes", "Before commits", "CI/CD validation"]
            },
            
            "lint": {
                "category": "quality",
                "description": "Code quality checks and formatting",
                "keywords": ["formatting", "style", "quality", "ruff"],
                "beginner_friendly": True,
                "examples": ["lint check", "lint fix", "lint --auto-fix"],
                "when_to_use": ["Before commits", "Code review prep", "Maintaining code quality"]
            },
            
            "build": {
                "category": "packaging",
                "description": "Build distributions and executables",
                "keywords": ["package", "distribute", "executable", "wheel"],
                "beginner_friendly": False,
                "examples": ["build dist", "build exe", "build dogfood"],
                "when_to_use": ["Creating releases", "Building executables", "Distribution packaging"]
            },
            
            "workflow": {
                "category": "automation",
                "description": "Execute workflow templates with automation",
                "keywords": ["automation", "templates", "ci/cd", "orchestration"],
                "beginner_friendly": False,
                "examples": ["workflow list", "workflow run ci_cd", "workflow status"],
                "when_to_use": ["Automating complex tasks", "CI/CD processes", "Repeatable workflows"]
            },
            
            "ai": {
                "category": "intelligence",
                "description": "AI-powered development assistance",
                "keywords": ["ai", "assistance", "intelligent", "help"],
                "beginner_friendly": True,
                "examples": ["ai assist", "ai plan", "ai fix-tests"],
                "when_to_use": ["Getting help", "Planning features", "Fixing issues"]
            },
            
            "knowledge": {
                "category": "intelligence",
                "description": "Code understanding and knowledge management",
                "keywords": ["search", "understanding", "analysis", "patterns"],
                "beginner_friendly": False,
                "examples": ["knowledge analyze", "knowledge search 'auth'", "knowledge insights"],
                "when_to_use": ["Understanding codebase", "Finding code patterns", "Code analysis"]
            }
        }
    
    def _build_workflow_guides(self) -> List[WorkflowGuide]:
        """Build guided workflow library."""
        
        guides = []
        
        # New project setup
        guides.append(WorkflowGuide(
            name="new_project_setup",
            description="Set up a new Python project with uvmgr",
            category="getting_started",
            steps=[
                {
                    "command": "workspace init myproject --type python",
                    "description": "Initialize workspace with unified configuration",
                    "verification": "Check that .uvmgr/workspace.yaml exists"
                },
                {
                    "command": "deps add --dev pytest coverage ruff",
                    "description": "Add essential development dependencies",
                    "verification": "Check pyproject.toml for dev dependencies"
                },
                {
                    "command": "workspace config set global.auto_test true",
                    "description": "Enable automatic testing",
                    "verification": "Verify config with workspace status"
                }
            ],
            estimated_time="5 minutes",
            difficulty="beginner"
        ))
        
        # Code quality workflow
        guides.append(WorkflowGuide(
            name="code_quality_check",
            description="Run comprehensive code quality checks",
            category="quality_assurance",
            steps=[
                {
                    "command": "lint check",
                    "description": "Check code formatting and style",
                    "verification": "No linting errors reported"
                },
                {
                    "command": "tests run --coverage",
                    "description": "Run tests with coverage report",
                    "verification": "All tests pass with good coverage"
                },
                {
                    "command": "knowledge analyze",
                    "description": "Analyze code patterns and complexity",
                    "verification": "Knowledge base updated with insights"
                }
            ],
            estimated_time="3-5 minutes",
            difficulty="beginner"
        ))
        
        # AI-enhanced development
        guides.append(WorkflowGuide(
            name="ai_enhanced_development",
            description="Use AI features for intelligent development",
            category="ai_workflow",
            steps=[
                {
                    "command": "knowledge analyze --force",
                    "description": "Build comprehensive project knowledge",
                    "verification": "Project analysis completed"
                },
                {
                    "command": "ai assist 'How can I improve this codebase?'",
                    "description": "Get AI-powered improvement suggestions",
                    "verification": "Receive contextual suggestions"
                },
                {
                    "command": "workflow run ai_enhancement",
                    "description": "Run AI enhancement workflow",
                    "verification": "Workflow completes successfully"
                }
            ],
            prerequisites=["Project with existing code"],
            estimated_time="10-15 minutes",
            difficulty="intermediate"
        ))
        
        return guides
    
    def suggest_commands(self, context: Optional[UserContext] = None, query: str = "") -> List[CommandSuggestion]:
        """Generate intelligent command suggestions based on context."""
        
        if context is None:
            context = ProjectAnalyzer.analyze_current_context()
        
        suggestions = []
        
        # Query-based suggestions
        if query:
            suggestions.extend(self._query_based_suggestions(query, context))
        
        # Context-based suggestions
        suggestions.extend(self._context_based_suggestions(context))
        
        # Learning-based suggestions
        suggestions.extend(self._learning_based_suggestions(context))
        
        # Sort by confidence and relevance
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        # Observe discovery interaction
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "discovery_suggest",
                "query": query,
                "suggestions_count": str(len(suggestions)),
                "user_level": context.user_level,
                "project_type": context.project_type
            },
            context={
                "command_discovery": True,
                "user_guidance": True
            }
        )
        
        return suggestions[:10]  # Top 10 suggestions
    
    def _query_based_suggestions(self, query: str, context: UserContext) -> List[CommandSuggestion]:
        """Generate suggestions based on user query."""
        
        suggestions = []
        query_lower = query.lower()
        
        # Keyword matching
        for cmd, info in self.command_registry.items():
            relevance = 0.0
            
            # Direct command name match
            if query_lower in cmd:
                relevance += 0.8
            
            # Keyword matching
            for keyword in info["keywords"]:
                if keyword in query_lower:
                    relevance += 0.6
            
            # Description matching
            if any(word in info["description"].lower() for word in query_lower.split()):
                relevance += 0.4
            
            if relevance > 0:
                suggestions.append(CommandSuggestion(
                    command=cmd,
                    description=info["description"],
                    confidence=min(relevance, 1.0),
                    rationale=f"Matches query '{query}'",
                    category=info["category"],
                    examples=info["examples"][:2]
                ))
        
        return suggestions
    
    def _context_based_suggestions(self, context: UserContext) -> List[CommandSuggestion]:
        """Generate suggestions based on project context."""
        
        suggestions = []
        
        # Project type specific suggestions
        if context.project_type == "python":
            if "tests" not in context.recent_commands:
                suggestions.append(CommandSuggestion(
                    command="tests",
                    description="Run test suite - recommended for Python projects",
                    confidence=0.8,
                    rationale="Python project without recent testing",
                    category="quality",
                    examples=["tests run", "tests coverage"]
                ))
        
        # Git status based suggestions
        if context.git_status and context.git_status != "clean":
            suggestions.append(CommandSuggestion(
                command="lint",
                description="Check code quality before committing",
                confidence=0.7,
                rationale=f"Git status: {context.git_status}",
                category="quality",
                examples=["lint check", "lint fix"]
            ))
        
        # Environment specific suggestions
        if context.environment == "development":
            suggestions.append(CommandSuggestion(
                command="workspace",
                description="Switch to staging environment for testing",
                confidence=0.5,
                rationale="Currently in development environment",
                category="configuration",
                examples=["workspace env switch staging"]
            ))
        
        # File-based suggestions
        if "pyproject.toml" in context.project_files:
            if "deps" not in context.recent_commands:
                suggestions.append(CommandSuggestion(
                    command="deps",
                    description="Manage project dependencies",
                    confidence=0.6,
                    rationale="Project has pyproject.toml",
                    category="dependencies",
                    examples=["deps list", "deps add <package>"]
                ))
        
        return suggestions
    
    def _learning_based_suggestions(self, context: UserContext) -> List[CommandSuggestion]:
        """Generate suggestions based on usage patterns and learning."""
        
        suggestions = []
        
        # User level appropriate suggestions
        if context.user_level == "beginner":
            # Suggest foundational commands
            basic_commands = ["workspace", "deps", "tests", "lint"]
            for cmd in basic_commands:
                if cmd not in context.recent_commands:
                    info = self.command_registry[cmd]
                    suggestions.append(CommandSuggestion(
                        command=cmd,
                        description=f"Essential command: {info['description']}",
                        confidence=0.6,
                        rationale="Recommended for beginners",
                        category=info["category"],
                        examples=info["examples"][:1]
                    ))
        
        elif context.user_level == "advanced":
            # Suggest advanced features
            advanced_commands = ["workflow", "knowledge", "ai"]
            for cmd in advanced_commands:
                if cmd not in context.recent_commands:
                    info = self.command_registry[cmd]
                    suggestions.append(CommandSuggestion(
                        command=cmd,
                        description=f"Advanced feature: {info['description']}",
                        confidence=0.5,
                        rationale="Advanced user capabilities",
                        category=info["category"],
                        examples=info["examples"][:1]
                    ))
        
        # Pattern-based suggestions from AGI insights
        agi_insights = get_agi_insights()
        if agi_insights["understanding_confidence"] < 0.7:
            suggestions.append(CommandSuggestion(
                command="knowledge analyze",
                description="Build AI understanding of your codebase",
                confidence=0.7,
                rationale="Low AI understanding confidence",
                category="intelligence",
                examples=["knowledge analyze --force"]
            ))
        
        return suggestions
    
    def get_workflow_guide(self, name: str) -> Optional[WorkflowGuide]:
        """Get specific workflow guide."""
        return next((guide for guide in self.workflow_guides if guide.name == name), None)
    
    def suggest_workflows(self, context: Optional[UserContext] = None) -> List[WorkflowGuide]:
        """Suggest relevant workflow guides."""
        
        if context is None:
            context = ProjectAnalyzer.analyze_current_context()
        
        relevant_guides = []
        
        for guide in self.workflow_guides:
            relevance = 0.0
            
            # Match difficulty to user level
            if guide.difficulty == context.user_level:
                relevance += 0.5
            elif guide.difficulty == "beginner" and context.user_level in ["intermediate", "advanced"]:
                relevance += 0.3
            
            # Match category to project type
            if context.project_type == "python" and guide.category in ["getting_started", "quality_assurance"]:
                relevance += 0.4
            
            if context.user_level == "advanced" and guide.category == "ai_workflow":
                relevance += 0.6
            
            if relevance > 0:
                relevant_guides.append(guide)
        
        return sorted(relevant_guides, key=lambda g: g.difficulty == context.user_level, reverse=True)
    
    def fuzzy_search_commands(self, partial: str) -> List[Tuple[str, float]]:
        """Fuzzy search for command completion."""
        
        matches = []
        
        for cmd in self.command_registry.keys():
            # Use difflib for fuzzy matching
            similarity = difflib.SequenceMatcher(None, partial.lower(), cmd.lower()).ratio()
            if similarity > 0.3:  # Minimum similarity threshold
                matches.append((cmd, similarity))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)


# Global discovery engine instance
_discovery_engine: Optional[CommandDiscoveryEngine] = None

def get_discovery_engine() -> CommandDiscoveryEngine:
    """Get the global command discovery engine."""
    global _discovery_engine
    
    if _discovery_engine is None:
        _discovery_engine = CommandDiscoveryEngine()
    
    return _discovery_engine

def suggest_commands(query: str = "", context: Optional[UserContext] = None) -> List[CommandSuggestion]:
    """Get intelligent command suggestions."""
    return get_discovery_engine().suggest_commands(context, query)

def suggest_workflows(context: Optional[UserContext] = None) -> List[WorkflowGuide]:
    """Get relevant workflow guides."""
    return get_discovery_engine().suggest_workflows(context)