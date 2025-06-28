"""
uvmgr.runtime.agent
===================

BPMN workflow execution package.

This package contains the implementation of BPMN workflow execution,
with the main implementation in the spiff module.
"""

from __future__ import annotations

# Import from the parent agent module
try:
    from ..agent import get_workflow_agent, execute_bpmn_workflow, WorkflowStatus
except ImportError:
    # Fallback - define stub functions
    def get_workflow_agent():
        raise NotImplementedError("Workflow agent not available")
    
    async def execute_bpmn_workflow(*args, **kwargs):
        raise NotImplementedError("BPMN workflow execution not available")
    
    class WorkflowStatus:
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"

__all__ = ["spiff", "get_workflow_agent", "execute_bpmn_workflow", "WorkflowStatus"]
