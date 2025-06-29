"""
End-to-End Test for Agent Guides Integration
============================================

This test validates the complete agent guides integration with DSPy and Lean Six Sigma
principles on external projects, demonstrating the 3-tier architecture in action.
"""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import subprocess
import sys

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from uvmgr.ops.agent_guides import (
    install_agent_guides,
    search_conversations,
    execute_multi_mind_analysis,
    analyze_code_deep,
    create_custom_guide,
    validate_guides,
    execute_anti_repetition_workflow,
    get_guide_status
)

console = Console()


class TestAgentGuidesE2E:
    """End-to-end test suite for agent guides integration."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Setup
        self.test_dir = Path(tempfile.mkdtemp())
        self.guides_dir = self.test_dir / "agent-guides"
        self.guides_dir.mkdir(parents=True, exist_ok=True)
        
        yield
        
        # Teardown
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_01_install_agent_guides(self):
        """Test installing agent guides from tokenbender repository."""
        console.print(Panel("🔧 [bold cyan]Test 1: Installing Agent Guides[/bold cyan]"))
        
        # Install guides
        result = install_agent_guides(
            source="tokenbender/agent-guides",
            target_dir=self.guides_dir,
            force=True
        )
        
        # Validate results
        assert result["guides_count"] > 0
        assert result["source"] == "tokenbender/agent-guides"
        assert result["guides_path"].exists()
        assert len(result["guides"]) > 0
        
        console.print(f"✅ Installed {result['guides_count']} guides")
        console.print(f"📁 Path: {result['guides_path']}")
        
        return result
    
    def test_02_validate_guides(self):
        """Test guide validation using Lean Six Sigma principles."""
        console.print(Panel("🔍 [bold cyan]Test 2: Validating Guides[/bold cyan]"))
        
        # First install guides
        install_result = install_agent_guides(
            source="tokenbender/agent-guides",
            target_dir=self.guides_dir,
            force=True
        )
        
        # Validate guides
        validation_result = validate_guides(install_result["guides_path"])
        
        # Validate results
        assert validation_result["valid"] is True
        assert validation_result["guides_count"] > 0
        assert len(validation_result["errors"]) == 0
        
        console.print(f"✅ Validation passed: {validation_result['guides_count']} guides")
        if validation_result["warnings"]:
            console.print(f"⚠️  Warnings: {len(validation_result['warnings'])}")
        
        return validation_result
    
    def test_03_search_conversations(self):
        """Test conversation and guide search functionality."""
        console.print(Panel("🔍 [bold cyan]Test 3: Search Functionality[/bold cyan]"))
        
        # Test search across multiple sources
        search_query = "machine learning pipeline"
        sources = ["conversations", "guides", "code"]
        
        search_results = search_conversations(
            query=search_query,
            sources=sources,
            max_results=5
        )
        
        # Validate results
        assert "query" in search_results
        assert "sources" in search_results
        assert "results" in search_results
        assert search_results["query"] == search_query
        assert search_results["sources"] == sources
        
        console.print(f"🔍 Query: {search_query}")
        console.print(f"📊 Found {len(search_results['results'])} results")
        
        # Display results table
        if search_results["results"]:
            table = Table(title="Search Results")
            table.add_column("Source", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Relevance", style="green")
            
            for result in search_results["results"][:3]:  # Show first 3
                table.add_row(
                    result.get("source", "Unknown"),
                    result.get("title", "No title")[:40],
                    f"{result.get('relevance', 0):.2f}"
                )
            console.print(table)
        
        return search_results
    
    def test_04_multi_mind_analysis(self):
        """Test multi-mind analysis with DSPy integration."""
        console.print(Panel("🧠 [bold cyan]Test 4: Multi-Mind Analysis[/bold cyan]"))
        
        # Test topic for analysis
        topic = "Should we implement quantum error correction in our ML pipeline?"
        analysis_type = "collaborative"
        rounds = 2  # Reduced for testing
        experts = ["Software Architect", "ML Engineer", "DevOps Specialist"]
        
        # Execute analysis
        analysis_result = execute_multi_mind_analysis(
            topic=topic,
            analysis_type=analysis_type,
            rounds=rounds,
            experts=experts
        )
        
        # Validate results
        assert analysis_result.topic == topic
        assert analysis_result.rounds_completed == rounds
        assert len(analysis_result.experts) == len(experts)
        assert analysis_result.duration > 0
        
        console.print(f"📋 Topic: {topic}")
        console.print(f"👥 Experts: {', '.join(analysis_result.experts)}")
        console.print(f"🔄 Rounds: {analysis_result.rounds_completed}")
        console.print(f"⏱️  Duration: {analysis_result.duration:.2f}s")
        
        # Display expert insights
        if analysis_result.expert_insights:
            console.print("\n💡 [bold]Expert Insights:[/bold]")
            for expert, insights in analysis_result.expert_insights.items():
                console.print(f"  🔬 {expert}: {len(insights)} insights")
        
        # Display consensus
        if analysis_result.consensus:
            console.print(f"\n✅ [bold green]Consensus:[/bold green] {analysis_result.consensus[:100]}...")
        
        return analysis_result
    
    def test_05_deep_code_analysis(self):
        """Test deep code analysis on external project."""
        console.print(Panel("🔍 [bold cyan]Test 5: Deep Code Analysis[/bold cyan]"))
        
        # Create a test file for analysis
        test_file = self.test_dir / "test_code.py"
        test_code = '''
def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def optimize_fibonacci(n):
    """Optimized fibonacci with memoization."""
    memo = {}
    def fib(n):
        if n in memo:
            return memo[n]
        if n <= 1:
            return n
        memo[n] = fib(n-1) + fib(n-2)
        return memo[n]
    return fib(n)

# Performance test
import time
start = time.time()
result = fibonacci(35)
end = time.time()
print(f"Standard: {result} in {end-start:.2f}s")

start = time.time()
result = optimize_fibonacci(35)
end = time.time()
print(f"Optimized: {result} in {end-start:.2f}s")
'''
        test_file.write_text(test_code)
        
        # Analyze the code
        analysis_result = analyze_code_deep(
            target=str(test_file),
            depth="deep",
            include_performance=True,
            include_security=True
        )
        
        # Validate results
        assert analysis_result.target == str(test_file)
        assert analysis_result.complexity in ["Low", "Medium", "High", "Unknown"]
        assert isinstance(analysis_result.performance_score, float)
        assert isinstance(analysis_result.security_score, float)
        assert isinstance(analysis_result.maintainability_score, float)
        
        console.print(f"🎯 Target: {analysis_result.target}")
        console.print(f"📊 Complexity: {analysis_result.complexity}")
        console.print(f"⚡ Performance Score: {analysis_result.performance_score:.1f}/10")
        console.print(f"🔒 Security Score: {analysis_result.security_score:.1f}/10")
        console.print(f"🔧 Maintainability Score: {analysis_result.maintainability_score:.1f}/10")
        
        # Display issues
        if analysis_result.issues:
            console.print(f"\n⚠️  Issues Found: {len(analysis_result.issues)}")
            for issue in analysis_result.issues[:2]:  # Show first 2
                console.print(f"  • {issue.get('severity', 'Unknown')}: {issue.get('description', 'No description')}")
        
        # Display recommendations
        if analysis_result.recommendations:
            console.print(f"\n💡 Recommendations: {len(analysis_result.recommendations)}")
            for rec in analysis_result.recommendations[:2]:  # Show first 2
                console.print(f"  • {rec}")
        
        return analysis_result
    
    def test_06_create_custom_guide(self):
        """Test custom guide creation with DSPy."""
        console.print(Panel("📝 [bold cyan]Test 6: Custom Guide Creation[/bold cyan]"))
        
        # Create custom guide
        guide_name = "ml-pipeline-optimization"
        template = "workflow"
        description = "Machine learning pipeline optimization guide"
        
        guide_result = create_custom_guide(
            name=guide_name,
            template=template,
            description=description,
            interactive=False,
            output_dir=self.guides_dir / "custom"
        )
        
        # Validate results
        assert guide_result["name"] == guide_name
        assert guide_result["template"] == template
        assert guide_result["output_path"].exists()
        assert guide_result["file_size"] > 0
        assert guide_result["duration"] > 0
        
        console.print(f"📋 Guide Name: {guide_result['name']}")
        console.print(f"📄 Template: {guide_result['template']}")
        console.print(f"📁 Output: {guide_result['output_path']}")
        console.print(f"📏 Size: {guide_result['file_size']} bytes")
        console.print(f"⏱️  Creation Time: {guide_result['duration']:.2f}s")
        
        # Display content preview
        if guide_result.get("content_preview"):
            console.print(f"\n📝 Content Preview: {guide_result['content_preview']}")
        
        return guide_result
    
    def test_07_anti_repetition_workflow(self):
        """Test anti-repetition workflow execution."""
        console.print(Panel("🔄 [bold cyan]Test 7: Anti-Repetition Workflow[/bold cyan]"))
        
        # Test workflow parameters
        workflow_name = "knowledge-building"
        parameters = {
            "topic": "Machine Learning Pipeline Optimization",
            "depth": "comprehensive",
            "include_examples": True,
            "target_audience": "developers"
        }
        iterations = 3
        
        # Execute workflow
        workflow_result = execute_anti_repetition_workflow(
            workflow_name=workflow_name,
            parameters=parameters,
            iterations=iterations,
            anti_repetition=True,
            save_progress=True
        )
        
        # Validate results
        assert workflow_result["workflow_name"] == workflow_name
        assert workflow_result["iterations_completed"] == iterations
        assert workflow_result["success_rate"] >= 0.0
        assert workflow_result["total_duration"] > 0
        assert workflow_result["anti_repetition"] is True
        
        console.print(f"📋 Workflow: {workflow_result['workflow_name']}")
        console.print(f"🔄 Iterations: {workflow_result['iterations_completed']}")
        console.print(f"📊 Success Rate: {workflow_result['success_rate']:.1%}")
        console.print(f"⏱️  Total Duration: {workflow_result['total_duration']:.2f}s")
        console.print(f"🚫 Anti-Repetition: {'✅' if workflow_result['anti_repetition'] else '❌'}")
        
        # Display iteration results
        if workflow_result.get("iteration_results"):
            console.print("\n📊 [bold]Iteration Results:[/bold]")
            for i, result in enumerate(workflow_result["iteration_results"], 1):
                status = "✅ Success" if result.get("success") else "❌ Failed"
                console.print(f"  Iteration {i}: {status} ({result.get('duration', 0):.2f}s)")
        
        # Display key insights
        if workflow_result.get("key_insights"):
            console.print(f"\n💡 Key Insights: {len(workflow_result['key_insights'])}")
            for insight in workflow_result["key_insights"][:2]:  # Show first 2
                console.print(f"  • {insight}")
        
        return workflow_result
    
    def test_08_guide_status(self):
        """Test guide status and metrics."""
        console.print(Panel("📊 [bold cyan]Test 8: Guide Status and Metrics[/bold cyan]"))
        
        # First install some guides
        install_agent_guides(
            source="tokenbender/agent-guides",
            target_dir=self.guides_dir,
            force=True
        )
        
        # Get status with detailed metrics
        status_result = get_guide_status(detailed=True, include_metrics=True)
        
        # Validate results
        assert "active" in status_result
        assert "installation_path" in status_result
        assert "guides_count" in status_result
        assert "guides" in status_result
        assert "metrics" in status_result
        
        console.print(f"📊 Status: {'✅ Active' if status_result['active'] else '❌ Inactive'}")
        console.print(f"📁 Installation Path: {status_result['installation_path']}")
        console.print(f"📚 Guides Count: {status_result['guides_count']}")
        console.print(f"🕒 Last Updated: {status_result.get('last_updated', 'Unknown')}")
        
        # Display metrics
        if status_result.get("metrics"):
            console.print("\n📈 [bold]Metrics:[/bold]")
            metrics_table = Table()
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="green")
            
            for key, value in status_result["metrics"].items():
                if isinstance(value, float):
                    metrics_table.add_row(key, f"{value:.2f}")
                else:
                    metrics_table.add_row(key, str(value))
            
            console.print(metrics_table)
        
        # Display detailed guides
        if status_result.get("guides") and len(status_result["guides"]) > 0:
            console.print(f"\n📚 [bold]Installed Guides:[/bold]")
            guides_table = Table()
            guides_table.add_column("Guide", style="cyan")
            guides_table.add_column("Type", style="white")
            guides_table.add_column("Size", style="green")
            
            for guide in status_result["guides"][:5]:  # Show first 5
                guides_table.add_row(
                    guide.get("name", "Unknown"),
                    guide.get("type", "Unknown"),
                    f"{guide.get('size', 0)} bytes"
                )
            
            console.print(guides_table)
        
        return status_result
    
    def test_09_external_project_integration(self):
        """Test integration with external project."""
        console.print(Panel("🌐 [bold cyan]Test 9: External Project Integration[/bold cyan]"))
        
        # Create a mock external project structure
        external_project = self.test_dir / "external-project"
        external_project.mkdir(parents=True, exist_ok=True)
        
        # Create project files
        (external_project / "src").mkdir()
        (external_project / "tests").mkdir()
        (external_project / "docs").mkdir()
        
        # Create sample files
        main_file = external_project / "src" / "main.py"
        main_file.write_text('''
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process input data and return results."""
    try:
        # Process the data
        result = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                result[key] = value * 2
            elif isinstance(value, str):
                result[key] = value.upper()
            else:
                result[key] = value
        
        logger.info(f"Processed {len(data)} items")
        return result
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise

