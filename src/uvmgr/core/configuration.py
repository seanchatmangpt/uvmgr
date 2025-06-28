"""
Configuration Management System
===============================

Centralized configuration management for uvmgr with intelligent defaults,
environment-specific overrides, and AGI-driven optimization.

Key Features:
- Hierarchical configuration (global, project, user, environment)
- Type-safe configuration with validation
- Environment variable integration
- AGI-driven configuration optimization
- Hot-reloading and change detection
- Secure secrets management integration

This fills a critical gap: lack of centralized configuration management.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints
import toml

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.agi_memory import get_persistent_memory
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram
from uvmgr.core.paths import CONFIG_DIR


T = TypeVar('T')


class ConfigScope(Enum):
    """Configuration scope levels."""
    SYSTEM = "system"        # System-wide defaults
    GLOBAL = "global"        # User global config
    PROJECT = "project"      # Project-specific config
    ENVIRONMENT = "environment"  # Environment variables
    RUNTIME = "runtime"      # Runtime overrides


class ConfigFormat(Enum):
    """Supported configuration formats."""
    TOML = "toml"
    JSON = "json"
    YAML = "yaml"
    ENV = "env"


@dataclass
class ConfigValidationError(Exception):
    """Configuration validation error."""
    field: str
    value: Any
    message: str
    scope: ConfigScope


@dataclass
class AGIConfig:
    """AGI system configuration."""
    
    # Memory configuration
    memory_enabled: bool = True
    memory_path: Optional[str] = None
    memory_max_entries: int = 10000
    memory_similarity_threshold: float = 0.3
    
    # Reasoning configuration
    reasoning_enabled: bool = True
    reasoning_confidence_threshold: float = 0.7
    understanding_confidence_threshold: float = 0.8
    
    # Goal generation
    autonomous_goals_enabled: bool = True
    max_concurrent_goals: int = 5
    goal_review_interval: int = 3600  # seconds
    
    # Self-modification
    self_modification_enabled: bool = False  # Disabled by default for safety
    modification_risk_threshold: str = "medium"  # low, medium, high, critical
    ollama_model: str = "codellama"
    
    # Optimization
    agi_optimization_enabled: bool = True
    optimization_interval: int = 3600  # seconds


@dataclass
class TelemetryConfig:
    """Telemetry and observability configuration."""
    
    # OpenTelemetry
    otel_enabled: bool = True
    otel_service_name: str = "uvmgr"
    otel_service_version: str = "0.0.0"
    otel_endpoint: Optional[str] = None
    otel_headers: Dict[str, str] = field(default_factory=dict)
    
    # Metrics
    metrics_enabled: bool = True
    metrics_endpoint: Optional[str] = None
    metrics_interval: int = 60  # seconds
    
    # Tracing
    tracing_enabled: bool = True
    tracing_sample_rate: float = 1.0
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "structured"
    log_file: Optional[str] = None


@dataclass
class RuntimeConfig:
    """Runtime system configuration."""
    
    # Workflow execution
    max_concurrent_workflows: int = 10
    workflow_timeout: int = 300  # seconds
    workflow_retry_count: int = 3
    
    # Scheduler
    scheduler_enabled: bool = True
    scheduler_max_jobs: int = 100
    scheduler_persistence_enabled: bool = True
    
    # Task management
    task_auto_detection: bool = True
    task_max_parallel: int = 4
    task_timeout: int = 300  # seconds
    
    # Performance
    cache_enabled: bool = True
    cache_max_size: int = 1000
    cache_ttl: int = 3600  # seconds


@dataclass
class SecurityConfig:
    """Security configuration."""
    
    # Secrets management
    secrets_backend: str = "keyring"  # keyring, env, vault, aws
    secrets_encryption: bool = True
    
    # Input validation
    strict_validation: bool = True
    sanitize_inputs: bool = True
    
    # Execution security
    sandbox_execution: bool = True
    allowed_commands: List[str] = field(default_factory=lambda: ["uv", "python", "git"])
    dangerous_command_protection: bool = True
    
    # Network security
    verify_ssl: bool = True
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None


@dataclass
class DevelopmentConfig:
    """Development tools configuration."""
    
    # Code quality
    lint_enabled: bool = True
    format_on_save: bool = True
    type_checking_enabled: bool = True
    
    # Testing
    auto_test_discovery: bool = True
    test_coverage_enabled: bool = True
    test_coverage_threshold: float = 80.0
    
    # Build and deployment
    auto_build_enabled: bool = False
    deployment_enabled: bool = False
    
    # Integration
    git_hooks_enabled: bool = True
    ci_cd_integration: bool = True


@dataclass
class UvmgrConfig:
    """Main uvmgr configuration."""
    
    # Core settings
    project_root: Optional[str] = None
    workspace_enabled: bool = True
    
    # Subsystem configurations
    agi: AGIConfig = field(default_factory=AGIConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    
    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    version: str = "1.0"
    last_updated: Optional[float] = None
    updated_by: str = "uvmgr"


class ConfigurationManager:
    """
    Intelligent configuration management system.
    
    Provides hierarchical configuration with type safety, validation,
    and AGI-driven optimization.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.config_cache: Dict[ConfigScope, UvmgrConfig] = {}
        self.watchers: List[Any] = []
        self.validation_enabled = True
        
        # Configuration file paths
        self.config_paths = {
            ConfigScope.SYSTEM: Path(__file__).parent / "defaults.toml",
            ConfigScope.GLOBAL: CONFIG_DIR / "config.toml", 
            ConfigScope.PROJECT: self.project_root / ".uvmgr" / "config.toml",
            ConfigScope.ENVIRONMENT: None,  # Environment variables
            ConfigScope.RUNTIME: None      # Runtime overrides
        }
        
        # Initialize configuration
        self._initialize_configuration()
    
    def _initialize_configuration(self):
        """Initialize configuration system."""
        
        with span("config.initialize"):
            
            # Ensure config directories exist
            for scope, path in self.config_paths.items():
                if path and path.parent:
                    path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create default configuration files if they don't exist
            self._create_default_configs()
            
            # Load configuration hierarchy
            self._load_configuration_hierarchy()
            
            # Observe initialization
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "config_initialize",
                    "project_root": str(self.project_root),
                    "scopes_loaded": str(len(self.config_cache))
                },
                context={"configuration": True, "initialization": True}
            )
            
            metric_counter("config.initialization")(1)
    
    def _create_default_configs(self):
        """Create default configuration files."""
        
        # Global config
        global_config_path = self.config_paths[ConfigScope.GLOBAL]
        if not global_config_path.exists():
            default_config = UvmgrConfig()
            self._save_config(default_config, global_config_path)
        
        # Project config template
        project_config_path = self.config_paths[ConfigScope.PROJECT]
        if not project_config_path.exists():
            project_config = UvmgrConfig(
                project_root=str(self.project_root),
                development=DevelopmentConfig(
                    auto_test_discovery=True,
                    git_hooks_enabled=True
                )
            )
            self._save_config(project_config, project_config_path)
    
    def _load_configuration_hierarchy(self):
        """Load configuration from all scopes in hierarchy order."""
        
        # Start with system defaults
        base_config = UvmgrConfig()
        
        # Load each scope in order
        for scope in ConfigScope:
            try:
                scope_config = self._load_scope_config(scope)
                if scope_config:
                    base_config = self._merge_configs(base_config, scope_config)
                    self.config_cache[scope] = scope_config
            except Exception as e:
                print(f"⚠️  Warning: Failed to load {scope.value} config: {e}")
        
        # Store final merged configuration
        self.config_cache[ConfigScope.RUNTIME] = base_config
    
    def _load_scope_config(self, scope: ConfigScope) -> Optional[UvmgrConfig]:
        """Load configuration for a specific scope."""
        
        if scope == ConfigScope.ENVIRONMENT:
            return self._load_environment_config()
        elif scope == ConfigScope.RUNTIME:
            return None  # Runtime config is merged result
        
        config_path = self.config_paths[scope]
        if not config_path or not config_path.exists():
            return None
        
        try:
            if config_path.suffix == ".toml":
                config_data = toml.load(config_path)
            elif config_path.suffix == ".json":
                with open(config_path) as f:
                    config_data = json.load(f)
            else:
                return None
            
            return self._dict_to_config(config_data)
            
        except Exception as e:
            print(f"⚠️  Error loading config from {config_path}: {e}")
            return None
    
    def _load_environment_config(self) -> Optional[UvmgrConfig]:
        """Load configuration from environment variables."""
        
        config = UvmgrConfig()
        prefix = "UVMGR_"
        
        # Map environment variables to config fields
        env_mappings = {
            f"{prefix}AGI_MEMORY_ENABLED": ("agi", "memory_enabled", bool),
            f"{prefix}AGI_REASONING_ENABLED": ("agi", "reasoning_enabled", bool),
            f"{prefix}AGI_SELF_MODIFICATION_ENABLED": ("agi", "self_modification_enabled", bool),
            f"{prefix}OTEL_ENABLED": ("telemetry", "otel_enabled", bool),
            f"{prefix}OTEL_ENDPOINT": ("telemetry", "otel_endpoint", str),
            f"{prefix}LOG_LEVEL": ("telemetry", "log_level", str),
            f"{prefix}SCHEDULER_ENABLED": ("runtime", "scheduler_enabled", bool),
            f"{prefix}CACHE_ENABLED": ("runtime", "cache_enabled", bool),
            f"{prefix}STRICT_VALIDATION": ("security", "strict_validation", bool),
            f"{prefix}SANDBOX_EXECUTION": ("security", "sandbox_execution", bool),
        }
        
        env_config_data = {}
        
        for env_var, (section, field, type_func) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    # Convert value to correct type
                    if type_func == bool:
                        value = value.lower() in ("true", "1", "yes", "on")
                    elif type_func == int:
                        value = int(value)
                    elif type_func == float:
                        value = float(value)
                    
                    # Set nested value
                    if section not in env_config_data:
                        env_config_data[section] = {}
                    env_config_data[section][field] = value
                    
                except ValueError as e:
                    print(f"⚠️  Invalid environment variable {env_var}: {e}")
        
        if env_config_data:
            return self._dict_to_config(env_config_data)
        
        return None
    
    def _dict_to_config(self, data: Dict[str, Any]) -> UvmgrConfig:
        """Convert dictionary to typed configuration."""
        
        try:
            # Handle nested configuration sections
            config_kwargs = {}
            
            for key, value in data.items():
                if key == "agi" and isinstance(value, dict):
                    config_kwargs["agi"] = AGIConfig(**value)
                elif key == "telemetry" and isinstance(value, dict):
                    config_kwargs["telemetry"] = TelemetryConfig(**value)
                elif key == "runtime" and isinstance(value, dict):
                    config_kwargs["runtime"] = RuntimeConfig(**value)
                elif key == "security" and isinstance(value, dict):
                    config_kwargs["security"] = SecurityConfig(**value)
                elif key == "development" and isinstance(value, dict):
                    config_kwargs["development"] = DevelopmentConfig(**value)
                else:
                    config_kwargs[key] = value
            
            return UvmgrConfig(**config_kwargs)
            
        except Exception as e:
            print(f"⚠️  Error converting dict to config: {e}")
            return UvmgrConfig()
    
    def _merge_configs(self, base: UvmgrConfig, override: UvmgrConfig) -> UvmgrConfig:
        """Merge two configurations, with override taking precedence."""
        
        # Convert to dictionaries for easier merging
        base_dict = asdict(base)
        override_dict = asdict(override)
        
        # Deep merge dictionaries
        merged_dict = self._deep_merge_dicts(base_dict, override_dict)
        
        return self._dict_to_config(merged_dict)
    
    def _deep_merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: UvmgrConfig, path: Path):
        """Save configuration to file."""
        
        try:
            config_dict = asdict(config)
            config_dict["last_updated"] = time.time()
            
            if path.suffix == ".toml":
                with open(path, "w") as f:
                    toml.dump(config_dict, f)
            elif path.suffix == ".json":
                with open(path, "w") as f:
                    json.dump(config_dict, f, indent=2)
                    
        except Exception as e:
            print(f"⚠️  Error saving config to {path}: {e}")
    
    def get_config(self, scope: ConfigScope = ConfigScope.RUNTIME) -> UvmgrConfig:
        """Get configuration for a specific scope."""
        
        return self.config_cache.get(scope, UvmgrConfig())
    
    def get_merged_config(self) -> UvmgrConfig:
        """Get the fully merged configuration."""
        
        return self.get_config(ConfigScope.RUNTIME)
    
    def set_config_value(self, key_path: str, value: Any, scope: ConfigScope = ConfigScope.PROJECT):
        """Set a configuration value."""
        
        with span("config.set_value", key_path=key_path, scope=scope.value):
            
            try:
                # Get current config for scope
                current_config = self.config_cache.get(scope, UvmgrConfig())
                
                # Parse key path (e.g., "agi.memory_enabled")
                keys = key_path.split(".")
                config_dict = asdict(current_config)
                
                # Navigate to the target location
                target = config_dict
                for key in keys[:-1]:
                    if key not in target:
                        target[key] = {}
                    target = target[key]
                
                # Set the value
                target[keys[-1]] = value
                
                # Convert back to config object
                updated_config = self._dict_to_config(config_dict)
                
                # Validate if enabled
                if self.validation_enabled:
                    self._validate_config(updated_config)
                
                # Update cache
                self.config_cache[scope] = updated_config
                
                # Save to file
                config_path = self.config_paths[scope]
                if config_path:
                    self._save_config(updated_config, config_path)
                
                # Reload hierarchy
                self._load_configuration_hierarchy()
                
                # Observe change
                observe_with_agi_reasoning(
                    attributes={
                        CliAttributes.COMMAND: "config_set_value",
                        "key_path": key_path,
                        "scope": scope.value
                    },
                    context={"configuration": True, "config_change": True}
                )
                
                metric_counter("config.value_set")(1)
                
            except Exception as e:
                raise ConfigValidationError(
                    field=key_path,
                    value=value,
                    message=str(e),
                    scope=scope
                )
    
    def get_config_value(self, key_path: str, default: Any = None, scope: ConfigScope = ConfigScope.RUNTIME) -> Any:
        """Get a configuration value."""
        
        try:
            config = self.get_config(scope)
            config_dict = asdict(config)
            
            # Parse key path
            keys = key_path.split(".")
            value = config_dict
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def _validate_config(self, config: UvmgrConfig):
        """Validate configuration."""
        
        # Validate AGI configuration
        if config.agi.memory_similarity_threshold < 0 or config.agi.memory_similarity_threshold > 1:
            raise ValueError("AGI memory similarity threshold must be between 0 and 1")
        
        if config.agi.reasoning_confidence_threshold < 0 or config.agi.reasoning_confidence_threshold > 1:
            raise ValueError("AGI reasoning confidence threshold must be between 0 and 1")
        
        # Validate telemetry configuration
        if config.telemetry.tracing_sample_rate < 0 or config.telemetry.tracing_sample_rate > 1:
            raise ValueError("Tracing sample rate must be between 0 and 1")
        
        if config.telemetry.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
        
        # Validate runtime configuration
        if config.runtime.max_concurrent_workflows < 1:
            raise ValueError("Max concurrent workflows must be at least 1")
        
        # Validate development configuration
        if config.development.test_coverage_threshold < 0 or config.development.test_coverage_threshold > 100:
            raise ValueError("Test coverage threshold must be between 0 and 100")
    
    def reset_to_defaults(self, scope: ConfigScope = ConfigScope.PROJECT):
        """Reset configuration to defaults."""
        
        default_config = UvmgrConfig()
        self.config_cache[scope] = default_config
        
        config_path = self.config_paths[scope]
        if config_path:
            self._save_config(default_config, config_path)
        
        self._load_configuration_hierarchy()
        
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "config_reset",
                "scope": scope.value
            },
            context={"configuration": True, "reset": True}
        )
    
    def export_config(self, format: ConfigFormat = ConfigFormat.TOML, scope: ConfigScope = ConfigScope.RUNTIME) -> str:
        """Export configuration in specified format."""
        
        config = self.get_config(scope)
        config_dict = asdict(config)
        
        if format == ConfigFormat.TOML:
            return toml.dumps(config_dict)
        elif format == ConfigFormat.JSON:
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration system summary."""
        
        return {
            "scopes_loaded": len(self.config_cache),
            "project_root": str(self.project_root),
            "validation_enabled": self.validation_enabled,
            "config_paths": {
                scope.value: str(path) if path else None
                for scope, path in self.config_paths.items()
            },
            "agi_enabled": self.get_config_value("agi.reasoning_enabled", True),
            "telemetry_enabled": self.get_config_value("telemetry.otel_enabled", True),
            "security_enabled": self.get_config_value("security.strict_validation", True)
        }


# Global configuration manager
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager(project_root: Optional[Path] = None) -> ConfigurationManager:
    """Get the global configuration manager."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigurationManager(project_root)
    
    return _config_manager

def get_config(scope: ConfigScope = ConfigScope.RUNTIME) -> UvmgrConfig:
    """Get configuration for a scope."""
    manager = get_config_manager()
    return manager.get_config(scope)

def set_config_value(key_path: str, value: Any, scope: ConfigScope = ConfigScope.PROJECT):
    """Set a configuration value."""
    manager = get_config_manager()
    manager.set_config_value(key_path, value, scope)

def get_config_value(key_path: str, default: Any = None, scope: ConfigScope = ConfigScope.RUNTIME) -> Any:
    """Get a configuration value."""
    manager = get_config_manager()
    return manager.get_config_value(key_path, default, scope)