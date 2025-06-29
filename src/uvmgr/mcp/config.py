"""
MCP configuration management for uvmgr.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from uvmgr.core.telemetry import span

logger = logging.getLogger(__name__)


@dataclass
class MCPConfig:
    """MCP configuration settings."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Client settings
    server_url: str = "http://localhost:8000"
    timeout: int = 30
    max_retries: int = 3
    
    # DSPy settings
    dspy_enabled: bool = True
    dspy_model: str = "gpt-4"
    dspy_temperature: float = 0.1
    
    # Validation settings
    default_validation_level: str = "strict"
    enable_ml_validation: bool = True
    enable_behavioral_validation: bool = True
    
    # Telemetry settings
    enable_telemetry: bool = True
    telemetry_level: str = "info"
    
    # Security settings
    enable_auth: bool = False
    auth_token: Optional[str] = None
    allowed_origins: list = None
    
    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ["*"]


class MCPConfigManager:
    """Manages MCP configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".uvmgr" / "mcp_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> MCPConfig:
        """Load configuration from file."""
        with span("mcp.load_config"):
            try:
                if self.config_path.exists():
                    with open(self.config_path, 'r') as f:
                        config_data = json.load(f)
                    return MCPConfig(**config_data)
                else:
                    # Create default config
                    config = MCPConfig()
                    self._save_config(config)
                    return config
            except Exception as e:
                logger.warning(f"Failed to load MCP config: {e}")
                return MCPConfig()
    
    def _save_config(self, config: MCPConfig):
        """Save configuration to file."""
        with span("mcp.save_config"):
            try:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(asdict(config), f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save MCP config: {e}")
    
    def get_config(self) -> MCPConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, **kwargs):
        """Update configuration."""
        with span("mcp.update_config"):
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    logger.warning(f"Unknown config key: {key}")
            
            self._save_config(self.config)
    
    def reset_config(self):
        """Reset configuration to defaults."""
        with span("mcp.reset_config"):
            self.config = MCPConfig()
            self._save_config(self.config)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return issues."""
        with span("mcp.validate_config"):
            issues = []
            
            # Validate port
            if not (1 <= self.config.port <= 65535):
                issues.append(f"Invalid port: {self.config.port}")
            
            # Validate timeout
            if self.config.timeout <= 0:
                issues.append(f"Invalid timeout: {self.config.timeout}")
            
            # Validate max_retries
            if self.config.max_retries < 0:
                issues.append(f"Invalid max_retries: {self.config.max_retries}")
            
            # Validate DSPy temperature
            if not (0 <= self.config.dspy_temperature <= 2):
                issues.append(f"Invalid DSPy temperature: {self.config.dspy_temperature}")
            
            # Validate validation level
            valid_levels = ["strict", "moderate", "lenient"]
            if self.config.default_validation_level not in valid_levels:
                issues.append(f"Invalid validation level: {self.config.default_validation_level}")
            
            # Validate telemetry level
            valid_telemetry_levels = ["debug", "info", "warning", "error"]
            if self.config.telemetry_level not in valid_telemetry_levels:
                issues.append(f"Invalid telemetry level: {self.config.telemetry_level}")
            
            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "config": asdict(self.config)
            }


# Global config manager instance
config_manager = MCPConfigManager()


def get_mcp_config() -> MCPConfig:
    """Get MCP configuration."""
    return config_manager.get_config()


def update_mcp_config(**kwargs):
    """Update MCP configuration."""
    config_manager.update_config(**kwargs)


def validate_mcp_config() -> Dict[str, Any]:
    """Validate MCP configuration."""
    return config_manager.validate_config() 