def validate_input(data: Dict[str, Any]) -> bool:
    """Validate input data."""
    if not isinstance(data, dict):
        return False
    return len(data) > 0
''')
        
        test_file = external_project / "tests" / "test_main.py"
        test_file.write_text('''
import pytest
from src.main import process_data, validate_input

def test_process_data():
    """Test data processing function."""
    input_data = {"a": 1, "b": "hello", "c": 3.14}
    result = process_data(input_data)
    
    assert result["a"] == 2
    assert result["b"] == "HELLO"
    assert result["c"] == 6.28

def test_validate_input():
    """Test input validation."""
    assert validate_input({"a": 1}) is True
    assert validate_input({}) is False
    assert validate_input("not a dict") is False
''')
        
        # Analyze the external project
        console.print(f"📁 External Project: {external_project}")
        
        # Test 1: Analyze main.py
        main_analysis = analyze_code_deep(
            target=str(main_file),
            depth="comprehensive",
            include_performance=True,
            include_security=True
        )
        
        console.print(f"\n🔍 Main.py Analysis:")
        console.print(f"  📊 Complexity: {main_analysis.complexity}")
        console.print(f"  ⚡ Performance: {main_analysis.performance_score:.1f}/10")
        console.print(f"  🔒 Security: {main_analysis.security_score:.1f}/10")
        console.print(f"  🔧 Maintainability: {main_analysis.maintainability_score:.1f}/10")
        
        # Test 2: Multi-mind analysis on project architecture
        architecture_analysis = execute_multi_mind_analysis(
            topic="How should we optimize this external project's architecture?",
            analysis_type="collaborative",
            rounds=2,
            experts=["Software Architect", "DevOps Engineer", "Security Specialist"]
        )
        
        console.print(f"\n🧠 Architecture Analysis:")
        console.print(f"  👥 Experts: {len(architecture_analysis.experts)}")
        console.print(f"  🔄 Rounds: {architecture_analysis.rounds_completed}")
        console.print(f"  ⏱️  Duration: {architecture_analysis.duration:.2f}s")
        
        # Test 3: Create project-specific guide
        project_guide = create_custom_guide(
            name="external-project-optimization",
            template="workflow",
            description="Optimization guide for external project",
            output_dir=self.guides_dir / "external"
        )
        
        console.print(f"\n📝 Project Guide Created:")
        console.print(f"  📋 Name: {project_guide['name']}")
        console.print(f"  📁 Path: {project_guide['output_path']}")
        console.print(f"  📏 Size: {project_guide['file_size']} bytes")
        
        return {
            "project_path": external_project,
            "main_analysis": main_analysis,
            "architecture_analysis": architecture_analysis,
            "project_guide": project_guide
        }
    
    def test_10_end_to_end_workflow(self):
        """Complete end-to-end workflow test."""
        console.print(Panel("🚀 [bold cyan]Test 10: Complete E2E Workflow[/bold cyan]"))
        
        results = {}
        
        # Step 1: Install guides
        console.print("\n📚 [bold]Step 1: Installing Agent Guides[/bold]")
        results["install"] = self.test_01_install_agent_guides()
        
        # Step 2: Validate guides
        console.print("\n🔍 [bold]Step 2: Validating Guides[/bold]")
        results["validate"] = self.test_02_validate_guides()
        
        # Step 3: Search for relevant content
        console.print("\n🔍 [bold]Step 3: Searching for Content[/bold]")
        results["search"] = self.test_03_search_conversations()
        
        # Step 4: Multi-mind analysis
        console.print("\n🧠 [bold]Step 4: Multi-Mind Analysis[/bold]")
        results["multi_mind"] = self.test_04_multi_mind_analysis()
        
        # Step 5: Code analysis
        console.print("\n🔍 [bold]Step 5: Code Analysis[/bold]")
        results["code_analysis"] = self.test_05_deep_code_analysis()
        
        # Step 6: Create custom guide
        console.print("\n📝 [bold]Step 6: Creating Custom Guide[/bold]")
        results["custom_guide"] = self.test_06_create_custom_guide()
        
        # Step 7: Execute workflow
        console.print("\n🔄 [bold]Step 7: Executing Workflow[/bold]")
        results["workflow"] = self.test_07_anti_repetition_workflow()
        
        # Step 8: Check status
        console.print("\n📊 [bold]Step 8: Checking Status[/bold]")
        results["status"] = self.test_08_guide_status()
        
        # Step 9: External project integration
        console.print("\n🌐 [bold]Step 9: External Project Integration[/bold]")
        results["external"] = self.test_09_external_project_integration()
        
        # Summary
        console.print(Panel("✅ [bold green]E2E Test Summary[/bold green]"))
        
        summary_table = Table(title="Test Results Summary")
        summary_table.add_column("Test", style="cyan")
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Details", style="white")
        
        for test_name, result in results.items():
            if isinstance(result, dict):
                if "guides_count" in result:
                    details = f"{result['guides_count']} guides"
                elif "rounds_completed" in result:
                    details = f"{result['rounds_completed']} rounds"
                elif "performance_score" in result:
                    details = f"Score: {result['performance_score']:.1f}/10"
                else:
                    details = "Completed"
            else:
                details = "Completed"
            
            summary_table.add_row(test_name.replace("_", " ").title(), "✅ Pass", details)
        
        console.print(summary_table)
        
        # Validate overall success
        assert len(results) == 9  # All tests completed
        assert results["install"]["guides_count"] > 0
        assert results["validate"]["valid"] is True
        assert results["multi_mind"].rounds_completed > 0
        assert results["code_analysis"].performance_score > 0
        
        console.print("\n🎉 [bold green]All E2E tests completed successfully![/bold green]")
        
        return results


def run_e2e_tests():
    """Run all end-to-end tests."""
    console.print(Panel.fit(
        "🧪 [bold cyan]Agent Guides E2E Test Suite[/bold cyan]\n"
        "Testing complete integration with DSPy and Lean Six Sigma",
        border_style="cyan"
    ))
    
    # Create test instance
    test_suite = TestAgentGuidesE2E()
    
    # Run tests
    results = {}
    
    try:
        # Individual tests
        results["install"] = test_suite.test_01_install_agent_guides()
        results["validate"] = test_suite.test_02_validate_guides()
        results["search"] = test_suite.test_03_search_conversations()
        results["multi_mind"] = test_suite.test_04_multi_mind_analysis()
        results["code_analysis"] = test_suite.test_05_deep_code_analysis()
        results["custom_guide"] = test_suite.test_06_create_custom_guide()
        results["workflow"] = test_suite.test_07_anti_repetition_workflow()
        results["status"] = test_suite.test_08_guide_status()
        results["external"] = test_suite.test_09_external_project_integration()
        
        # Complete E2E workflow
        results["e2e"] = test_suite.test_10_end_to_end_workflow()
        
        console.print(Panel.fit(
            "✅ [bold green]All E2E Tests Passed![/bold green]\n"
            "Agent guides integration is working correctly with external projects.",
            border_style="green"
        ))
        
        return results
        
    except Exception as e:
        console.print(Panel.fit(
            f"❌ [bold red]E2E Test Failed: {e}[/bold red]",
            border_style="red"
        ))
        raise


if __name__ == "__main__":
    # Run E2E tests
    run_e2e_tests() 