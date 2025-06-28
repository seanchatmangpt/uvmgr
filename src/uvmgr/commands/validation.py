"""
Validation dashboard and monitoring commands.
"""

import typer
from typing import Optional, List
from datetime import datetime, timedelta
import json
from uvmgr.core.validation import ValidationOrchestrator, ValidationLevel
from uvmgr.core.telemetry import span, get_current_span
from uvmgr.ops.actions_ops import GitHubActionsOps
from uvmgr.runtime.actions import get_github_token, get_repo_info

app = typer.Typer(help="Validation dashboard and monitoring commands")


@app.command()
def dashboard(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    time_window: str = typer.Option(
        "1h", 
        "--time-window", 
        "-t",
        help="Time window for analysis (e.g., 1h, 24h, 7d)"
    )
):
    """Show validation dashboard with real-time metrics."""
    with span("validation.dashboard", validation_level=validation_level.value, time_window=time_window):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, validation_level)
        
        try:
            # Collect validation metrics
            metrics = collect_validation_metrics(ops, time_window)
            
            # Display dashboard
            display_validation_dashboard(metrics, validation_level)
            
        except Exception as e:
            typer.echo(f"❌ Error generating validation dashboard: {e}")
            raise typer.Exit(1)


@app.command()
def analyze(
    data_file: str = typer.Argument(..., help="JSON file containing data to analyze"),
    validation_level: ValidationLevel = typer.Option(
        ValidationLevel.STRICT, 
        "--validation-level", 
        "-v",
        help="Validation level (basic, strict, paranoid)"
    ),
    output_format: str = typer.Option(
        "text", 
        "--format", 
        "-f",
        help="Output format (text, json, csv)"
    )
):
    """Analyze data file for hallucinations and validation issues."""
    with span("validation.analyze", data_file=data_file, validation_level=validation_level.value):
        try:
            # Load data
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Create validator
            validator = ValidationOrchestrator(validation_level)
            
            # Analyze data
            results = analyze_data_file(data, validator)
            
            # Output results
            if output_format == "json":
                typer.echo(json.dumps(results, indent=2))
            elif output_format == "csv":
                output_csv_results(results)
            else:
                display_analysis_results(results)
                
        except Exception as e:
            typer.echo(f"❌ Error analyzing data file: {e}")
            raise typer.Exit(1)


@app.command()
def monitor(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    interval: int = typer.Option(
        30, 
        "--interval", 
        "-i",
        help="Monitoring interval in seconds"
    ),
    duration: Optional[int] = typer.Option(
        None, 
        "--duration", 
        "-d",
        help="Monitoring duration in minutes (default: continuous)"
    ),
    alert_threshold: float = typer.Option(
        0.7, 
        "--threshold", 
        "-t",
        help="Alert threshold for validation confidence"
    )
):
    """Monitor validation performance in real-time."""
    with span("validation.monitor", interval=interval, alert_threshold=alert_threshold):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, ValidationLevel.STRICT)
        
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration) if duration else None
            
            typer.echo(f"🔍 Starting validation monitoring for {owner}/{repo}")
            typer.echo(f"   Interval: {interval}s, Alert threshold: {alert_threshold}")
            typer.echo(f"   Duration: {'Continuous' if not duration else f'{duration} minutes'}")
            typer.echo()
            
            while True:
                current_time = datetime.now()
                if end_time and current_time >= end_time:
                    break
                
                # Collect metrics
                metrics = collect_realtime_metrics(ops)
                
                # Display current status
                display_monitoring_status(metrics, alert_threshold)
                
                # Check for alerts
                check_alerts(metrics, alert_threshold)
                
                # Wait for next interval
                import time
                time.sleep(interval)
                
        except KeyboardInterrupt:
            typer.echo("\n🛑 Monitoring stopped by user")
        except Exception as e:
            typer.echo(f"❌ Error during monitoring: {e}")
            raise typer.Exit(1)


