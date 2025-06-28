#!/usr/bin/env python3
"""
OTEL-Based Failure Detection and Incident Response
=================================================

Automated failure detection system that monitors OpenTelemetry data in real-time,
detects anomalies, and triggers incident response workflows.

Features:
- Real-time span monitoring
- Failure pattern detection
- Automated alerting
- Incident report generation
- Performance degradation detection
- SLA violation monitoring
"""

import asyncio
import json
import logging
import statistics
import sys
import time
import urllib.request
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FailurePattern:
    """Definition of a failure pattern to detect."""
    name: str
    description: str
    detector: Callable[[Dict[str, Any]], bool]
    severity: str  # "critical", "high", "medium", "low"
    cooldown_minutes: int = 5  # Prevent alert spam


@dataclass
class PerformanceSLA:
    """Service Level Agreement for performance metrics."""
    metric: str
    threshold: float
    comparison: str  # "less_than", "greater_than"
    window_seconds: int = 300  # 5-minute window


@dataclass
class Incident:
    """Represents a detected incident."""
    id: str
    pattern: str
    severity: str
    timestamp: datetime
    details: Dict[str, Any]
    affected_spans: List[str]
    recovery_time: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate incident duration."""
        if self.recovery_time:
            return self.recovery_time - self.timestamp
        return datetime.now() - self.timestamp


class OTELFailureDetector:
    """Real-time failure detection based on OpenTelemetry data."""
    
    def __init__(self,
                 otel_endpoint: str = "http://localhost:4318",
                 threshold: float = 0.95,
                 webhook_url: Optional[str] = None):
        self.otel_endpoint = otel_endpoint
        self.threshold = threshold
        self.webhook_url = webhook_url
        
        # Detection patterns
        self.patterns = self._initialize_patterns()
        
        # Performance SLAs
        self.slas = self._initialize_slas()
        
        # State tracking
        self.span_buffer = deque(maxlen=1000)  # Recent spans
        self.metric_buffer = defaultdict(lambda: deque(maxlen=100))  # Recent metrics
        self.active_incidents: Dict[str, Incident] = {}
        self.incident_history: List[Incident] = []
        self.pattern_cooldowns: Dict[str, datetime] = {}
        
        # Performance baselines
        self.performance_baselines: Dict[str, float] = {}
        self.baseline_window = deque(maxlen=100)
        
        # Statistics
        self.stats = {
            "spans_processed": 0,
            "failures_detected": 0,
            "incidents_created": 0,
            "alerts_sent": 0,
            "sla_violations": 0
        }
    
    def _initialize_patterns(self) -> List[FailurePattern]:
        """Initialize failure detection patterns."""
        return [
            FailurePattern(
                name="high_error_rate",
                description="Error rate exceeds threshold",
                detector=self._detect_high_error_rate,
                severity="critical",
                cooldown_minutes=10
            ),
            FailurePattern(
                name="performance_degradation",
                description="Significant performance degradation detected",
                detector=self._detect_performance_degradation,
                severity="high",
                cooldown_minutes=15
            ),
            FailurePattern(
                name="dependency_failure",
                description="External dependency failures",
                detector=self._detect_dependency_failure,
                severity="high",
                cooldown_minutes=5
            ),
            FailurePattern(
                name="cascading_failures",
                description="Cascading failures across services",
                detector=self._detect_cascading_failures,
                severity="critical",
                cooldown_minutes=20
            ),
            FailurePattern(
                name="resource_exhaustion",
                description="Resource exhaustion detected",
                detector=self._detect_resource_exhaustion,
                severity="high",
                cooldown_minutes=10
            ),
            FailurePattern(
                name="repeated_timeouts",
                description="Repeated timeout errors",
                detector=self._detect_repeated_timeouts,
                severity="medium",
                cooldown_minutes=5
            ),
            FailurePattern(
                name="invalid_responses",
                description="High rate of invalid responses",
                detector=self._detect_invalid_responses,
                severity="medium",
                cooldown_minutes=10
            )
        ]
    
    def _initialize_slas(self) -> List[PerformanceSLA]:
        """Initialize performance SLAs."""
        return [
            PerformanceSLA(
                metric="command_duration_seconds",
                threshold=5.0,
                comparison="less_than",
                window_seconds=300
            ),
            PerformanceSLA(
                metric="search_duration_seconds",
                threshold=5.0,
                comparison="less_than",
                window_seconds=300
            ),
            PerformanceSLA(
                metric="success_rate",
                threshold=0.95,
                comparison="greater_than",
                window_seconds=600
            ),
            PerformanceSLA(
                metric="dependency_install_seconds",
                threshold=120.0,
                comparison="less_than",
                window_seconds=300
            )
        ]
    
    def _detect_high_error_rate(self, context: Dict[str, Any]) -> bool:
        """Detect high error rate pattern."""
        recent_spans = list(self.span_buffer)
        if len(recent_spans) < 10:
            return False
        
        error_count = sum(1 for span in recent_spans[-50:] 
                         if span.get("status", {}).get("code") == "ERROR")
        error_rate = error_count / min(50, len(recent_spans))
        
        return error_rate > (1 - self.threshold)
    
    def _detect_performance_degradation(self, context: Dict[str, Any]) -> bool:
        """Detect performance degradation pattern."""
        if not self.performance_baselines:
            return False
        
        for operation, baseline in self.performance_baselines.items():
            recent_durations = [
                span.get("duration_ms", 0) 
                for span in self.span_buffer 
                if span.get("name") == operation
            ][-20:]
            
            if recent_durations and len(recent_durations) >= 5:
                avg_duration = statistics.mean(recent_durations)
                if avg_duration > baseline * 2:  # 2x slower than baseline
                    context["degraded_operation"] = operation
                    context["baseline_ms"] = baseline
                    context["current_ms"] = avg_duration
                    return True
        
        return False
    
    def _detect_dependency_failure(self, context: Dict[str, Any]) -> bool:
        """Detect external dependency failures."""
        dependency_errors = [
            span for span in list(self.span_buffer)[-30:]
            if "http" in span.get("name", "").lower() or 
               "grpc" in span.get("name", "").lower() or
               "database" in span.get("name", "").lower()
        ]
        
        if len(dependency_errors) >= 5:
            error_count = sum(1 for span in dependency_errors 
                             if span.get("status", {}).get("code") == "ERROR")
            if error_count >= 3:
                context["failed_dependencies"] = list(set(
                    span.get("name") for span in dependency_errors
                    if span.get("status", {}).get("code") == "ERROR"
                ))
                return True
        
        return False
    
    def _detect_cascading_failures(self, context: Dict[str, Any]) -> bool:
        """Detect cascading failures across services."""
        recent_errors = [
            span for span in list(self.span_buffer)[-50:]
            if span.get("status", {}).get("code") == "ERROR"
        ]
        
        if len(recent_errors) < 5:
            return False
        
        # Check for rapid error spread
        error_services = defaultdict(list)
        for span in recent_errors:
            service = span.get("service_name", "unknown")
            timestamp = span.get("timestamp", 0)
            error_services[service].append(timestamp)
        
        if len(error_services) >= 3:  # Errors in 3+ services
            # Check if errors started spreading rapidly
            first_errors = [min(timestamps) for timestamps in error_services.values()]
            if max(first_errors) - min(first_errors) < 30:  # Within 30 seconds
                context["affected_services"] = list(error_services.keys())
                return True
        
        return False
    
    def _detect_resource_exhaustion(self, context: Dict[str, Any]) -> bool:
        """Detect resource exhaustion patterns."""
        # Look for specific error messages
        exhaustion_keywords = [
            "out of memory", "memory exhausted", "too many open files",
            "connection pool exhausted", "queue full", "disk full"
        ]
        
        recent_spans = list(self.span_buffer)[-30:]
        exhaustion_errors = []
        
        for span in recent_spans:
            error_msg = str(span.get("events", [])).lower()
            for keyword in exhaustion_keywords:
                if keyword in error_msg:
                    exhaustion_errors.append({
                        "span": span.get("name"),
                        "resource": keyword,
                        "timestamp": span.get("timestamp")
                    })
        
        if len(exhaustion_errors) >= 2:
            context["resource_issues"] = exhaustion_errors
            return True
        
        return False
    
    def _detect_repeated_timeouts(self, context: Dict[str, Any]) -> bool:
        """Detect repeated timeout errors."""
        timeout_keywords = ["timeout", "timed out", "deadline exceeded"]
        
        recent_spans = list(self.span_buffer)[-30:]
        timeout_count = 0
        
        for span in recent_spans:
            if span.get("status", {}).get("code") == "ERROR":
                error_msg = str(span.get("events", [])).lower()
                if any(keyword in error_msg for keyword in timeout_keywords):
                    timeout_count += 1
        
        if timeout_count >= 3:
            context["timeout_count"] = timeout_count
            return True
        
        return False
    
    def _detect_invalid_responses(self, context: Dict[str, Any]) -> bool:
        """Detect high rate of invalid responses."""
        response_errors = [
            span for span in list(self.span_buffer)[-30:]
            if "parse" in span.get("name", "").lower() or
               "decode" in span.get("name", "").lower() or
               "invalid" in str(span.get("events", [])).lower()
        ]
        
        if len(response_errors) >= 3:
            context["invalid_response_count"] = len(response_errors)
            return True
        
        return False
    
    def process_span(self, span: Dict[str, Any]):
        """Process an individual span for failure detection."""
        self.span_buffer.append(span)
        self.stats["spans_processed"] += 1
        
        # Update performance baselines
        self._update_performance_baseline(span)
        
        # Check for failures
        for pattern in self.patterns:
            if self._should_check_pattern(pattern):
                context = {"span": span}
                if pattern.detector(context):
                    self._handle_failure_detection(pattern, context)
    
    def _update_performance_baseline(self, span: Dict[str, Any]):
        """Update performance baselines with successful operations."""
        if span.get("status", {}).get("code") != "ERROR":
            operation = span.get("name", "")
            duration_ms = span.get("duration_ms", 0)
            
            if operation and duration_ms > 0:
                self.baseline_window.append((operation, duration_ms))
                
                # Recalculate baseline every 100 spans
                if len(self.baseline_window) == 100:
                    operation_durations = defaultdict(list)
                    for op, dur in self.baseline_window:
                        operation_durations[op].append(dur)
                    
                    for op, durations in operation_durations.items():
                        if len(durations) >= 5:
                            # Use 75th percentile as baseline
                            sorted_durations = sorted(durations)
                            p75_index = int(len(sorted_durations) * 0.75)
                            self.performance_baselines[op] = sorted_durations[p75_index]
    
    def _should_check_pattern(self, pattern: FailurePattern) -> bool:
        """Check if pattern should be evaluated (cooldown logic)."""
        if pattern.name in self.pattern_cooldowns:
            cooldown_until = self.pattern_cooldowns[pattern.name]
            if datetime.now() < cooldown_until:
                return False
        return True
    
    def _handle_failure_detection(self, pattern: FailurePattern, context: Dict[str, Any]):
        """Handle detected failure pattern."""
        self.stats["failures_detected"] += 1
        
        # Create incident
        incident = self._create_incident(pattern, context)
        
        # Check if this is a new incident or escalation
        existing = self._find_related_incident(incident)
        if existing:
            self._escalate_incident(existing, incident)
        else:
            self._register_incident(incident)
            self._send_alert(incident)
        
        # Update cooldown
        cooldown_until = datetime.now() + timedelta(minutes=pattern.cooldown_minutes)
        self.pattern_cooldowns[pattern.name] = cooldown_until
    
    def _create_incident(self, pattern: FailurePattern, context: Dict[str, Any]) -> Incident:
        """Create an incident from detected pattern."""
        incident_id = f"{pattern.name}_{int(time.time())}"
        
        affected_spans = []
        if "span" in context:
            affected_spans.append(context["span"].get("span_id", "unknown"))
        
        return Incident(
            id=incident_id,
            pattern=pattern.name,
            severity=pattern.severity,
            timestamp=datetime.now(),
            details=context,
            affected_spans=affected_spans
        )
    
    def _find_related_incident(self, incident: Incident) -> Optional[Incident]:
        """Find related active incident."""
        for active_id, active_incident in self.active_incidents.items():
            if active_incident.pattern == incident.pattern:
                # Same pattern within reasonable time window
                if (incident.timestamp - active_incident.timestamp).total_seconds() < 3600:
                    return active_incident
        return None
    
    def _escalate_incident(self, existing: Incident, new: Incident):
        """Escalate existing incident."""
        logger.warning(f"Escalating incident {existing.id}: {new.pattern}")
        
        # Add affected spans
        existing.affected_spans.extend(new.affected_spans)
        
        # Update details
        existing.details["escalation_count"] = existing.details.get("escalation_count", 0) + 1
        existing.details["latest_detection"] = new.timestamp.isoformat()
        
        # Increase severity if needed
        severity_order = ["low", "medium", "high", "critical"]
        if severity_order.index(new.severity) > severity_order.index(existing.severity):
            existing.severity = new.severity
    
    def _register_incident(self, incident: Incident):
        """Register new incident."""
        self.active_incidents[incident.id] = incident
        self.incident_history.append(incident)
        self.stats["incidents_created"] += 1
        
        logger.error(f"New incident created: {incident.id} - {incident.pattern} ({incident.severity})")
    
    def _send_alert(self, incident: Incident):
        """Send alert for incident."""
        alert_data = {
            "incident_id": incident.id,
            "pattern": incident.pattern,
            "severity": incident.severity,
            "timestamp": incident.timestamp.isoformat(),
            "details": incident.details,
            "affected_spans": incident.affected_spans,
            "detector": "uvmgr-otel-failure-detector"
        }
        
        # Log alert
        logger.critical(f"ALERT: {incident.pattern} - {incident.severity}")
        logger.critical(f"Details: {json.dumps(alert_data, indent=2)}")
        
        # Send webhook if configured
        if self.webhook_url:
            try:
                self._send_webhook(alert_data)
                self.stats["alerts_sent"] += 1
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")
        
        # Generate incident report
        self._generate_incident_report(incident)
    
    def _send_webhook(self, data: Dict[str, Any]):
        """Send webhook notification."""
        req = urllib.request.Request(
            self.webhook_url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=10)
    
    def _generate_incident_report(self, incident: Incident):
        """Generate detailed incident report."""
        report_path = Path(f"incident_reports/incident_{incident.id}.md")
        report_path.parent.mkdir(exist_ok=True)
        
        report = f"""# Incident Report: {incident.id}

