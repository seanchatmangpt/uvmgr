"""
Event-Driven Automation Engine
=============================

This module addresses the critical automation gap by providing intelligent event-driven workflows.

Key features:
1. **File System Watchers**: Automatic triggers on file changes
2. **Git Hook Integration**: Workflow triggers on git events
3. **Intelligent Scheduling**: Adaptive scheduling based on patterns
4. **Event Correlation**: Smart event aggregation and filtering
5. **Self-Healing Workflows**: Automatic recovery and adaptation

The 80/20 approach: 20% of automation features that provide 80% of workflow automation value.
"""

from __future__ import annotations

import asyncio
import time
import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Set, Union
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor

# Conditional imports for file watching
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    Observer = None
    FileSystemEventHandler = None
    FileSystemEvent = None
    WATCHDOG_AVAILABLE = False

from uvmgr.core.semconv import WorkflowAttributes, WorkflowOperations, CliAttributes
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning, get_agi_insights
from uvmgr.core.workspace import get_workspace_config, get_workspace_manager
from uvmgr.core.workflows import get_workflow_engine, execute_workflow
from uvmgr.core.instrumentation import add_span_event


class EventType(Enum):
    """Types of automation events."""
    FILE_CHANGED = "file_changed"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GIT_BRANCH = "git_branch"
    DEPENDENCY_CHANGED = "dependency_changed"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    WORKFLOW_COMPLETED = "workflow_completed"
    ERROR_OCCURRED = "error_occurred"


class TriggerCondition(Enum):
    """Trigger condition types."""
    IMMEDIATE = "immediate"
    DEBOUNCED = "debounced"
    BATCH = "batch"
    SCHEDULED = "scheduled"
    CONDITIONAL = "conditional"


@dataclass
class AutomationEvent:
    """Represents an automation event that can trigger workflows."""
    
    id: str
    event_type: EventType
    timestamp: float
    source: str  # File path, git operation, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Event correlation
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    
    # Processing state
    processed: bool = False
    processing_started: Optional[float] = None
    processing_completed: Optional[float] = None


@dataclass
class AutomationRule:
    """Defines when and how to trigger automated workflows."""
    
    id: str
    name: str
    description: str
    
    # Trigger conditions
    event_types: List[EventType]
    file_patterns: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Trigger behavior
    trigger_condition: TriggerCondition = TriggerCondition.IMMEDIATE
    debounce_seconds: float = 5.0
    batch_size: int = 1
    
    # Actions
    workflow_template: str = ""
    workflow_parameters: Dict[str, Any] = field(default_factory=dict)
    command: str = ""
    
    # State
    enabled: bool = True
    last_triggered: Optional[float] = None
    trigger_count: int = 0
    
    # Smart features
    adaptive_parameters: bool = True
    failure_retry: bool = True
    max_retries: int = 3


@dataclass
class AutomationExecution:
    """Tracks execution of automated workflows."""
    
    id: str
    rule_id: str
    trigger_event_id: str
    
    # Execution details
    started_at: float
    completed_at: Optional[float] = None
    status: str = "running"  # running, completed, failed, cancelled
    
    # Results
    workflow_execution_id: Optional[str] = None
    command_output: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metrics
    execution_time: Optional[float] = None
    retry_count: int = 0


