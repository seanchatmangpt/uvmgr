"""Declarative workflow models for task orchestration."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from datetime import timedelta


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    

class TaskDependency(BaseModel):
    """Task dependency specification."""
    
    model_config = ConfigDict(extra="forbid")
    
    task_id: str
    condition: Optional[str] = None  # SpEL expression
    
    
class TaskNode(BaseModel):
    """Workflow task node."""
    
    model_config = ConfigDict(extra="forbid")
    
    id: str    name: str
    command: str
    description: Optional[str] = None
    dependencies: List[TaskDependency] = Field(default_factory=list)
    retry_count: int = 0
    timeout: Optional[timedelta] = None
    environment: Dict[str, str] = Field(default_factory=dict)
    on_failure: Optional[str] = None  # Task ID to run on failure
    on_success: Optional[str] = None  # Task ID to run on success
    parallel: bool = False
    
    
class WorkflowDefinition(BaseModel):
    """Declarative workflow definition."""
    
    model_config = ConfigDict(extra="forbid")
    
    id: str
    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    tasks: List[TaskNode]
    variables: Dict[str, Any] = Field(default_factory=dict)
    triggers: List[str] = Field(default_factory=list)  # cron expressions
    max_parallel_tasks: int = 4
    default_timeout: timedelta = Field(default=timedelta(minutes=30))