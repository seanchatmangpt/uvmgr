"""
Event Stream Models (FastSocket/AshSwarm Pattern)
=================================================

Declarative models for asynchronous event-driven architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    # Project Events
    PROJECT_CREATED = "project.created"
    PROJECT_BUILD_STARTED = "project.build.started"
    PROJECT_BUILD_COMPLETED = "project.build.completed"
    PROJECT_TEST_STARTED = "project.test.started"
    PROJECT_TEST_COMPLETED = "project.test.completed"

    # Dependency Events
    DEPENDENCY_ADDED = "dependency.added"
    DEPENDENCY_UPDATED = "dependency.updated"
    DEPENDENCY_REMOVED = "dependency.removed"
    DEPENDENCY_RISK_DETECTED = "dependency.risk.detected"

    # System Events
    CACHE_CLEARED = "cache.cleared"
    TELEMETRY_SENT = "telemetry.sent"
    ERROR_OCCURRED = "error.occurred"


class EventPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Event(BaseModel):
    """Base event model for all system events"""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL

    # Event Metadata
    source: str = Field(..., description="Event source (e.g., 'cli', 'agent')")
    correlation_id: str | None = Field(None, description="For tracking related events")
    user_id: str | None = None

    # Event Payload
    data: dict[str, Any] = Field(default_factory=dict)

    # Routing Information
    topic: str | None = None
    partition_key: str | None = None

    class Config:
        use_enum_values = True
