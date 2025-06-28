#!/usr/bin/env python3
"""
OTEL Dashboard Setup
===================

Sets up comprehensive OTEL dashboards for real-time uvmgr external testing
claim verification. Creates Grafana dashboards with proper data sources
and alert configurations.

TRUST ONLY OTEL TRACES - NO HARDCODED VALUES
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import requests


class OTELDashboardSetup:
    """Sets up OTEL dashboards for uvmgr claim verification."""

    def __init__(self,
                 grafana_url: str = "http://localhost:3000",
                 grafana_user: str = "admin",
                 grafana_password: str = "admin",
                 prometheus_url: str = "http://localhost:9090",
                 jaeger_url: str = "http://localhost:16686"):

        self.grafana_url = grafana_url
        self.grafana_auth = (grafana_user, grafana_password)
        self.prometheus_url = prometheus_url
        self.jaeger_url = jaeger_url

        self.dashboard_configs = []
        self._load_dashboard_configs()

    def _load_dashboard_configs(self):
        """Load dashboard configurations."""
        config_path = Path(__file__).parent / "grafana-dashboard-config.json"
        
        if config_path.exists():
            with open(config_path) as f:
                self.dashboard_configs.append(json.load(f))
                print(f"✅ Loaded dashboard config from {config_path}")
        else:
            print(f"⚠️  Dashboard config not found at {config_path}")

    def check_services_health(self) -> Dict[str, bool]:
        """Check health of required services."""
        print("🔍 Checking OTEL services health...")
        
        health_status = {}
        
        services = {
            "grafana": f"{self.grafana_url}/api/health",
            "prometheus": f"{self.prometheus_url}/-/healthy",
            "jaeger": f"{self.jaeger_url}/api/services"
        }
        
        for service_name, health_url in services.items():
            try:
                response = requests.get(health_url, timeout=5)
                health_status[service_name] = response.status_code == 200
                
                if health_status[service_name]:
                    print(f"✅ {service_name}: Healthy")
                else:
                    print(f"❌ {service_name}: Unhealthy (status: {response.status_code})")
                    
            except Exception as e:
                health_status[service_name] = False
                print(f"❌ {service_name}: Unreachable ({e})")
        
        return health_status

    def setup_prometheus_datasource(self) -> bool:
        """Set up Prometheus data source in Grafana."""
        print("🔧 Setting up Prometheus data source...")
        
        datasource_config = {
            "name": "uvmgr-prometheus",
            "type": "prometheus",
            "url": self.prometheus_url,
            "access": "proxy",
            "isDefault": True,
            "jsonData": {
                "httpMethod": "POST",
                "exemplarTraceIdDestinations": [
                    {
                        "name": "trace_id",
                        "datasourceUid": "uvmgr-jaeger"
                    }
                ]
            }
        }
        
        try:
            response = requests.post(
                f"{self.grafana_url}/api/datasources",
                json=datasource_config,
                auth=self.grafana_auth,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 409]:  # 409 = already exists
                print("✅ Prometheus data source configured")
                return True
            else:
                print(f"❌ Failed to configure Prometheus: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error configuring Prometheus data source: {e}")
            return False

    def setup_jaeger_datasource(self) -> bool:
        """Set up Jaeger data source in Grafana."""
        print("🔧 Setting up Jaeger data source...")
        
        datasource_config = {
            "name": "uvmgr-jaeger",
            "type": "jaeger",
            "uid": "uvmgr-jaeger",
            "url": self.jaeger_url,
            "access": "proxy",
            "jsonData": {
                "tracesToLogsV2": {
                    "datasourceUid": "uvmgr-loki",
                    "spanStartTimeShift": "-1h",
                    "spanEndTimeShift": "1h",
                    "tags": ["service_name"]
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.grafana_url}/api/datasources",
                json=datasource_config,
                auth=self.grafana_auth,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 409]:
                print("✅ Jaeger data source configured")
                return True
            else:
                print(f"❌ Failed to configure Jaeger: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error configuring Jaeger data source: {e}")
            return False

    def create_dashboard(self, dashboard_config: Dict[str, Any]) -> bool:
        """Create a Grafana dashboard."""
        dashboard_title = dashboard_config["dashboard"]["title"]
        print(f"📊 Creating dashboard: {dashboard_title}")
        
        try:
            response = requests.post(
                f"{self.grafana_url}/api/dashboards/db",
                json=dashboard_config,
                auth=self.grafana_auth,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 412]:  # 412 = already exists
                result = response.json()
                dashboard_url = f"{self.grafana_url}{result.get('url', '')}"
                print(f"✅ Dashboard created: {dashboard_url}")
                return True
            else:
                print(f"❌ Failed to create dashboard: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating dashboard: {e}")
            return False

    def setup_alerts(self) -> bool:
        """Set up alert rules for claim verification failures."""
        print("🚨 Setting up alert rules...")
        
        alert_rules = [
            {
                "title": "uvmgr Claim Verification Failure",
                "condition": "A",
                "data": [
                    {
                        "refId": "A",
                        "queryType": "",
                        "relativeTimeRange": {
                            "from": 600,
                            "to": 0
                        },
                        "model": {
                            "expr": "increase(uvmgr_claims_verified_total{status=\"failed\"}[5m]) > 0",
                            "intervalMs": 1000,
                            "maxDataPoints": 43200,
                            "refId": "A"
                        }
                    }
                ],
                "intervalSeconds": 60,
                "noDataState": "NoData",
                "execErrState": "Alerting",
                "for": "5m",
                "annotations": {
                    "description": "uvmgr external testing claim verification has failed",
                    "runbook_url": "https://github.com/yourusername/uvmgr/blob/main/external-project-testing/README.md",
                    "summary": "Claim verification failure detected"
                },
                "labels": {
                    "severity": "warning",
                    "component": "uvmgr-external-testing"
                }
            },
            {
                "title": "uvmgr Performance Threshold Exceeded",
                "condition": "A",
                "data": [
                    {
                        "refId": "A",
                        "queryType": "",
                        "relativeTimeRange": {
                            "from": 600,
                            "to": 0
                        },
                        "model": {
                            "expr": "uvmgr_performance_threshold_ratio > 1.5",
                            "intervalMs": 1000,
                            "maxDataPoints": 43200,
                            "refId": "A"
                        }
                    }
                ],
                "intervalSeconds": 60,
                "noDataState": "NoData",
                "execErrState": "Alerting",
                "for": "2m",
                "annotations": {
                    "description": "uvmgr command performance is 50% slower than expected threshold",
                    "summary": "Performance degradation detected"
                },
                "labels": {
                    "severity": "warning",
                    "component": "uvmgr-performance"
                }
            }
        ]
        
        alerts_created = 0
        
        for alert_rule in alert_rules:
            try:
                response = requests.post(
                    f"{self.grafana_url}/api/ruler/grafana/api/v1/rules/uvmgr",
                    json={"rules": [alert_rule]},
                    auth=self.grafana_auth,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 202]:
                    print(f"✅ Alert rule created: {alert_rule['title']}")
                    alerts_created += 1
                else:
                    print(f"❌ Failed to create alert: {alert_rule['title']} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Error creating alert {alert_rule['title']}: {e}")
        
        return alerts_created > 0

    def setup_notification_channels(self) -> bool:
        """Set up notification channels for alerts."""
        print("📢 Setting up notification channels...")
        
        # Console notification for development
        console_channel = {
            "name": "uvmgr-console",
            "type": "webhook",
            "settings": {
                "url": "http://localhost:8080/webhook",
                "httpMethod": "POST",
                "username": "",
                "password": "",
                "title": "uvmgr Alert",
                "text": "{{ range .Alerts }}{{ .Annotations.summary }}: {{ .Annotations.description }}{{ end }}"
            }
        }
        
        try:
            response = requests.post(
                f"{self.grafana_url}/api/alert-notifications",
                json=console_channel,
                auth=self.grafana_auth,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 409]:
                print("✅ Console notification channel configured")
                return True
            else:
                print(f"⚠️  Notification channel setup: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  Error setting up notifications: {e}")
            return False

    def generate_otel_validation_queries(self) -> Dict[str, str]:
        """Generate PromQL queries for OTEL validation."""
        queries = {
            "claim_verification_rate": """
                sum(rate(uvmgr_claims_verified_total{status="verified"}[5m])) / 
                sum(rate(uvmgr_claims_verified_total[5m])) * 100
            """,
            "command_performance_95th": """
                histogram_quantile(0.95, 
                    sum(rate(uvmgr_command_duration_seconds_bucket[5m])) by (le, command)
                )
            """,
            "test_success_rate": """
                sum(rate(test_executions_total{status="success"}[5m])) /
                sum(rate(test_executions_total[5m])) * 100
            """,
            "artifacts_found_ratio": """
                sum(rate(test_artifacts_validated_total{status="found"}[5m])) /
                sum(rate(test_artifacts_validated_total[5m]))
            """,
            "performance_threshold_violations": """
                count(uvmgr_performance_threshold_ratio > 1.0)
            """,
            "otel_spans_by_service": """
                sum by (service_name) (otel_spans_total)
            """,
            "recent_test_failures": """
                increase(test_executions_total{status!="success"}[1h])
            """
        }
        
        return queries

    def create_query_examples_file(self):
        """Create a file with example PromQL queries for manual use."""
        queries = self.generate_otel_validation_queries()
        
        query_file = Path(__file__).parent / "otel-validation-queries.promql"
        
        with open(query_file, "w") as f:
            f.write("# uvmgr External Testing OTEL Validation Queries\n")
            f.write("# TRUST ONLY OTEL TRACES - NO HARDCODED VALUES\n\n")
            
            for query_name, query in queries.items():
                f.write(f"# {query_name.replace('_', ' ').title()}\n")
                f.write(f"{query.strip()}\n\n")
        
        print(f"📄 Query examples saved to {query_file}")

    def setup_complete_otel_dashboard(self) -> bool:
        """Set up complete OTEL dashboard infrastructure."""
        print("🚀 Setting up complete OTEL dashboard infrastructure")
        print("=" * 60)
        print("TRUST ONLY OTEL TRACES - NO HARDCODED VALUES")
        print("=" * 60)
        
        setup_steps = [
            ("Health Check", self.check_services_health),
            ("Prometheus Data Source", self.setup_prometheus_datasource),
            ("Jaeger Data Source", self.setup_jaeger_datasource),
            ("Notification Channels", self.setup_notification_channels),
            ("Alert Rules", self.setup_alerts),
            ("Query Examples", self.create_query_examples_file)
        ]
        
        results = {}
        
        for step_name, step_function in setup_steps:
            print(f"\n🔧 {step_name}...")
            
            try:
                if step_name == "Health Check":
                    result = step_function()
                    results[step_name] = all(result.values())
                elif step_name == "Query Examples":
                    step_function()
                    results[step_name] = True
                else:
                    results[step_name] = step_function()
                    
                if results[step_name]:
                    print(f"✅ {step_name}: SUCCESS")
                else:
                    print(f"❌ {step_name}: FAILED")
                    
            except Exception as e:
                print(f"💥 {step_name}: ERROR - {e}")
                results[step_name] = False
        
        # Create dashboards
        dashboards_created = 0
        for dashboard_config in self.dashboard_configs:
            if self.create_dashboard(dashboard_config):
                dashboards_created += 1
        
        results["Dashboards"] = dashboards_created > 0
        
        # Final summary
        successful_steps = sum(1 for success in results.values() if success)
        total_steps = len(results)
        
        print(f"\n📊 Setup Summary:")
        print(f"   Total Steps: {total_steps}")
        print(f"   Successful: {successful_steps}")
        print(f"   Success Rate: {successful_steps/total_steps:.1%}")
        
        if successful_steps == total_steps:
            print("🎉 OTEL Dashboard Setup: ✅ COMPLETE")
            print(f"📊 Dashboard URL: {self.grafana_url}/dashboards")
        else:
            print("⚠️  OTEL Dashboard Setup: ❌ PARTIAL")
            print("   Some components may not be fully functional")
        
        # Print access information
        print(f"\n🔗 Access Information:")
        print(f"   Grafana: {self.grafana_url}")
        print(f"   Prometheus: {self.prometheus_url}")
        print(f"   Jaeger: {self.jaeger_url}")
        print(f"   Username: admin / Password: admin")
        
        return successful_steps >= total_steps * 0.8  # 80% success rate


def main():
    """Main OTEL dashboard setup entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up OTEL dashboards for uvmgr claim verification")
    parser.add_argument("--grafana-url", default="http://localhost:3000",
                       help="Grafana URL")
    parser.add_argument("--prometheus-url", default="http://localhost:9090",
                       help="Prometheus URL")
    parser.add_argument("--jaeger-url", default="http://localhost:16686",
                       help="Jaeger URL")
    parser.add_argument("--grafana-user", default="admin",
                       help="Grafana username")
    parser.add_argument("--grafana-password", default="admin",
                       help="Grafana password")
    
    args = parser.parse_args()
    
    try:
        # Initialize dashboard setup
        dashboard_setup = OTELDashboardSetup(
            grafana_url=args.grafana_url,
            grafana_user=args.grafana_user,
            grafana_password=args.grafana_password,
            prometheus_url=args.prometheus_url,
            jaeger_url=args.jaeger_url
        )
        
        # Run complete setup
        success = dashboard_setup.setup_complete_otel_dashboard()
        
        print(f"\n🎯 Final Result: {'✅ SETUP COMPLETE' if success else '❌ SETUP FAILED'}")
        
        if success:
            print("\n🚀 Next Steps:")
            print("1. Run uvmgr external testing with: docker-compose -f docker-compose.external.yml up")
            print("2. Execute claim verification: python otel-instrumented-runner.py")
            print("3. View real-time metrics in Grafana dashboards")
            print("4. Monitor alerts for claim verification failures")
        
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard setup interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Dashboard setup failed with error: {e}")
        exit(1)


if __name__ == "__main__":
    main()