@app.command()
def report(
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Repository owner"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Repository name"),
    start_date: str = typer.Option(
        None, 
        "--start-date", 
        "-s",
        help="Start date (YYYY-MM-DD)"
    ),
    end_date: str = typer.Option(
        None, 
        "--end-date", 
        "-e",
        help="End date (YYYY-MM-DD)"
    ),
    output_file: Optional[str] = typer.Option(
        None, 
        "--output", 
        "-o",
        help="Output file path"
    )
):
    """Generate validation performance report."""
    with span("validation.report", start_date=start_date, end_date=end_date):
        token = get_github_token()
        owner, repo = get_repo_info(owner, repo)
        
        ops = GitHubActionsOps(token, owner, repo, ValidationLevel.STRICT)
        
        try:
            # Generate report
            report_data = generate_validation_report(ops, start_date, end_date)
            
            # Output report
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
                typer.echo(f"📄 Report saved to {output_file}")
            else:
                display_validation_report(report_data)
                
        except Exception as e:
            typer.echo(f"❌ Error generating validation report: {e}")
            raise typer.Exit(1)


def collect_validation_metrics(ops: GitHubActionsOps, time_window: str) -> dict:
    """Collect validation metrics for the dashboard."""
    metrics = {
        "total_requests": 0,
        "valid_requests": 0,
        "invalid_requests": 0,
        "average_confidence": 0.0,
        "validation_issues": [],
        "issue_types": {},
        "response_times": [],
        "ml_scores": [],
        "behavior_scores": []
    }
    
    try:
        # Test different endpoints
        endpoints = [
            ("workflows", ops.list_workflows),
            ("workflow_runs", lambda: ops.list_workflow_runs(per_page=10)),
            ("secrets", ops.list_secrets),
            ("variables", ops.list_variables)
        ]
        
        for endpoint_name, endpoint_func in endpoints:
            try:
                result = endpoint_func()
                metrics["total_requests"] += 1
                
                if result["validation"].is_valid:
                    metrics["valid_requests"] += 1
                else:
                    metrics["invalid_requests"] += 1
                    metrics["validation_issues"].extend(result["validation"].issues)
                
                metrics["average_confidence"] += result["validation"].confidence
                
                # Collect detailed metrics
                if "ml_score" in result["validation"].metadata:
                    metrics["ml_scores"].append(result["validation"].metadata["ml_score"])
                
                if "behavior_score" in result["validation"].metadata:
                    metrics["behavior_scores"].append(result["validation"].metadata["behavior_score"])
                
                # Categorize issues
                for issue in result["validation"].issues:
                    issue_type = issue.split(":")[0] if ":" in issue else "Other"
                    metrics["issue_types"][issue_type] = metrics["issue_types"].get(issue_type, 0) + 1
                    
            except Exception as e:
                metrics["total_requests"] += 1
                metrics["invalid_requests"] += 1
                metrics["validation_issues"].append(f"Request failed: {str(e)}")
        
        # Calculate averages
        if metrics["total_requests"] > 0:
            metrics["average_confidence"] /= metrics["total_requests"]
        
    except Exception as e:
        metrics["validation_issues"].append(f"Metrics collection failed: {str(e)}")
    
    return metrics


def display_validation_dashboard(metrics: dict, validation_level: ValidationLevel):
    """Display the validation dashboard."""
    typer.echo("📊 Validation Dashboard")
    typer.echo("=" * 50)
    
    # Overall statistics
    success_rate = (metrics["valid_requests"] / max(metrics["total_requests"], 1)) * 100
    typer.echo(f"🎯 Success Rate: {success_rate:.1f}%")
    typer.echo(f"📈 Average Confidence: {metrics['average_confidence']:.2f}")
    typer.echo(f"🔍 Total Requests: {metrics['total_requests']}")
    typer.echo(f"✅ Valid Requests: {metrics['valid_requests']}")
    typer.echo(f"❌ Invalid Requests: {metrics['invalid_requests']}")
    typer.echo()
    
    # Issue breakdown
    if metrics["issue_types"]:
        typer.echo("🚨 Issue Breakdown:")
        for issue_type, count in sorted(metrics["issue_types"].items(), key=lambda x: x[1], reverse=True):
            typer.echo(f"   {issue_type}: {count}")
        typer.echo()
    
    # ML and Behavioral scores
    if metrics["ml_scores"]:
        avg_ml_score = sum(metrics["ml_scores"]) / len(metrics["ml_scores"])
        typer.echo(f"🤖 Average ML Score: {avg_ml_score:.2f}")
    
    if metrics["behavior_scores"]:
        avg_behavior_score = sum(metrics["behavior_scores"]) / len(metrics["behavior_scores"])
        typer.echo(f"🧠 Average Behavior Score: {avg_behavior_score:.2f}")
    
    typer.echo()
    typer.echo(f"⚙️  Validation Level: {validation_level.value}")
    
    # Recent issues
    if metrics["validation_issues"]:
        typer.echo("\n🚨 Recent Issues:")
        for issue in metrics["validation_issues"][-5:]:  # Show last 5 issues
            typer.echo(f"   • {issue}")