## Summary
- **Pattern**: {incident.pattern}
- **Severity**: {incident.severity}
- **Detected**: {incident.timestamp.isoformat()}
- **Duration**: {incident.duration or "Ongoing"}

## Details
{json.dumps(incident.details, indent=2)}

## Affected Components
- **Spans**: {len(incident.affected_spans)}
- **Span IDs**: {', '.join(incident.affected_spans[:10])}

## Recommended Actions
{self._get_recommended_actions(incident)}

## Detector Statistics
- **Spans Processed**: {self.stats['spans_processed']}
- **Failures Detected**: {self.stats['failures_detected']}
- **Active Incidents**: {len(self.active_incidents)}

---
Generated by uvmgr OTEL Failure Detector
"""
        
        report_path.write_text(report)
        logger.info(f"Incident report generated: {report_path}")
    
    def _get_recommended_actions(self, incident: Incident) -> str:
        """Get recommended actions for incident type."""
        actions = {
            "high_error_rate": """
1. Check application logs for error details
2. Review recent deployments or configuration changes
3. Verify external dependencies are healthy
4. Consider rolling back recent changes
5. Scale up resources if needed
""",
            "performance_degradation": """
1. Profile the degraded operations
2. Check database query performance
3. Review resource utilization (CPU, memory, I/O)
4. Look for lock contention or blocking operations
5. Consider caching or optimization strategies
""",
            "dependency_failure": """
