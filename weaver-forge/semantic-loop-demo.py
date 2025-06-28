#!/usr/bin/env python3
"""
Semantic Feedback Loop Demonstration
====================================

This demonstrates the Weaver-Forge-OTEL feedback loop for self-evolving systems.
Based on PhD thesis Chapter 4: OpenTelemetry, Weaver, and Forge.
"""

import asyncio
import json
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Simulated OTEL spans for demonstration
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# Set up tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("semantic-loop-demo")

# Add console exporter for visibility
provider = trace.get_tracer_provider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)


@dataclass
class WeaverIntent:
    """Represents a Weaver template capturing semantic intent."""
    id: str
    goal: str
    agents: List[str]
    telemetry_bindings: Dict[str, Any]
    success_criteria: List[str]
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "WeaverIntent":
        """Load Weaver intent from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
            weaver = data['weaver']
            return cls(
                id=weaver['id'],
                goal=weaver['intent']['goal'],
                agents=[a['name'] for a in weaver['intent']['agents']],
                telemetry_bindings=weaver['telemetry'],
                success_criteria=weaver['intent']['success_criteria']
            )


@dataclass
class ForgeChange:
    """Represents a Forge-tracked change with metadata."""
    id: str
    timestamp: datetime
    change_type: str
    affected_files: List[str]
    weaver_source: str
    span_id: str
    validation_result: Optional[Dict[str, Any]] = None
    git_commit: Optional[str] = None
    
    def to_telemetry_attributes(self) -> Dict[str, Any]:
        """Convert to OTEL span attributes."""
        return {
            "forge.change_id": self.id,
            "forge.change_type": self.change_type,
            "forge.affected_files": ",".join(self.affected_files),
            "forge.weaver_source": self.weaver_source,
            "forge.validation_success": bool(self.validation_result)
        }


@dataclass
class SemanticFeedback:
    """Feedback derived from OTEL spans."""
    span_name: str
    success: bool
    duration_ms: float
    attributes: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    
    def suggests_improvement(self) -> bool:
        """Check if this feedback suggests system improvement needed."""
        return (
            not self.success or 
            self.duration_ms > 5000 or  # Slow operation
            len(self.errors) > 0 or
            self.attributes.get('success_rate', 100) < 80
        )


class SemanticFeedbackLoop:
    """
    Implements the Weaver-Forge-OTEL semantic feedback loop.
    
    This demonstrates how:
    1. Weaver captures intent
    2. Forge tracks changes 
    3. OTEL provides reflection
    4. The loop refines itself
    """
    
    def __init__(self):
        self.weaver_templates: Dict[str, WeaverIntent] = {}
        self.forge_changes: List[ForgeChange] = []
        self.feedback_history: List[SemanticFeedback] = []
        self.evolution_count = 0
        
    async def load_weaver_intent(self, yaml_path: Path) -> WeaverIntent:
        """Step 1: Load semantic intent from Weaver."""
        with tracer.start_as_current_span("weaver.load_intent") as span:
            intent = WeaverIntent.from_yaml(yaml_path)
            self.weaver_templates[intent.id] = intent
            
            span.set_attributes({
                "weaver.template_id": intent.id,
                "weaver.goal": intent.goal,
                "weaver.agent_count": len(intent.agents)
            })
            
            print(f"📋 Loaded Weaver intent: {intent.goal}")
            return intent
    
    async def execute_with_forge(self, intent: WeaverIntent) -> ForgeChange:
        """Step 2: Execute intent and track changes with Forge."""
        with tracer.start_as_current_span("forge.execute_change") as span:
            # Simulate executing the intent
            change = ForgeChange(
                id=f"change_{int(time.time())}",
                timestamp=datetime.now(),
                change_type="external_validation",
                affected_files=[
                    "test-external-projects.py",
                    "auto-install-uvmgr.sh"
                ],
                weaver_source=intent.id,
                span_id=format(span.get_span_context().span_id, '016x')
            )
            
            # Simulate validation
            await asyncio.sleep(0.5)  # Simulate work
            
            # Run validation (simulated results)
            success_rate = 78.6  # From our actual test results
            change.validation_result = {
                "success_rate": success_rate,
                "projects_tested": 5,
                "projects_passed": 2,
                "meets_criteria": success_rate >= 80
            }
            
            span.set_attributes(change.to_telemetry_attributes())
            span.set_attribute("validation.success_rate", success_rate)
            
            self.forge_changes.append(change)
            print(f"🔧 Forge tracked change: {change.id} (success rate: {success_rate}%)")
            
            return change
    
    async def collect_otel_feedback(self, change: ForgeChange) -> SemanticFeedback:
        """Step 3: Collect feedback from OTEL spans."""
        with tracer.start_as_current_span("otel.collect_feedback") as span:
            # Analyze the execution
            feedback = SemanticFeedback(
                span_name="external_project.validate",
                success=change.validation_result['meets_criteria'],
                duration_ms=1500,  # Simulated
                attributes={
                    "success_rate": change.validation_result['success_rate'],
                    "projects_tested": change.validation_result['projects_tested'],
                    "forge_change_id": change.id,
                    "improvement_needed": change.validation_result['success_rate'] < 80
                }
            )
            
            if not feedback.success:
                feedback.errors.append("Success rate below 80% threshold")
            
            span.set_attributes({
                "feedback.success": feedback.success,
                "feedback.improvement_needed": feedback.suggests_improvement()
            })
            
            self.feedback_history.append(feedback)
            print(f"📡 OTEL feedback: {'❌ Needs improvement' if feedback.suggests_improvement() else '✅ Working well'}")
            
            return feedback
    
    async def evolve_system(self, feedback: SemanticFeedback) -> Optional[WeaverIntent]:
        """Step 4: Use feedback to evolve the system."""
        if not feedback.suggests_improvement():
            return None
            
        with tracer.start_as_current_span("semantic.evolve") as span:
            print("🔄 Evolving system based on feedback...")
            
            # Analyze what needs improvement
            current_rate = feedback.attributes.get('success_rate', 0)
            gap = 80 - current_rate
            
            # Generate evolved intent (simplified for demo)
            evolved_intent = WeaverIntent(
                id=f"evolved_{self.evolution_count}",
                goal="Improve external project validation success rate",
                agents=["EnhancedValidator", "ErrorAnalyzer"],
                telemetry_bindings={
                    "focus_areas": ["lint_command_fixes", "installation_verification"]
                },
                success_criteria=[
                    f"Increase success rate by {gap:.1f}%",
                    "Fix identified failure patterns"
                ]
            )
            
            self.evolution_count += 1
            self.weaver_templates[evolved_intent.id] = evolved_intent
            
            span.set_attributes({
                "evolution.count": self.evolution_count,
                "evolution.current_rate": current_rate,
                "evolution.target_improvement": gap
            })
            
            print(f"🧬 Generated evolved intent: {evolved_intent.goal}")
            return evolved_intent
    
    async def demonstrate_loop(self):
        """Run the complete semantic feedback loop."""
        print("=== Semantic Feedback Loop Demonstration ===\n")
        
        # Load initial intent
        weaver_file = Path("/Users/sac/dev/uvmgr/weaver-forge/external-validation-feedback.yaml")
        intent = await self.load_weaver_intent(weaver_file)
        
        # Run the loop
        for iteration in range(3):
            print(f"\n--- Iteration {iteration + 1} ---")
            
            # Execute with Forge
            change = await self.execute_with_forge(intent)
            
            # Collect OTEL feedback
            feedback = await self.collect_otel_feedback(change)
            
            # Evolve if needed
            evolved = await self.evolve_system(feedback)
            if evolved:
                intent = evolved  # Use evolved intent in next iteration
            
            await asyncio.sleep(1)  # Pause between iterations
        
        # Final summary
        print("\n=== Loop Summary ===")
        print(f"Total executions: {len(self.forge_changes)}")
        print(f"Evolution count: {self.evolution_count}")
        print(f"Success rate progression: {[f.attributes.get('success_rate', 0) for f in self.feedback_history]}")
        
        # Show the feedback loop visualization
        print("\n=== Feedback Loop Visualization ===")
        print("""
        Weaver File ──→ LLM/Agent Execution
             ↑                    ↓
             │                    ↓
        Refined Template     Forge Patch + Tests
             ↑                    ↓
             │                    ↓
        Span Analysis ←── OTEL Span Emission
        """)


async def main():
    """Main demonstration entry point."""
    loop = SemanticFeedbackLoop()
    await loop.demonstrate_loop()
    
    print("\n✅ Semantic feedback loop demonstration complete!")
    print("\nThis demonstrates PhD thesis Chapter 4 concepts:")
    print("- Weaver: Declarative intention encoding")
    print("- Forge: Trace-aware system modification")
    print("- OTEL: System reflexivity and feedback")
    print("- Loop: Self-evolving intelligence")


if __name__ == "__main__":
    asyncio.run(main())