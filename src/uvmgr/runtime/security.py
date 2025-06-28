"""
uvmgr.runtime.security
---------------------
Runtime layer for security scanning and vulnerability management.

This module provides the runtime implementation for security operations,
integrating with external security tools like safety, bandit, and pip-audit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.semconv import SecurityAttributes, SecurityOperations
from uvmgr.core.shell import colour
from uvmgr.core.telemetry import span


def run_comprehensive_scan(
    project_path: Path,
    severity_threshold: str = "medium",
    audit_dependencies: bool = True,
    scan_code: bool = True,
    scan_secrets: bool = True,
    fix_mode: bool = False
) -> Dict[str, Any]:
    """
    Run comprehensive security scan using multiple tools.
    
    Args:
        project_path: Path to the project to scan
        severity_threshold: Minimum severity level to report
        audit_dependencies: Whether to audit dependencies for vulnerabilities
        scan_code: Whether to scan code for security issues
        scan_secrets: Whether to scan for exposed secrets
        fix_mode: Whether to attempt automatic fixes
        
    Returns:
        Dictionary with comprehensive scan results
    """
    with span("security.comprehensive_scan", project_path=str(project_path)):
        add_span_attributes(**{
            SecurityAttributes.OPERATION: SecurityOperations.SCAN,
            SecurityAttributes.PROJECT_PATH: str(project_path),
            SecurityAttributes.SEVERITY_THRESHOLD: severity_threshold,
            SecurityAttributes.SCAN_TYPE: "comprehensive",
        })
        add_span_event("security.scan.started", {
            "path": str(project_path),
            "severity_threshold": severity_threshold,
            "fix_mode": fix_mode
        })
        
        results = {}
        total_issues = 0
        
        try:
            # 1. Dependency vulnerability audit
            if audit_dependencies:
                results["dependencies"] = run_dependency_audit(project_path, fix_mode)
                total_issues += len(results["dependencies"])
            
            # 2. Code security scanning with bandit
            if scan_code:
                results["code"] = run_code_security_scan(project_path)
                total_issues += len(results["code"])
            
            # 3. Secret detection
            if scan_secrets:
                results["secrets"] = run_secret_scan(project_path)
                total_issues += len(results["secrets"])
            
            # 4. Configuration security check
            results["configuration"] = run_config_security_check(project_path)
            total_issues += len(results["configuration"].get("issues", []))
            
            add_span_attributes(**{
                SecurityAttributes.VULNERABILITY_COUNT: total_issues,
                SecurityAttributes.ISSUES_FOUND: total_issues,
            })
            add_span_event("security.scan.completed", {
                "total_issues": total_issues,
                "success": True
            })
            
            colour(f"✅ Security scan completed: {total_issues} issues found", "cyan")
            return results
            
        except Exception as e:
            add_span_event("security.scan.failed", {"error": str(e)})
            colour(f"❌ Security scan failed: {e}", "red")
            raise


def run_dependency_audit(project_path: Path, fix_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Run dependency vulnerability audit using safety and pip-audit.
    
    Args:
        project_path: Path to the project
        fix_mode: Whether to attempt fixes
        
    Returns:
        List of vulnerability dictionaries
    """
    with span("security.dependency_audit", project_path=str(project_path)):
        add_span_attributes(**{
            SecurityAttributes.OPERATION: SecurityOperations.AUDIT,
            SecurityAttributes.PROJECT_PATH: str(project_path),
        })
        add_span_event("security.audit.started", {"fix_mode": fix_mode})
        
        vulnerabilities = []
        
        try:
            # Try safety first (most comprehensive)
            safety_vulns = _run_safety_audit(project_path)
            vulnerabilities.extend(safety_vulns)
            
            # Try pip-audit as backup/supplement
            pip_audit_vulns = _run_pip_audit(project_path)
            vulnerabilities.extend(pip_audit_vulns)
            
            # Remove duplicates
            unique_vulns = _deduplicate_vulnerabilities(vulnerabilities)
            
            add_span_attributes(**{
                SecurityAttributes.VULNERABILITY_COUNT: len(unique_vulns),
            })
            add_span_event("security.audit.completed", {
                "vulnerabilities_found": len(unique_vulns),
                "tools_used": ["safety", "pip-audit"]
            })
            
            if unique_vulns:
                colour(f"⚠️  Found {len(unique_vulns)} dependency vulnerabilities", "yellow")
            else:
                colour("✅ No dependency vulnerabilities found", "green")
                
            return unique_vulns
            
        except Exception as e:
            add_span_event("security.audit.failed", {"error": str(e)})
            colour(f"❌ Dependency audit failed: {e}", "red")
            return []


