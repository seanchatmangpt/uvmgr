"""
uvmgr.ops.otel - OpenTelemetry Operations
========================================

Operations layer for OpenTelemetry instrumentation and validation.

This module provides the business logic for OTEL operations, including
validation, code generation, testing, and dashboard management.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import metric_counter, metric_histogram, span
from uvmgr.ops.weaver import check_registry

# Paths
WEAVER_PATH = Path(__file__).parent.parent.parent.parent / "tools" / "weaver"
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "weaver-forge" / "registry"


def validate_semantic_conventions(registry_path: Path = REGISTRY_PATH) -> Dict[str, Any]:
    """Validate semantic conventions using Weaver."""
    with span("otel.validate_semantic_conventions", registry=str(registry_path)):
        add_span_attributes(**{
            "otel.operation": "validate_semantic_conventions",
            "otel.registry_path": str(registry_path),
        })
        add_span_event("otel.validation.started", {"registry": str(registry_path)})
        
        start_time = time.time()
        
        try:
            result = check_registry(registry=registry_path, future=True)
            duration = time.time() - start_time
            
            add_span_event("otel.validation.completed", {
                "duration": duration,
                "success": result["status"] == "success"
            })
            metric_counter("otel.validation.executed")(1)
            metric_histogram("otel.validation.duration")(duration)
            
            return {
                "status": "success" if result["status"] == "success" else "failed",
                "duration": duration,
                "output": result.get("output", ""),
                "message": "Semantic conventions are valid!" if result["status"] == "success" else "Validation failed"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("otel.validation.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("otel.validation.failed")(1)
            raise


def generate_code_from_conventions(registry_path: Path = REGISTRY_PATH) -> Dict[str, Any]:
    """Generate code from semantic conventions."""
    with span("otel.generate_code", registry=str(registry_path)):
        add_span_attributes(**{
            "otel.operation": "generate_code",
            "otel.registry_path": str(registry_path),
        })
        add_span_event("otel.generation.started", {"registry": str(registry_path)})
        
        start_time = time.time()
        
        try:
            from uvmgr.core.process import run_logged
            
            # Run the validation script which handles generation
            script_path = registry_path.parent / "validate_semconv.py"
            result = run_logged(["python", str(script_path)], capture=True)
            duration = time.time() - start_time
            
            add_span_event("otel.generation.completed", {
                "duration": duration,
                "success": True
            })
            metric_counter("otel.generation.executed")(1)
            metric_histogram("otel.generation.duration")(duration)
            
            return {
                "status": "success",
                "duration": duration,
                "output": result,
                "message": "Code generation completed!"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("otel.generation.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("otel.generation.failed")(1)
            raise


def setup_dashboard_stack() -> Dict[str, Any]:
    """Setup the OTEL dashboard stack (Grafana, Prometheus, Jaeger)."""
    with span("otel.setup_dashboard"):
        add_span_attributes(**{
            "otel.operation": "setup_dashboard",
        })
        add_span_event("otel.dashboard.setup.started")
        
        start_time = time.time()
        
        try:
            from uvmgr.core.process import run_logged
            
            # Create docker-compose file for the stack
            compose_content = """
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true

volumes:
  grafana-storage:
