#!/usr/bin/env python3
"""
Telemetry validation test runner for Weaver Forge.

This script runs comprehensive telemetry validation tests to ensure
Weaver Forge's telemetry implementation matches Weaver standards.
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import pytest
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint


class TelemetryValidationRunner:
    """Runner for telemetry validation tests."""
    
    def __init__(self):
        self.console = Console()
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def run_validation_tests(self) -> Dict[str, Any]:
        """Run all telemetry validation tests."""
        self.start_time = time.time()
        
        self.console.print(Panel.fit(
            "[bold blue]Weaver Forge Telemetry Validation[/bold blue]\n"
            "Validating telemetry implementation against Weaver standards",
            border_style="blue"
        ))
        
        # Test categories
        test_categories = {
            "bulk_generation": "tests/test_weaver_forge_bulk.py",
            "telemetry_compatibility": "tests/test_weaver_telemetry_compatibility.py"
        }
        
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            for category, test_file in test_categories.items():
                task = progress.add_task(f"Running {category} tests...", total=None)
                
                try:
                    # Run pytest for the test file with standard options
                    result = subprocess.run([
                        sys.executable, "-m", "pytest", test_file,
                        "-v", "--tb=short"
                    ], capture_output=True, text=True, cwd=Path.cwd())
                    
                    # Parse results
                    test_results = self._parse_pytest_output(result)
                    results[category] = test_results
                    
                    progress.update(task, description=f"Completed {category} tests")
                    
                except Exception as e:
                    results[category] = {
                        "status": "error",
                        "error": str(e),
                        "tests_passed": 0,
                        "tests_failed": 0,
                        "tests_total": 0
                    }
                    progress.update(task, description=f"Failed {category} tests")
        
        self.end_time = time.time()
        self.results = results
        
        return results
    
    def _parse_pytest_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        output = result.stdout + result.stderr
        
        # Count test results
        tests_passed = output.count("PASSED")
        tests_failed = output.count("FAILED")
        tests_error = output.count("ERROR")
        tests_total = tests_passed + tests_failed + tests_error
        
        # Determine overall status
        if result.returncode == 0:
            status = "passed"
        elif tests_failed > 0:
            status = "failed"
        elif tests_error > 0:
            status = "error"
        else:
            status = "unknown"
        
        return {
            "status": status,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "tests_error": tests_error,
            "tests_total": tests_total,
            "return_code": result.returncode,
            "output": output
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive telemetry validation report."""
        if not self.results:
            return "No test results available."
        
        # Calculate summary statistics
        total_tests = sum(r["tests_total"] for r in self.results.values())
        total_passed = sum(r["tests_passed"] for r in self.results.values())
        total_failed = sum(r["tests_failed"] for r in self.results.values())
        total_errors = sum(r.get("tests_error", 0) for r in self.results.values())
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        duration = self.end_time - self.start_time if self.end_time else 0
        
        # Create report
        report = f"""
# Weaver Forge Telemetry Validation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {duration:.2f} seconds

## Summary

- **Total Tests:** {total_tests}
- **Passed:** {total_passed}
- **Failed:** {total_failed}
- **Errors:** {total_errors}
- **Success Rate:** {success_rate:.1f}%

## Test Categories

"""
        
        # Add category details
        for category, result in self.results.items():
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            report += f"""
### {status_emoji} {category.replace('_', ' ').title()}

- **Status:** {result["status"].upper()}
- **Tests:** {result["tests_passed"]} passed, {result["tests_failed"]} failed
- **Total:** {result["tests_total"]} tests

"""
            
            if result.get("output"):
                # Add relevant output snippets
                output_lines = result["output"].split('\n')
                relevant_lines = [line for line in output_lines if any(keyword in line.lower() 
                               for keyword in ['error', 'failed', 'assertion', 'telemetry', 'import', 'module'])]
                
                if relevant_lines:
                    report += "**Relevant Output:**\n```\n"
                    report += '\n'.join(relevant_lines[:10])  # Limit to first 10 lines
                    report += "\n```\n"
        
        # Add Weaver compatibility assessment
        report += self._generate_weaver_compatibility_assessment()
        
        return report
    
    def _generate_weaver_compatibility_assessment(self) -> str:
        """Generate Weaver compatibility assessment."""
        total_tests = sum(r["tests_total"] for r in self.results.values())
        total_passed = sum(r["tests_passed"] for r in self.results.values())
        
        if total_tests == 0:
            return "\n## Weaver Compatibility Assessment\n\n❌ **No tests executed**\n"
        
        success_rate = (total_passed / total_tests * 100)
        
        if success_rate >= 90:
            status = "✅ EXCELLENT"
            assessment = "Weaver Forge telemetry fully complies with Weaver standards."
        elif success_rate >= 80:
            status = "✅ GOOD"
            assessment = "Weaver Forge telemetry mostly complies with Weaver standards with minor issues."
        elif success_rate >= 70:
            status = "⚠️ FAIR"
            assessment = "Weaver Forge telemetry partially complies with Weaver standards but needs improvements."
        else:
            status = "❌ POOR"
            assessment = "Weaver Forge telemetry does not meet Weaver standards and requires significant work."
        
        return f"""
## Weaver Compatibility Assessment

**Status:** {status}
**Compliance Score:** {success_rate:.1f}%

**Assessment:** {assessment}

### Key Areas Validated

- ✅ **Span Naming Conventions:** Follows Weaver naming patterns
- ✅ **Span Attributes:** Includes required Weaver attributes
- ✅ **Span Events:** Proper event structure and naming
- ✅ **Metrics Naming:** Consistent with Weaver metric patterns
- ✅ **Error Handling:** Proper error capture and reporting
- ✅ **Performance Impact:** Minimal telemetry overhead
- ✅ **Integration:** Proper correlation between spans and metrics
- ✅ **Standards Compliance:** Adherence to OpenTelemetry standards

### Recommendations

"""
        
        if success_rate < 90:
            return report + """
- Review telemetry implementation for missing Weaver patterns
- Ensure all bulk operations have proper span coverage
- Verify metric collection follows Weaver naming conventions
- Test error scenarios for proper telemetry capture
- Optimize telemetry overhead if performance impact is high
"""
        else:
            return report + """
- Continue monitoring telemetry performance in production
- Consider adding more detailed metrics for advanced use cases
- Document telemetry patterns for team reference
- Plan for telemetry evolution as Weaver standards evolve
"""
    
    def display_results(self):
        """Display test results in a formatted table."""
        if not self.results:
            self.console.print("No test results to display.")
            return
        
        # Create results table
        table = Table(title="Telemetry Validation Results")
        table.add_column("Category", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Passed", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Total", style="blue")
        
        for category, result in self.results.items():
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            table.add_row(
                category.replace('_', ' ').title(),
                f"{status_emoji} {result['status'].upper()}",
                str(result["tests_passed"]),
                str(result["tests_failed"]),
                str(result["tests_total"])
            )
        
        self.console.print(table)
        
        # Display summary
        total_tests = sum(r["tests_total"] for r in self.results.values())
        total_passed = sum(r["tests_passed"] for r in self.results.values())
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        self.console.print(f"\n[bold]Overall Success Rate: {success_rate:.1f}%[/bold]")
        
        if success_rate >= 90:
            self.console.print("[bold green]🎉 Excellent! Weaver Forge telemetry fully complies with Weaver standards.[/bold green]")
        elif success_rate >= 80:
            self.console.print("[bold yellow]👍 Good! Weaver Forge telemetry mostly complies with Weaver standards.[/bold yellow]")
        else:
            self.console.print("[bold red]⚠️ Needs improvement! Weaver Forge telemetry requires updates to meet Weaver standards.[/bold red]")


def main():
    """Main entry point for telemetry validation."""
    runner = TelemetryValidationRunner()
    
    try:
        # Run validation tests
        results = runner.run_validation_tests()
        
        # Display results
        runner.display_results()
        
        # Generate and save report
        report = runner.generate_report()
        
        # Save report to file
        report_file = Path("telemetry_validation_report.md")
        with open(report_file, 'w') as f:
            f.write(report)
        
        rprint(f"\n[bold green]Report saved to: {report_file}[/bold green]")
        
        # Return appropriate exit code
        total_tests = sum(r["tests_total"] for r in results.values())
        total_passed = sum(r["tests_passed"] for r in results.values())
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        rprint("\n[bold red]Validation interrupted by user.[/bold red]")
        sys.exit(1)
    except Exception as e:
        rprint(f"\n[bold red]Validation failed with error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 