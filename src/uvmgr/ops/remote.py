from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span
from uvmgr.core.instrumentation import add_span_attributes, add_span_event


@timed
def run(
    host: str, 
    command: str,
    user: Optional[str] = None,
    port: int = 22,
    key_file: Optional[str] = None,
    timeout: int = 30,
    env_vars: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    capture_output: bool = True
) -> Dict[str, Any]:
    """Execute a command on a remote host via SSH."""
    from uvmgr.runtime import remote as _rt

    with span("remote.run", host=host, command=command):
        add_span_attributes({
            "remote.host": host,
            "remote.user": user or "default",
            "remote.port": port,
            "remote.timeout": timeout,
            "remote.has_env_vars": bool(env_vars),
            "remote.working_dir": working_dir or "default"
        })
        
        return _rt.run(
            host=host,
            command=command,
            user=user,
            port=port,
            key_file=key_file,
            timeout=timeout,
            env_vars=env_vars or {},
            working_dir=working_dir,
            capture_output=capture_output
        )


def list_hosts() -> List[Dict[str, Any]]:
    """List configured remote hosts."""
    with span("remote.list_hosts"):
        config_file = _get_hosts_config_file()
        
        if not config_file.exists():
            add_span_event("hosts_config_not_found", {"config_file": str(config_file)})
            return []
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                hosts = config.get("hosts", [])
                
            add_span_attributes({
                "hosts_count": len(hosts),
                "config_file": str(config_file)
            })
            
            return hosts
            
        except Exception as e:
            add_span_event("hosts_config_read_failed", {"error": str(e)})
            return []


def add_host(
    name: str,
    host: str,
    user: str = "",
    port: int = 22,
    key_file: str = "",
    description: str = ""
) -> Dict[str, Any]:
    """Add a new remote host configuration."""
    with span("remote.add_host", name=name, host=host):
        config_file = _get_hosts_config_file()
        
        # Load existing config
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                config = {"hosts": []}
        else:
            config = {"hosts": []}
        
        # Check if host already exists
        existing_hosts = config.get("hosts", [])
        for existing_host in existing_hosts:
            if existing_host.get("name") == name:
                raise ValueError(f"Host '{name}' already exists")
        
        # Add new host
        new_host = {
            "name": name,
            "host": host,
            "user": user,
            "port": port,
            "key_file": key_file,
            "description": description,
            "created_at": _get_current_timestamp()
        }
        
        config["hosts"].append(new_host)
        
        # Save config
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        add_span_attributes({
            "host_name": name,
            "host_address": host,
            "port": port
        })
        
        add_span_event("host_added", {
            "name": name,
            "host": host,
            "config_file": str(config_file)
        })
        
        return new_host


def _get_hosts_config_file() -> Path:
    """Get the path to the hosts configuration file."""
    config_dir = Path.home() / ".uvmgr" / "config"
    return config_dir / "remote_hosts.json"


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()
