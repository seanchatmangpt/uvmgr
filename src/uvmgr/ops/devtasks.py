"""
Development Tasks Operations
============================

This module provides intelligent development task automation and management
with AGI-driven optimization and comprehensive observability.

The system can:
- Automatically detect and execute common development tasks
- Optimize task sequences based on project patterns
- Learn from execution patterns to improve efficiency
- Provide intelligent task recommendations
- Integrate with uvmgr's workflow and scheduling systems

Key Features:
- Intelligent task detection and execution
- AGI-driven task optimization
- Performance monitoring and adaptation
- Integration with BPMN workflows and scheduling
- Comprehensive telemetry and observability
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.agi_memory import get_persistent_memory
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram
from uvmgr.core.shell import run_cmd


class TaskType(Enum):
    """Types of development tasks."""
    BUILD = "build"
    TEST = "test"
    LINT = "lint"
    FORMAT = "format"
    TYPECHECK = "typecheck"
    SECURITY_SCAN = "security_scan"
    DEPENDENCY_UPDATE = "dependency_update"
    DOCUMENTATION = "documentation"
    CLEANUP = "cleanup"
    BENCHMARK = "benchmark"
    DEPLOY = "deploy"
    CUSTOM = "custom"


class TaskPriority(Enum):
    """Task execution priority."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class TaskDefinition:
    """Definition of a development task."""
    id: str
    name: str
    task_type: TaskType
    priority: TaskPriority
    command: str
    description: str
    working_dir: Optional[Path] = None
    environment: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300  # 5 minutes default
    retry_count: int = 0
    enabled: bool = True
    conditions: List[str] = field(default_factory=list)  # Conditions for execution
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecutionResult:
    """Result of task execution."""
    task_id: str
    task_name: str
    status: TaskStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0