class FileWatcher:
    """File system watcher for automation triggers."""
    
    def __init__(self, automation_engine: 'AutomationEngine'):
        self.automation_engine = automation_engine
        self.observer: Optional[Observer] = None
        self.watched_paths: Set[str] = set()
        
    def start_watching(self, path: Path):
        """Start watching a directory for changes."""
        
        if not WATCHDOG_AVAILABLE:
            return False
        
        if self.observer is None:
            self.observer = Observer()
            self.observer.start()
        
        path_str = str(path)
        if path_str not in self.watched_paths:
            event_handler = AutomationFileHandler(self.automation_engine)
            self.observer.schedule(event_handler, path_str, recursive=True)
            self.watched_paths.add(path_str)
            
        return True
    
    def stop_watching(self):
        """Stop file watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.watched_paths.clear()


if WATCHDOG_AVAILABLE:
    class AutomationFileHandler(FileSystemEventHandler):
        """File system event handler for automation."""
        
        def __init__(self, automation_engine: 'AutomationEngine'):
            self.automation_engine = automation_engine
            
            # Ignore patterns
            self.ignore_patterns = {
                '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
                '.venv', 'node_modules', '.uvmgr', '.DS_Store'
            }
        
        def on_any_event(self, event: FileSystemEvent):
            """Handle any file system event."""
            
            if event.is_directory:
                return
            
            # Check ignore patterns
            path = Path(event.src_path)
            if any(pattern in str(path) for pattern in self.ignore_patterns):
                return
            
            # Map watchdog events to automation events
            event_type_map = {
                'modified': EventType.FILE_CHANGED,
                'created': EventType.FILE_CREATED,
                'deleted': EventType.FILE_DELETED
            }
            
            automation_event_type = event_type_map.get(event.event_type)
            if automation_event_type:
                self.automation_engine.emit_event(
                    automation_event_type,
                    str(path),
                    metadata={
                        'file_name': path.name,
                        'file_extension': path.suffix,
                        'file_size': path.stat().st_size if path.exists() else 0
                    }
                )
else:
    # Placeholder class when watchdog is not available
    class AutomationFileHandler:
        def __init__(self, automation_engine):
            pass


class GitIntegration:
    """Git integration for automation triggers."""
    
    @staticmethod
    def setup_git_hooks(automation_engine: 'AutomationEngine', project_root: Path):
        """Set up git hooks for automation."""
        
        git_dir = project_root / '.git'
        if not git_dir.exists():
            return False
        
        hooks_dir = git_dir / 'hooks'
        hooks_dir.mkdir(exist_ok=True)
        
        # Pre-commit hook
        pre_commit_hook = hooks_dir / 'pre-commit'
        pre_commit_content = f"""#!/bin/sh
# uvmgr automation pre-commit hook
cd "{project_root}"
uvmgr automation trigger git_commit --metadata "stage=pre-commit"
"""
        
        pre_commit_hook.write_text(pre_commit_content)
        pre_commit_hook.chmod(0o755)
        
        # Post-commit hook  
        post_commit_hook = hooks_dir / 'post-commit'
        post_commit_content = f"""#!/bin/sh
# uvmgr automation post-commit hook
cd "{project_root}"
uvmgr automation trigger git_commit --metadata "stage=post-commit"
"""
        
        post_commit_hook.write_text(post_commit_content)
        post_commit_hook.chmod(0o755)
        
        return True
    
    @staticmethod
    def detect_git_events(project_root: Path) -> List[AutomationEvent]:
        """Detect recent git events."""
        
        events = []
        git_dir = project_root / '.git'
        
        if not git_dir.exists():
            return events
        
        try:
            import subprocess
            
            # Get recent commits
            result = subprocess.run(
                ['git', 'log', '--oneline', '-5'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                for commit in commits:
                    if commit:
                        commit_hash = commit.split()[0]
                        events.append(AutomationEvent(
                            id=f"git_commit_{commit_hash}",
                            event_type=EventType.GIT_COMMIT,
                            timestamp=time.time(),
                            source="git",
                            metadata={'commit': commit}
                        ))
        
        except Exception:
            pass
        
        return events


class IntelligentScheduler:
    """Intelligent scheduling for automation rules."""
    
    def __init__(self):
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the intelligent scheduler."""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
    
    def schedule_rule(self, rule: AutomationRule, next_run: datetime):
        """Schedule an automation rule."""
        self.scheduled_tasks[rule.id] = {
            'rule': rule,
            'next_run': next_run,
            'created_at': time.time()
        }
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            now = datetime.now()
            
            # Check scheduled tasks
            for task_id, task_info in list(self.scheduled_tasks.items()):
                if task_info['next_run'] <= now:
                    # Trigger the rule
                    rule = task_info['rule']
                    # TODO: Integrate with automation engine
                    
                    # Remove from schedule
                    del self.scheduled_tasks[task_id]
            
            time.sleep(1)  # Check every second


class AutomationEngine:
    """
    Intelligent event-driven automation engine for uvmgr.
    
    Provides automated workflow execution based on file changes, git events,
    and intelligent scheduling.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.rules: Dict[str, AutomationRule] = {}
        self.events: List[AutomationEvent] = []
        self.executions: Dict[str, AutomationExecution] = {}
        
        # Components
        self.file_watcher = FileWatcher(self)
        self.scheduler = IntelligentScheduler()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Event processing
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Load default rules
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default automation rules."""
        
        # Python file change rule
        python_rule = AutomationRule(
            id="python_file_changes",
            name="Python File Quality Check",
            description="Run quality checks when Python files change",
            event_types=[EventType.FILE_CHANGED],
            file_patterns=["*.py"],
            trigger_condition=TriggerCondition.DEBOUNCED,
            debounce_seconds=3.0,
            workflow_template="development",
            workflow_parameters={"quick_mode": True}
        )
        self.rules[python_rule.id] = python_rule
        
        # Git commit rule
        git_rule = AutomationRule(
            id="git_commit_ci",
            name="Git Commit CI",
            description="Run CI workflow on git commits",
            event_types=[EventType.GIT_COMMIT],
            trigger_condition=TriggerCondition.IMMEDIATE,
            workflow_template="ci_cd",
            workflow_parameters={"environment": "development"}
        )
        self.rules[git_rule.id] = git_rule
        
        # Dependency change rule
        deps_rule = AutomationRule(
            id="dependency_changes",
            name="Dependency Updates",
            description="Run tests when dependencies change",
            event_types=[EventType.FILE_CHANGED],
            file_patterns=["pyproject.toml", "requirements*.txt"],
            trigger_condition=TriggerCondition.IMMEDIATE,
            command="tests run"
        )
        self.rules[deps_rule.id] = deps_rule
        
        # Scheduled quality check
        scheduled_rule = AutomationRule(
            id="daily_quality_check",
            name="Daily Quality Assessment", 
            description="Daily comprehensive quality and security check",
            event_types=[EventType.SCHEDULED],
            trigger_condition=TriggerCondition.SCHEDULED,
            workflow_template="ci_cd",
            workflow_parameters={"full_analysis": True, "security_scan": True}
        )
        self.rules[scheduled_rule.id] = scheduled_rule
    
    async def start(self):
        """Start the automation engine."""
        if self.running:
            return
        
        self.running = True
        
        # Start file watching
        if WATCHDOG_AVAILABLE:
            self.file_watcher.start_watching(self.workspace_root)
        
        # Start scheduler
        self.scheduler.start()
        
        # Start event processing
        self.processing_task = asyncio.create_task(self._process_events())
        
        # Set up git hooks
        GitIntegration.setup_git_hooks(self, self.workspace_root)
        
        # Observe automation start
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "automation_start",
                WorkflowAttributes.ENGINE: "uvmgr_automation_engine",
                "rules_count": str(len(self.rules)),
                "file_watching": str(WATCHDOG_AVAILABLE)
            },
            context={
                "automation_engine": True,
                "event_driven": True
            }
        )
    
    async def stop(self):
        """Stop the automation engine."""
        if not self.running:
            return
        
        self.running = False
        
        # Stop components
        self.file_watcher.stop_watching()
        self.scheduler.stop()
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        self.executor.shutdown(wait=True)
    
    def emit_event(self, event_type: EventType, source: str, metadata: Dict[str, Any] = None):
        """Emit an automation event."""
        
        metadata = metadata or {}
        
        # Create event
        event = AutomationEvent(
            id=f"{event_type.value}_{int(time.time())}_{hashlib.md5(source.encode()).hexdigest()[:8]}",
            event_type=event_type,
            timestamp=time.time(),
            source=source,
            metadata=metadata
        )
        
        # Add to queue for processing
        asyncio.create_task(self.event_queue.put(event))
        
        # Store event
        self.events.append(event)
        
        # Keep only recent events (last 1000)
        if len(self.events) > 1000:
            self.events = self.events[-1000:]
    
    async def _process_events(self):
        """Main event processing loop."""
        
        debounce_cache: Dict[str, List[AutomationEvent]] = {}
        
        while self.running:
            try:
                # Get event from queue (with timeout)
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                
                # Find matching rules
                matching_rules = self._find_matching_rules(event)
                
                for rule in matching_rules:
                    if not rule.enabled:
                        continue
                    
                    # Handle different trigger conditions
                    if rule.trigger_condition == TriggerCondition.IMMEDIATE:
                        await self._execute_rule(rule, event)
                    
                    elif rule.trigger_condition == TriggerCondition.DEBOUNCED:
                        # Add to debounce cache
                        cache_key = f"{rule.id}_{event.event_type.value}"
                        if cache_key not in debounce_cache:
                            debounce_cache[cache_key] = []
                        debounce_cache[cache_key].append(event)
                        
                        # Schedule debounced execution
                        asyncio.create_task(
                            self._debounced_execution(rule, cache_key, debounce_cache)
                        )
                
                # Mark event as processed
                event.processed = True
                
            except asyncio.TimeoutError:
                # No events in queue, continue
                continue
            except Exception as e:
                # Log error and continue
                print(f"Error processing automation event: {e}")
                continue
    
    def _find_matching_rules(self, event: AutomationEvent) -> List[AutomationRule]:
        """Find rules that match an event."""
        
        matching_rules = []
        
        for rule in self.rules.values():
            # Check event type
            if event.event_type not in rule.event_types:
                continue
            
            # Check file patterns
            if rule.file_patterns and event.event_type in [EventType.FILE_CHANGED, EventType.FILE_CREATED, EventType.FILE_DELETED]:
                source_path = Path(event.source)
                pattern_match = any(
                    source_path.match(pattern) for pattern in rule.file_patterns
                )
                if not pattern_match:
                    continue
            
            # Check conditions
            if rule.conditions:
                if not self._evaluate_rule_conditions(rule, event):
                    continue
            
            matching_rules.append(rule)
        
        return matching_rules
    
    def _evaluate_rule_conditions(self, rule: AutomationRule, event: AutomationEvent) -> bool:
        """Evaluate rule conditions."""
        
        # Simple condition evaluation
        for condition_key, condition_value in rule.conditions.items():
            if condition_key == "min_file_size":
                file_size = event.metadata.get("file_size", 0)
                if file_size < condition_value:
                    return False
            
            elif condition_key == "file_extensions":
                file_ext = event.metadata.get("file_extension", "")
                if file_ext not in condition_value:
                    return False
            
            elif condition_key == "agi_decision":
                # Use AGI reasoning for complex decisions
                insights = get_agi_insights()
                if condition_value == "high_confidence_needed":
                    if insights["understanding_confidence"] < 0.8:
                        return False
        
        return True
    
    async def _debounced_execution(self, rule: AutomationRule, cache_key: str, debounce_cache: Dict[str, List[AutomationEvent]]):
        """Execute rule after debounce period."""
        
        await asyncio.sleep(rule.debounce_seconds)
        
        # Get accumulated events
        events = debounce_cache.get(cache_key, [])
        if events:
            # Execute with the latest event
            latest_event = events[-1]
            await self._execute_rule(rule, latest_event, batch_events=events)
            
            # Clear cache
            debounce_cache.pop(cache_key, None)
    
    async def _execute_rule(self, rule: AutomationRule, trigger_event: AutomationEvent, batch_events: List[AutomationEvent] = None):
        """Execute an automation rule."""
        
        execution_id = f"exec_{rule.id}_{int(time.time())}"
        
        execution = AutomationExecution(
            id=execution_id,
            rule_id=rule.id,
            trigger_event_id=trigger_event.id,
            started_at=time.time()
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Update rule statistics
            rule.last_triggered = time.time()
            rule.trigger_count += 1
            
            # Prepare parameters
            parameters = rule.workflow_parameters.copy()
            
            # Add adaptive parameters
            if rule.adaptive_parameters:
                parameters.update(self._generate_adaptive_parameters(rule, trigger_event, batch_events))
            
            # Execute workflow or command
            if rule.workflow_template:
                # Execute workflow
                workflow_execution = await execute_workflow(rule.workflow_template, parameters)
                execution.workflow_execution_id = workflow_execution.workflow_id
                execution.status = "completed" if workflow_execution.status.value == "success" else "failed"
                
            elif rule.command:
                # Execute command through subprocess with proper handling
                try:
                    import subprocess
                    import shlex
                    
                    # Parse command and inject parameters
                    command = rule.command
                    for key, value in parameters.items():
                        command = command.replace(f"{{{key}}}", str(value))
                    
                    # Security check - validate command is allowed
                    allowed_commands = [
                        'uvmgr', 'python', 'pip', 'uv', 'git', 'echo', 'cat', 'ls',
                        'grep', 'find', 'test', 'bash', 'sh'
                    ]
                    cmd_parts = shlex.split(command)
                    base_cmd = cmd_parts[0].split('/')[-1] if cmd_parts else ''
                    
                    if not any(base_cmd.startswith(allowed) for allowed in allowed_commands):
                        raise ValueError(f"Command not allowed for security reasons: {base_cmd}")
                    
                    # Execute command with timeout
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=rule.timeout or 60,
                        env={**os.environ, **parameters}  # Include parameters as env vars
                    )
                    
                    execution.command_output = result.stdout
                    if result.stderr:
                        execution.command_output += f"\nSTDERR:\n{result.stderr}"
                    
                    execution.status = "completed" if result.returncode == 0 else "failed"
                    execution.exit_code = result.returncode
                    
                    # Log command execution for telemetry
                    add_span_event("automation.command_executed", {
                        "command": base_cmd,
                        "exit_code": result.returncode,
                        "execution_time": time.time() - execution.started_at
                    })
                    
                except subprocess.TimeoutExpired:
                    execution.status = "failed"
                    execution.error_message = f"Command timed out after {rule.timeout or 60} seconds"
                except Exception as e:
                    execution.status = "failed"
                    execution.error_message = f"Command execution failed: {str(e)}"
            
            execution.completed_at = time.time()
            execution.execution_time = execution.completed_at - execution.started_at
            
            # Observe execution
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "automation_execute",
                    WorkflowAttributes.OPERATION: "automated_execution",
                    "rule_id": rule.id,
                    "execution_id": execution_id,
                    "trigger_event": trigger_event.event_type.value,
                    "status": execution.status
                },
                context={
                    "automation_execution": True,
                    "event_driven": True
                }
            )
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = time.time()
            
            # Retry logic
            if rule.failure_retry and execution.retry_count < rule.max_retries:
                execution.retry_count += 1
                # Schedule retry
                asyncio.create_task(self._retry_execution(rule, trigger_event, execution))
    
    async def _retry_execution(self, rule: AutomationRule, trigger_event: AutomationEvent, original_execution: AutomationExecution):
        """Retry failed execution."""
        
        # Wait before retry (exponential backoff)
        retry_delay = 2 ** original_execution.retry_count
        await asyncio.sleep(retry_delay)
        
        # Retry execution
        await self._execute_rule(rule, trigger_event)
    
    def _generate_adaptive_parameters(self, rule: AutomationRule, trigger_event: AutomationEvent, batch_events: List[AutomationEvent] = None) -> Dict[str, Any]:
        """Generate adaptive parameters based on context."""
        
        adaptive_params = {}
        
        # Time-based adaptations
        current_hour = datetime.now().hour
        if current_hour < 9 or current_hour > 18:  # Outside work hours
            adaptive_params["quick_mode"] = True
            adaptive_params["notifications"] = False
        
        # Event frequency adaptations
        if batch_events and len(batch_events) > 5:
            adaptive_params["batch_mode"] = True
            adaptive_params["incremental"] = True
        
        # File type adaptations
        if trigger_event.event_type in [EventType.FILE_CHANGED, EventType.FILE_CREATED]:
            file_ext = trigger_event.metadata.get("file_extension", "")
            if file_ext in [".py", ".pyx"]:
                adaptive_params["python_focused"] = True
            elif file_ext in [".md", ".rst", ".txt"]:
                adaptive_params["docs_only"] = True
        
        # AGI-based adaptations
        insights = get_agi_insights()
        if insights["understanding_confidence"] > 0.9:
            adaptive_params["advanced_analysis"] = True
        
        return adaptive_params
    
    def add_rule(self, rule: AutomationRule):
        """Add a new automation rule."""
        self.rules[rule.id] = rule
    
    def remove_rule(self, rule_id: str):
        """Remove an automation rule."""
        self.rules.pop(rule_id, None)
    
    def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        """Get automation rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self) -> List[AutomationRule]:
        """List all automation rules."""
        return list(self.rules.values())
    
    def get_recent_events(self, limit: int = 50) -> List[AutomationEvent]:
        """Get recent automation events."""
        return self.events[-limit:] if self.events else []
    
    def get_executions(self, rule_id: Optional[str] = None) -> List[AutomationExecution]:
        """Get automation executions."""
        executions = list(self.executions.values())
        
        if rule_id:
            executions = [e for e in executions if e.rule_id == rule_id]
        
        return sorted(executions, key=lambda x: x.started_at, reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get automation engine statistics."""
        
        total_executions = len(self.executions)
        successful_executions = len([e for e in self.executions.values() if e.status == "completed"])
        failed_executions = len([e for e in self.executions.values() if e.status == "failed"])
        
        return {
            "rules_count": len(self.rules),
            "active_rules": len([r for r in self.rules.values() if r.enabled]),
            "total_events": len(self.events),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / max(1, total_executions),
            "file_watching_enabled": WATCHDOG_AVAILABLE and self.file_watcher.observer is not None,
            "scheduler_running": self.scheduler.running
        }


# Global automation engine instance
_automation_engine: Optional[AutomationEngine] = None

def get_automation_engine(workspace_root: Optional[Path] = None) -> AutomationEngine:
    """Get the global automation engine instance."""
    global _automation_engine
    
    if _automation_engine is None:
        _automation_engine = AutomationEngine(workspace_root)
    
    return _automation_engine

async def start_automation():
    """Start the global automation engine."""
    engine = get_automation_engine()
    await engine.start()

async def stop_automation():
    """Stop the global automation engine."""
    engine = get_automation_engine()
    await engine.stop()