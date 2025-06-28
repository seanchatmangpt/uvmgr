"""
Enhanced Error Handling and Recovery
====================================

Intelligent error handling and recovery system with AGI-driven diagnostics
and automatic recovery strategies.

Key Features:
- Contextual error classification and analysis
- AGI-driven error diagnosis and recovery suggestions
- Automatic retry mechanisms with exponential backoff
- Error pattern learning and prevention
- Graceful degradation strategies
- Comprehensive error reporting and tracking

This fills a critical gap: inconsistent error handling across the system.
"""

from __future__ import annotations

import asyncio
import functools
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union, TypeVar

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.agi_memory import get_persistent_memory
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram


T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYSTEM = "system"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    PERMISSION = "permission"
    RESOURCE = "resource"
    EXTERNAL_SERVICE = "external_service"
    USER_INPUT = "user_input"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies."""
    RETRY = "retry"
    FALLBACK = "fallback"
    DEGRADE = "degrade"
    ABORT = "abort"
    MANUAL = "manual"
    RESTART = "restart"


@dataclass
class ErrorContext:
    """Context information for an error."""
    
    # Basic information
    error_id: str
    timestamp: float
    operation: str
    component: str
    
    # Error details
    exception_type: str
    exception_message: str
    stack_trace: str
    
    # Classification
    severity: ErrorSeverity
    category: ErrorCategory
    
    # Context
    user_input: Optional[Dict[str, Any]] = None
    system_state: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, str]] = None
    
    # Recovery information
    recovery_strategy: Optional[RecoveryStrategy] = None
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    
    # Learning data
    similar_errors: List[str] = field(default_factory=list)
    agi_insights: Optional[Dict[str, Any]] = None
    
    # Resolution
    resolved: bool = False
    resolution_method: Optional[str] = None
    resolution_time: Optional[float] = None


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    
    success: bool
    strategy_used: RecoveryStrategy
    duration: float
    error_id: str
    attempt_number: int
    
    # Recovery details
    recovery_data: Optional[Dict[str, Any]] = None
    fallback_used: bool = False
    degraded_functionality: bool = False
    
    # Next steps
    requires_manual_intervention: bool = False
    recommended_actions: List[str] = field(default_factory=list)


class ErrorPattern:
    """Represents a learned error pattern."""
    
    def __init__(self, pattern_id: str, error_signature: str):
        self.pattern_id = pattern_id
        self.error_signature = error_signature
        self.occurrence_count = 1
        self.success_recovery_strategies: Dict[RecoveryStrategy, int] = {}
        self.failure_recovery_strategies: Dict[RecoveryStrategy, int] = {}
        self.first_seen = time.time()
        self.last_seen = time.time()
        
    def record_recovery_attempt(self, strategy: RecoveryStrategy, success: bool):
        """Record a recovery attempt for this pattern."""
        self.last_seen = time.time()
        
        if success:
            self.success_recovery_strategies[strategy] = self.success_recovery_strategies.get(strategy, 0) + 1
        else:
            self.failure_recovery_strategies[strategy] = self.failure_recovery_strategies.get(strategy, 0) + 1
    
    def get_best_recovery_strategy(self) -> Optional[RecoveryStrategy]:
        """Get the most successful recovery strategy for this pattern."""
        if not self.success_recovery_strategies:
            return None
        
        return max(self.success_recovery_strategies.items(), key=lambda x: x[1])[0]


class IntelligentErrorHandler:
    """
    Intelligent error handling and recovery system.
    
    Provides AGI-driven error diagnosis, classification, and recovery
    with learning capabilities and pattern recognition.
    """
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.recovery_strategies: Dict[ErrorCategory, List[RecoveryStrategy]] = {}
        self.global_handlers: Dict[Type[Exception], Callable] = {}
        
        # Performance settings
        self.max_recovery_attempts = 3
        self.retry_base_delay = 1.0
        self.retry_max_delay = 60.0
        self.pattern_learning_enabled = True
        
        # Initialize default recovery strategies
        self._initialize_recovery_strategies()
        
        # Initialize default exception handlers
        self._initialize_default_handlers()
    
    def _initialize_recovery_strategies(self):
        """Initialize default recovery strategies by error category."""
        
        self.recovery_strategies = {
            ErrorCategory.NETWORK: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.DEGRADE
            ],
            ErrorCategory.CONFIGURATION: [
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.MANUAL
            ],
            ErrorCategory.PERMISSION: [
                RecoveryStrategy.DEGRADE,
                RecoveryStrategy.MANUAL
            ],
            ErrorCategory.RESOURCE: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.DEGRADE,
                RecoveryStrategy.RESTART
            ],
            ErrorCategory.EXTERNAL_SERVICE: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.DEGRADE
            ],
            ErrorCategory.USER_INPUT: [
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.MANUAL
            ],
            ErrorCategory.VALIDATION: [
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.MANUAL
            ],
            ErrorCategory.SYSTEM: [
                RecoveryStrategy.RESTART,
                RecoveryStrategy.ABORT
            ],
            ErrorCategory.RUNTIME: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK
            ],
            ErrorCategory.UNKNOWN: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.ABORT
            ]
        }
    
    def _initialize_default_handlers(self):
        """Initialize default exception handlers."""
        
        # Network-related errors
        self.global_handlers[ConnectionError] = self._handle_connection_error
        self.global_handlers[TimeoutError] = self._handle_timeout_error
        
        # Permission errors
        self.global_handlers[PermissionError] = self._handle_permission_error
        
        # File system errors
        self.global_handlers[FileNotFoundError] = self._handle_file_not_found_error
        self.global_handlers[IsADirectoryError] = self._handle_directory_error
        
        # Value errors
        self.global_handlers[ValueError] = self._handle_value_error
        self.global_handlers[TypeError] = self._handle_type_error
        
        # Import errors
        self.global_handlers[ImportError] = self._handle_import_error
        self.global_handlers[ModuleNotFoundError] = self._handle_module_not_found_error
    
    async def handle_error(self, 
                          exception: Exception,
                          operation: str,
                          component: str,
                          context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """Handle an error with intelligent diagnosis and recovery."""
        
        error_id = f"error_{uuid.uuid4().hex[:8]}"
        
        with span("error_handling.handle_error", error_id=error_id, operation=operation):
            
            # Create error context
            error_context = ErrorContext(
                error_id=error_id,
                timestamp=time.time(),
                operation=operation,
                component=component,
                exception_type=type(exception).__name__,
                exception_message=str(exception),
                stack_trace=traceback.format_exc(),
                severity=self._classify_severity(exception),
                category=self._classify_category(exception),
                user_input=context.get("user_input") if context else None,
                system_state=context.get("system_state") if context else None,
                environment=dict(os.environ) if context and context.get("include_env") else None
            )
            
            # Perform AGI-driven analysis
            await self._agi_analyze_error(error_context)
            
            # Find similar errors and patterns
            await self._find_similar_errors(error_context)
            
            # Store error for learning
            self.error_history.append(error_context)
            
            # Learn from error pattern
            if self.pattern_learning_enabled:
                self._learn_error_pattern(error_context)
            
            # Observe error occurrence
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "error_occurred",
                    "error_id": error_id,
                    "error_type": error_context.exception_type,
                    "severity": error_context.severity.value,
                    "category": error_context.category.value,
                    "operation": operation,
                    "component": component
                },
                context={
                    "error_handling": True,
                    "error_occurred": True
                }
            )
            
            # Record metrics
            metric_counter("errors.occurred")(1, {
                "error_type": error_context.exception_type,
                "severity": error_context.severity.value,
                "category": error_context.category.value,
                "component": component
            })
            
            return error_context
    
    async def attempt_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Attempt to recover from an error."""
        
        start_time = time.time()
        error_context.recovery_attempts += 1
        
        with span("error_handling.attempt_recovery", 
                 error_id=error_context.error_id,
                 attempt=error_context.recovery_attempts):
            
            # Determine recovery strategy
            strategy = self._determine_recovery_strategy(error_context)
            error_context.recovery_strategy = strategy
            
            try:
                # Execute recovery strategy
                result = await self._execute_recovery_strategy(error_context, strategy)
                
                # Record recovery attempt
                if self.pattern_learning_enabled:
                    self._record_recovery_attempt(error_context, strategy, result.success)
                
                # Observe recovery attempt
                observe_with_agi_reasoning(
                    attributes={
                        CliAttributes.COMMAND: "error_recovery_attempt",
                        "error_id": error_context.error_id,
                        "strategy": strategy.value,
                        "success": str(result.success),
                        "attempt_number": str(error_context.recovery_attempts)
                    },
                    context={
                        "error_handling": True,
                        "recovery_attempt": True
                    }
                )
                
                # Record metrics
                metric_counter("errors.recovery_attempts")(1, {
                    "strategy": strategy.value,
                    "success": str(result.success)
                })
                
                metric_histogram("errors.recovery_duration")(result.duration)
                
                if result.success:
                    error_context.resolved = True
                    error_context.resolution_method = strategy.value
                    error_context.resolution_time = time.time()
                
                return result
                
            except Exception as e:
                # Recovery itself failed
                duration = time.time() - start_time
                
                return RecoveryResult(
                    success=False,
                    strategy_used=strategy,
                    duration=duration,
                    error_id=error_context.error_id,
                    attempt_number=error_context.recovery_attempts,
                    requires_manual_intervention=True,
                    recommended_actions=[f"Recovery strategy {strategy.value} failed: {str(e)}"]
                )
    
    def _classify_severity(self, exception: Exception) -> ErrorSeverity:
        """Classify error severity."""
        
        # Critical errors that halt operation
        critical_types = (SystemExit, KeyboardInterrupt, MemoryError)
        if isinstance(exception, critical_types):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        high_severity_types = (
            ConnectionError, PermissionError, FileNotFoundError, 
            ImportError, ModuleNotFoundError
        )
        if isinstance(exception, high_severity_types):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        medium_severity_types = (ValueError, TypeError, AttributeError)
        if isinstance(exception, medium_severity_types):
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _classify_category(self, exception: Exception) -> ErrorCategory:
        """Classify error category."""
        
        # Network errors
        network_types = (ConnectionError, TimeoutError)
        if isinstance(exception, network_types):
            return ErrorCategory.NETWORK
        
        # Permission errors
        if isinstance(exception, PermissionError):
            return ErrorCategory.PERMISSION
        
        # File system errors
        file_types = (FileNotFoundError, IsADirectoryError, FileExistsError)
        if isinstance(exception, file_types):
            return ErrorCategory.SYSTEM
        
        # Import errors
        import_types = (ImportError, ModuleNotFoundError)
        if isinstance(exception, import_types):
            return ErrorCategory.EXTERNAL_SERVICE
        
        # Validation errors
        validation_types = (ValueError, TypeError)
        if isinstance(exception, validation_types):
            return ErrorCategory.VALIDATION
        
        # Runtime errors
        runtime_types = (RuntimeError, AttributeError)
        if isinstance(exception, runtime_types):
            return ErrorCategory.RUNTIME
        
        return ErrorCategory.UNKNOWN
    
    async def _agi_analyze_error(self, error_context: ErrorContext):
        """Use AGI to analyze the error and provide insights."""
        
        try:
            # Create analysis context for AGI
            analysis_context = {
                "error_type": error_context.exception_type,
                "error_message": error_context.exception_message,
                "operation": error_context.operation,
                "component": error_context.component,
                "severity": error_context.severity.value,
                "category": error_context.category.value
            }
            
            # Store in AGI memory for pattern learning
            memory = get_persistent_memory()
            memory.store_knowledge(
                content=f"Error occurred: {error_context.exception_type} in {error_context.component}",
                knowledge_type="error_occurrence",
                metadata=analysis_context
            )
            
            # Simple AGI insights (in a real implementation, this would be more sophisticated)
            error_context.agi_insights = {
                "common_causes": self._get_common_causes(error_context.exception_type),
                "recommended_actions": self._get_recommended_actions(error_context.category),
                "prevention_strategies": self._get_prevention_strategies(error_context.category)
            }
            
        except Exception as e:
            # Don't let AGI analysis failure prevent error handling
            print(f"⚠️  AGI error analysis failed: {e}")
    
    async def _find_similar_errors(self, error_context: ErrorContext):
        """Find similar errors in history for pattern matching."""
        
        try:
            # Look for similar errors in recent history
            similar_errors = []
            
            for historical_error in self.error_history[-100:]:  # Last 100 errors
                if (historical_error.exception_type == error_context.exception_type and
                    historical_error.component == error_context.component):
                    similar_errors.append(historical_error.error_id)
            
            error_context.similar_errors = similar_errors
            
            # If we have similar errors, suggest learned recovery strategies
            if similar_errors:
                pattern_signature = f"{error_context.exception_type}_{error_context.component}"
                if pattern_signature in self.error_patterns:
                    pattern = self.error_patterns[pattern_signature]
                    best_strategy = pattern.get_best_recovery_strategy()
                    if best_strategy:
                        error_context.recovery_strategy = best_strategy
            
        except Exception as e:
            print(f"⚠️  Similar error analysis failed: {e}")
    
    def _learn_error_pattern(self, error_context: ErrorContext):
        """Learn from error pattern for future recovery."""
        
        pattern_signature = f"{error_context.exception_type}_{error_context.component}"
        
        if pattern_signature in self.error_patterns:
            self.error_patterns[pattern_signature].occurrence_count += 1
            self.error_patterns[pattern_signature].last_seen = time.time()
        else:
            self.error_patterns[pattern_signature] = ErrorPattern(
                pattern_id=pattern_signature,
                error_signature=pattern_signature
            )
    
    def _record_recovery_attempt(self, 
                                error_context: ErrorContext, 
                                strategy: RecoveryStrategy, 
                                success: bool):
        """Record recovery attempt for pattern learning."""
        
        pattern_signature = f"{error_context.exception_type}_{error_context.component}"
        
        if pattern_signature in self.error_patterns:
            self.error_patterns[pattern_signature].record_recovery_attempt(strategy, success)
    
    def _determine_recovery_strategy(self, error_context: ErrorContext) -> RecoveryStrategy:
        """Determine the best recovery strategy for an error."""
        
        # Use learned strategy if available
        if error_context.recovery_strategy:
            return error_context.recovery_strategy
        
        # Check if we have a pattern for this error
        pattern_signature = f"{error_context.exception_type}_{error_context.component}"
        if pattern_signature in self.error_patterns:
            best_strategy = self.error_patterns[pattern_signature].get_best_recovery_strategy()
            if best_strategy:
                return best_strategy
        
        # Use category-based default strategies
        strategies = self.recovery_strategies.get(error_context.category, [RecoveryStrategy.ABORT])
        
        # Return first strategy for this attempt number
        strategy_index = min(error_context.recovery_attempts - 1, len(strategies) - 1)
        return strategies[strategy_index]
    
    async def _execute_recovery_strategy(self, 
                                       error_context: ErrorContext,
                                       strategy: RecoveryStrategy) -> RecoveryResult:
        """Execute a specific recovery strategy."""
        
        start_time = time.time()
        
        try:
            if strategy == RecoveryStrategy.RETRY:
                # Exponential backoff retry
                delay = min(
                    self.retry_base_delay * (2 ** (error_context.recovery_attempts - 1)),
                    self.retry_max_delay
                )
                await asyncio.sleep(delay)
                
                return RecoveryResult(
                    success=True,  # Assume retry will work (actual retry happens in calling code)
                    strategy_used=strategy,
                    duration=time.time() - start_time,
                    error_id=error_context.error_id,
                    attempt_number=error_context.recovery_attempts,
                    recovery_data={"retry_delay": delay}
                )
            
            elif strategy == RecoveryStrategy.FALLBACK:
                return RecoveryResult(
                    success=True,
                    strategy_used=strategy,
                    duration=time.time() - start_time,
                    error_id=error_context.error_id,
                    attempt_number=error_context.recovery_attempts,
                    fallback_used=True,
                    recommended_actions=["Use fallback implementation", "Verify fallback works correctly"]
                )
            
            elif strategy == RecoveryStrategy.DEGRADE:
                return RecoveryResult(
                    success=True,
                    strategy_used=strategy,
                    duration=time.time() - start_time,
                    error_id=error_context.error_id,
                    attempt_number=error_context.recovery_attempts,
                    degraded_functionality=True,
                    recommended_actions=["Continue with reduced functionality", "Monitor for resolution"]
                )
            
            elif strategy == RecoveryStrategy.MANUAL:
                return RecoveryResult(
                    success=False,
                    strategy_used=strategy,
                    duration=time.time() - start_time,
                    error_id=error_context.error_id,
                    attempt_number=error_context.recovery_attempts,
                    requires_manual_intervention=True,
                    recommended_actions=self._get_manual_intervention_actions(error_context)
                )
            
            else:  # ABORT, RESTART, etc.
                return RecoveryResult(
                    success=False,
                    strategy_used=strategy,
                    duration=time.time() - start_time,
                    error_id=error_context.error_id,
                    attempt_number=error_context.recovery_attempts,
                    recommended_actions=[f"Execute {strategy.value} strategy"]
                )
                
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy_used=strategy,
                duration=time.time() - start_time,
                error_id=error_context.error_id,
                attempt_number=error_context.recovery_attempts,
                recommended_actions=[f"Recovery strategy execution failed: {str(e)}"]
            )
    
    def _get_common_causes(self, exception_type: str) -> List[str]:
        """Get common causes for an exception type."""
        
        common_causes = {
            "ConnectionError": [
                "Network connectivity issues",
                "Service unavailable",
                "Firewall blocking connection",
                "Incorrect URL or endpoint"
            ],
            "FileNotFoundError": [
                "File or directory doesn't exist",
                "Incorrect file path",
                "File moved or deleted",
                "Permission issues"
            ],
            "ImportError": [
                "Module not installed",
                "Incorrect module name",
                "Python path issues",
                "Dependency version conflicts"
            ],
            "ValueError": [
                "Invalid input data",
                "Incorrect data format",
                "Out of range values",
                "Type conversion issues"
            ]
        }
        
        return common_causes.get(exception_type, ["Unknown cause"])
    
    def _get_recommended_actions(self, category: ErrorCategory) -> List[str]:
        """Get recommended actions for an error category."""
        
        actions = {
            ErrorCategory.NETWORK: [
                "Check network connectivity",
                "Verify service endpoints",
                "Check firewall settings",
                "Try alternative endpoints"
            ],
            ErrorCategory.PERMISSION: [
                "Check file/directory permissions",
                "Run with appropriate privileges",
                "Verify user access rights"
            ],
            ErrorCategory.CONFIGURATION: [
                "Verify configuration files",
                "Check environment variables",
                "Validate configuration syntax"
            ],
            ErrorCategory.VALIDATION: [
                "Validate input data",
                "Check data types and formats",
                "Verify business logic constraints"
            ]
        }
        
        return actions.get(category, ["Contact support"])
    
    def _get_prevention_strategies(self, category: ErrorCategory) -> List[str]:
        """Get prevention strategies for an error category."""
        
        strategies = {
            ErrorCategory.NETWORK: [
                "Implement connection pooling",
                "Add retry mechanisms",
                "Use circuit breakers",
                "Monitor service health"
            ],
            ErrorCategory.VALIDATION: [
                "Add input validation",
                "Use type hints and validation",
                "Implement schema validation"
            ],
            ErrorCategory.CONFIGURATION: [
                "Use configuration validation",
                "Provide default values",
                "Document configuration options"
            ]
        }
        
        return strategies.get(category, ["Implement better error handling"])
    
    def _get_manual_intervention_actions(self, error_context: ErrorContext) -> List[str]:
        """Get manual intervention actions for an error."""
        
        base_actions = [
            f"Review error details: {error_context.exception_message}",
            f"Check {error_context.component} configuration",
            "Consult documentation or support"
        ]
        
        if error_context.agi_insights:
            base_actions.extend(error_context.agi_insights.get("recommended_actions", []))
        
        return base_actions
    
    # Default exception handlers
    async def _handle_connection_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle connection errors."""
        return await self.attempt_recovery(error_context)
    
    async def _handle_timeout_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle timeout errors."""
        return await self.attempt_recovery(error_context)
    
    async def _handle_permission_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle permission errors."""
        return await self.attempt_recovery(error_context)
    
    async def _handle_file_not_found_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle file not found errors."""
        return await self.attempt_recovery(error_context)
    
    async def _handle_directory_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle directory errors."""
        return await self.attempt_recovery(error_context)
    
    async def _handle_value_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle value errors."""
        return await self.attempt_recovery(error_context)
    
    async def _handle_type_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle type errors."""
        return await self.attempt_recovery(error_context)
    
    async def _handle_import_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle import errors."""
        return await self.attempt_recovery(error_context)
    
    async def _handle_module_not_found_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle module not found errors."""
        return await self.attempt_recovery(error_context)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics."""
        
        if not self.error_history:
            return {
                "total_errors": 0,
                "resolution_rate": 0.0,
                "patterns_learned": len(self.error_patterns)
            }
        
        total_errors = len(self.error_history)
        resolved_errors = len([e for e in self.error_history if e.resolved])
        
        # Category breakdown
        category_counts = {}
        for error in self.error_history:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Severity breakdown
        severity_counts = {}
        for error in self.error_history:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors": total_errors,
            "resolved_errors": resolved_errors,
            "resolution_rate": (resolved_errors / total_errors) * 100,
            "patterns_learned": len(self.error_patterns),
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "average_recovery_attempts": sum(e.recovery_attempts for e in self.error_history) / total_errors
        }


