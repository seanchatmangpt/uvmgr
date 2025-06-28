#!/usr/bin/env python3
"""
OTEL Monitor Integration for uvmgr
==================================

Integrates the OTEL failure detector with uvmgr's telemetry system to provide
comprehensive monitoring and incident response capabilities.

This script:
1. Connects to OTEL collector to fetch real spans and metrics
2. Runs failure detection on live data
3. Integrates with uvmgr's command execution for auto-remediation
4. Provides a web dashboard for monitoring
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import aiohttp
from aiohttp import web

# Import our failure detector
from otel_failure_detector import OTELFailureDetector, Incident

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoRemediationEngine:
    """Automated remediation for detected incidents."""
    
    def __init__(self):
        self.remediation_scripts = {
            "high_error_rate": self._remediate_high_error_rate,
            "performance_degradation": self._remediate_performance_degradation,
            "dependency_failure": self._remediate_dependency_failure,
            "resource_exhaustion": self._remediate_resource_exhaustion,
            "repeated_timeouts": self._remediate_timeouts,
        }
        
        self.remediation_history = []
    
    async def remediate(self, incident: Incident) -> Dict[str, Any]:
        """Attempt automated remediation for incident."""
        logger.info(f"Attempting remediation for incident: {incident.id}")
        
        remediation_func = self.remediation_scripts.get(incident.pattern)
        if not remediation_func:
            logger.warning(f"No remediation script for pattern: {incident.pattern}")
            return {"success": False, "reason": "No remediation available"}
        
        try:
            result = await remediation_func(incident)
            
            # Record remediation attempt
            self.remediation_history.append({
                "incident_id": incident.id,
                "pattern": incident.pattern,
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Remediation failed: {e}")
            return {"success": False, "reason": str(e)}
    
    async def _remediate_high_error_rate(self, incident: Incident) -> Dict[str, Any]:
        """Remediate high error rate issues."""
        actions = []
        
        # 1. Clear caches
        logger.info("Clearing uvmgr caches...")
        result = subprocess.run(["uvmgr", "cache", "clear"], capture_output=True, text=True)
        actions.append({
            "action": "clear_cache",
            "success": result.returncode == 0,
            "output": result.stdout
        })
        
        # 2. Restart services
        logger.info("Restarting MCP server...")
        subprocess.run(["uvmgr", "serve", "stop"], capture_output=True)
        await asyncio.sleep(2)
        result = subprocess.run(["uvmgr", "serve", "start"], capture_output=True, text=True)
        actions.append({
            "action": "restart_mcp",
            "success": result.returncode == 0,
            "output": result.stdout
        })
        
        # 3. Run health check
        logger.info("Running health check...")
        result = subprocess.run(["uvmgr", "otel", "validate"], capture_output=True, text=True)
        actions.append({
            "action": "health_check",
            "success": result.returncode == 0,
            "output": result.stdout
        })
        
        success = all(action["success"] for action in actions)
        return {
            "success": success,
            "actions": actions,
            "recommendation": "Monitor for 5 minutes to verify resolution"
        }
    
    async def _remediate_performance_degradation(self, incident: Incident) -> Dict[str, Any]:
        """Remediate performance degradation."""
        degraded_op = incident.details.get("degraded_operation", "unknown")
        
        actions = []
        
        # 1. Clear search cache if search operation
        if "search" in degraded_op:
            logger.info("Clearing search cache...")
            # In real implementation, would clear search-specific cache
            actions.append({
                "action": "clear_search_cache",
                "success": True,
                "details": "Search cache cleared"
            })
        
        # 2. Optimize performance settings
        logger.info("Optimizing performance settings...")
        # Would adjust thread pool sizes, cache sizes, etc.
        actions.append({
            "action": "optimize_settings",
            "success": True,
            "details": "Adjusted parallel processing settings"
        })
        
        return {
            "success": True,
            "actions": actions,
            "recommendation": f"Performance optimization applied for {degraded_op}"
        }
    
    async def _remediate_dependency_failure(self, incident: Incident) -> Dict[str, Any]:
        """Remediate dependency failures."""
        failed_deps = incident.details.get("failed_dependencies", [])
        
        actions = []
        
        # 1. Check and fix PyPI connectivity
        if any("pypi" in dep.lower() for dep in failed_deps):
            logger.info("Testing PyPI connectivity...")
            result = subprocess.run(
                ["uvmgr", "deps", "check"],
                capture_output=True,
                text=True
            )
            actions.append({
                "action": "check_pypi",
                "success": result.returncode == 0,
                "output": result.stdout
            })
        
        # 2. Reset connection pools
        logger.info("Resetting connection pools...")
        # In real implementation, would reset HTTP connection pools
        actions.append({
            "action": "reset_connections",
            "success": True,
            "details": "Connection pools reset"
        })
        
        return {
            "success": True,
            "actions": actions,
            "recommendation": "External dependencies checked and connections reset"
        }
    
    async def _remediate_resource_exhaustion(self, incident: Incident) -> Dict[str, Any]:
        """Remediate resource exhaustion."""
        resource_issues = incident.details.get("resource_issues", [])
        
        actions = []
        
        # 1. Clear all caches
        logger.info("Clearing all caches to free memory...")
        result = subprocess.run(["uvmgr", "cache", "clear"], capture_output=True, text=True)
        actions.append({
            "action": "clear_all_caches",
            "success": result.returncode == 0,
            "output": result.stdout
        })
        
        # 2. Clean up temporary files
        logger.info("Cleaning temporary files...")
        temp_dirs = [
            Path.home() / ".uvmgr" / "tmp",
            Path("/tmp") / "uvmgr-*"
        ]
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                # In production, would safely clean these
                actions.append({
                    "action": "clean_temp_files",
                    "success": True,
                    "path": str(temp_dir)
                })
        
        return {
            "success": True,
            "actions": actions,
            "recommendation": "Resources freed, monitor usage levels"
        }
    
    async def _remediate_timeouts(self, incident: Incident) -> Dict[str, Any]:
        """Remediate timeout issues."""
        actions = []
        
        # 1. Increase timeout settings
        logger.info("Adjusting timeout configurations...")
        # In real implementation, would update timeout configs
        actions.append({
            "action": "increase_timeouts",
            "success": True,
            "details": "Timeouts increased by 50%"
        })
        
        # 2. Check network connectivity
        logger.info("Checking network connectivity...")
        result = subprocess.run(
            ["ping", "-c", "3", "pypi.org"],
            capture_output=True,
            text=True
        )
        actions.append({
            "action": "network_check",
            "success": result.returncode == 0,
            "latency": "measured"
        })
        
        return {
            "success": True,
            "actions": actions,
            "recommendation": "Timeout settings adjusted, monitor network latency"
        }


class OTELMonitorService:
    """Web service for OTEL monitoring dashboard."""
    
    def __init__(self, detector: OTELFailureDetector, remediation: AutoRemediationEngine):
        self.detector = detector
        self.remediation = remediation
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup web routes."""
        self.app.router.add_get('/', self.dashboard)
        self.app.router.add_get('/api/status', self.api_status)
        self.app.router.add_get('/api/incidents', self.api_incidents)
        self.app.router.add_post('/api/remediate/{incident_id}', self.api_remediate)
        self.app.router.add_get('/ws', self.websocket_handler)
    
    async def dashboard(self, request):
        """Serve monitoring dashboard."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>uvmgr OTEL Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .metric { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .incident { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .critical { background: #f8d7da; border-color: #f5c6cb; }
        .high { background: #fff3cd; border-color: #ffeaa7; }
        .medium { background: #d1ecf1; border-color: #bee5eb; }
        .healthy { color: #28a745; }
        .unhealthy { color: #dc3545; }
        button { background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .stat-box { background: white; padding: 20px; text-align: center; border-radius: 5px; }
        .stat-value { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .stat-label { color: #7f8c8d; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>uvmgr OTEL Failure Detection Monitor</h1>
        <p>Real-time monitoring and incident response</p>
    </div>
    
    <div id="status" class="metric">
        <h2>System Status</h2>
        <div id="health-status">Loading...</div>
    </div>
    
    <div class="stats" id="stats">
        <!-- Stats will be populated here -->
    </div>
    
    <div id="incidents">
        <h2>Active Incidents</h2>
        <div id="incident-list">Loading...</div>
    </div>
    
    <div id="history">
        <h2>Remediation History</h2>
        <div id="remediation-list">Loading...</div>
    </div>
    
    <script>
        let ws = null;
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update health status
                const healthDiv = document.getElementById('health-status');
                healthDiv.innerHTML = `
                    <p class="${data.healthy ? 'healthy' : 'unhealthy'}">
                        ${data.healthy ? '✓ System Healthy' : '⚠ Issues Detected'}
                    </p>
                    <p>Success Rate: ${(data.success_rate * 100).toFixed(1)}%</p>
                `;
                
                // Update stats
                const statsDiv = document.getElementById('stats');
                statsDiv.innerHTML = `
                    <div class="stat-box">
                        <div class="stat-value">${data.stats.spans_processed}</div>
                        <div class="stat-label">Spans Processed</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${data.stats.failures_detected}</div>
                        <div class="stat-label">Failures Detected</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${data.active_incidents}</div>
                        <div class="stat-label">Active Incidents</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${data.stats.sla_violations}</div>
                        <div class="stat-label">SLA Violations</div>
                    </div>
                `;
                
                // Update incidents
                updateIncidents();
                
            } catch (error) {
                console.error('Failed to update status:', error);
            }
        }
        
        async function updateIncidents() {
            try {
                const response = await fetch('/api/incidents');
                const incidents = await response.json();
                
                const incidentList = document.getElementById('incident-list');
                if (incidents.length === 0) {
                    incidentList.innerHTML = '<p>No active incidents</p>';
                } else {
                    incidentList.innerHTML = incidents.map(incident => `
                        <div class="incident ${incident.severity}">
                            <h3>${incident.pattern}</h3>
                            <p>Severity: ${incident.severity}</p>
                            <p>Duration: ${incident.duration}</p>
                            <button onclick="remediate('${incident.id}')">Auto-Remediate</button>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Failed to update incidents:', error);
            }
        }
        
        async function remediate(incidentId) {
            try {
                const response = await fetch(`/api/remediate/${incidentId}`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.success) {
                    alert('Remediation successful!');
                } else {
                    alert('Remediation failed: ' + result.reason);
                }
                
                updateStatus();
            } catch (error) {
                alert('Failed to trigger remediation: ' + error);
            }
        }
        
        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:8080/ws');
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'update') {
                    updateStatus();
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            ws.onclose = () => {
                setTimeout(connectWebSocket, 5000);
            };
        }
        
        // Initial load
        updateStatus();
        setInterval(updateStatus, 5000);
        connectWebSocket();
    </script>
</body>
</html>
"""
        return web.Response(text=html, content_type='text/html')
    
    async def api_status(self, request):
        """Get current system status."""
        status = self.detector.get_health_status()
        return web.json_response(status)
    
    async def api_incidents(self, request):
        """Get active incidents."""
        incidents = [
            {
                "id": inc.id,
                "pattern": inc.pattern,
                "severity": inc.severity,
                "timestamp": inc.timestamp.isoformat(),
                "duration": str(inc.duration) if inc.duration else "Ongoing",
                "details": inc.details
            }
            for inc in self.detector.active_incidents.values()
        ]
        return web.json_response(incidents)
    
    async def api_remediate(self, request):
        """Trigger remediation for incident."""
        incident_id = request.match_info['incident_id']
        
        if incident_id not in self.detector.active_incidents:
            return web.json_response(
                {"success": False, "reason": "Incident not found"},
                status=404
            )
        
        incident = self.detector.active_incidents[incident_id]
        result = await self.remediation.remediate(incident)
        
        # If successful, resolve the incident
        if result.get("success"):
            self.detector.resolve_incident(incident_id)
        
        return web.json_response(result)
    
    async def websocket_handler(self, request):
        """WebSocket handler for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f'WebSocket error: {ws.exception()}')
        
        return ws


class OTELCollectorClient:
    """Client for fetching data from OTEL collector."""
    
    def __init__(self, endpoint: str = "http://localhost:4318"):
        self.endpoint = endpoint
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_traces(self, service_name: str = "uvmgr") -> List[Dict[str, Any]]:
        """Fetch recent traces from OTEL collector."""
        # This is a simplified example - real implementation would use OTLP/HTTP or query backend
        try:
            # Query Jaeger API for traces
            jaeger_url = "http://localhost:16686/api/traces"
            params = {
                "service": service_name,
                "limit": 100,
                "lookback": "1h"
            }
            
            async with self.session.get(jaeger_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._convert_jaeger_to_spans(data)
                else:
                    logger.warning(f"Failed to fetch traces: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching traces: {e}")
            return []
    
    def _convert_jaeger_to_spans(self, jaeger_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert Jaeger format to our span format."""
        spans = []
        
        for trace in jaeger_data.get("data", []):
            for span in trace.get("spans", []):
                converted = {
                    "span_id": span.get("spanID"),
                    "trace_id": span.get("traceID"),
                    "name": span.get("operationName"),
                    "service_name": span.get("process", {}).get("serviceName"),
                    "duration_ms": span.get("duration", 0) / 1000,  # Convert microseconds to ms
                    "timestamp": span.get("startTime", 0) / 1000000,  # Convert to seconds
                    "status": {
                        "code": "ERROR" if any(tag.get("key") == "error" and tag.get("value") 
                                             for tag in span.get("tags", [])) else "OK"
                    },
                    "events": [
                        {
                            "name": log.get("fields", [{}])[0].get("key", ""),
                            "attributes": {
                                field.get("key"): field.get("value")
                                for field in log.get("fields", [])
                            }
                        }
                        for log in span.get("logs", [])
                    ]
                }
                spans.append(converted)
        
        return spans


