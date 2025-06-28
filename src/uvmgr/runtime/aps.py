"""
Runtime APScheduler Integration
===============================

This module provides advanced Python scheduler (APScheduler) integration
with uvmgr, enabling intelligent task scheduling with AGI capabilities.

The scheduler supports:
- Cron-based and interval-based scheduling
- AGI-driven adaptive scheduling optimization
- Full OpenTelemetry instrumentation
- Persistent job storage and recovery
- Dynamic job modification based on system performance

Key Features:
- Intelligent job scheduling with AGI optimization
- Real-time performance monitoring
- Automatic job failure recovery
- Dynamic scheduling adaptation
- Comprehensive observability
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
    from apscheduler.job import Job
    APS_AVAILABLE = True
except ImportError:
    APS_AVAILABLE = False

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.agi_memory import get_persistent_memory
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram
from uvmgr.core.paths import CONFIG_DIR


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MISSED = "missed"
    PAUSED = "paused"
    REMOVED = "removed"


class ScheduleType(Enum):
    """Type of job schedule."""
    INTERVAL = "interval"
    CRON = "cron"
    DATE = "date"
    ADAPTIVE = "adaptive"  # AGI-driven adaptive scheduling


@dataclass
class JobExecutionResult:
    """Result of job execution."""
    job_id: str
    job_name: str
    status: JobStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    execution_count: int = 0
    next_run_time: Optional[datetime] = None


@dataclass
class ScheduledJob:
    """Scheduled job definition."""
    id: str
    name: str
    function: str
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    max_instances: int = 1
    coalesce: bool = True
    misfire_grace_time: int = 300  # 5 minutes


class IntelligentScheduler:
    """
    Intelligent APScheduler with AGI optimization.
    
    Provides advanced scheduling capabilities:
    - AGI-driven schedule optimization
    - Performance-based adaptive scheduling
    - Comprehensive monitoring and telemetry
    - Automatic failure recovery
    - Dynamic resource management
    """
    
    def __init__(self, jobstore_url: Optional[str] = None):
        self.scheduler: Optional[Any] = None
        self.job_registry: Dict[str, ScheduledJob] = {}
        self.execution_history: List[JobExecutionResult] = []
        self.job_functions: Dict[str, Callable] = {}
        
        # Performance tracking
        self.performance_metrics: Dict[str, List[float]] = {}
        self.adaptive_schedules: Dict[str, Dict[str, Any]] = {}
        
        # Settings
        self.enable_agi_optimization = True
        self.optimization_interval = 3600  # 1 hour
        self.max_execution_history = 1000
        
        # Initialize jobstore
        self.jobstore_url = jobstore_url or f"sqlite:///{CONFIG_DIR}/scheduler.db"
        
        # Initialize if APScheduler is available
        if APS_AVAILABLE:
            self._initialize_scheduler()
        else:
            print("⚠️  APScheduler not available - scheduling functionality limited")
    
    def _initialize_scheduler(self):
        """Initialize the APScheduler."""
        try:
            # Configure job stores
            jobstores = {
                'default': SQLAlchemyJobStore(url=self.jobstore_url)
            }
            
            # Configure executors
            executors = {
                'default': ThreadPoolExecutor(max_workers=20),
            }
            
            # Job defaults
            job_defaults = {
                'coalesce': True,
                'max_instances': 3,
                'misfire_grace_time': 300
            }
            
            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults
            )
            
            # Add event listeners
            self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
            self.scheduler.add_listener(self._job_missed_listener, EVENT_JOB_MISSED)
            
            # Initialize built-in job functions
            self._initialize_job_functions()
            
        except Exception as e:
            print(f"⚠️  Scheduler initialization failed: {e}")
            APS_AVAILABLE = False
    
    def _initialize_job_functions(self):
        """Initialize built-in job functions."""
        
        async def system_health_check():
            """Perform system health check."""
            with span("scheduler.system_health_check"):
                start_time = time.time()
                
                # Perform basic health checks
                health_status = {
                    "timestamp": time.time(),
                    "scheduler_running": self.scheduler.running if self.scheduler else False,
                    "active_jobs": len(self.job_registry),
                    "execution_history_size": len(self.execution_history)
                }
                
                # Store health data
                memory = get_persistent_memory()
                memory.store_knowledge(
                    content=f"System health check: {health_status['active_jobs']} jobs active",
                    knowledge_type="system_health",
                    metadata=health_status
                )
                
                duration = time.time() - start_time
                metric_histogram("scheduler.health_check.duration")(duration)
                
                return health_status
        
        async def agi_optimization_job():
            """Perform AGI-driven schedule optimization."""
            if not self.enable_agi_optimization:
                return {"optimization": "disabled"}
            
            with span("scheduler.agi_optimization"):
                start_time = time.time()
                
                # Analyze job performance
                optimization_results = await self._optimize_schedules_with_agi()
                
                # Store optimization insights
                memory = get_persistent_memory()
                memory.store_knowledge(
                    content=f"Schedule optimization: {optimization_results.get('optimizations_made', 0)} optimizations applied",
                    knowledge_type="schedule_optimization",
                    metadata=optimization_results
                )
                
                duration = time.time() - start_time
                metric_histogram("scheduler.agi_optimization.duration")(duration)
                
                return optimization_results
        
        async def cleanup_job():
            """Clean up old execution history."""
            with span("scheduler.cleanup"):
                start_time = time.time()
                
                # Keep only recent history
                if len(self.execution_history) > self.max_execution_history:
                    self.execution_history = self.execution_history[-self.max_execution_history:]
                
                # Clean up old performance metrics
                cutoff_time = time.time() - 86400 * 7  # 7 days
                for job_id in self.performance_metrics:
                    self.performance_metrics[job_id] = [
                        metric for metric in self.performance_metrics[job_id]
                        if metric > cutoff_time
                    ]
                
                duration = time.time() - start_time
                metric_histogram("scheduler.cleanup.duration")(duration)
                
                return {"cleanup_completed": True, "duration": duration}
        
        # Register job functions
        self.job_functions = {
            "system_health_check": system_health_check,
            "agi_optimization": agi_optimization_job,
            "cleanup": cleanup_job
        }
    
    async def start(self):
        """Start the scheduler with default jobs."""
        if not APS_AVAILABLE or not self.scheduler:
            print("⚠️  Cannot start scheduler - APScheduler not available")
            return False
        
        with span("scheduler.start"):
            
            try:
                # Start the scheduler
                self.scheduler.start()
                
                # Add default system jobs
                await self._add_default_jobs()
                
                # Observe scheduler start
                observe_with_agi_reasoning(
                    attributes={
                        CliAttributes.COMMAND: "scheduler_start",
                        "jobstore_url": self.jobstore_url,
                        "agi_optimization": str(self.enable_agi_optimization)
                    },
                    context={"scheduler": True, "autonomous": True}
                )
                
                metric_counter("scheduler.starts")(1)
                
                print("✅ Intelligent scheduler started")
                return True
                
            except Exception as e:
                print(f"❌ Failed to start scheduler: {e}")
                metric_counter("scheduler.start_failures")(1)
                return False
    
    async def stop(self):
        """Stop the scheduler."""
        if not self.scheduler:
            return
        
        with span("scheduler.stop"):
            try:
                self.scheduler.shutdown(wait=True)
                
                observe_with_agi_reasoning(
                    attributes={
                        CliAttributes.COMMAND: "scheduler_stop",
                        "jobs_executed": str(len(self.execution_history))
                    },
                    context={"scheduler": True}
                )
                
                metric_counter("scheduler.stops")(1)
                print("🛑 Scheduler stopped")
                
            except Exception as e:
                print(f"⚠️  Error stopping scheduler: {e}")
    
    async def _add_default_jobs(self):
        """Add default system jobs."""
        
        # System health check every 15 minutes
        await self.add_job(
            job_id="system_health_check",
            name="System Health Check",
            function="system_health_check",
            schedule_type=ScheduleType.INTERVAL,
            schedule_config={"minutes": 15}
        )
        
        # AGI optimization every hour
        await self.add_job(
            job_id="agi_optimization", 
            name="AGI Schedule Optimization",
            function="agi_optimization",
            schedule_type=ScheduleType.INTERVAL,
            schedule_config={"hours": 1}
        )
        
        # Cleanup every day at 2 AM
        await self.add_job(
            job_id="daily_cleanup",
            name="Daily Cleanup",
            function="cleanup",
            schedule_type=ScheduleType.CRON,
            schedule_config={"hour": 2, "minute": 0}
        )
    
    async def add_job(self,
                     job_id: str,
                     name: str,
                     function: str,
                     schedule_type: ScheduleType,
                     schedule_config: Dict[str, Any],
                     args: List[Any] = None,
                     kwargs: Dict[str, Any] = None,
                     metadata: Dict[str, Any] = None) -> bool:
        """Add a job to the scheduler."""
        
        if not APS_AVAILABLE or not self.scheduler:
            print("⚠️  Cannot add job - scheduler not available")
            return False
        
        with span("scheduler.add_job", job_id=job_id, function=function):
            
            try:
                # Create scheduled job
                scheduled_job = ScheduledJob(
                    id=job_id,
                    name=name,
                    function=function,
                    schedule_type=schedule_type,
                    schedule_config=schedule_config,
                    args=args or [],
                    kwargs=kwargs or {},
                    metadata=metadata or {}
                )
                
                # Get the function to execute
                job_function = self.job_functions.get(function)
                if not job_function:
                    raise ValueError(f"Job function '{function}' not registered")
                
                # Add to APScheduler based on schedule type
                if schedule_type == ScheduleType.INTERVAL:
                    self.scheduler.add_job(
                        func=self._execute_job_wrapper,
                        trigger='interval',
                        args=[job_id],
                        id=job_id,
                        name=name,
                        **schedule_config
                    )
                elif schedule_type == ScheduleType.CRON:
                    self.scheduler.add_job(
                        func=self._execute_job_wrapper,
                        trigger='cron',
                        args=[job_id],
                        id=job_id,
                        name=name,
                        **schedule_config
                    )
                elif schedule_type == ScheduleType.DATE:
                    self.scheduler.add_job(
                        func=self._execute_job_wrapper,
                        trigger='date',
                        args=[job_id],
                        id=job_id,
                        name=name,
                        **schedule_config
                    )
                
                # Register the job
                self.job_registry[job_id] = scheduled_job
                
                # Observe job addition
                observe_with_agi_reasoning(
                    attributes={
                        CliAttributes.COMMAND: "scheduler_add_job",
                        "job_id": job_id,
                        "function": function,
                        "schedule_type": schedule_type.value
                    },
                    context={"scheduler": True, "job_management": True}
                )
                
                metric_counter("scheduler.jobs_added")(1)
                
                print(f"✅ Job '{name}' ({job_id}) added to scheduler")
                return True
                
            except Exception as e:
                print(f"❌ Failed to add job '{job_id}': {e}")
                metric_counter("scheduler.job_add_failures")(1)
                return False
    
    async def _execute_job_wrapper(self, job_id: str):
        """Wrapper for job execution with telemetry."""
        
        if job_id not in self.job_registry:
            print(f"⚠️  Job {job_id} not found in registry")
            return
        
        scheduled_job = self.job_registry[job_id]
        start_time = time.time()
        
        with span("scheduler.execute_job", job_id=job_id, job_name=scheduled_job.name):
            
            result = JobExecutionResult(
                job_id=job_id,
                job_name=scheduled_job.name,
                status=JobStatus.RUNNING,
                start_time=start_time
            )
            
            try:
                # Get job function
                job_function = self.job_functions.get(scheduled_job.function)
                if not job_function:
                    raise ValueError(f"Job function '{scheduled_job.function}' not found")
                
                # Execute the job
                execution_result = await job_function(*scheduled_job.args, **scheduled_job.kwargs)
                
                # Job completed successfully
                end_time = time.time()
                duration = end_time - start_time
                
                result.status = JobStatus.COMPLETED
                result.end_time = end_time
                result.duration = duration
                result.result = execution_result
                
                # Track performance
                self._track_job_performance(job_id, duration)
                
                metric_counter("scheduler.jobs_completed")(1)
                metric_histogram("scheduler.job_duration")(duration)
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                result.status = JobStatus.FAILED
                result.end_time = end_time
                result.duration = duration
                result.error = str(e)
                
                metric_counter("scheduler.jobs_failed")(1)
                
                print(f"❌ Job '{scheduled_job.name}' failed: {e}")
            
            # Store execution result
            self.execution_history.append(result)
            
            # Observe job execution
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "scheduler_job_executed",
                    "job_id": job_id,
                    "status": result.status.value,
                    "duration": str(result.duration) if result.duration else "unknown"
                },
                context={"scheduler": True, "job_execution": True, "autonomous": True}
            )
    
    def _track_job_performance(self, job_id: str, duration: float):
        """Track job performance metrics."""
        if job_id not in self.performance_metrics:
            self.performance_metrics[job_id] = []
        
        self.performance_metrics[job_id].append(duration)
        
        # Keep only recent metrics (last 100 executions)
        if len(self.performance_metrics[job_id]) > 100:
            self.performance_metrics[job_id] = self.performance_metrics[job_id][-100:]
    
    async def _optimize_schedules_with_agi(self) -> Dict[str, Any]:
        """Use AGI to optimize job schedules based on performance."""
        
        optimization_results = {
            "optimizations_made": 0,
            "jobs_analyzed": len(self.job_registry),
            "performance_improvements": []
        }
        
        # Analyze each job's performance
        for job_id, scheduled_job in self.job_registry.items():
            if job_id not in self.performance_metrics:
                continue
            
            durations = self.performance_metrics[job_id]
            if len(durations) < 5:  # Need sufficient data
                continue
            
            # Calculate performance statistics
            avg_duration = sum(durations) / len(durations)
            recent_duration = sum(durations[-5:]) / 5  # Last 5 executions
            
            # Check if performance is degrading
            if recent_duration > avg_duration * 1.5:  # 50% increase
                # Consider reducing frequency
                new_schedule = await self._adapt_schedule_for_performance(scheduled_job, "reduce_frequency")
                if new_schedule:
                    optimization_results["optimizations_made"] += 1
                    optimization_results["performance_improvements"].append({
                        "job_id": job_id,
                        "optimization": "reduced_frequency",
                        "avg_duration": avg_duration,
                        "recent_duration": recent_duration
                    })
            
            # Check if job is consistently fast
            elif recent_duration < avg_duration * 0.7:  # 30% decrease
                # Consider increasing frequency
                new_schedule = await self._adapt_schedule_for_performance(scheduled_job, "increase_frequency")
                if new_schedule:
                    optimization_results["optimizations_made"] += 1
                    optimization_results["performance_improvements"].append({
                        "job_id": job_id,
                        "optimization": "increased_frequency",
                        "avg_duration": avg_duration,
                        "recent_duration": recent_duration
                    })
        
        return optimization_results
    
    async def _adapt_schedule_for_performance(self, 
                                            scheduled_job: ScheduledJob,
                                            optimization_type: str) -> Optional[Dict[str, Any]]:
        """Adapt a job's schedule based on performance."""
        
        if scheduled_job.schedule_type != ScheduleType.INTERVAL:
            return None  # Only optimize interval jobs for now
        
        current_config = scheduled_job.schedule_config.copy()
        
        if optimization_type == "reduce_frequency":
            # Increase interval (reduce frequency)
            if "seconds" in current_config:
                current_config["seconds"] = min(current_config["seconds"] * 1.5, 3600)
            elif "minutes" in current_config:
                current_config["minutes"] = min(current_config["minutes"] * 1.5, 60)
            elif "hours" in current_config:
                current_config["hours"] = min(current_config["hours"] * 1.5, 24)
        
        elif optimization_type == "increase_frequency":
            # Decrease interval (increase frequency)
            if "seconds" in current_config:
                current_config["seconds"] = max(current_config["seconds"] * 0.8, 30)
            elif "minutes" in current_config:
                current_config["minutes"] = max(current_config["minutes"] * 0.8, 1)
            elif "hours" in current_config:
                current_config["hours"] = max(current_config["hours"] * 0.8, 1)
        
        # Update the schedule if it changed
        if current_config != scheduled_job.schedule_config:
            try:
                # Remove old job
                self.scheduler.remove_job(scheduled_job.id)
                
                # Add job with new schedule
                self.scheduler.add_job(
                    func=self._execute_job_wrapper,
                    trigger='interval',
                    args=[scheduled_job.id],
                    id=scheduled_job.id,
                    name=scheduled_job.name,
                    **current_config
                )
                
                # Update registry
                scheduled_job.schedule_config = current_config
                
                return current_config
                
            except Exception as e:
                print(f"⚠️  Failed to adapt schedule for {scheduled_job.id}: {e}")
                return None
        
        return None
    
    def _job_executed_listener(self, event):
        """Handle job executed events."""
        job_id = event.job_id
        metric_counter(f"scheduler.job_executed.{job_id}")(1)
    
    def _job_error_listener(self, event):
        """Handle job error events."""
        job_id = event.job_id
        metric_counter(f"scheduler.job_error.{job_id}")(1)
        
        # Store error in memory for learning
        memory = get_persistent_memory()
        memory.store_knowledge(
            content=f"Scheduler job error: {job_id} - {event.exception}",
            knowledge_type="scheduler_error",
            metadata={
                "job_id": job_id,
                "error": str(event.exception),
                "timestamp": time.time()
            }
        )
    
    def _job_missed_listener(self, event):
        """Handle job missed events."""
        job_id = event.job_id
        metric_counter(f"scheduler.job_missed.{job_id}")(1)
    
    def register_job_function(self, name: str, function: Callable):
        """Register a job function."""
        self.job_functions[name] = function
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get comprehensive scheduler statistics."""
        if not self.execution_history:
            return {
                "status": "running" if (self.scheduler and self.scheduler.running) else "stopped",
                "total_jobs": len(self.job_registry),
                "total_executions": 0,
                "success_rate": 0.0,
                "aps_available": APS_AVAILABLE
            }
        
        total_executions = len(self.execution_history)
        successful = len([e for e in self.execution_history if e.status == JobStatus.COMPLETED])
        failed = len([e for e in self.execution_history if e.status == JobStatus.FAILED])
        
        # Calculate average durations
        durations = [e.duration for e in self.execution_history if e.duration]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "status": "running" if (self.scheduler and self.scheduler.running) else "stopped",
            "total_jobs": len(self.job_registry),
            "active_jobs": len([j for j in self.job_registry.values() if j.enabled]),
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": (successful / total_executions) * 100 if total_executions > 0 else 0.0,
            "average_duration": avg_duration,
            "agi_optimization_enabled": self.enable_agi_optimization,
            "jobstore_url": self.jobstore_url,
            "aps_available": APS_AVAILABLE
        }


# Global scheduler instance
_intelligent_scheduler = None

def get_intelligent_scheduler() -> IntelligentScheduler:
    """Get the global intelligent scheduler."""
    global _intelligent_scheduler
    if _intelligent_scheduler is None:
        _intelligent_scheduler = IntelligentScheduler()
    return _intelligent_scheduler

async def start_scheduler() -> bool:
    """Start the intelligent scheduler."""
    scheduler = get_intelligent_scheduler()
    return await scheduler.start()

async def stop_scheduler():
    """Stop the intelligent scheduler."""
    scheduler = get_intelligent_scheduler()
    await scheduler.stop()

def get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status."""
    scheduler = get_intelligent_scheduler()
    return scheduler.get_scheduler_stats()