# Global error handler
_error_handler: Optional[IntelligentErrorHandler] = None

def get_error_handler() -> IntelligentErrorHandler:
    """Get the global error handler."""
    global _error_handler
    
    if _error_handler is None:
        _error_handler = IntelligentErrorHandler()
    
    return _error_handler

async def handle_error_with_recovery(exception: Exception,
                                   operation: str,
                                   component: str,
                                   context: Optional[Dict[str, Any]] = None,
                                   max_attempts: int = 3) -> Optional[RecoveryResult]:
    """Handle an error with automatic recovery attempts."""
    
    handler = get_error_handler()
    
    # Create error context
    error_context = await handler.handle_error(exception, operation, component, context)
    
    # Attempt recovery
    for attempt in range(max_attempts):
        if error_context.recovery_attempts >= error_context.max_recovery_attempts:
            break
        
        recovery_result = await handler.attempt_recovery(error_context)
        
        if recovery_result.success:
            return recovery_result
        
        if recovery_result.requires_manual_intervention:
            break
    
    return None

def error_handler(operation: str = None, component: str = None, max_attempts: int = 3):
    """Decorator for automatic error handling with recovery."""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                recovery_result = await handle_error_with_recovery(
                    e, 
                    operation or func.__name__,
                    component or func.__module__,
                    max_attempts=max_attempts
                )
                
                if recovery_result and recovery_result.success:
                    # Retry the function
                    return await func(*args, **kwargs)
                else:
                    # Re-raise if recovery failed
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # For sync functions, we can only log the error
                asyncio.create_task(
                    handle_error_with_recovery(
                        e,
                        operation or func.__name__,
                        component or func.__module__,
                        max_attempts=1  # No retry for sync functions
                    )
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator