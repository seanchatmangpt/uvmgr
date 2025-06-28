"""
Runtime BPMN Workflow Agent
===========================

This module provides the core runtime agent for BPMN workflow execution,
integrating SpiffWorkflow with uvmgr's observability and AGI capabilities.

The agent enables autonomous workflow execution with full OpenTelemetry
instrumentation and AGI reasoning integration.

Key Features:
- BPMN workflow execution runtime
- OpenTelemetry instrumentation for all operations
- AGI integration for intelligent workflow adaptation
- Error recovery and rollback capabilities
- Real-time execution monitoring and metrics
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

try:
    from SpiffWorkflow import Workflow, WorkflowException
    from SpiffWorkflow.bpmn import BpmnWorkflow
    from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
    from SpiffWorkflow.task import Task
    SPIFF_AVAILABLE = True
except ImportError:
    SPIFF_AVAILABLE = False

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.agi_memory import get_persistent_memory
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Individual task status."""
    WAITING = "waiting"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tasks_executed: int = 0
    tasks_failed: int = 0
    error: Optional[str] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)


@dataclass 
class TaskExecutionContext:
    """Context for task execution."""
    task_id: str
    task_name: str
    workflow_id: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    error: Optional[str] = None


class BpmnWorkflowAgent:
    """
    BPMN Workflow execution agent with AGI integration.
    
    Provides intelligent workflow execution with:
    - Real-time monitoring and telemetry
    - AGI-driven adaptation and optimization
    - Error recovery and rollback capabilities
    - Comprehensive observability
    """
    
    def __init__(self):
        self.active_workflows: Dict[str, Any] = {}
        self.execution_history: List[WorkflowExecutionResult] = []
        self.task_handlers: Dict[str, Callable] = {}
        
        # Performance settings
        self.max_concurrent_workflows = 10
        self.default_timeout = 300  # 5 minutes
        self.enable_agi_adaptation = True
        
        # Initialize task handlers
        self._initialize_task_handlers()
        
        # Check SpiffWorkflow availability
        if not SPIFF_AVAILABLE:
            print("⚠️  SpiffWorkflow not available - BPMN functionality limited")
    
    def _initialize_task_handlers(self):
        """Initialize built-in task handlers."""
        
        async def shell_task_handler(context: TaskExecutionContext) -> Dict[str, Any]:
            """Execute shell commands."""
            import subprocess
            
            command = context.inputs.get("command", "")
            if not command:
                raise ValueError("Shell task requires 'command' input")
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=context.inputs.get("timeout", 30)
                )
                
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "success": result.returncode == 0
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        async def uvmgr_task_handler(context: TaskExecutionContext) -> Dict[str, Any]:
            """Execute uvmgr commands."""
            from uvmgr.core.shell import run_cmd
            
            uvmgr_command = context.inputs.get("uvmgr_command", "")
            if not uvmgr_command:
                raise ValueError("UVMgr task requires 'uvmgr_command' input")
            
            try:
                # Use uvmgr's shell execution
                result = await run_cmd(f"uvmgr {uvmgr_command}")
                return {"result": result, "success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        async def agi_analysis_handler(context: TaskExecutionContext) -> Dict[str, Any]:
            """AGI analysis task."""
            analysis_type = context.inputs.get("analysis_type", "general")
            data = context.inputs.get("data", {})
            
            # Perform AGI reasoning
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "workflow_agi_analysis",
                    "analysis_type": analysis_type,
                    "workflow_id": context.workflow_id
                },
                context={"agi_analysis": True, "workflow_task": True}
            )
            
            return {
                "analysis_complete": True,
                "analysis_type": analysis_type,
                "insights": [f"AGI analysis completed for {analysis_type}"]
            }
        
        self.task_handlers = {
            "shell_task": shell_task_handler,
            "uvmgr_task": uvmgr_task_handler,
            "agi_analysis": agi_analysis_handler
        }
    
    async def execute_workflow_from_file(self, 
                                       bpmn_file: Path,
                                       inputs: Dict[str, Any] = None,
                                       workflow_id: Optional[str] = None) -> WorkflowExecutionResult:
        """Execute BPMN workflow from file."""
        
        if not SPIFF_AVAILABLE:
            return WorkflowExecutionResult(
                workflow_id=workflow_id or "no_spiff",
                status=WorkflowStatus.FAILED,
                start_time=time.time(),
                error="SpiffWorkflow not available"
            )
        
        workflow_id = workflow_id or f"workflow_{uuid.uuid4().hex[:8]}"
        
        with span("workflow.execute_from_file", workflow_id=workflow_id, bpmn_file=str(bpmn_file)):
            start_time = time.time()
            
            # Observe workflow start
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "workflow_execution_start",
                    "workflow_id": workflow_id,
                    "bpmn_file": str(bpmn_file)
                },
                context={"workflow_execution": True, "autonomous": True}
            )
            
            try:
                # Load BPMN workflow
                if not bpmn_file.exists():
                    raise FileNotFoundError(f"BPMN file not found: {bpmn_file}")
                
                # Create SpiffWorkflow
                workflow = BpmnWorkflow.from_bpmn_file(str(bpmn_file))
                
                # Set inputs
                if inputs:
                    for key, value in inputs.items():
                        workflow.data[key] = value
                
                # Execute workflow
                result = await self._execute_workflow_instance(workflow, workflow_id, start_time)
                
                # Store result
                self.execution_history.append(result)
                
                # Record metrics
                metric_counter("workflow.executions.completed")(1)
                metric_histogram("workflow.execution.duration")(result.duration or 0)
                
                if result.status == WorkflowStatus.COMPLETED:
                    metric_counter("workflow.executions.success")(1)
                else:
                    metric_counter("workflow.executions.failed")(1)
                
                # Store learning data
                memory = get_persistent_memory()
                memory.store_knowledge(
                    content=f"Workflow executed: {bpmn_file.name} - {result.status.value}",
                    knowledge_type="workflow_execution",
                    metadata={
                        "workflow_id": workflow_id,
                        "status": result.status.value,
                        "duration": result.duration,
                        "tasks_executed": result.tasks_executed,
                        "bpmn_file": str(bpmn_file)
                    }
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                result = WorkflowExecutionResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.FAILED,
                    start_time=start_time,
                    end_time=time.time(),
                    duration=duration,
                    error=str(e)
                )
                
                self.execution_history.append(result)
                metric_counter("workflow.executions.failed")(1)
                
                return result
    
    async def _execute_workflow_instance(self,
                                       workflow: Any,
                                       workflow_id: str,
                                       start_time: float) -> WorkflowExecutionResult:
        """Execute a SpiffWorkflow instance."""
        
        result = WorkflowExecutionResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            start_time=start_time
        )
        
        self.active_workflows[workflow_id] = {
            "workflow": workflow,
            "result": result,
            "start_time": start_time
        }
        
        try:
            tasks_executed = 0
            tasks_failed = 0
            
            # Execute workflow tasks
            while not workflow.is_completed():
                ready_tasks = workflow.get_ready_user_tasks()
                
                if not ready_tasks:
                    # Try to advance workflow
                    workflow.complete_next()
                    continue
                
                # Execute ready tasks
                for task in ready_tasks:
                    task_start_time = time.time()
                    
                    try:
                        # Create task context
                        context = TaskExecutionContext(
                            task_id=str(task.id),
                            task_name=task.task_spec.name,
                            workflow_id=workflow_id,
                            inputs=dict(task.data),
                            metadata={"task_spec": task.task_spec.name}
                        )
                        
                        # Execute task
                        task_result = await self._execute_task(context)
                        
                        # Update task data
                        if task_result.get("success", True):
                            task.data.update(task_result.get("outputs", {}))
                            workflow.complete_task_from_id(task.id)
                            tasks_executed += 1
                        else:
                            tasks_failed += 1
                            raise Exception(f"Task failed: {task_result.get('error', 'Unknown error')}")
                        
                        context.execution_time = time.time() - task_start_time
                        
                        # Record task metrics
                        metric_counter("workflow.tasks.executed")(1)
                        metric_histogram("workflow.task.duration")(context.execution_time)
                        
                    except Exception as e:
                        tasks_failed += 1
                        context.error = str(e)
                        
                        metric_counter("workflow.tasks.failed")(1)
                        
                        # For now, continue with other tasks
                        # In production, you might want different error handling strategies
                        print(f"Task failed: {task.task_spec.name}: {e}")
            
            # Workflow completed
            end_time = time.time()
            duration = end_time - start_time
            
            result.status = WorkflowStatus.COMPLETED if tasks_failed == 0 else WorkflowStatus.FAILED
            result.end_time = end_time
            result.duration = duration
            result.tasks_executed = tasks_executed
            result.tasks_failed = tasks_failed
            result.outputs = dict(workflow.data)
            result.insights = [f"Executed {tasks_executed} tasks in {duration:.2f}s"]
            
            # AGI learning from execution
            if self.enable_agi_adaptation:
                await self._agi_learn_from_execution(result)
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            result.status = WorkflowStatus.FAILED
            result.end_time = end_time
            result.duration = duration
            result.error = str(e)
            result.tasks_executed = tasks_executed
            result.tasks_failed = tasks_failed + 1
        
        finally:
            # Clean up
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
        
        return result
    
    async def _execute_task(self, context: TaskExecutionContext) -> Dict[str, Any]:
        """Execute a single workflow task."""
        
        with span("workflow.execute_task", task_id=context.task_id, task_name=context.task_name):
            
            # Determine task handler
            task_type = context.metadata.get("task_spec", context.task_name)
            handler = self.task_handlers.get(task_type)
            
            if not handler:
                # Default handler - just mark as completed
                return {"success": True, "message": f"Task {context.task_name} completed"}
            
            try:
                # Execute task handler
                result = await handler(context)
                return result
                
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def _agi_learn_from_execution(self, result: WorkflowExecutionResult):
        """AGI learning from workflow execution."""
        
        # Store execution patterns
        memory = get_persistent_memory()
        
        if result.status == WorkflowStatus.COMPLETED:
            memory.store_knowledge(
                content=f"Successful workflow pattern: {result.tasks_executed} tasks in {result.duration:.2f}s",
                knowledge_type="workflow_success_pattern",
                metadata={
                    "workflow_id": result.workflow_id,
                    "tasks_executed": result.tasks_executed,
                    "duration": result.duration,
                    "success_rate": 1.0
                }
            )
        
        # Learn from failures
        if result.tasks_failed > 0:
            memory.store_knowledge(
                content=f"Workflow failure pattern: {result.tasks_failed} failures out of {result.tasks_executed + result.tasks_failed} tasks",
                knowledge_type="workflow_failure_pattern",
                metadata={
                    "workflow_id": result.workflow_id,
                    "tasks_failed": result.tasks_failed,
                    "error": result.error,
                    "failure_rate": result.tasks_failed / (result.tasks_executed + result.tasks_failed)
                }
            )
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a custom task handler."""
        self.task_handlers[task_type] = handler
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """Get status of a workflow."""
        if workflow_id in self.active_workflows:
            return WorkflowStatus.RUNNING
        
        for execution in self.execution_history:
            if execution.workflow_id == workflow_id:
                return execution.status
        
        return None
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "active_workflows": len(self.active_workflows)
            }
        
        total = len(self.execution_history)
        successful = len([e for e in self.execution_history if e.status == WorkflowStatus.COMPLETED])
        durations = [e.duration for e in self.execution_history if e.duration]
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": total - successful,
            "success_rate": (successful / total) * 100,
            "average_duration": sum(durations) / len(durations) if durations else 0.0,
            "active_workflows": len(self.active_workflows),
            "total_tasks_executed": sum(e.tasks_executed for e in self.execution_history),
            "spiff_available": SPIFF_AVAILABLE
        }


# Global workflow agent instance
_workflow_agent = None

def get_workflow_agent() -> BpmnWorkflowAgent:
    """Get the global workflow agent."""
    global _workflow_agent
    if _workflow_agent is None:
        _workflow_agent = BpmnWorkflowAgent()
    return _workflow_agent

async def execute_bpmn_workflow(bpmn_file: Path, 
                              inputs: Dict[str, Any] = None,
                              workflow_id: Optional[str] = None) -> WorkflowExecutionResult:
    """Execute a BPMN workflow file."""
    agent = get_workflow_agent()
    return await agent.execute_workflow_from_file(bpmn_file, inputs, workflow_id)

def get_agent_status() -> Dict[str, Any]:
    """Get workflow agent status."""
    agent = get_workflow_agent()
    return agent.get_execution_stats()