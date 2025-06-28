# OTEL-Based Failure Detection and Incident Response

## Overview

The OTEL failure detection system provides real-time monitoring, anomaly detection, and automated incident response for uvmgr deployments. It continuously analyzes OpenTelemetry data to identify failure patterns and can automatically remediate common issues.

## Features

### 🔍 Failure Pattern Detection
- **High Error Rate**: Detects when error rates exceed thresholds
- **Performance Degradation**: Identifies operations running 2x slower than baseline
- **Dependency Failures**: Monitors external service health
- **Cascading Failures**: Detects failure spread across services
- **Resource Exhaustion**: Identifies memory, connection, and disk issues
- **Repeated Timeouts**: Tracks timeout patterns
- **Invalid Responses**: Monitors data serialization issues

### 🚨 Incident Management
- Automated incident creation with severity levels
- Incident escalation for recurring issues
- Cooldown periods to prevent alert fatigue
- Detailed incident reports with recommendations
- Automatic resolution tracking

### 🔧 Auto-Remediation
- Clear caches for memory issues
- Restart services for persistent errors
- Reset connection pools for network issues
- Adjust timeout configurations
- Performance optimization for degraded operations

### 📊 SLA Monitoring
- Track performance against defined SLAs
- Monitor success rates, latencies, and throughput
- Alert on SLA violations
- Historical trend analysis

## Quick Start

### 1. Basic Failure Detection

```bash
# Start the failure detector with default settings
python otel-failure-detector.py

# With custom success threshold
python otel-failure-detector.py --threshold 0.99

# With webhook notifications
python otel-failure-detector.py --webhook https://your-webhook.com/alerts
```

### 2. Integrated Monitoring with Dashboard

```bash
# Start the integrated monitor with web dashboard
python otel-monitor-integration.py --mode monitor

# Dashboard will be available at http://localhost:8080
```

### 3. Test Mode with Simulated Data

```bash
# Run with simulated failure scenarios
python otel-monitor-integration.py --mode test
```

## Configuration

### Failure Patterns

Configure detection patterns in `otel-failure-detector.py`:

```python
FailurePattern(
    name="custom_pattern",
    description="Description of what this detects",
    detector=custom_detector_function,
    severity="high",  # critical, high, medium, low
    cooldown_minutes=10
)
```

### Performance SLAs

Define SLAs for monitoring:

```python
PerformanceSLA(
    metric="operation_duration_seconds",
    threshold=5.0,
    comparison="less_than",  # or "greater_than"
    window_seconds=300  # 5-minute window
)
```

### Auto-Remediation Scripts

Add custom remediation logic:

```python
async def _remediate_custom_issue(self, incident: Incident) -> Dict[str, Any]:
    # Custom remediation logic
    actions = []
    
    # Perform remediation steps
    result = subprocess.run(["uvmgr", "custom", "fix"], capture_output=True)
    
    actions.append({
        "action": "custom_fix",
        "success": result.returncode == 0,
        "output": result.stdout
    })
    
    return {"success": True, "actions": actions}
```

## Integration with uvmgr

### 1. Docker Compose Setup

Add to your `docker-compose.external.yml`:

```yaml
services:
  failure-detector:
    build:
      context: .
      dockerfile: Dockerfile.external
    command: python otel-failure-detector.py
    environment:
      - OTEL_ENDPOINT=http://otel-collector:4318
    depends_on:
      - otel-collector
      - jaeger
    
  monitor-dashboard:
    build:
      context: .
      dockerfile: Dockerfile.external
    command: python otel-monitor-integration.py --mode monitor
    ports:
      - "8080:8080"
    depends_on:
      - failure-detector
      - otel-collector
```

### 2. Webhook Integration

Configure webhooks for external notifications:

```python
# Slack webhook example
webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Custom webhook handler
def send_custom_alert(incident_data):
    formatted_message = {
        "text": f"🚨 uvmgr Incident: {incident_data['pattern']}",
        "severity": incident_data['severity'],
        "details": incident_data['details']
    }
    requests.post(webhook_url, json=formatted_message)
```

