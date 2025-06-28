import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

from uvmgr.core.telemetry import span
from uvmgr.core.instrumentation import add_span_event, add_span_attributes
from uvmgr.core.process import run as local_run


class RemoteExecutionError(Exception):
    """Error during remote command execution."""
    pass


def run(host: str, cmd: str, *args, **kwargs) -> subprocess.CompletedProcess:
    """Execute command on remote host via SSH.
    
    Args:
        host: Remote hostname or IP address
        cmd: Command to execute remotely
        *args: Additional command arguments
        **kwargs: Additional options (user, key_file, timeout, etc.)
        
    Returns:
        CompletedProcess result from remote execution
        
    Raises:
        RemoteExecutionError: If remote execution fails
    """
    with span("remote.run", host=host, cmd=cmd) as current_span:
        try:
            # Extract SSH options
            user = kwargs.get('user', 'root')
            key_file = kwargs.get('key_file')
            port = kwargs.get('port', 22)
            timeout = kwargs.get('timeout', 300)
            
            # Build SSH command
            ssh_cmd = _build_ssh_command(host, cmd, user, key_file, port, args)
            
            add_span_attributes({
                'remote.host': host,
                'remote.user': user,
                'remote.port': port,
                'remote.command': cmd
            })
            
            add_span_event('remote.execution.start')
            
            # Execute via SSH
            result = local_run(
                ssh_cmd,
                timeout=timeout,
                capture=kwargs.get('capture', True),
                text=kwargs.get('text', True)
            )
            
            add_span_event('remote.execution.success', {
                'exit_code': result.returncode,
                'stdout_length': len(result.stdout) if result.stdout else 0
            })
            
            return result
            
        except subprocess.CalledProcessError as e:
            add_span_event('remote.execution.error', {
                'error': str(e),
                'exit_code': e.returncode
            })
            raise RemoteExecutionError(f"Remote command failed on {host}: {e}") from e
        except Exception as e:
            add_span_event('remote.execution.exception', {'error': str(e)})
            raise RemoteExecutionError(f"Remote execution failed: {e}") from e


def _build_ssh_command(
    host: str, 
    cmd: str, 
    user: str, 
    key_file: Optional[str], 
    port: int,
    args: tuple
) -> List[str]:
    """Build SSH command with proper escaping and options."""
    ssh_cmd = ['ssh']
    
    # SSH options for non-interactive execution
    ssh_cmd.extend([
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'LogLevel=ERROR',
        '-o', 'ConnectTimeout=30'
    ])
    
    # Add key file if specified
    if key_file:
        ssh_cmd.extend(['-i', str(key_file)])
        
    # Add port if not default
    if port != 22:
        ssh_cmd.extend(['-p', str(port)])
        
    # Add user@host
    ssh_cmd.append(f"{user}@{host}")
    
    # Add command with arguments
    full_cmd = f"{cmd} {' '.join(str(arg) for arg in args)}" if args else cmd
    ssh_cmd.append(full_cmd)
    
    return ssh_cmd


async def run_async(host: str, cmd: str, *args, **kwargs) -> subprocess.CompletedProcess:
    """Async version of remote execution."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run, host, cmd, *args, **kwargs)


def run_parallel(
    hosts: List[str], 
    cmd: str, 
    *args, 
    max_concurrent: int = 10,
    **kwargs
) -> Dict[str, Union[subprocess.CompletedProcess, Exception]]:
    """Execute command on multiple hosts in parallel.
    
    Args:
        hosts: List of hostnames/IPs to execute on
        cmd: Command to execute
        *args: Command arguments
        max_concurrent: Maximum concurrent executions
        **kwargs: SSH options
        
    Returns:
        Dict mapping hostname to result or exception
    """
    async def _run_all():
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _run_one(host: str):
            async with semaphore:
                try:
                    return await run_async(host, cmd, *args, **kwargs)
                except Exception as e:
                    return e
                    
        tasks = [_run_one(host) for host in hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip(hosts, results))
        
    return asyncio.run(_run_all())


def copy_file(local_path: Union[str, Path], remote_path: str, host: str, **kwargs) -> bool:
    """Copy file to remote host via SCP.
    
    Args:
        local_path: Local file path
        remote_path: Remote destination path
        host: Remote hostname
        **kwargs: SSH options (user, key_file, port)
        
    Returns:
        True if copy succeeded
        
    Raises:
        RemoteExecutionError: If copy fails
    """
    with span("remote.copy_file", local_path=str(local_path), remote_path=remote_path, host=host):
        try:
            user = kwargs.get('user', 'root')
            key_file = kwargs.get('key_file')
            port = kwargs.get('port', 22)
            
            scp_cmd = ['scp']
            
            # SCP options
            scp_cmd.extend([
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'LogLevel=ERROR'
            ])
            
            if key_file:
                scp_cmd.extend(['-i', str(key_file)])
                
            if port != 22:
                scp_cmd.extend(['-P', str(port)])
                
            scp_cmd.extend([str(local_path), f"{user}@{host}:{remote_path}"])
            
            result = local_run(scp_cmd)
            return result.returncode == 0
            
        except Exception as e:
            raise RemoteExecutionError(f"File copy failed: {e}") from e