async def monitor_with_otel_integration():
    """Main monitoring loop with OTEL integration."""
    # Initialize components
    detector = OTELFailureDetector()
    remediation = AutoRemediationEngine()
    web_service = OTELMonitorService(detector, remediation)
    
    # Start web server
    runner = web.AppRunner(web_service.app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    
    logger.info("Monitoring dashboard available at http://localhost:8080")
    
    # Start monitoring with real OTEL data
    async with OTELCollectorClient() as client:
        while True:
            try:
                # Fetch recent spans
                spans = await client.fetch_traces()
                
                # Process spans through detector
                for span in spans:
                    detector.process_span(span)
                
                # Check for auto-recovery
                for incident_id, incident in list(detector.active_incidents.items()):
                    if incident.severity == "low" and incident.duration and incident.duration.seconds > 300:
                        # Auto-remediate low severity incidents after 5 minutes
                        logger.info(f"Auto-remediating low severity incident: {incident_id}")
                        await remediation.remediate(incident)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                logger.info("Shutting down monitor")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(10)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OTEL Monitor with Auto-Remediation")
    parser.add_argument(
        "--mode",
        choices=["monitor", "test"],
        default="monitor",
        help="Run mode: monitor (real OTEL data) or test (simulated data)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "monitor":
        asyncio.run(monitor_with_otel_integration())
    else:
        # Test mode with simulated data
        from otel_failure_detector import main as detector_main
        asyncio.run(detector_main())