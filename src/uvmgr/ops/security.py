"""
Security operations for vulnerability scanning and analysis.

Implements 80/20 security analysis: focuses on the 20% of checks that catch 
80% of common vulnerabilities.
"""

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from uvmgr.core.instrumentation import span, metric_counter
from uvmgr.core.semconv import SecurityAttributes, SecurityOperations


@span("security.comprehensive_scan")
def comprehensive_scan(
    project_path: Path,
    severity_threshold: str = "medium",
    audit_dependencies: bool = True,
    scan_code: bool = True,
    scan_secrets: bool = True,
    fix_mode: bool = False
) -> Dict[str, Any]:
    """
    Perform comprehensive security scanning.
    
    80/20 Approach: Focus on the most common and critical security issues.
    """
    start_time = time.time()
    results = {}
    
    with span("security.scan",
              **{SecurityAttributes.OPERATION: SecurityOperations.SCAN,
                 SecurityAttributes.PROJECT_PATH: str(project_path),
                 SecurityAttributes.SEVERITY_THRESHOLD: severity_threshold}) as current_span:
        
        # 1. Dependency vulnerabilities (highest impact - 40% of security issues)
        if audit_dependencies:
            results["dependencies"] = audit_dependencies_impl(project_path, fix_mode)
        
        # 2. Secret detection (high impact - 25% of security issues) 
        if scan_secrets:
            results["secrets"] = scan_secrets_impl(project_path)
        
        # 3. Code security analysis (medium impact - 20% of security issues)
        if scan_code:
            results["code"] = scan_code_security(project_path)
        
        # 4. Configuration security (lower impact - 15% of security issues)
        results["configuration"] = check_security_config_impl(project_path)
        
        # Record metrics
        scan_duration = time.time() - start_time
        total_issues = sum(len(v) if isinstance(v, list) else 0 for v in results.values())
        
        current_span.set_attributes({
            "scan.duration_seconds": scan_duration,
            "scan.total_issues": total_issues,
            "scan.categories_scanned": len(results)
        })
        
        metric_counter("security.scans_completed")(1, {
            "severity_threshold": severity_threshold,
            "total_issues": str(total_issues)
        })
    
    return results


@span("security.audit_dependencies") 
def audit_dependencies(
    project_path: Path,
    fix_vulnerabilities: bool = False
) -> Dict[str, Any]:
    """
    Audit project dependencies for known vulnerabilities.
    
    Uses safety and pip-audit for comprehensive vulnerability detection.
    """
    return audit_dependencies_impl(project_path, fix_vulnerabilities)


def audit_dependencies_impl(project_path: Path, fix_mode: bool = False) -> List[Dict[str, Any]]:
    """Implementation of dependency auditing."""
    vulnerabilities = []
    
    # Check if we have a requirements file or pyproject.toml
    requirements_files = [
        project_path / "requirements.txt",
        project_path / "pyproject.toml",
        project_path / "setup.py",
        project_path / "Pipfile"
    ]
    
    found_requirements = [f for f in requirements_files if f.exists()]
    
    if not found_requirements:
        return []
    
    try:
        # Use safety for vulnerability scanning
        safety_result = _run_safety_check(project_path)
        vulnerabilities.extend(safety_result)
        
        # Use pip-audit as backup/additional check
        pip_audit_result = _run_pip_audit(project_path)
        vulnerabilities.extend(pip_audit_result)
        
        # Remove duplicates
        seen = set()
        unique_vulns = []
        for vuln in vulnerabilities:
            key = (vuln.get("package"), vuln.get("id"))
            if key not in seen:
                seen.add(key)
                unique_vulns.append(vuln)
        
        # Attempt fixes if requested
        if fix_mode and unique_vulns:
            _attempt_vulnerability_fixes(project_path, unique_vulns)
        
        return unique_vulns
        
    except Exception as e:
        # Fallback to basic pattern matching
        return _basic_dependency_check(project_path)


