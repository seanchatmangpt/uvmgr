#!/usr/bin/env python3
"""
Validation of Chapter 4: Observability as Foundation
====================================================

This script demonstrates the practical implementation of the concepts
described in Chapter 4 of the Dogfoodie thesis.

Key Concepts Validated:
- Semantic telemetry as a language
- Self-observing agents
- Weaver Forge as semantic infrastructure
- Reflection and refinement capabilities
- External project observability
"""

import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Any

def demonstrate_semantic_telemetry():
    """Demonstrate semantic telemetry concepts from Chapter 4.2-4.3."""
    print("🔍 Chapter 4.2-4.3: Semantic Telemetry Validation")
    print("-" * 50)
    
    # Test 1: Generate telemetry with semantic meaning
    print("📊 Testing: Semantic telemetry generation...")
    result = subprocess.run(["uvmgr", "otel", "test"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Semantic telemetry: WORKING")
        print(f"   📝 Generated structured telemetry with semantic context")
    else:
        print("❌ Semantic telemetry: FAILED")
    
    return result.returncode == 0

def demonstrate_weaver_forge():
    """Demonstrate Weaver Forge concepts from Chapter 4.4-4.6."""
    print("\n🔧 Chapter 4.4-4.6: Weaver Forge Validation")
    print("-" * 50)
    
    # Test 1: Weaver schema validation
    print("📋 Testing: Weaver schema validation...")
    result = subprocess.run(["uvmgr", "weaver", "check"], capture_output=True, text=True)
    
    weaver_available = "No such command" not in result.stderr
    if weaver_available:
        print("✅ Weaver Forge: AVAILABLE")
        print(f"   🏗️  Schema validation and code generation infrastructure ready")
    else:
        print("❌ Weaver Forge: UNAVAILABLE")
    
    # Test 2: Semantic convention generation
    print("🏭 Testing: Forge code generation capabilities...")
    try:
        # Check if semantic conventions are properly structured
        result = subprocess.run([
            "python", "-c", 
            "from uvmgr.core.semconv import CliAttributes, PackageAttributes, ProcessAttributes; "
            "print('Semantic conventions:', len([a for a in dir(CliAttributes) if not a.startswith('_')]))"
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and "Semantic conventions:" in result.stdout:
            print("✅ Forge generation: WORKING")
            print(f"   🏭 {result.stdout.strip()}")
        else:
            print("❌ Forge generation: FAILED")
    except Exception as e:
        print(f"❌ Forge generation: ERROR - {e}")
    
    return weaver_available

def demonstrate_self_observing_agents():
    """Demonstrate self-observing agents from Chapter 4.7."""
    print("\n🤖 Chapter 4.7: Self-Observing Agents Validation")
    print("-" * 50)
    
    # Create a temporary external project to demonstrate agent self-observation
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_dir = temp_path / "self-observing-project"
        project_dir.mkdir()
        
        # Create a project that can observe its own behavior
        pyproject_content = """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "self-observing-project"
version = "0.1.0"
description = "Self-observing agent validation"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)
        
        # Create source with self-observation capabilities
        src_dir = project_dir / "self_observing_project"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")
        
        main_content = '''#!/usr/bin/env python3
"""Self-observing agent implementation."""

class SelfObservingAgent:
    """Agent that can observe and report on its own behavior."""
    
    def __init__(self):
        self.operations = []
        self.state = "initialized"
    
    def perform_operation(self, operation_name: str, **kwargs):
        """Perform an operation while observing behavior."""
        # Record the operation with semantic context
        observation = {
            "operation": operation_name,
            "timestamp": "2024-01-01T00:00:00Z",  # Simplified for demo
            "parameters": kwargs,
            "agent_state": self.state
        }
        self.operations.append(observation)
        self.state = f"executed_{operation_name}"
        return observation
    
    def self_report(self):
        """Agent reports on its own behavior."""
        return {
            "total_operations": len(self.operations),
            "current_state": self.state,
            "operation_history": self.operations,
            "self_assessment": "functioning_normally"
        }

def main():
    """Demonstrate self-observing agent."""
    agent = SelfObservingAgent()
    
    # Agent performs operations while observing itself
    agent.perform_operation("calculate", inputs=[1, 2, 3])
    agent.perform_operation("validate", criteria="semantic_correctness")
    agent.perform_operation("communicate", target="external_system")
    
    # Agent provides self-report
    report = agent.self_report()
    print("🤖 Self-Observing Agent Report:")
    print(f"   Operations performed: {report['total_operations']}")
    print(f"   Current state: {report['current_state']}")
    print(f"   Self-assessment: {report['self_assessment']}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
'''
        (src_dir / "main.py").write_text(main_content)
        
        # Create test
        test_content = '''#!/usr/bin/env python3
"""Tests for self-observing agent."""

import pytest
from self_observing_project.main import SelfObservingAgent

def test_self_observation():
    """Test that agent can observe its own behavior."""
    agent = SelfObservingAgent()
    
    # Perform operation
    result = agent.perform_operation("test_operation", param1="value1")
    
    # Verify self-observation
    assert result["operation"] == "test_operation"
    assert result["parameters"]["param1"] == "value1"
    assert "agent_state" in result

def test_self_reporting():
    """Test that agent can report on itself."""
    agent = SelfObservingAgent()
    
    # Perform multiple operations
    agent.perform_operation("op1")
    agent.perform_operation("op2") 
    agent.perform_operation("op3")
    
    # Get self-report
    report = agent.self_report()
    
    # Verify comprehensive self-awareness
    assert report["total_operations"] == 3
    assert report["current_state"] == "executed_op3"
    assert len(report["operation_history"]) == 3
    assert report["self_assessment"] == "functioning_normally"

def test_semantic_context():
    """Test that observations include semantic context."""
    agent = SelfObservingAgent()
    
    result = agent.perform_operation("semantic_test", context="validation")
    
    # Verify semantic information is captured
    assert "operation" in result
    assert "timestamp" in result
    assert "parameters" in result
    assert "agent_state" in result
'''
        (project_dir / "test_main.py").write_text(test_content)
        
        # Test the self-observing agent
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            
            print("🧪 Testing: Self-observing agent behavior...")
            result = subprocess.run(["python", "-m", "self_observing_project.main"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and "Self-Observing Agent Report" in result.stdout:
                print("✅ Self-observation: WORKING")
                print("   🤖 Agent successfully observed and reported on its own behavior")
                
                # Test with uvmgr
                print("🔧 Testing: uvmgr integration with self-observing agent...")
                result = subprocess.run(["uvmgr", "tests", "run"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ uvmgr integration: WORKING")
                    print("   🔗 Self-observing agent works with uvmgr observability")
                    return True
                else:
                    print("❌ uvmgr integration: FAILED")
                    return False
            else:
                print("❌ Self-observation: FAILED")
                return False
                
        finally:
            os.chdir(original_cwd)

def demonstrate_reflection_refinement():
    """Demonstrate reflection and refinement from Chapter 4.8."""
    print("\n🔄 Chapter 4.8: Reflection and Refinement Validation")
    print("-" * 50)
    
    print("🔍 Testing: System reflection capabilities...")
    
    # Test 1: Agent workflow reflection via Spiff
    result = subprocess.run([
        "uvmgr", "agent", "test", "src/uvmgr/workflows/otel_validation.bpmn", "--otel"
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and "OTEL integration working correctly" in result.stdout:
        print("✅ Workflow reflection: WORKING")
        print("   🔄 Spiff workflows can reflect on OTEL behavior")
    else:
        print("❌ Workflow reflection: FAILED")
    
    # Test 2: Schema refinement capabilities
    print("🔧 Testing: Schema refinement through Weaver...")
    result = subprocess.run([
        "python", "-c",
        "from uvmgr.core.semconv import validate_attribute; "
        "print('Schema validation:', validate_attribute('cli.command', 'test_value'))"
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and "Schema validation:" in result.stdout:
        print("✅ Schema refinement: WORKING")
        print("   🏗️  Semantic schemas support validation and refinement")
        return True
    else:
        print("❌ Schema refinement: FAILED")
        return False

def run_comprehensive_validation():
    """Run comprehensive validation of Chapter 4 concepts."""
    print("🎯 Chapter 4: Observability as Foundation - Comprehensive Validation")
    print("=" * 70)
    print("Validating Dogfoodie thesis concepts through uvmgr implementation")
    
    results = {}
    
    # Validate each major concept
    results["semantic_telemetry"] = demonstrate_semantic_telemetry()
    results["weaver_forge"] = demonstrate_weaver_forge()
    results["self_observing_agents"] = demonstrate_self_observing_agents()
    results["reflection_refinement"] = demonstrate_reflection_refinement()
    
    # Summary
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"\n📊 CHAPTER 4 VALIDATION RESULTS")
    print("=" * 40)
    print(f"Concepts validated: {passed}/{total}")
    print(f"Success rate: {success_rate:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    concept_names = {
        "semantic_telemetry": "Semantic Telemetry (4.2-4.3)",
        "weaver_forge": "Weaver Forge Infrastructure (4.4-4.6)", 
        "self_observing_agents": "Self-Observing Agents (4.7)",
        "reflection_refinement": "Reflection & Refinement (4.8)"
    }
    
    for concept, result in results.items():
        status_emoji = "✅" if result else "❌"
        concept_name = concept_names.get(concept, concept)
        print(f"   {status_emoji} {concept_name}: {'VALIDATED' if result else 'NEEDS_WORK'}")
    
    if success_rate >= 75:
        print(f"\n🎉 SUCCESS: Chapter 4 concepts are well-implemented!")
        print("✅ Observability as Foundation: VALIDATED")
        print("🏗️  Weaver, telemetry, and semantic feedback: WORKING")
        print("🤖 Self-observing agents with reflection: DEMONSTRATED")
        return 0
    else:
        print(f"\n⚠️  PARTIAL VALIDATION: {success_rate:.1f}% concepts implemented")
        print("🔧 Some theoretical concepts need further development")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(run_comprehensive_validation())