### 3. Grafana Integration

Import the failure detection dashboard:

1. Open Grafana at http://localhost:3000
2. Import dashboard from `grafana-dashboards/failure-detection.json`
3. Configure alerts based on detector metrics

## Usage Examples

### Monitor Specific Operations

```bash
# Monitor search operations
python otel-failure-detector.py --filter "search.*"

# Monitor dependency operations
python otel-failure-detector.py --filter "deps.*"
```

### Custom Thresholds

```python
# Configure in code
detector = OTELFailureDetector(
    threshold=0.99,  # 99% success rate required
    performance_degradation_factor=1.5,  # Alert if 50% slower
    error_burst_window=60  # Look at last 60 seconds for bursts
)
```

### Incident Response Workflow

1. **Detection**: Pattern identified in OTEL data
2. **Incident Creation**: Automated incident with details
3. **Notification**: Webhook/dashboard alert sent
4. **Auto-Remediation**: Attempted if configured
5. **Verification**: Re-check after remediation
6. **Resolution**: Auto or manual resolution

## API Endpoints

The monitoring dashboard provides these REST endpoints:

- `GET /api/status` - Current system health status
- `GET /api/incidents` - List active incidents
- `POST /api/remediate/{incident_id}` - Trigger remediation
- `GET /api/history` - Remediation history
- `WS /ws` - WebSocket for real-time updates

## Best Practices

### 1. Baseline Establishment
- Run for 24-48 hours to establish performance baselines
- Adjust thresholds based on actual system behavior
- Review and tune detection patterns

### 2. Alert Fatigue Prevention
- Use appropriate cooldown periods
- Set realistic thresholds
- Group related alerts into incidents
- Implement alert routing based on severity

### 3. Remediation Safety
- Test remediation scripts in development first
- Implement gradual/canary rollouts
- Always include rollback procedures
- Monitor remediation effectiveness

### 4. Performance Impact
- The detector uses streaming processing
- Minimal memory footprint with circular buffers
- Async processing prevents blocking
- Configurable sampling rates for high-volume systems

## Troubleshooting

### No Incidents Detected
```bash
# Check OTEL collector connectivity
curl http://localhost:4318/v1/traces

# Verify spans are being received
python -c "from otel_failure_detector import OTELCollectorClient; ..."

# Lower threshold temporarily
python otel-failure-detector.py --threshold 0.90
```

### Too Many False Positives
```python
# Increase cooldown periods
pattern.cooldown_minutes = 30

# Adjust thresholds
detector.threshold = 0.98

# Require more samples
MIN_SPAN_COUNT = 50  # Don't detect until we have enough data
```

### Remediation Not Working
```bash
# Test remediation scripts manually
uvmgr cache clear
uvmgr serve restart

# Check permissions
ls -la ~/.uvmgr/

# Review remediation logs
tail -f incident_reports/remediation.log
```

## Metrics and Observability

The failure detector itself is instrumented with metrics:

- `failure_detector_spans_processed_total` - Total spans analyzed
- `failure_detector_incidents_created_total` - Incidents created
- `failure_detector_remediation_success_rate` - Remediation effectiveness
- `failure_detector_pattern_matches_total` - Matches per pattern
- `failure_detector_processing_duration_seconds` - Processing performance

## Future Enhancements

- [ ] Machine learning for anomaly detection
- [ ] Predictive failure analysis
- [ ] Multi-cluster support
- [ ] Integration with PagerDuty/OpsGenie
- [ ] Runbook automation
- [ ] Capacity planning recommendations
- [ ] Cost analysis for incidents

## Contributing

To add new failure patterns or remediation scripts:

1. Add pattern to `_initialize_patterns()`
2. Implement detector function
3. Add remediation to `AutoRemediationEngine`
4. Test with simulated data
5. Document the pattern and remediation

Remember: **Trust Only OTEL Data** - All detection and decisions are based on actual telemetry, never assumptions.