@dataclass
class TaskSequence:
    """Sequence of related tasks."""
    id: str
    name: str
    description: str
    tasks: List[str]  # Task IDs in execution order
    parallel_groups: List[List[str]] = field(default_factory=list)  # Tasks that can run in parallel
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntelligentDevTaskManager:
    """
    Intelligent development task manager with AGI optimization.
    
    Provides advanced task management capabilities:
    - Automatic task detection and registration
    - AGI-driven task optimization and sequencing
    - Performance monitoring and adaptation
    - Intelligent failure recovery
    - Integration with project workflows
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.task_registry: Dict[str, TaskDefinition] = {}
        self.task_sequences: Dict[str, TaskSequence] = {}
        self.execution_history: List[TaskExecutionResult] = []
        self.task_handlers: Dict[TaskType, Callable] = {}
        
        # Performance tracking
        self.performance_baselines: Dict[str, float] = {}
        self.optimization_insights: List[str] = []
        
        # Settings
        self.enable_agi_optimization = True
        self.auto_detect_tasks = True
        self.max_parallel_tasks = 4
        self.max_execution_history = 500
        
        # Initialize
        self._initialize_task_handlers()
        if self.auto_detect_tasks:
            asyncio.create_task(self._auto_detect_project_tasks())
    
    def _initialize_task_handlers(self):
        """Initialize task type handlers."""
        
        async def build_handler(task_def: TaskDefinition) -> TaskExecutionResult:
            """Handle build tasks."""
            return await self._execute_command_task(task_def, TaskType.BUILD)
        
        async def test_handler(task_def: TaskDefinition) -> TaskExecutionResult:
            """Handle test tasks with enhanced reporting."""
            result = await self._execute_command_task(task_def, TaskType.TEST)
            
            # Extract test metrics if possible
            if result.status == TaskStatus.COMPLETED:
                result.performance_metrics.update(
                    self._extract_test_metrics(result.stdout)
                )
            
            return result
        
        async def lint_handler(task_def: TaskDefinition) -> TaskExecutionResult:
            """Handle linting tasks."""
            result = await self._execute_command_task(task_def, TaskType.LINT)
            
            # Extract lint metrics
            if result.status == TaskStatus.COMPLETED:
                result.performance_metrics.update(
                    self._extract_lint_metrics(result.stdout, result.stderr)
                )
            
            return result
        
        self.task_handlers = {
            TaskType.BUILD: build_handler,
            TaskType.TEST: test_handler,
            TaskType.LINT: lint_handler,
            TaskType.FORMAT: lambda td: self._execute_command_task(td, TaskType.FORMAT),
            TaskType.TYPECHECK: lambda td: self._execute_command_task(td, TaskType.TYPECHECK),
            TaskType.SECURITY_SCAN: lambda td: self._execute_command_task(td, TaskType.SECURITY_SCAN),
            TaskType.DOCUMENTATION: lambda td: self._execute_command_task(td, TaskType.DOCUMENTATION),
            TaskType.CLEANUP: lambda td: self._execute_command_task(td, TaskType.CLEANUP),
            TaskType.CUSTOM: lambda td: self._execute_command_task(td, TaskType.CUSTOM),
        }
    
    async def _auto_detect_project_tasks(self):
        """Automatically detect and register common project tasks."""
        
        with span("devtasks.auto_detect", project_root=str(self.project_root)):
            
            detected_tasks = []
            
            # Check for package.json (Node.js projects)
            package_json = self.project_root / "package.json"
            if package_json.exists():
                detected_tasks.extend(self._detect_nodejs_tasks(package_json))
            
            # Check for pyproject.toml (Python projects)
            pyproject_toml = self.project_root / "pyproject.toml"
            if pyproject_toml.exists():
                detected_tasks.extend(self._detect_python_tasks(pyproject_toml))
            
            # Check for Cargo.toml (Rust projects)
            cargo_toml = self.project_root / "Cargo.toml"
            if cargo_toml.exists():
                detected_tasks.extend(self._detect_rust_tasks(cargo_toml))
            
            # Check for Makefile
            makefile = self.project_root / "Makefile"
            if makefile.exists():
                detected_tasks.extend(self._detect_makefile_tasks(makefile))
            
            # Register detected tasks
            for task_def in detected_tasks:
                await self.register_task(task_def)
            
            # Create common task sequences
            await self._create_common_sequences()
            
            # Observe detection results
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "devtasks_auto_detect",
                    "tasks_detected": str(len(detected_tasks)),
                    "project_root": str(self.project_root)
                },
                context={"devtasks": True, "auto_detection": True}
            )
            
            metric_counter("devtasks.auto_detect.completed")(1)
            metric_counter("devtasks.tasks_detected")(len(detected_tasks))
    
    def _detect_python_tasks(self, pyproject_toml: Path) -> List[TaskDefinition]:
        """Detect Python project tasks."""
        tasks = []
        
        try:
            import tomllib
            with open(pyproject_toml, 'rb') as f:
                config = tomllib.load(f)
            
            # Poetry tasks
            poe_tasks = config.get("tool", {}).get("poe", {}).get("tasks", {})
            for task_name, task_config in poe_tasks.items():
                if isinstance(task_config, dict):
                    cmd = task_config.get("cmd", "")
                    help_text = task_config.get("help", f"Poetry task: {task_name}")
                else:
                    cmd = str(task_config)
                    help_text = f"Poetry task: {task_name}"
                
                task_type = self._infer_task_type(task_name, cmd)
                
                tasks.append(TaskDefinition(
                    id=f"poe_{task_name}",
                    name=f"poe {task_name}",
                    task_type=task_type,
                    priority=self._infer_task_priority(task_type),
                    command=f"poe {task_name}",
                    description=help_text,
                    working_dir=self.project_root,
                    metadata={"source": "pyproject.toml", "tool": "poethepoet"}
                ))
            
            # Standard Python tools
            if "ruff" in str(config):
                tasks.append(TaskDefinition(
                    id="python_lint_ruff",
                    name="Python Lint (Ruff)",
                    task_type=TaskType.LINT,
                    priority=TaskPriority.HIGH,
                    command="ruff check .",
                    description="Run Ruff linting",
                    working_dir=self.project_root,
                    metadata={"source": "auto_detect", "tool": "ruff"}
                ))
                
                tasks.append(TaskDefinition(
                    id="python_format_ruff",
                    name="Python Format (Ruff)",
                    task_type=TaskType.FORMAT,
                    priority=TaskPriority.MEDIUM,
                    command="ruff format .",
                    description="Format code with Ruff",
                    working_dir=self.project_root,
                    metadata={"source": "auto_detect", "tool": "ruff"}
                ))
            
            # pytest
            if "pytest" in str(config):
                tasks.append(TaskDefinition(
                    id="python_test_pytest",
                    name="Python Tests (pytest)",
                    task_type=TaskType.TEST,
                    priority=TaskPriority.CRITICAL,
                    command="pytest -v",
                    description="Run Python tests with pytest",
                    working_dir=self.project_root,
                    timeout=600,  # 10 minutes for tests
                    metadata={"source": "auto_detect", "tool": "pytest"}
                ))
            
            # mypy
            if "mypy" in str(config):
                tasks.append(TaskDefinition(
                    id="python_typecheck_mypy",
                    name="Python Type Check (mypy)",
                    task_type=TaskType.TYPECHECK,
                    priority=TaskPriority.HIGH,
                    command="mypy .",
                    description="Run mypy type checking",
                    working_dir=self.project_root,
                    metadata={"source": "auto_detect", "tool": "mypy"}
                ))
            
        except Exception as e:
            print(f"⚠️  Error detecting Python tasks: {e}")
        
        return tasks
    
    def _detect_nodejs_tasks(self, package_json: Path) -> List[TaskDefinition]:
        """Detect Node.js project tasks."""
        tasks = []
        
        try:
            with open(package_json) as f:
                config = json.load(f)
            
            scripts = config.get("scripts", {})
            for script_name, script_cmd in scripts.items():
                task_type = self._infer_task_type(script_name, script_cmd)
                
                tasks.append(TaskDefinition(
                    id=f"npm_{script_name}",
                    name=f"npm run {script_name}",
                    task_type=task_type,
                    priority=self._infer_task_priority(task_type),
                    command=f"npm run {script_name}",
                    description=f"NPM script: {script_name}",
                    working_dir=self.project_root,
                    metadata={"source": "package.json", "tool": "npm"}
                ))
        
        except Exception as e:
            print(f"⚠️  Error detecting Node.js tasks: {e}")
        
        return tasks
    
    def _detect_rust_tasks(self, cargo_toml: Path) -> List[TaskDefinition]:
        """Detect Rust project tasks."""
        tasks = [
            TaskDefinition(
                id="rust_build",
                name="Rust Build",
                task_type=TaskType.BUILD,
                priority=TaskPriority.HIGH,
                command="cargo build",
                description="Build Rust project",
                working_dir=self.project_root,
                metadata={"source": "auto_detect", "tool": "cargo"}
            ),
            TaskDefinition(
                id="rust_test",
                name="Rust Tests",
                task_type=TaskType.TEST,
                priority=TaskPriority.CRITICAL,
                command="cargo test",
                description="Run Rust tests",
                working_dir=self.project_root,
                timeout=600,
                metadata={"source": "auto_detect", "tool": "cargo"}
            ),
            TaskDefinition(
                id="rust_clippy",
                name="Rust Lint (Clippy)",
                task_type=TaskType.LINT,
                priority=TaskPriority.HIGH,
                command="cargo clippy",
                description="Run Clippy linting",
                working_dir=self.project_root,
                metadata={"source": "auto_detect", "tool": "cargo"}
            ),
            TaskDefinition(
                id="rust_format",
                name="Rust Format",
                task_type=TaskType.FORMAT,
                priority=TaskPriority.MEDIUM,
                command="cargo fmt",
                description="Format Rust code",
                working_dir=self.project_root,
                metadata={"source": "auto_detect", "tool": "cargo"}
            )
        ]
        
        return tasks
    
    def _detect_makefile_tasks(self, makefile: Path) -> List[TaskDefinition]:
        """Detect Makefile tasks."""
        tasks = []
        
        try:
            content = makefile.read_text()
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and ':' in line and not line.startswith('\t') and not line.startswith('#'):
                    target = line.split(':')[0].strip()
                    if target and not target.startswith('.'):
                        task_type = self._infer_task_type(target, "")
                        
                        tasks.append(TaskDefinition(
                            id=f"make_{target}",
                            name=f"make {target}",
                            task_type=task_type,
                            priority=self._infer_task_priority(task_type),
                            command=f"make {target}",
                            description=f"Makefile target: {target}",
                            working_dir=self.project_root,
                            metadata={"source": "Makefile", "tool": "make"}
                        ))
        
        except Exception as e:
            print(f"⚠️  Error detecting Makefile tasks: {e}")
        
        return tasks
    
    def _infer_task_type(self, name: str, command: str) -> TaskType:
        """Infer task type from name and command."""
        name_lower = name.lower()
        command_lower = command.lower()
        
        if any(keyword in name_lower for keyword in ["test", "spec", "check"]):
            return TaskType.TEST
        elif any(keyword in name_lower for keyword in ["build", "compile", "bundle"]):
            return TaskType.BUILD
        elif any(keyword in name_lower for keyword in ["lint", "flake", "eslint", "ruff check"]):
            return TaskType.LINT
        elif any(keyword in name_lower for keyword in ["format", "fmt", "prettier"]):
            return TaskType.FORMAT
        elif any(keyword in name_lower for keyword in ["type", "mypy", "tsc"]):
            return TaskType.TYPECHECK
        elif any(keyword in name_lower for keyword in ["security", "audit", "safety"]):
            return TaskType.SECURITY_SCAN
        elif any(keyword in name_lower for keyword in ["doc", "docs"]):
            return TaskType.DOCUMENTATION
        elif any(keyword in name_lower for keyword in ["clean", "cleanup"]):
            return TaskType.CLEANUP
        elif any(keyword in name_lower for keyword in ["bench", "perf"]):
            return TaskType.BENCHMARK
        elif any(keyword in name_lower for keyword in ["deploy", "release"]):
            return TaskType.DEPLOY
        else:
            return TaskType.CUSTOM
    
    def _infer_task_priority(self, task_type: TaskType) -> TaskPriority:
        """Infer task priority from type."""
        priority_map = {
            TaskType.TEST: TaskPriority.CRITICAL,
            TaskType.BUILD: TaskPriority.HIGH,
            TaskType.LINT: TaskPriority.HIGH,
            TaskType.TYPECHECK: TaskPriority.HIGH,
            TaskType.SECURITY_SCAN: TaskPriority.HIGH,
            TaskType.FORMAT: TaskPriority.MEDIUM,
            TaskType.DOCUMENTATION: TaskPriority.MEDIUM,
            TaskType.CLEANUP: TaskPriority.LOW,
            TaskType.BENCHMARK: TaskPriority.LOW,
            TaskType.DEPLOY: TaskPriority.MEDIUM,
            TaskType.CUSTOM: TaskPriority.MEDIUM
        }
        
        return priority_map.get(task_type, TaskPriority.MEDIUM)
    
    async def register_task(self, task_def: TaskDefinition) -> bool:
        """Register a task definition."""
        
        with span("devtasks.register_task", task_id=task_def.id, task_type=task_def.task_type.value):
            
            try:
                self.task_registry[task_def.id] = task_def
                
                # Observe task registration
                observe_with_agi_reasoning(
                    attributes={
                        CliAttributes.COMMAND: "devtasks_register_task",
                        "task_id": task_def.id,
                        "task_type": task_def.task_type.value,
                        "priority": task_def.priority.value
                    },
                    context={"devtasks": True, "task_registration": True}
                )
                
                metric_counter("devtasks.tasks_registered")(1)
                return True
                
            except Exception as e:
                print(f"❌ Failed to register task '{task_def.id}': {e}")
                return False
    
    async def execute_task(self, task_id: str) -> TaskExecutionResult:
        """Execute a single task."""
        
        if task_id not in self.task_registry:
            return TaskExecutionResult(
                task_id=task_id,
                task_name="unknown",
                status=TaskStatus.FAILED,
                start_time=time.time(),
                error=f"Task '{task_id}' not found"
            )
        
        task_def = self.task_registry[task_id]
        
        with span("devtasks.execute_task", task_id=task_id, task_type=task_def.task_type.value):
            
            start_time = time.time()
            
            # Check conditions
            if not await self._check_task_conditions(task_def):
                return TaskExecutionResult(
                    task_id=task_id,
                    task_name=task_def.name,
                    status=TaskStatus.SKIPPED,
                    start_time=start_time,
                    end_time=time.time()
                )
            
            # Execute task using appropriate handler
            handler = self.task_handlers.get(task_def.task_type)
            if handler:
                result = await handler(task_def)
            else:
                result = await self._execute_command_task(task_def, task_def.task_type)
            
            # Store execution result
            self.execution_history.append(result)
            
            # Observe execution
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "devtasks_execute_task",
                    "task_id": task_id,
                    "status": result.status.value,
                    "duration": str(result.duration) if result.duration else "unknown"
                },
                context={"devtasks": True, "task_execution": True}
            )
            
            # Track performance
            await self._track_task_performance(result)
            
            # AGI learning
            if self.enable_agi_optimization:
                await self._learn_from_execution(result)
            
            return result
    
    async def _execute_command_task(self, 
                                  task_def: TaskDefinition,
                                  task_type: TaskType) -> TaskExecutionResult:
        """Execute a command-based task."""
        
        start_time = time.time()
        result = TaskExecutionResult(
            task_id=task_def.id,
            task_name=task_def.name,
            status=TaskStatus.RUNNING,
            start_time=start_time
        )
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(task_def.environment)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                task_def.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=task_def.working_dir or self.project_root,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=task_def.timeout
                )
                
                result.exit_code = process.returncode
                result.stdout = stdout.decode('utf-8', errors='replace')
                result.stderr = stderr.decode('utf-8', errors='replace')
                
                if result.exit_code == 0:
                    result.status = TaskStatus.COMPLETED
                else:
                    result.status = TaskStatus.FAILED
                    result.error = f"Command failed with exit code {result.exit_code}"
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                result.status = TaskStatus.FAILED
                result.error = f"Task timed out after {task_def.timeout} seconds"
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
        
        finally:
            end_time = time.time()
            result.end_time = end_time
            result.duration = end_time - start_time
        
        return result
    
    async def _check_task_conditions(self, task_def: TaskDefinition) -> bool:
        """Check if task conditions are met."""
        for condition in task_def.conditions:
            if condition == "has_tests" and not self._has_test_files():
                return False
            elif condition == "has_lint_config" and not self._has_lint_config():
                return False
            # Add more conditions as needed
        
        return True
    
    def _has_test_files(self) -> bool:
        """Check if project has test files."""
        test_patterns = ["test_*.py", "*_test.py", "*.test.js", "*.spec.js"]
        for pattern in test_patterns:
            if list(self.project_root.glob(f"**/{pattern}")):
                return True
        return False
    
    def _has_lint_config(self) -> bool:
        """Check if project has linting configuration."""
        lint_configs = [".eslintrc*", "ruff.toml", ".ruff.toml", "setup.cfg", "pyproject.toml"]
        for config in lint_configs:
            if list(self.project_root.glob(config)):
                return True
        return False
    
    def _extract_test_metrics(self, stdout: str) -> Dict[str, Any]:
        """Extract test metrics from test output."""
        metrics = {}
        
        # pytest patterns
        if "passed" in stdout or "failed" in stdout:
            lines = stdout.split('\n')
            for line in lines:
                if " passed" in line and " failed" in line:
                    # Parse pytest summary line
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            metrics["tests_passed"] = int(parts[i-1])
                        elif part == "failed" and i > 0:
                            metrics["tests_failed"] = int(parts[i-1])
        
        return metrics
    
    def _extract_lint_metrics(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extract linting metrics from output."""
        metrics = {}
        
        # Count issues in output
        combined_output = stdout + stderr
        lines = combined_output.split('\n')
        
        # Simple issue counting
        issue_count = sum(1 for line in lines if any(
            keyword in line.lower() 
            for keyword in ["error:", "warning:", "E:", "W:", "F:", "C:"]
        ))
        
        if issue_count > 0:
            metrics["lint_issues"] = issue_count
        
        return metrics
    
    async def _track_task_performance(self, result: TaskExecutionResult):
        """Track task performance for optimization."""
        if result.duration:
            task_id = result.task_id
            
            # Update baseline if this is first execution or significantly better
            if task_id not in self.performance_baselines:
                self.performance_baselines[task_id] = result.duration
            elif result.duration < self.performance_baselines[task_id] * 0.8:
                self.performance_baselines[task_id] = result.duration
            
            # Record metrics
            metric_histogram(f"devtasks.duration.{task_id}")(result.duration)
            metric_counter(f"devtasks.executions.{result.status.value}")(1)
    
    async def _learn_from_execution(self, result: TaskExecutionResult):
        """Learn from task execution for AGI optimization."""
        memory = get_persistent_memory()
        
        if result.status == TaskStatus.COMPLETED:
            memory.store_knowledge(
                content=f"Task success: {result.task_name} completed in {result.duration:.2f}s",
                knowledge_type="task_success",
                metadata={
                    "task_id": result.task_id,
                    "duration": result.duration,
                    "performance_metrics": result.performance_metrics
                }
            )
        elif result.status == TaskStatus.FAILED:
            memory.store_knowledge(
                content=f"Task failure: {result.task_name} failed - {result.error}",
                knowledge_type="task_failure",
                metadata={
                    "task_id": result.task_id,
                    "error": result.error,
                    "exit_code": result.exit_code
                }
            )
    
    async def _create_common_sequences(self):
        """Create common task sequences."""
        
        # Quality assurance sequence
        qa_tasks = []
        for task_id, task_def in self.task_registry.items():
            if task_def.task_type in [TaskType.LINT, TaskType.TYPECHECK, TaskType.TEST]:
                qa_tasks.append(task_id)
        
        if qa_tasks:
            qa_sequence = TaskSequence(
                id="qa_sequence",
                name="Quality Assurance",
                description="Run all quality assurance tasks",
                tasks=qa_tasks,
                metadata={"auto_generated": True}
            )
            self.task_sequences["qa_sequence"] = qa_sequence
        
        # Build and test sequence
        build_tasks = [task_id for task_id, task_def in self.task_registry.items() 
                      if task_def.task_type == TaskType.BUILD]
        test_tasks = [task_id for task_id, task_def in self.task_registry.items() 
                     if task_def.task_type == TaskType.TEST]
        
        if build_tasks and test_tasks:
            build_test_sequence = TaskSequence(
                id="build_test_sequence",
                name="Build and Test",
                description="Build project and run tests",
                tasks=build_tasks + test_tasks,
                metadata={"auto_generated": True}
            )
            self.task_sequences["build_test_sequence"] = build_test_sequence
    
    async def execute_sequence(self, sequence_id: str) -> List[TaskExecutionResult]:
        """Execute a task sequence."""
        
        if sequence_id not in self.task_sequences:
            return []
        
        sequence = self.task_sequences[sequence_id]
        results = []
        
        with span("devtasks.execute_sequence", sequence_id=sequence_id):
            
            # Execute tasks in order
            for task_id in sequence.tasks:
                if task_id in self.task_registry:
                    result = await self.execute_task(task_id)
                    results.append(result)
                    
                    # Stop on failure if not configured to continue
                    if result.status == TaskStatus.FAILED:
                        break
            
            # Observe sequence execution
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "devtasks_execute_sequence",
                    "sequence_id": sequence_id,
                    "tasks_executed": str(len(results)),
                    "successful": str(sum(1 for r in results if r.status == TaskStatus.COMPLETED))
                },
                context={"devtasks": True, "sequence_execution": True}
            )
        
        return results
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get comprehensive task statistics."""
        total_tasks = len(self.task_registry)
        total_executions = len(self.execution_history)
        
        if total_executions == 0:
            return {
                "total_tasks": total_tasks,
                "total_executions": 0,
                "success_rate": 0.0,
                "task_types": [],
                "sequences": len(self.task_sequences)
            }
        
        successful = sum(1 for r in self.execution_history if r.status == TaskStatus.COMPLETED)
        failed = sum(1 for r in self.execution_history if r.status == TaskStatus.FAILED)
        
        # Task type distribution
        task_types = {}
        for task_def in self.task_registry.values():
            task_type = task_def.task_type.value
            task_types[task_type] = task_types.get(task_type, 0) + 1
        
        # Average durations
        durations = [r.duration for r in self.execution_history if r.duration]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "total_tasks": total_tasks,
            "enabled_tasks": sum(1 for t in self.task_registry.values() if t.enabled),
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": (successful / total_executions) * 100,
            "average_duration": avg_duration,
            "task_types": task_types,
            "sequences": len(self.task_sequences),
            "agi_optimization_enabled": self.enable_agi_optimization,
            "project_root": str(self.project_root)
        }


# Global task manager instance
_dev_task_manager = None

def get_dev_task_manager(project_root: Optional[Path] = None) -> IntelligentDevTaskManager:
    """Get the global development task manager."""
    global _dev_task_manager
    if _dev_task_manager is None:
        _dev_task_manager = IntelligentDevTaskManager(project_root)
    return _dev_task_manager

async def execute_dev_task(task_id: str) -> TaskExecutionResult:
    """Execute a development task."""
    manager = get_dev_task_manager()
    return await manager.execute_task(task_id)

async def execute_task_sequence(sequence_id: str) -> List[TaskExecutionResult]:
    """Execute a task sequence."""
    manager = get_dev_task_manager()
    return await manager.execute_sequence(sequence_id)

def get_devtask_status() -> Dict[str, Any]:
    """Get development task system status."""
    manager = get_dev_task_manager()
    return manager.get_task_stats()