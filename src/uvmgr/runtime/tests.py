"""
Test execution runtime implementation.

This module handles the actual execution of test frameworks (pytest, coverage)
at the runtime layer. It manages subprocess calls and file I/O operations
for test execution and reporting.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import span
from uvmgr.core.process import run_logged


def execute_pytest(
    verbose: bool = False,
    parallel: bool = True,
    coverage: bool = True,
    fail_fast: bool = False,
    test_types: Optional[List[str]] = None,
    markers: Optional[List[str]] = None,
    generate_report: bool = True
) -> Dict[str, Any]:
    """
    Execute pytest with specified options.
    
    Parameters
    ----------
    verbose : bool
        Whether to run tests verbosely
    parallel : bool
        Whether to run tests in parallel
    coverage : bool
        Whether to collect coverage data
    fail_fast : bool
        Whether to stop on first failure
    test_types : Optional[List[str]]
        Test types to run
    markers : Optional[List[str]]
        Test markers to run
    generate_report : bool
        Whether to generate comprehensive report
        
    Returns
    -------
    Dict[str, Any]
        Test execution results
    """
    with span("runtime.pytest.execute"):
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
            
        if parallel:
            # Try to use pytest-xdist if available
            try:
                import subprocess
                result = subprocess.run(
                    ["python", "-c", "import xdist"],
                    capture_output=True,
                    check=True
                )
                cmd.extend(["-n", "auto"])
            except subprocess.CalledProcessError:
                # xdist not available, continue without parallel execution
                pass
                
        if fail_fast:
            cmd.append("-x")
            
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=xml", "--cov-report=term"])
            
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
                
        # Add JSON report for parsing results
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_report_path = f.name
            
        cmd.extend(["--json-report", f"--json-report-file={json_report_path}"])
        
        try:
            # Execute pytest
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse JSON report if available
            test_results = _parse_pytest_json_report(json_report_path)
            
            # Parse coverage if collected
            coverage_results = {}
            if coverage:
                coverage_results = _parse_coverage_report()
                
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "total_tests": test_results.get("total", 0),
                "passed": test_results.get("passed", 0),
                "failed": test_results.get("failed", 0),
                "skipped": test_results.get("skipped", 0),
                "coverage": coverage_results,
                "test_results": test_results
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out",
                "timeout": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up temporary JSON report
            try:
                Path(json_report_path).unlink(missing_ok=True)
            except:
                pass


def generate_coverage_report(
    format_type: str = "html",
    min_coverage: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate coverage reports using coverage.py.
    
    Parameters
    ----------
    format_type : str
        Format type (html, xml, term)
    min_coverage : Optional[float]
        Minimum coverage threshold
        
    Returns
    -------
    Dict[str, Any]
        Coverage report results
    """
    with span("runtime.coverage.report"):
        cmd = ["python", "-m", "coverage"]
        
        if format_type == "html":
            cmd.extend(["html", "--directory=reports/htmlcov"])
        elif format_type == "xml":
            cmd.extend(["xml", "-o", "reports/coverage.xml"])
        elif format_type == "term":
            cmd.append("report")
        else:
            cmd.append("report")
            
        if min_coverage:
            cmd.extend(["--fail-under", str(min_coverage)])
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse coverage percentage from output
            coverage_percentage = _extract_coverage_percentage(result.stdout)
            
            return {
                "success": True,
                "format": format_type,
                "percentage": coverage_percentage,
                "output": result.stdout,
                "meets_threshold": min_coverage is None or coverage_percentage >= min_coverage
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "output": e.stdout,
                "stderr": e.stderr
            }


def run_ci_pipeline(
    quick: bool = False,
    comprehensive: bool = True
) -> Dict[str, Any]:
    """
    Run CI verification pipeline.
    
    Parameters
    ----------
    quick : bool
        Whether to run quick checks only
    comprehensive : bool
        Whether to run comprehensive verification
        
    Returns
    -------
    Dict[str, Any]
        CI pipeline results
    """
    with span("runtime.ci.pipeline"):
        results = {
            "quick": quick,
            "comprehensive": comprehensive,
            "steps": [],
            "overall_success": True
        }
        
        # Step 1: Run linting (quick check)
        lint_result = _run_ci_step("lint", ["python", "-m", "ruff", "check", "."])
        results["steps"].append(lint_result)
        if not lint_result["success"]:
            results["overall_success"] = False
            
        # Step 2: Run type checking (quick check)
        mypy_result = _run_ci_step("type_check", ["python", "-m", "mypy", "src"])
        results["steps"].append(mypy_result)
        if not mypy_result["success"]:
            results["overall_success"] = False
            
        if not quick:
            # Step 3: Run full test suite
            test_result = execute_pytest(coverage=comprehensive)
            test_step = {
                "name": "test_suite",
                "success": test_result["success"],
                "details": test_result
            }
            results["steps"].append(test_step)
            if not test_result["success"]:
                results["overall_success"] = False
                
            results["test_results"] = test_result
            
            if comprehensive:
                # Step 4: Security checks
                security_result = _run_ci_step("security", ["python", "-m", "safety", "check"])
                results["steps"].append(security_result)
                # Don't fail CI for security warnings, just record them
                
        return results