def analyze_data_file(data: dict, validator: ValidationOrchestrator) -> dict:
    """Analyze a data file for validation issues."""
    results = {
        "file_analysis": {},
        "item_analysis": [],
        "summary": {
            "total_items": 0,
            "valid_items": 0,
            "invalid_items": 0,
            "average_confidence": 0.0,
            "issue_types": {}
        }
    }
    
    # Analyze file structure
    results["file_analysis"] = {
        "type": type(data).__name__,
        "size": len(str(data)),
        "has_workflow_runs": "workflow_runs" in data,
        "has_workflows": isinstance(data, list) and len(data) > 0
    }
    
    # Analyze individual items
    if isinstance(data, dict) and "workflow_runs" in data:
        items = data["workflow_runs"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    
    results["summary"]["total_items"] = len(items)
    
    for i, item in enumerate(items):
        if isinstance(item, dict):
            result = validator.hallucination_detector.validate_workflow_run(item)
        else:
            result = validator.hallucination_detector.validate_workflow_list([item])
        
        item_result = {
            "index": i,
            "is_valid": result.is_valid,
            "confidence": result.confidence,
            "issues": result.issues,
            "metadata": result.metadata
        }
        
        results["item_analysis"].append(item_result)
        
        if result.is_valid:
            results["summary"]["valid_items"] += 1
        else:
            results["summary"]["invalid_items"] += 1
        
        results["summary"]["average_confidence"] += result.confidence
        
        # Categorize issues
        for issue in result.issues:
            issue_type = issue.split(":")[0] if ":" in issue else "Other"
            results["summary"]["issue_types"][issue_type] = results["summary"]["issue_types"].get(issue_type, 0) + 1
    
    # Calculate averages
    if results["summary"]["total_items"] > 0:
        results["summary"]["average_confidence"] /= results["summary"]["total_items"]
    
    return results


def display_analysis_results(results: dict):
    """Display analysis results."""
    typer.echo("🔍 Data Analysis Results")
    typer.echo("=" * 50)
    
    # File analysis
    file_analysis = results["file_analysis"]
    typer.echo(f"📁 File Type: {file_analysis['type']}")
    typer.echo(f"📏 File Size: {file_analysis['size']} characters")
    typer.echo(f"🔄 Has Workflow Runs: {file_analysis['has_workflow_runs']}")
    typer.echo(f"⚙️  Has Workflows: {file_analysis['has_workflows']}")
    typer.echo()
    
    # Summary
    summary = results["summary"]
    success_rate = (summary["valid_items"] / max(summary["total_items"], 1)) * 100
    typer.echo(f"📊 Summary:")
    typer.echo(f"   Total Items: {summary['total_items']}")
    typer.echo(f"   Valid Items: {summary['valid_items']}")
    typer.echo(f"   Invalid Items: {summary['invalid_items']}")
    typer.echo(f"   Success Rate: {success_rate:.1f}%")
    typer.echo(f"   Average Confidence: {summary['average_confidence']:.2f}")
    typer.echo()
    
    # Issue breakdown
    if summary["issue_types"]:
        typer.echo("🚨 Issue Breakdown:")
        for issue_type, count in sorted(summary["issue_types"].items(), key=lambda x: x[1], reverse=True):
            typer.echo(f"   {issue_type}: {count}")
        typer.echo()
    
    # Item details
    if len(results["item_analysis"]) <= 10:
        typer.echo("📋 Item Details:")
        for item in results["item_analysis"]:
            status_emoji = "✅" if item["is_valid"] else "❌"
            typer.echo(f"   {status_emoji} Item {item['index']}: Confidence {item['confidence']:.2f}")
            if item["issues"]:
                for issue in item["issues"]:
                    typer.echo(f"      • {issue}")


def output_csv_results(results: dict):
    """Output analysis results in CSV format."""
    import csv
    import sys
    
    writer = csv.writer(sys.stdout)
    writer.writerow(["Index", "Valid", "Confidence", "Issues"])
    
    for item in results["item_analysis"]:
        issues_str = "; ".join(item["issues"]) if item["issues"] else ""
        writer.writerow([item["index"], item["is_valid"], f"{item['confidence']:.2f}", issues_str])


def collect_realtime_metrics(ops: GitHubActionsOps) -> dict:
    """Collect real-time validation metrics."""
    start_time = datetime.now()
    
    try:
        result = ops.list_workflow_runs(per_page=5)
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        
        return {
            "timestamp": start_time.isoformat(),
            "response_time": response_time,
            "is_valid": result["validation"].is_valid,
            "confidence": result["validation"].confidence,
            "issues": result["validation"].issues,
            "ml_score": result["validation"].metadata.get("ml_score", 0.0),
            "behavior_score": result["validation"].metadata.get("behavior_score", 0.0)
        }
    except Exception as e:
        return {
            "timestamp": start_time.isoformat(),
            "response_time": 0,
            "is_valid": False,
            "confidence": 0.0,
            "issues": [f"Request failed: {str(e)}"],
            "ml_score": 0.0,
            "behavior_score": 0.0
        }


def display_monitoring_status(metrics: dict, alert_threshold: float):
    """Display current monitoring status."""
    timestamp = datetime.fromisoformat(metrics["timestamp"]).strftime("%H:%M:%S")
    status_emoji = "✅" if metrics["is_valid"] else "❌"
    confidence_emoji = "🟢" if metrics["confidence"] >= alert_threshold else "🔴"
    
    typer.echo(f"[{timestamp}] {status_emoji} Confidence: {confidence_emoji} {metrics['confidence']:.2f} "
               f"| Response: {metrics['response_time']:.0f}ms "
               f"| ML: {metrics['ml_score']:.2f} "
               f"| Behavior: {metrics['behavior_score']:.2f}")


def check_alerts(metrics: dict, alert_threshold: float):
    """Check for validation alerts."""
    if metrics["confidence"] < alert_threshold:
        typer.echo(f"🚨 ALERT: Low validation confidence ({metrics['confidence']:.2f} < {alert_threshold})")
        if metrics["issues"]:
            typer.echo(f"   Issues: {', '.join(metrics['issues'][:3])}")  # Show first 3 issues


def generate_validation_report(ops: GitHubActionsOps, start_date: str, end_date: str) -> dict:
    """Generate a comprehensive validation report."""
    report = {
        "report_info": {
            "generated_at": datetime.now().isoformat(),
            "start_date": start_date,
            "end_date": end_date,
            "validation_level": "strict"
        },
        "summary": {
            "total_requests": 0,
            "valid_requests": 0,
            "invalid_requests": 0,
            "average_confidence": 0.0,
            "total_issues": 0
        },
        "trends": {
            "confidence_over_time": [],
            "issue_frequency": {},
            "response_times": []
        },
        "recommendations": []
    }
    
    # Collect data for the specified period
    # This is a simplified implementation - in a real system, you'd query historical data
    try:
        # Simulate historical data collection
        for i in range(10):  # Simulate 10 historical requests
            result = ops.list_workflow_runs(per_page=5)
            
            report["summary"]["total_requests"] += 1
            if result["validation"].is_valid:
                report["summary"]["valid_requests"] += 1
            else:
                report["summary"]["invalid_requests"] += 1
                report["summary"]["total_issues"] += len(result["validation"].issues)
            
            report["summary"]["average_confidence"] += result["validation"].confidence
            
            # Track trends
            report["trends"]["confidence_over_time"].append({
                "timestamp": datetime.now().isoformat(),
                "confidence": result["validation"].confidence
            })
            
            # Track issue frequency
            for issue in result["validation"].issues:
                issue_type = issue.split(":")[0] if ":" in issue else "Other"
                report["trends"]["issue_frequency"][issue_type] = report["trends"]["issue_frequency"].get(issue_type, 0) + 1
        
        # Calculate averages
        if report["summary"]["total_requests"] > 0:
            report["summary"]["average_confidence"] /= report["summary"]["total_requests"]
        
        # Generate recommendations
        if report["summary"]["average_confidence"] < 0.8:
            report["recommendations"].append("Consider upgrading to paranoid validation level")
        
        if report["summary"]["invalid_requests"] > report["summary"]["total_requests"] * 0.2:
            report["recommendations"].append("High failure rate detected - review validation patterns")
        
        most_common_issue = max(report["trends"]["issue_frequency"].items(), key=lambda x: x[1])[0] if report["trends"]["issue_frequency"] else None
        if most_common_issue:
            report["recommendations"].append(f"Address most common issue: {most_common_issue}")
        
    except Exception as e:
        report["recommendations"].append(f"Error collecting data: {str(e)}")
    
    return report


def display_validation_report(report: dict):
    """Display the validation report."""
    typer.echo("📊 Validation Performance Report")
    typer.echo("=" * 60)
    
    # Report info
    info = report["report_info"]
    typer.echo(f"📅 Generated: {info['generated_at']}")
    if info["start_date"] and info["end_date"]:
        typer.echo(f"📅 Period: {info['start_date']} to {info['end_date']}")
    typer.echo(f"⚙️  Validation Level: {info['validation_level']}")
    typer.echo()
    
    # Summary
    summary = report["summary"]
    success_rate = (summary["valid_requests"] / max(summary["total_requests"], 1)) * 100
    typer.echo("📈 Summary Statistics:")
    typer.echo(f"   Total Requests: {summary['total_requests']}")
    typer.echo(f"   Valid Requests: {summary['valid_requests']}")
    typer.echo(f"   Invalid Requests: {summary['invalid_requests']}")
    typer.echo(f"   Success Rate: {success_rate:.1f}%")
    typer.echo(f"   Average Confidence: {summary['average_confidence']:.2f}")
    typer.echo(f"   Total Issues: {summary['total_issues']}")
    typer.echo()
    
    # Issue frequency
    if report["trends"]["issue_frequency"]:
        typer.echo("🚨 Issue Frequency:")
        for issue_type, count in sorted(report["trends"]["issue_frequency"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / max(summary["total_requests"], 1)) * 100
            typer.echo(f"   {issue_type}: {count} ({percentage:.1f}%)")
        typer.echo()
    
    # Recommendations
    if report["recommendations"]:
        typer.echo("💡 Recommendations:")
        for i, recommendation in enumerate(report["recommendations"], 1):
            typer.echo(f"   {i}. {recommendation}")
        typer.echo()
    
    typer.echo("✅ Report generation complete") 