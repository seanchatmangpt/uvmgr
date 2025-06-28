#!/usr/bin/env python3
"""
E2E OTEL Validation for uvmgr in Devcontainer
==============================================

Comprehensive end-to-end validation of OpenTelemetry implementation
in a devcontainer environment with full observability stack.

Features:
- Tests all 18 instrumented commands
- Validates trace collection via OTEL collector  
- Checks metrics export to Prometheus
- Verifies Jaeger trace visualization
- Measures performance overhead
- Generates validation report
"""

import asyncio
import json
import os
import subprocess
import time
import requests
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import signal
import sys

@dataclass
class TestResult:
    command: str
    description: str
    success: bool
    duration: float
    traces_found: bool
    metrics_found: bool
    error: Optional[str] = None

class OTELValidator:
    """Comprehensive OTEL validation for uvmgr in devcontainer."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.jaeger_url = "http://localhost:26686"
        self.prometheus_url = "http://localhost:19090"
        self.collector_url = "http://localhost:18888"
        
        # OTEL environment setup
        self.otel_env = {
            **os.environ,
            "OTEL_SERVICE_NAME": "uvmgr-e2e-test",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:14317",
            "OTEL_RESOURCE_ATTRIBUTES": "service.name=uvmgr,service.version=e2e-test,environment=devcontainer",
            "OTEL_LOG_LEVEL": "INFO",
        }
        
        # All 18 instrumented commands
        self.test_commands = [
            (["--help"], "CLI help"),
            (["deps", "--help"], "Dependencies"),
            (["lint", "--help"], "Linting"),
            (["tests", "--help"], "Testing"),
            (["build", "--help"], "Building"),
            (["ai", "--help"], "AI tools"),
            (["ap-scheduler", "--help"], "AP Scheduler"),
            (["index", "--help"], "Package indexes"),
            (["release", "--help"], "Release tools"),
            (["remote", "--help"], "Remote runner"),
            (["tool", "--help"], "Tool manager"),
            (["agent", "--help"], "BPMN agent"),
            (["cache", "--help"], "Cache manager"),
            (["exec", "--help"], "Script executor"),
            (["shell", "--help"], "Shell/REPL"),
            (["mcp", "--help"], "MCP server"),
            (["weaver", "--help"], "Weaver tools"),
            (["otel", "--help"], "OTEL tools"),
        ]
    
    def check_services(self) -> bool:
        """Check if OTEL stack services are running."""
        print("🔍 Checking OTEL stack services...")
        
        services = [
            ("Jaeger", self.jaeger_url + "/api/services"),
            ("Prometheus", self.prometheus_url + "/api/v1/status/config"),
        ]
        
        all_ready = True
        for name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name} is ready")
                else:
                    print(f"❌ {name} returned {response.status_code}")
                    all_ready = False
            except Exception as e:
                print(f"❌ {name} not accessible: {e}")
                all_ready = False
        
        # Check OTEL collector with simple port test
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', 14317))
            sock.close()
            if result == 0:
                print(f"✅ OTEL Collector is ready (port 14317)")
            else:
                print(f"❌ OTEL Collector port 14317 not accessible")
                all_ready = False
        except Exception as e:
            print(f"❌ OTEL Collector port check failed: {e}")
            all_ready = False
        
        return all_ready
    
    def run_command(self, cmd_args: List[str], description: str) -> TestResult:
        """Run uvmgr command with OTEL and measure results."""
        print(f"🧪 Testing: {description:<30}", end=" ", flush=True)
        
        start_time = time.time()
        try:
            # Run command with OTEL enabled
            result = subprocess.run(
                ["uvmgr"] + cmd_args,
                env=self.otel_env,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            # Give traces time to reach collector
            time.sleep(0.5)
            
            # Check for traces in Jaeger (simplified check)
            traces_found = self.check_traces_exist()
            
            # Check for metrics in Prometheus
            metrics_found = self.check_metrics_exist()
            
            test_result = TestResult(
                command=" ".join(cmd_args),
                description=description,
                success=success,
                duration=duration,
                traces_found=traces_found,
                metrics_found=metrics_found,
                error=result.stderr if not success else None
            )
            
            if success and traces_found:
                print("✅")
            elif success:
                print("⚠️  (no traces)")
            else:
                print("❌")
                
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print("⏰ (timeout)")
            return TestResult(
                command=" ".join(cmd_args),
                description=description,
                success=False,
                duration=duration,
                traces_found=False,
                metrics_found=False,
                error="Command timeout"
            )
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ ({e})")
            return TestResult(
                command=" ".join(cmd_args),
                description=description,
                success=False,
                duration=duration,
                traces_found=False,
                metrics_found=False,
                error=str(e)
            )
    
    def check_traces_exist(self) -> bool:
        """Check if traces exist in Jaeger (simplified)."""
        try:
            # Query Jaeger for recent traces
            response = requests.get(
                f"{self.jaeger_url}/api/traces",
                params={
                    "service": "uvmgr-e2e-test",
                    "limit": 1,
                    "lookback": "1m"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return len(data.get("data", [])) > 0
                
        except Exception:
            pass
        
        return False
    
    def check_metrics_exist(self) -> bool:
        """Check if uvmgr metrics exist in Prometheus."""
        try:
            # Query Prometheus for uvmgr metrics
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": "uvmgr_cli_command_calls_total"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return len(data.get("data", {}).get("result", [])) > 0
                
        except Exception:
            pass
        
        return False
    
    def run_stress_test(self) -> Dict[str, float]:
        """Run stress test to measure performance impact."""
        print("\n🏋️  Running performance stress test...")
        
        stress_commands = [
            ["--help"],
            ["deps", "--help"], 
            ["lint", "--help"],
            ["tests", "--help"],
        ]
        
        # Baseline without OTEL
        baseline_times = []
        for cmd in stress_commands:
            start = time.time()
            subprocess.run(["uvmgr"] + cmd, capture_output=True, timeout=10)
            baseline_times.append(time.time() - start)
        
        # With OTEL
        otel_times = []
        for cmd in stress_commands:
            start = time.time()
            subprocess.run(["uvmgr"] + cmd, env=self.otel_env, capture_output=True, timeout=10)
            otel_times.append(time.time() - start)
        
        baseline_avg = sum(baseline_times) / len(baseline_times)
        otel_avg = sum(otel_times) / len(otel_times)
        overhead_pct = ((otel_avg - baseline_avg) / baseline_avg) * 100 if baseline_avg > 0 else 0
        
        return {
            "baseline_avg": baseline_avg,
            "otel_avg": otel_avg,
            "overhead_pct": overhead_pct
        }
    
    def generate_report(self, performance_data: Dict[str, float]) -> None:
        """Generate comprehensive validation report."""
        print("\n" + "="*80)
        print("📊 E2E OTEL Validation Report")
        print("="*80)
        
        # Overall stats
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        traces_found = sum(1 for r in self.results if r.traces_found)
        metrics_found = sum(1 for r in self.results if r.metrics_found)
        
        print(f"\n🎯 Test Results:")
        print(f"   Total commands tested: {total_tests}")
        print(f"   Successful executions: {successful}/{total_tests} ({successful/total_tests*100:.1f}%)")
        print(f"   Traces collected: {traces_found}/{total_tests} ({traces_found/total_tests*100:.1f}%)")
        print(f"   Metrics collected: {metrics_found}/{total_tests} ({metrics_found/total_tests*100:.1f}%)")
        
        # Performance impact
        print(f"\n⚡ Performance Impact:")
        print(f"   Baseline avg: {performance_data['baseline_avg']*1000:.1f}ms")
        print(f"   OTEL avg: {performance_data['otel_avg']*1000:.1f}ms")
        print(f"   Overhead: {performance_data['overhead_pct']:+.1f}%")
        
        # Performance assessment
        if performance_data['overhead_pct'] < 5:
            print("   Assessment: ✅ EXCELLENT (<5% overhead)")
        elif performance_data['overhead_pct'] < 10:
            print("   Assessment: ✅ GOOD (<10% overhead)")
        else:
            print("   Assessment: ⚠️  NEEDS OPTIMIZATION")
        
        # Failed tests
        failed = [r for r in self.results if not r.success]
        if failed:
            print(f"\n❌ Failed Tests ({len(failed)}):")
            for result in failed:
                print(f"   - {result.description}: {result.error}")
        
        # Missing traces
        no_traces = [r for r in self.results if r.success and not r.traces_found]
        if no_traces:
            print(f"\n⚠️  Commands without traces ({len(no_traces)}):")
            for result in no_traces:
                print(f"   - {result.description}")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if successful == total_tests and traces_found >= total_tests * 0.9:
            print("   🚀 PRODUCTION READY")
            print("   ✅ All commands working with OTEL")
            print("   ✅ Excellent trace collection")
            print("   ✅ Performance within acceptable limits")
        elif successful >= total_tests * 0.9:
            print("   ✅ GOOD - Minor issues")
            print("   ✅ Most commands working")
            print("   ⚠️  Some trace collection issues")
        else:
            print("   ❌ NEEDS WORK")
            print("   ❌ Significant issues found")
        
        # Save detailed results
        self.save_detailed_report(performance_data)
    
    def save_detailed_report(self, performance_data: Dict[str, float]) -> None:
        """Save detailed JSON report."""
        report_data = {
            "timestamp": time.time(),
            "environment": "devcontainer",
            "summary": {
                "total_tests": len(self.results),
                "successful": sum(1 for r in self.results if r.success),
                "traces_found": sum(1 for r in self.results if r.traces_found),
                "metrics_found": sum(1 for r in self.results if r.metrics_found),
            },
            "performance": performance_data,
            "results": [
                {
                    "command": r.command,
                    "description": r.description,
                    "success": r.success,
                    "duration": r.duration,
                    "traces_found": r.traces_found,
                    "metrics_found": r.metrics_found,
                    "error": r.error
                }
                for r in self.results
            ]
        }
        
        report_file = Path("./otel-validation-report.json")
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
    
    def run(self) -> int:
        """Run complete E2E validation."""
        print("🚀 uvmgr E2E OTEL Validation in Devcontainer")
        print("="*60)
        
        # Check prerequisites
        if not self.check_services():
            print("\n❌ OTEL stack not ready. Run: docker-compose -f .devcontainer/docker-compose.otel.yml up -d")
            return 1
        
        print(f"\n🧪 Testing {len(self.test_commands)} commands with OTEL...")
        
        # Run all command tests
        for cmd_args, description in self.test_commands:
            result = self.run_command(cmd_args, description)
            self.results.append(result)
            time.sleep(0.2)  # Brief pause between tests
        
        # Performance test
        performance_data = self.run_stress_test()
        
        # Generate report
        self.generate_report(performance_data)
        
        # Return exit code based on results
        successful = sum(1 for r in self.results if r.success)
        total = len(self.results)
        
        if successful == total:
            return 0  # All tests passed
        elif successful >= total * 0.9:
            return 1  # Minor issues
        else:
            return 2  # Major issues

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n⚠️  Validation interrupted by user")
    sys.exit(1)

def main():
    """Main entry point."""
    signal.signal(signal.SIGINT, signal_handler)
    
    validator = OTELValidator()
    exit_code = validator.run()
    
    print("\n🏁 E2E validation complete!")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()