def _run_safety_check(project_path: Path) -> List[Dict[str, Any]]:
    """Run safety check for vulnerability scanning."""
    vulnerabilities = []
    
    try:
        # Run safety check
        cmd = ["safety", "check", "--json"]
        result = subprocess.run(
            cmd, 
            cwd=project_path, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0 or result.stdout:
            # Parse safety JSON output
            try:
                safety_data = json.loads(result.stdout)
                for vuln in safety_data:
                    vulnerabilities.append({
                        "package": vuln.get("package_name"),
                        "version": vuln.get("installed_version"),
                        "id": vuln.get("vulnerability_id"),
                        "severity": _map_safety_severity(vuln.get("severity", "medium")),
                        "description": vuln.get("advisory"),
                        "fixed_in": vuln.get("fixed_in", "Unknown"),
                        "source": "safety"
                    })
            except json.JSONDecodeError:
                pass
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return vulnerabilities


def _run_pip_audit(project_path: Path) -> List[Dict[str, Any]]:
    """Run pip-audit for additional vulnerability detection."""
    vulnerabilities = []
    
    try:
        cmd = ["pip-audit", "--format=json"]
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                audit_data = json.loads(result.stdout)
                for vuln in audit_data.get("vulnerabilities", []):
                    vulnerabilities.append({
                        "package": vuln.get("package"),
                        "version": vuln.get("installed_version"),
                        "id": vuln.get("id"),
                        "severity": vuln.get("severity", "medium"),
                        "description": vuln.get("description"),
                        "fixed_in": vuln.get("fix_available", "Unknown"),
                        "source": "pip-audit"
                    })
            except json.JSONDecodeError:
                pass
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return vulnerabilities


def _basic_dependency_check(project_path: Path) -> List[Dict[str, Any]]:
    """Basic fallback dependency security check."""
    # Known vulnerable packages/versions (simplified for demo)
    known_vulnerabilities = {
        "urllib3": ["<1.26.5", "Security vulnerability in urllib3"],
        "requests": ["<2.20.0", "Security vulnerability in requests"],
        "jinja2": ["<2.11.3", "Template injection vulnerability"],
        "pyyaml": ["<5.4", "Code execution vulnerability"],
    }
    
    vulnerabilities = []
    
    # Check pyproject.toml
    pyproject_file = project_path / "pyproject.toml"
    if pyproject_file.exists():
        try:
            content = pyproject_file.read_text()
            for package, (version_constraint, description) in known_vulnerabilities.items():
                if package in content:
                    vulnerabilities.append({
                        "package": package,
                        "version": "unknown",
                        "id": f"BASIC-{package.upper()}",
                        "severity": "medium",
                        "description": description,
                        "fixed_in": version_constraint.replace("<", ">="),
                        "source": "basic_check"
                    })
        except Exception:
            pass
    
    return vulnerabilities


@span("security.scan_secrets")
def scan_secrets(
    project_path: Path,
    patterns_file: Optional[Path] = None,
    exclude_patterns: List[str] = None
) -> Dict[str, Any]:
    """
    Scan for exposed secrets and credentials.
    """
    return scan_secrets_impl(project_path, patterns_file, exclude_patterns or [])


def scan_secrets_impl(
    project_path: Path, 
    patterns_file: Optional[Path] = None,
    exclude_patterns: List[str] = None
) -> List[Dict[str, Any]]:
    """Implementation of secret scanning."""
    secrets = []
    exclude_patterns = exclude_patterns or [
        "*.pyc", "__pycache__", ".git", ".venv", "venv", "node_modules"
    ]
    
    # Common secret patterns (80/20 approach - most common secrets)
    secret_patterns = {
        "api_key": r"(?i)(api[_-]?key|apikey)[:=\s]['\"]?([a-zA-Z0-9]{20,})",
        "password": r"(?i)(password|passwd|pwd)[:=\s]['\"]?([^\\s'\"]{8,})",
        "token": r"(?i)(token|auth[_-]?token)[:=\s]['\"]?([a-zA-Z0-9]{20,})",
        "secret": r"(?i)(secret|secret[_-]?key)[:=\s]['\"]?([a-zA-Z0-9]{20,})",
        "aws_access_key": r"AKIA[0-9A-Z]{16}",
        "github_token": r"ghp_[a-zA-Z0-9]{36}",
        "jwt_token": r"eyJ[a-zA-Z0-9_-]*\\.eyJ[a-zA-Z0-9_-]*\\.[a-zA-Z0-9_-]*",
        "private_key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
    }
    
    # Load custom patterns if provided
    if patterns_file and patterns_file.exists():
        try:
            import yaml
            with open(patterns_file) as f:
                custom_patterns = yaml.safe_load(f)
                secret_patterns.update(custom_patterns)
        except Exception:
            pass
    
    # Scan files
    for file_path in _get_scannable_files(project_path, exclude_patterns):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\\n")
            
            for line_num, line in enumerate(lines, 1):
                for secret_type, pattern in secret_patterns.items():
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        secrets.append({
                            "file": str(file_path.relative_to(project_path)),
                            "line": line_num,
                            "type": secret_type,
                            "context": line.strip()[:100],
                            "match": match.group(0)[:20] + "..." if len(match.group(0)) > 20 else match.group(0)
                        })
        except Exception:
            continue
    
    return secrets


def scan_code_security(project_path: Path) -> List[Dict[str, Any]]:
    """
    Scan code for common security issues.
    
    80/20 approach: Focus on the most common code security patterns.
    """
    issues = []
    
    # Common security anti-patterns
    security_patterns = {
        "sql_injection": r"(?i)(execute|cursor\\.execute).*%.*%",
        "hardcoded_password": r"(?i)password\\s*=\\s*['\"][^'\"]{8,}['\"]",
        "eval_usage": r"\\beval\\s*\\(",
        "exec_usage": r"\\bexec\\s*\\(",
        "shell_injection": r"(?i)(os\\.system|subprocess\\.(call|run|Popen)).*\\+",
        "pickle_usage": r"\\bpickle\\.(loads?|dumps?)\\s*\\(",
        "yaml_unsafe": r"yaml\\.load\\s*\\([^,)]*\\)",
        "request_verify_false": r"requests\\.[a-z]+\\([^)]*verify\\s*=\\s*False",
    }
    
    python_files = list(project_path.rglob("*.py"))
    
    for file_path in python_files:
        if _should_skip_file(file_path):
            continue
            
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\\n")
            
            for line_num, line in enumerate(lines, 1):
                for issue_type, pattern in security_patterns.items():
                    if re.search(pattern, line):
                        issues.append({
                            "type": issue_type,
                            "severity": _get_severity_for_issue(issue_type),
                            "file": str(file_path.relative_to(project_path)),
                            "line": line_num,
                            "description": _get_description_for_issue(issue_type),
                            "context": line.strip()
                        })
        except Exception:
            continue
    
    return issues


@span("security.check_config")
def check_security_config(project_path: Path) -> Dict[str, Any]:
    """Check project security configuration."""
    return check_security_config_impl(project_path)


def check_security_config_impl(project_path: Path) -> Dict[str, Any]:
    """Implementation of security configuration checks."""
    issues = []
    
    # Check pyproject.toml security
    pyproject_file = project_path / "pyproject.toml"
    if pyproject_file.exists():
        issues.extend(_check_pyproject_security(pyproject_file))
    
    # Check requirements files
    for req_file in ["requirements.txt", "requirements-dev.txt"]:
        req_path = project_path / req_file
        if req_path.exists():
            issues.extend(_check_requirements_security(req_path))
    
    # Check CI configuration
    github_actions = project_path / ".github" / "workflows"
    if github_actions.exists():
        issues.extend(_check_ci_security(github_actions))
    
    return {"issues": issues}


def _check_pyproject_security(pyproject_file: Path) -> List[Dict[str, Any]]:
    """Check pyproject.toml for security issues."""
    issues = []
    
    try:
        content = pyproject_file.read_text()
        
        # Check for unpinned dependencies
        if "=" not in content and ">=" not in content:
            issues.append({
                "check": "dependency_pinning",
                "failed": True,
                "file": "pyproject.toml",
                "recommendation": "Pin dependency versions to prevent supply chain attacks"
            })
        
        # Check for dev dependencies in main
        if "[tool.setuptools]" in content and "include-package-data" in content:
            issues.append({
                "check": "package_data_security",
                "failed": False,
                "file": "pyproject.toml", 
                "recommendation": "Review included package data for sensitive files"
            })
            
    except Exception:
        pass
    
    return issues


def _check_requirements_security(req_file: Path) -> List[Dict[str, Any]]:
    """Check requirements file for security issues."""
    issues = []
    
    try:
        content = req_file.read_text()
        lines = content.strip().split("\\n")
        
        unpinned_count = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if "==" not in line and ">=" not in line:
                    unpinned_count += 1
        
        if unpinned_count > 0:
            issues.append({
                "check": "requirements_pinning",
                "failed": True,
                "file": str(req_file.name),
                "recommendation": f"Pin {unpinned_count} unpinned dependencies"
            })
            
    except Exception:
        pass
    
    return issues


def _check_ci_security(workflows_dir: Path) -> List[Dict[str, Any]]:
    """Check CI workflows for security issues."""
    issues = []
    
    for workflow_file in workflows_dir.rglob("*.yml"):
        try:
            content = workflow_file.read_text()
            
            # Check for secrets in workflow
            if "password" in content.lower() or "token" in content.lower():
                if "${{" not in content:  # Not using secrets properly
                    issues.append({
                        "check": "ci_secrets_exposure",
                        "failed": True,
                        "file": str(workflow_file.name),
                        "recommendation": "Use GitHub secrets instead of hardcoded credentials"
                    })
                    
        except Exception:
            continue
    
    return issues


# Helper functions

def _get_scannable_files(project_path: Path, exclude_patterns: List[str]) -> List[Path]:
    """Get list of files to scan, excluding patterns."""
    files = []
    
    for file_path in project_path.rglob("*"):
        if file_path.is_file():
            # Check if file should be excluded
            relative_path = str(file_path.relative_to(project_path))
            should_exclude = False
            
            for pattern in exclude_patterns:
                if pattern in relative_path:
                    should_exclude = True
                    break
            
            if not should_exclude and file_path.suffix in [".py", ".txt", ".yml", ".yaml", ".json", ".toml"]:
                files.append(file_path)
    
    return files


def _should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped during scanning."""
    skip_patterns = ["test_", "__pycache__", ".pyc", "venv", ".venv", ".git"]
    path_str = str(file_path)
    return any(pattern in path_str for pattern in skip_patterns)


def _get_severity_for_issue(issue_type: str) -> str:
    """Get severity level for security issue type."""
    high_severity = ["sql_injection", "eval_usage", "exec_usage", "shell_injection"]
    medium_severity = ["hardcoded_password", "pickle_usage", "yaml_unsafe"]
    
    if issue_type in high_severity:
        return "high"
    elif issue_type in medium_severity:
        return "medium"
    else:
        return "low"


def _get_description_for_issue(issue_type: str) -> str:
    """Get description for security issue type."""
    descriptions = {
        "sql_injection": "Potential SQL injection vulnerability",
        "hardcoded_password": "Hardcoded password found",
        "eval_usage": "Use of eval() can execute arbitrary code",
        "exec_usage": "Use of exec() can execute arbitrary code", 
        "shell_injection": "Potential shell injection vulnerability",
        "pickle_usage": "Pickle can execute arbitrary code when loading",
        "yaml_unsafe": "yaml.load() can execute arbitrary code",
        "request_verify_false": "SSL verification disabled"
    }
    return descriptions.get(issue_type, "Security issue detected")


def _map_safety_severity(safety_severity: str) -> str:
    """Map safety severity to our severity levels."""
    mapping = {
        "low": "low",
        "medium": "medium", 
        "high": "high",
        "critical": "critical"
    }
    return mapping.get(safety_severity.lower(), "medium")


def _attempt_vulnerability_fixes(project_path: Path, vulnerabilities: List[Dict[str, Any]]) -> None:
    """Attempt to automatically fix vulnerabilities."""
    # This would implement automatic fixes like updating requirements
    # For now, just log what would be fixed
    fixes_attempted = []
    
    for vuln in vulnerabilities:
        if vuln.get("fixed_in") and vuln.get("fixed_in") != "Unknown":
            fixes_attempted.append({
                "package": vuln.get("package"),
                "current": vuln.get("version"),
                "fix_version": vuln.get("fixed_in")
            })
    
    # In a real implementation, this would update requirements files
    # and run package updates


def format_sarif(results: Dict[str, Any]) -> str:
    """Format security results as SARIF JSON."""
    sarif = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "uvmgr-security",
                    "version": "1.0.0"
                }
            },
            "results": []
        }]
    }
    
    # Convert our results to SARIF format
    for category, issues in results.items():
        if isinstance(issues, list):
            for issue in issues:
                sarif_result = {
                    "ruleId": issue.get("type", "unknown"),
                    "level": _severity_to_sarif_level(issue.get("severity", "medium")),
                    "message": {"text": issue.get("description", "Security issue")},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": issue.get("file", "unknown")},
                            "region": {"startLine": issue.get("line", 1)}
                        }
                    }]
                }
                sarif["runs"][0]["results"].append(sarif_result)
    
    return json.dumps(sarif, indent=2)


def _severity_to_sarif_level(severity: str) -> str:
    """Convert severity to SARIF level."""
    mapping = {
        "low": "note",
        "medium": "warning", 
        "high": "error",
        "critical": "error"
    }
    return mapping.get(severity, "warning")