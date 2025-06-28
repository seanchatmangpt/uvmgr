"""
Unified Workspace and Configuration Management
===========================================

This module addresses the critical gap in uvmgr's configuration management by providing:

1. **Workspace-level configuration**: Project-wide settings and state
2. **Environment management**: dev/staging/prod environment support  
3. **Configuration inheritance**: Hierarchical config with overrides
4. **Unified settings**: Central configuration for all uvmgr commands
5. **State persistence**: Workspace state tracking and management

The 80/20 approach: 20% of configuration features that solve 80% of workflow problems.
"""

from __future__ import annotations

import os
import json
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from uvmgr.core.semconv import ProjectAttributes, CliAttributes
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment (dev/staging/prod)."""
    
    name: str
    python_version: Optional[str] = None
    dependencies: Dict[str, str] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    deployment_target: Optional[str] = None
    build_settings: Dict[str, Any] = field(default_factory=dict)
    test_settings: Dict[str, Any] = field(default_factory=dict)
    ai_settings: Dict[str, Any] = field(default_factory=dict)
    

@dataclass 
class WorkspaceConfig:
    """Unified configuration for uvmgr workspace."""
    
    # Project identity
    project_name: str
    project_version: str = "0.1.0"
    project_type: str = "python"  # python, fastapi, cli, library, etc.
    
    # Default environment
    default_environment: str = "development"
    
    # Environment configurations
    environments: Dict[str, EnvironmentConfig] = field(default_factory=dict)
    
    # Global settings
    global_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Command defaults
    command_defaults: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Workflow settings
    workflow_settings: Dict[str, Any] = field(default_factory=dict)
    
    # AI/AGI settings
    ai_config: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    

@dataclass
class WorkspaceState:
    """Runtime state for uvmgr workspace."""
    
    current_environment: str = "development"
    last_command: Optional[str] = None
    command_history: List[Dict[str, Any]] = field(default_factory=list)
    workflow_state: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    ai_context: Dict[str, Any] = field(default_factory=dict)
    

class WorkspaceManager:
    """
    Unified workspace and configuration manager for uvmgr.
    
    Addresses the critical gap by providing:
    - Centralized configuration management
    - Environment-specific settings
    - Workspace state tracking
    - Configuration inheritance and overrides
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.config_file = self.workspace_root / ".uvmgr" / "workspace.yaml"
        self.state_file = self.workspace_root / ".uvmgr" / "state.json"
        
        # Ensure .uvmgr directory exists
        self.config_file.parent.mkdir(exist_ok=True)
        
        self._config: Optional[WorkspaceConfig] = None
        self._state: Optional[WorkspaceState] = None
        
    def initialize_workspace(self, project_name: str, project_type: str = "python") -> WorkspaceConfig:
        """Initialize a new uvmgr workspace with unified configuration."""
        
        # Create default environments
        dev_env = EnvironmentConfig(
            name="development",
            python_version="3.11+",
            environment_variables={"DEBUG": "true"},
            test_settings={"coverage": True, "verbose": True},
            ai_settings={"model": "groq/llama-3.2-90b-text-preview", "temperature": 0.1}
        )
        
        staging_env = EnvironmentConfig(
            name="staging", 
            python_version="3.11+",
            environment_variables={"DEBUG": "false"},
            test_settings={"coverage": True, "verbose": False},
            deployment_target="staging"
        )
        
        prod_env = EnvironmentConfig(
            name="production",
            python_version="3.11+", 
            environment_variables={"DEBUG": "false"},
            test_settings={"coverage": True, "verbose": False},
            deployment_target="production",
            build_settings={"optimize": True, "minify": True}
        )
        
        # Create workspace configuration
        config = WorkspaceConfig(
            project_name=project_name,
            project_type=project_type,
            environments={
                "development": dev_env,
                "staging": staging_env,
                "production": prod_env
            },
            global_settings={
                "auto_install_deps": True,
                "auto_format": True,
                "auto_test": False,
                "telemetry_enabled": True
            },
            command_defaults={
                "tests": {"coverage": True, "verbose": False},
                "build": {"optimize": False, "include_source": True},
                "ai": {"model": "groq/llama-3.2-90b-text-preview", "temperature": 0.1},
                "lint": {"auto_fix": True, "strict": False}
            },
            workflow_settings={
                "auto_workflows": True,
                "parallel_execution": False,
                "retry_on_failure": True,
                "max_retries": 3
            },
            ai_config={
                "knowledge_base_enabled": True,
                "code_understanding": True,
                "autonomous_suggestions": True,
                "learning_enabled": True
            }
        )
        
        self._config = config
        self.save_config()
        
        # Initialize state
        self._state = WorkspaceState(current_environment="development")
        self.save_state()
        
        # Observe workspace initialization
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "workspace_init",
                ProjectAttributes.NAME: project_name,
                ProjectAttributes.LANGUAGE: "python",
                "project_type": project_type
            },
            context={
                "workspace_management": True,
                "unified_config": True,
                "environments_created": 3
            }
        )
        
        return config
    
    def load_config(self) -> WorkspaceConfig:
        """Load workspace configuration with intelligent defaults."""
        if self._config:
            return self._config
            
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                # Convert environments
                environments = {}
                for env_name, env_data in config_data.get("environments", {}).items():
                    environments[env_name] = EnvironmentConfig(**env_data)
                    
                config_data["environments"] = environments
                self._config = WorkspaceConfig(**config_data)
                
            except Exception as e:
                # Fallback to default config
                self._config = self._create_default_config()
        else:
            # Auto-initialize with defaults
            project_name = self.workspace_root.name
            self._config = self.initialize_workspace(project_name)
            
        return self._config
    
    def save_config(self):
        """Save workspace configuration."""
        if not self._config:
            return
            
        # Convert to serializable format
        config_dict = asdict(self._config)
        config_dict["updated_at"] = datetime.now().isoformat()
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def load_state(self) -> WorkspaceState:
        """Load workspace runtime state."""
        if self._state:
            return self._state
            
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                    self._state = WorkspaceState(**state_data)
            except Exception:
                self._state = WorkspaceState()
        else:
            self._state = WorkspaceState()
            
        return self._state
    
    def save_state(self):
        """Save workspace runtime state."""
        if not self._state:
            return
            
        with open(self.state_file, 'w') as f:
            json.dump(asdict(self._state), f, indent=2)
    
    def get_environment_config(self, env_name: Optional[str] = None) -> EnvironmentConfig:
        """Get configuration for specific environment."""
        config = self.load_config()
        state = self.load_state()
        
        env_name = env_name or state.current_environment or config.default_environment
        
        if env_name not in config.environments:
            raise ValueError(f"Environment '{env_name}' not found in workspace configuration")
            
        return config.environments[env_name]
    
    def switch_environment(self, env_name: str):
        """Switch to a different environment."""
        config = self.load_config()
        
        if env_name not in config.environments:
            raise ValueError(f"Environment '{env_name}' not found")
            
        state = self.load_state()
        state.current_environment = env_name
        self.save_state()
        
        # Observe environment switch
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "workspace_switch_env",
                "environment": env_name
            },
            context={
                "workspace_management": True,
                "environment_switch": True
            }
        )
    
    def get_command_config(self, command: str) -> Dict[str, Any]:
        """Get configuration for a specific command with inheritance."""
        config = self.load_config()
        env_config = self.get_environment_config()
        
        # Start with global defaults
        command_config = config.global_settings.copy()
        
        # Add command-specific defaults
        if command in config.command_defaults:
            command_config.update(config.command_defaults[command])
            
        # Apply environment-specific overrides
        env_settings = getattr(env_config, f"{command}_settings", {})
        if env_settings:
            command_config.update(env_settings)
            
        return command_config
    
    def update_command_history(self, command: str, args: Dict[str, Any], success: bool, duration: float):
        """Update command execution history."""
        state = self.load_state()
        
        history_entry = {
            "command": command,
            "args": args,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "environment": state.current_environment
        }
        
        state.command_history.append(history_entry)
        state.last_command = command
        
        # Keep only last 100 commands
        if len(state.command_history) > 100:
            state.command_history = state.command_history[-100:]
            
        self.save_state()
    
    def get_workspace_summary(self) -> Dict[str, Any]:
        """Get comprehensive workspace status summary."""
        config = self.load_config()
        state = self.load_state()
        env_config = self.get_environment_config()
        
        return {
            "workspace_root": str(self.workspace_root),
            "project": {
                "name": config.project_name,
                "version": config.project_version,
                "type": config.project_type
            },
            "current_environment": state.current_environment,
            "available_environments": list(config.environments.keys()),
            "recent_commands": state.command_history[-5:] if state.command_history else [],
            "global_settings": config.global_settings,
            "environment_config": {
                "python_version": env_config.python_version,
                "deployment_target": env_config.deployment_target,
                "dependencies_count": len(env_config.dependencies)
            },
            "ai_enabled": config.ai_config.get("knowledge_base_enabled", False),
            "workflows_enabled": config.workflow_settings.get("auto_workflows", False),
            "telemetry_enabled": config.global_settings.get("telemetry_enabled", True)
        }
    
    def _create_default_config(self) -> WorkspaceConfig:
        """Create default workspace configuration."""
        project_name = self.workspace_root.name
        return self.initialize_workspace(project_name)


# Global workspace manager instance
_workspace_manager: Optional[WorkspaceManager] = None

def get_workspace_manager(workspace_root: Optional[Path] = None) -> WorkspaceManager:
    """Get the global workspace manager instance."""
    global _workspace_manager
    
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager(workspace_root)
    
    return _workspace_manager

def get_workspace_config() -> WorkspaceConfig:
    """Get current workspace configuration."""
    return get_workspace_manager().load_config()

def get_environment_config(env_name: Optional[str] = None) -> EnvironmentConfig:
    """Get current environment configuration."""
    return get_workspace_manager().get_environment_config(env_name)

def get_command_config(command: str) -> Dict[str, Any]:
    """Get configuration for a command with inheritance."""
    return get_workspace_manager().get_command_config(command)

def update_command_history(command: str, args: Dict[str, Any], success: bool, duration: float):
    """Update workspace command history."""
    get_workspace_manager().update_command_history(command, args, success, duration)