def discover_test_files(
    path: Optional[Path] = None,
    pattern: str = "test_*.py"
) -> Dict[str, Any]:
    """
    Discover test files in the project.
    
    Parameters
    ----------
    path : Optional[Path]
        Path to search for tests
    pattern : str
        Test file pattern
        
    Returns
    -------
    Dict[str, Any]
        Test discovery results
    """
    with span("runtime.tests.discover"):
        search_path = path or Path(".")
        
        # Find test files
        test_files = list(search_path.rglob(pattern))
        
        # Categorize by type based on path
        test_types = {
            "unit": [],
            "integration": [],
            "e2e": []
        }
        
        for test_file in test_files:
            relative_path = test_file.relative_to(search_path)
            path_str = str(relative_path)
            
            if "integration" in path_str or "e2e" in path_str:
                if "e2e" in path_str:
                    test_types["e2e"].append(str(test_file))
                else:
                    test_types["integration"].append(str(test_file))
            else:
                test_types["unit"].append(str(test_file))
                
        return {
            "test_files": [str(f) for f in test_files],
            "test_types": test_types,
            "total_files": len(test_files)
        }


def validate_test_environment() -> Dict[str, Any]:
    """
    Validate that the test environment is properly configured.
    
    Returns
    -------
    Dict[str, Any]
        Environment validation results
    """
    with span("runtime.tests.validate_environment"):
        validation_results = {
            "valid": True,
            "dependencies_available": True,
            "issues": []
        }
        
        # Check pytest availability
        try:
            subprocess.run(
                ["python", "-m", "pytest", "--version"],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            validation_results["valid"] = False
            validation_results["dependencies_available"] = False
            validation_results["issues"].append("pytest not available")
            
        # Check coverage availability
        try:
            subprocess.run(
                ["python", "-m", "coverage", "--version"],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            validation_results["issues"].append("coverage not available")
            
        # Check test directory exists
        if not Path("tests").exists():
            validation_results["issues"].append("tests directory not found")
            
        return validation_results


# Helper functions

def _parse_pytest_json_report(json_path: str) -> Dict[str, Any]:
    """Parse pytest JSON report."""
    try:
        with open(json_path) as f:
            data = json.load(f)
            
        summary = data.get("summary", {})
        return {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "skipped": summary.get("skipped", 0),
            "errors": summary.get("error", 0)
        }
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0}


def _parse_coverage_report() -> Dict[str, Any]:
    """Parse coverage report from XML file."""
    try:
        import xml.etree.ElementTree as ET
        
        coverage_file = Path("reports/coverage.xml")
        if not coverage_file.exists():
            return {}
            
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        # Extract coverage percentage
        coverage_attr = root.get("line-rate", "0")
        percentage = float(coverage_attr) * 100
        
        return {
            "percentage": round(percentage, 2),
            "format": "xml"
        }
    except Exception:
        return {}


def _extract_coverage_percentage(output: str) -> float:
    """Extract coverage percentage from coverage output."""
    import re
    
    # Look for patterns like "TOTAL    100%"
    pattern = r"TOTAL\s+(\d+)%"
    match = re.search(pattern, output)
    if match:
        return float(match.group(1))
        
    # Look for patterns like "Total coverage: 95.5%"
    pattern = r"Total coverage:\s+(\d+(?:\.\d+)?)%"
    match = re.search(pattern, output)
    if match:
        return float(match.group(1))
        
    return 0.0


def _run_ci_step(name: str, cmd: List[str]) -> Dict[str, Any]:
    """Run a single CI step."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "name": name,
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "output": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "success": False,
            "error": "Step timed out"
        }
    except Exception as e:
        return {
            "name": name,
            "success": False,
            "error": str(e)
        }