1. Check status of external services
2. Verify network connectivity
3. Review authentication/authorization
4. Check for rate limiting or quota issues
5. Implement circuit breakers if not present
""",
            "cascading_failures": """
1. Isolate failing services immediately
2. Check service dependencies and communication
3. Review circuit breaker configurations
4. Implement bulkheads to prevent spread
5. Consider emergency traffic shedding
""",
            "resource_exhaustion": """
1. Check memory usage and garbage collection
2. Review connection pool settings
3. Look for resource leaks
4. Scale resources horizontally or vertically
5. Implement resource limits and quotas
""",
            "repeated_timeouts": """
1. Review timeout configurations
2. Check network latency and connectivity
3. Profile slow operations
4. Consider async processing for long operations
5. Implement retry with exponential backoff
""",
            "invalid_responses": """
1. Check API response formats
2. Verify data serialization/deserialization
3. Review recent API changes
4. Check for version mismatches
5. Implement response validation
"""
        }
        
        return actions.get(incident.pattern, "1. Investigate the issue\n2. Review logs and traces\n3. Contact on-call engineer")
    
    def check_sla_violations(self, metrics: Dict[str, float]):
        """Check for SLA violations."""
        for sla in self.slas:
            if sla.metric in metrics:
                value = metrics[sla.metric]
                
                # Store metric history
                self.metric_buffer[sla.metric].append((time.time(), value))
                
                # Calculate window average
                window_start = time.time() - sla.window_seconds
                window_values = [
                    v for t, v in self.metric_buffer[sla.metric]
                    if t >= window_start
                ]
                
                if window_values:
                    avg_value = statistics.mean(window_values)
                    
                    violated = False
                    if sla.comparison == "less_than" and avg_value >= sla.threshold:
                        violated = True
                    elif sla.comparison == "greater_than" and avg_value <= sla.threshold:
                        violated = True
                    
                    if violated:
                        self._handle_sla_violation(sla, avg_value)
    
    def _handle_sla_violation(self, sla: PerformanceSLA, actual_value: float):
        """Handle SLA violation."""
        self.stats["sla_violations"] += 1
        
        logger.error(f"SLA Violation: {sla.metric} = {actual_value:.2f} "
                    f"(threshold: {sla.comparison} {sla.threshold})")
        
        # Create SLA violation incident
        pattern = FailurePattern(
            name=f"sla_violation_{sla.metric}",
            description=f"SLA violation for {sla.metric}",
            detector=lambda ctx: True,  # Already detected
            severity="high",
            cooldown_minutes=30
        )
        
        context = {
            "sla_metric": sla.metric,
            "threshold": sla.threshold,
            "actual_value": actual_value,
            "comparison": sla.comparison,
            "window_seconds": sla.window_seconds
        }
        
        self._handle_failure_detection(pattern, context)
    
    def resolve_incident(self, incident_id: str):
        """Mark incident as resolved."""
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]
            incident.recovery_time = datetime.now()
            
            del self.active_incidents[incident_id]
            
            logger.info(f"Incident resolved: {incident_id} (duration: {incident.duration})")
            
            # Update incident report
            self._generate_incident_report(incident)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        recent_spans = list(self.span_buffer)
        error_count = sum(1 for span in recent_spans 
                         if span.get("status", {}).get("code") == "ERROR")
        
        success_rate = 1 - (error_count / len(recent_spans)) if recent_spans else 1.0
        
        return {
            "healthy": len(self.active_incidents) == 0 and success_rate >= self.threshold,
            "success_rate": success_rate,
            "active_incidents": len(self.active_incidents),
            "stats": self.stats,
            "performance_baselines": self.performance_baselines,
            "incidents": [
                {
                    "id": inc.id,
                    "pattern": inc.pattern,
                    "severity": inc.severity,
                    "duration": str(inc.duration) if inc.duration else "Ongoing"
                }
                for inc in self.active_incidents.values()
            ]
        }
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Starting OTEL failure detection monitor")
        
        while True:
            try:
                # Simulate fetching spans from OTEL collector
                # In production, this would query the actual OTEL backend
                
                # Check for incident recovery
                for incident_id, incident in list(self.active_incidents.items()):
                    # Auto-resolve incidents after no new detections for 30 minutes
                    if (datetime.now() - incident.timestamp).total_seconds() > 1800:
                        self.resolve_incident(incident_id)
                
                # Log status periodically
                if self.stats["spans_processed"] % 100 == 0:
                    status = self.get_health_status()
                    logger.info(f"Health Status: {json.dumps(status, indent=2)}")
                
                await asyncio.sleep(1)  # Check every second
                
            except KeyboardInterrupt:
                logger.info("Shutting down monitor")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)  # Back off on errors


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OTEL Failure Detection Monitor")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Success rate threshold (default: 0.95)"
    )
    parser.add_argument(
        "--webhook",
        type=str,
        help="Webhook URL for alerts"
    )
    parser.add_argument(
        "--otel-endpoint",
        type=str,
        default="http://localhost:4318",
        help="OTEL collector endpoint"
    )
    
    args = parser.parse_args()
    
    # Create detector
    detector = OTELFailureDetector(
        otel_endpoint=args.otel_endpoint,
        threshold=args.threshold,
        webhook_url=args.webhook
    )
    
    # Example: Simulate some spans for testing
    test_spans = [
        {
            "span_id": "test1",
            "name": "uvmgr.search.code",
            "status": {"code": "OK"},
            "duration_ms": 150,
            "timestamp": time.time()
        },
        {
            "span_id": "test2", 
            "name": "uvmgr.deps.install",
            "status": {"code": "ERROR"},
            "duration_ms": 5000,
            "timestamp": time.time(),
            "events": [{"name": "error", "attributes": {"message": "Connection timeout"}}]
        }
    ]
    
    for span in test_spans:
        detector.process_span(span)
    
    # Start monitoring
    await detector.monitor_loop()


if __name__ == "__main__":
    asyncio.run(main())