def run_code_security_scan(project_path: Path) -> List[Dict[str, Any]]:
    """
    Run code security scan using bandit.
    
    Args:
        project_path: Path to the project
        
    Returns:
        List of code security issues
    """
    with span("security.code_scan", project_path=str(project_path)):
        add_span_attributes(**{
            SecurityAttributes.OPERATION: SecurityOperations.CODE,
            SecurityAttributes.PROJECT_PATH: str(project_path),
        })
        add_span_event("security.code_scan.started", {})
        
        try:
            # Run bandit for Python code security
            issues = _run_bandit_scan(project_path)
            
            add_span_attributes(**{
                SecurityAttributes.ISSUES_FOUND: len(issues),
            })
            add_span_event("security.code_scan.completed", {
                "issues_found": len(issues)
            })
            
            if issues:
                colour(f"⚠️  Found {len(issues)} code security issues", "yellow")
            else:
                colour("✅ No code security issues found", "green")
                
            return issues
            
        except Exception as e:
            add_span_event("security.code_scan.failed", {"error": str(e)})
            colour(f"❌ Code security scan failed: {e}", "red")
            return []


def run_secret_scan(project_path: Path) -> List[Dict[str, Any]]:
    """
    Run secret detection scan.
    
    Args:
        project_path: Path to the project
        
    Returns:
        List of potential secrets found
    """
    with span("security.secret_scan", project_path=str(project_path)):
        add_span_attributes(**{
            SecurityAttributes.OPERATION: SecurityOperations.SECRETS,
            SecurityAttributes.PROJECT_PATH: str(project_path),
        })
        add_span_event("security.secret_scan.started", {})
        
        try:
            # Try detect-secrets if available, otherwise use basic patterns
            secrets = _run_detect_secrets(project_path)
            if not secrets:
                # Fallback to basic pattern matching
                from uvmgr.ops.security import scan_secrets_impl
                secrets = scan_secrets_impl(project_path)
            
            add_span_attributes(**{
                SecurityAttributes.ISSUES_FOUND: len(secrets),
            })
            add_span_event("security.secret_scan.completed", {
                "secrets_found": len(secrets)
            })
            
            if secrets:
                colour(f"⚠️  Found {len(secrets)} potential secrets", "yellow")
            else:
                colour("✅ No secrets detected", "green")
                
            return secrets
            
        except Exception as e:
            add_span_event("security.secret_scan.failed", {"error": str(e)})
            colour(f"❌ Secret scan failed: {e}", "red")
            return []


def run_config_security_check(project_path: Path) -> Dict[str, Any]:
    """
    Run security configuration check.
    
    Args:
        project_path: Path to the project
        
    Returns:
        Dictionary with configuration security results
    """
    with span("security.config_check", project_path=str(project_path)):
        add_span_attributes(**{
            SecurityAttributes.OPERATION: SecurityOperations.CONFIG,
            SecurityAttributes.PROJECT_PATH: str(project_path),
        })
        add_span_event("security.config_check.started", {})
        
        try:
            # Use the operations implementation
            from uvmgr.ops.security import check_security_config_impl
            results = check_security_config_impl(project_path)
            
            issues_count = len(results.get("issues", []))
            add_span_attributes(**{
                SecurityAttributes.ISSUES_FOUND: issues_count,
            })
            add_span_event("security.config_check.completed", {
                "issues_found": issues_count
            })
            
            if issues_count > 0:
                colour(f"⚠️  Found {issues_count} configuration security issues", "yellow")
            else:
                colour("✅ Security configuration looks good", "green")
                
            return results
            
        except Exception as e:
            add_span_event("security.config_check.failed", {"error": str(e)})
            colour(f"❌ Configuration security check failed: {e}", "red")
            return {"issues": []}


# Private helper functions

def _run_safety_audit(project_path: Path) -> List[Dict[str, Any]]:
    """Run safety audit for dependency vulnerabilities."""
    vulnerabilities = []
    
    try:
        # Run safety check with JSON output
        cmd = [sys.executable, "-m", "safety", "check", "--json", "--output", "json"]
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Safety returns exit code 64 for vulnerabilities found, which is not an error
        if result.stdout:
            try:
                safety_data = json.loads(result.stdout)
                for vuln in safety_data:
                    vulnerabilities.append({
                        "package": vuln.get("package_name", "unknown"),
                        "version": vuln.get("installed_version", "unknown"),
                        "id": vuln.get("vulnerability_id", "unknown"),
                        "severity": _map_safety_severity(vuln.get("severity", "medium")),
                        "description": vuln.get("advisory", "No description"),
                        "fixed_in": vuln.get("fixed_in", "Unknown"),
                        "source": "safety"
                    })
            except json.JSONDecodeError:
                colour("⚠️  Safety returned invalid JSON", "yellow")
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        colour("⚠️  Safety tool not available or timed out", "yellow")
    except Exception as e:
        colour(f"⚠️  Safety scan error: {e}", "yellow")
    
    return vulnerabilities