"""
            
            # Create prometheus config
            prometheus_config = """
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'uvmgr'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
"""
            
            # Write files
            compose_file = Path("otel-dashboard.yml")
            compose_file.write_text(compose_content)
            
            prometheus_file = Path("prometheus.yml")
            prometheus_file.write_text(prometheus_config)
            
            # Start the stack
            run_logged(["docker-compose", "-f", str(compose_file), "up", "-d"], capture=True)
            
            duration = time.time() - start_time
            
            add_span_event("otel.dashboard.setup.completed", {
                "duration": duration,
                "compose_file": str(compose_file),
                "prometheus_file": str(prometheus_file)
            })
            metric_counter("otel.dashboard.setup.executed")(1)
            
            return {
                "status": "success",
                "duration": duration,
                "message": "OTEL dashboard stack started successfully",
                "urls": {
                    "grafana": "http://localhost:3000",
                    "prometheus": "http://localhost:9090",
                    "jaeger": "http://localhost:16686"
                }
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("otel.dashboard.setup.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("otel.dashboard.setup.failed")(1)
            raise


def start_dashboard_stack() -> Dict[str, Any]:
    """Start the OTEL dashboard stack."""
    with span("otel.start_dashboard"):
        add_span_attributes(**{
            "otel.operation": "start_dashboard",
        })
        add_span_event("otel.dashboard.start.started")
        
        start_time = time.time()
        
        try:
            from uvmgr.core.process import run_logged
            
            compose_file = Path("otel-dashboard.yml")
            if not compose_file.exists():
                raise FileNotFoundError("Dashboard stack not set up. Run setup first.")
            
            run_logged(["docker-compose", "-f", str(compose_file), "start"], capture=True)
            duration = time.time() - start_time
            
            add_span_event("otel.dashboard.start.completed", {"duration": duration})
            metric_counter("otel.dashboard.start.executed")(1)
            
            return {
                "status": "success",
                "duration": duration,
                "message": "OTEL dashboard stack started"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("otel.dashboard.start.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("otel.dashboard.start.failed")(1)
            raise


def stop_dashboard_stack() -> Dict[str, Any]:
    """Stop the OTEL dashboard stack."""
    with span("otel.stop_dashboard"):
        add_span_attributes(**{
            "otel.operation": "stop_dashboard",
        })
        add_span_event("otel.dashboard.stop.started")
        
        start_time = time.time()
        
        try:
            from uvmgr.core.process import run_logged
            
            compose_file = Path("otel-dashboard.yml")
            if not compose_file.exists():
                raise FileNotFoundError("Dashboard stack not found.")
            
            run_logged(["docker-compose", "-f", str(compose_file), "stop"], capture=True)
            duration = time.time() - start_time
            
            add_span_event("otel.dashboard.stop.completed", {"duration": duration})
            metric_counter("otel.dashboard.stop.executed")(1)
            
            return {
                "status": "success",
                "duration": duration,
                "message": "OTEL dashboard stack stopped"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("otel.dashboard.stop.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("otel.dashboard.stop.failed")(1)
            raise


def check_dashboard_status(grafana_url: str = "http://localhost:3000", 
                          prometheus_url: str = "http://localhost:9090",
                          jaeger_url: str = "http://localhost:16686") -> Dict[str, Any]:
    """Check the status of the OTEL dashboard stack."""
    with span("otel.check_dashboard_status"):
        add_span_attributes(**{
            "otel.operation": "check_dashboard_status",
            "otel.grafana_url": grafana_url,
            "otel.prometheus_url": prometheus_url,
            "otel.jaeger_url": jaeger_url,
        })
        add_span_event("otel.dashboard.status.started")
        
        start_time = time.time()
        
        try:
            import requests
            
            status = {
                "grafana": "unknown",
                "prometheus": "unknown",
                "jaeger": "unknown"
            }
            
            # Check Grafana
            try:
                response = requests.get(f"{grafana_url}/api/health", timeout=5)
                status["grafana"] = "running" if response.status_code == 200 else "error"
            except Exception:
                status["grafana"] = "stopped"
            
            # Check Prometheus
            try:
                response = requests.get(f"{prometheus_url}/-/healthy", timeout=5)
                status["prometheus"] = "running" if response.status_code == 200 else "error"
            except Exception:
                status["prometheus"] = "stopped"
            
            # Check Jaeger
            try:
                response = requests.get(f"{jaeger_url}/", timeout=5)
                status["jaeger"] = "running" if response.status_code == 200 else "error"
            except Exception:
                status["jaeger"] = "stopped"
            
            duration = time.time() - start_time
            
            add_span_event("otel.dashboard.status.completed", {
                "duration": duration,
                "status": status
            })
            metric_counter("otel.dashboard.status.executed")(1)
            
            return {
                "status": "success",
                "duration": duration,
                "services": status,
                "urls": {
                    "grafana": grafana_url,
                    "prometheus": prometheus_url,
                    "jaeger": jaeger_url
                }
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("otel.dashboard.status.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("otel.dashboard.status.failed")(1)
            raise


def test_otlp_connectivity(endpoint: str) -> Dict[str, Any]:
    """Test OTLP connectivity to the specified endpoint."""
    with span("otel.test_otlp_connectivity", endpoint=endpoint):
        add_span_attributes(**{
            "otel.operation": "test_otlp_connectivity",
            "otel.endpoint": endpoint,
        })
        add_span_event("otel.otlp.test.started", {"endpoint": endpoint})
        
        start_time = time.time()
        
        try:
            import requests
            
            # Test HTTP connectivity
            response = requests.get(endpoint, timeout=10)
            duration = time.time() - start_time
            
            success = response.status_code in [200, 404, 405]  # 404/405 are OK for OTLP endpoints
            
            add_span_event("otel.otlp.test.completed", {
                "duration": duration,
                "success": success,
                "status_code": response.status_code
            })
            metric_counter("otel.otlp.test.executed")(1)
            
            return {
                "status": "success" if success else "failed",
                "duration": duration,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "message": f"OTLP endpoint {endpoint} is reachable" if success else f"OTLP endpoint {endpoint} is not reachable"
            }
            
        except Exception as e:
            duration = time.time() - start_time
            add_span_event("otel.otlp.test.failed", {
                "error": str(e),
                "duration": duration
            })
            metric_counter("otel.otlp.test.failed")(1)
            
            return {
                "status": "failed",
                "duration": duration,
                "endpoint": endpoint,
                "error": str(e),
                "message": f"Failed to connect to OTLP endpoint {endpoint}: {e}"
            } 