def _run_pip_audit(project_path: Path) -> List[Dict[str, Any]]:
    """Run pip-audit for dependency vulnerabilities."""
    vulnerabilities = []
    
    try:
        cmd = [sys.executable, "-m", "pip_audit", "--format=json"]
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                audit_data = json.loads(result.stdout)
                for vuln in audit_data.get("vulnerabilities", []):
                    vulnerabilities.append({
                        "package": vuln.get("package", "unknown"),
                        "version": vuln.get("installed_version", "unknown"),
                        "id": vuln.get("id", "unknown"),
                        "severity": vuln.get("severity", "medium"),
                        "description": vuln.get("description", "No description"),
                        "fixed_in": vuln.get("fix_available", "Unknown"),
                        "source": "pip-audit"
                    })
            except json.JSONDecodeError:
                colour("⚠️  pip-audit returned invalid JSON", "yellow")
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        colour("⚠️  pip-audit tool not available or timed out", "yellow")
    except Exception as e:
        colour(f"⚠️  pip-audit error: {e}", "yellow")
    
    return vulnerabilities


def _run_bandit_scan(project_path: Path) -> List[Dict[str, Any]]:
    """Run bandit for code security scanning."""
    issues = []
    
    try:
        cmd = [sys.executable, "-m", "bandit", "-r", str(project_path), "-f", "json"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Bandit returns exit code 1 for issues found
        if result.stdout:
            try:
                bandit_data = json.loads(result.stdout)
                for result_item in bandit_data.get("results", []):
                    issues.append({
                        "type": result_item.get("test_id", "unknown"),
                        "severity": result_item.get("issue_severity", "medium").lower(),
                        "confidence": result_item.get("issue_confidence", "medium").lower(),
                        "file": result_item.get("filename", "unknown"),
                        "line": result_item.get("line_number", 0),
                        "description": result_item.get("issue_text", "No description"),
                        "context": result_item.get("code", "")[:100],
                        "source": "bandit"
                    })
            except json.JSONDecodeError:
                colour("⚠️  Bandit returned invalid JSON", "yellow")
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        colour("⚠️  Bandit tool not available or timed out", "yellow")
        # Fallback to operations layer implementation
        try:
            from uvmgr.ops.security import scan_code_security
            issues = scan_code_security(project_path)
        except Exception:
            pass
    except Exception as e:
        colour(f"⚠️  Bandit scan error: {e}", "yellow")
    
    return issues


def _run_detect_secrets(project_path: Path) -> List[Dict[str, Any]]:
    """Run detect-secrets for secret detection."""
    secrets = []
    
    try:
        # Try detect-secrets if available
        cmd = [sys.executable, "-m", "detect_secrets", "scan", str(project_path), "--all-files"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                secrets_data = json.loads(result.stdout)
                for file_path, file_secrets in secrets_data.get("results", {}).items():
                    for secret in file_secrets:
                        secrets.append({
                            "file": file_path,
                            "line": secret.get("line_number", 0),
                            "type": secret.get("type", "unknown"),
                            "context": "Secret detected by detect-secrets",
                            "source": "detect-secrets"
                        })
            except json.JSONDecodeError:
                pass
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # detect-secrets not available, will use fallback
        pass
    except Exception:
        pass
    
    return secrets


def _deduplicate_vulnerabilities(vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate vulnerabilities from multiple sources."""
    seen = set()
    unique_vulns = []
    
    for vuln in vulnerabilities:
        # Create a key based on package and vulnerability ID
        key = (vuln.get("package", ""), vuln.get("id", ""))
        if key not in seen:
            seen.add(key)
            unique_vulns.append(vuln)
    
    return unique_vulns


def _map_safety_severity(safety_severity: str) -> str:
    """Map safety severity to standard levels."""
    mapping = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "critical"
    }
    return mapping.get(safety_severity.lower(), "medium")


def install_security_tools() -> Dict[str, bool]:
    """
    Install required security tools if not available.
    
    Returns:
        Dictionary of tool installation status
    """
    tools_status = {}
    
    security_tools = [
        ("safety", "safety"),
        ("pip-audit", "pip-audit"), 
        ("bandit", "bandit[toml]"),
        ("detect-secrets", "detect-secrets")
    ]
    
    for tool_name, pip_package in security_tools:
        try:
            # Check if tool is already available
            result = subprocess.run(
                [sys.executable, "-m", tool_name, "--version"],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                tools_status[tool_name] = True
                colour(f"✅ {tool_name} is available", "green")
            else:
                # Try to install
                colour(f"📦 Installing {tool_name}...", "cyan")
                install_result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", pip_package],
                    capture_output=True,
                    timeout=60
                )
                tools_status[tool_name] = install_result.returncode == 0
                if tools_status[tool_name]:
                    colour(f"✅ {tool_name} installed successfully", "green")
                else:
                    colour(f"❌ Failed to install {tool_name}", "red")
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            tools_status[tool_name] = False
            colour(f"❌ {tool_name} not available", "red")
    
    return tools_status