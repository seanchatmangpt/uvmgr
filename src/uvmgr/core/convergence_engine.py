"""
Technology Convergence Engine - Detecting Exponential Intersections
==================================================================

This module implements the convergence detection engine from "The Future Is Faster Than You Think" - 
identifying where multiple exponential technologies intersect to create transformative capabilities.

Key Convergence Areas:
- AI + Automation = Intelligent automation that improves itself
- AI + Sensors = Context-aware systems that understand the world
- AI + Networks = Distributed intelligence and collective learning
- Automation + Sensors = Self-monitoring and self-healing systems
- All Four Together = Autonomous, intelligent, connected, self-improving systems

The engine detects these convergences in the uvmgr ecosystem and suggests exponential opportunities.
"""

from __future__ import annotations

import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import asyncio

from uvmgr.core.semconv import (
    AIAttributes, WorkflowAttributes, CliAttributes, 
    ProcessAttributes, TestAttributes, ToolAttributes
)
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning, get_agi_insights


class TechnologyDomain(Enum):
    """Core technology domains for convergence detection."""
    AI = "artificial_intelligence"
    AUTOMATION = "automation"
    SENSORS = "sensors_telemetry"
    NETWORKS = "networks_connectivity"
    COMPUTE = "compute_processing"
    STORAGE = "storage_data"
    INTERFACE = "interfaces_ux"
    SECURITY = "security_privacy"


class ConvergenceLevel(Enum):
    """Levels of technology convergence."""
    NONE = "none"           # No convergence detected
    EMERGING = "emerging"   # Early signs of convergence
    ACTIVE = "active"       # Active convergence happening
    MATURE = "mature"       # Convergence is established
    EXPONENTIAL = "exponential"  # Exponential impact achieved


@dataclass
class TechnologyCapability:
    """Represents a specific technology capability in the system."""
    domain: TechnologyDomain
    name: str
    description: str
    maturity_level: float  # 0.0-1.0 indicating how mature this capability is
    usage_frequency: int   # How often this capability is used
    last_used: float
    
    # Convergence potential
    convergence_readiness: float  # 0.0-1.0 indicating readiness to converge
    active_convergences: Set[str] = field(default_factory=set)
    potential_convergences: List[str] = field(default_factory=list)
    
    # Impact metrics
    performance_impact: float = 0.0
    user_adoption: float = 0.0
    business_value: float = 0.0


@dataclass
class ConvergencePattern:
    """Represents a detected convergence pattern between technologies."""
    id: str
    name: str
    description: str
    
    # Participating technologies
    primary_domains: List[TechnologyDomain]
    
    # Convergence metrics
    convergence_level: ConvergenceLevel
    confidence_score: float  # 0.0-1.0 confidence in this convergence
    impact_multiplier: float  # Expected impact multiplier (1x, 10x, 100x, etc.)
    
    # Timeline (required fields)
    first_detected: float
    last_observed: float
    trend_direction: str  # "increasing", "stable", "decreasing"
    
    # Fields with defaults must come after fields without defaults
    secondary_domains: List[TechnologyDomain] = field(default_factory=list)
    
    # Evidence
    evidence_points: List[Dict[str, Any]] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)
    success_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Opportunities
    optimization_opportunities: List[str] = field(default_factory=list)
    expansion_opportunities: List[str] = field(default_factory=list)
    new_capability_opportunities: List[str] = field(default_factory=list)


@dataclass
class ExponentialOpportunity:
    """Represents an opportunity for exponential impact through convergence."""
    id: str
    name: str
    description: str
    
    # Contributing convergences
    required_convergences: List[str]
    
    # Impact assessment (required fields)
    potential_impact: float  # 1x to 1000x+ multiplier
    implementation_effort: float  # 0.0-1.0 effort required
    time_to_value: str  # "immediate", "short_term", "medium_term", "long_term"
    
    # Readiness assessment (required field)
    readiness_score: float  # 0.0-1.0 how ready we are to pursue this
    
    # Fields with defaults must come after fields without defaults
    enabling_convergences: List[str] = field(default_factory=list)
    blocking_factors: List[str] = field(default_factory=list)
    enabling_factors: List[str] = field(default_factory=list)
    
    # Implementation pathway
    implementation_steps: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)


class ConvergenceEngine:
    """
    Technology Convergence Detection and Opportunity Engine.
    
    Analyzes the uvmgr ecosystem to detect exponential convergences and opportunities.
    """
    
    def __init__(self):
        self.capabilities: Dict[str, TechnologyCapability] = {}
        self.convergence_patterns: Dict[str, ConvergencePattern] = {}
        self.exponential_opportunities: Dict[str, ExponentialOpportunity] = {}
        
        # Analysis state
        self.last_analysis: Optional[float] = None
        self.analysis_history: List[Dict[str, Any]] = []
        self.convergence_events: List[Dict[str, Any]] = []
        
        # Initialize built-in capabilities
        self._initialize_core_capabilities()
        self._initialize_known_convergences()
        self._initialize_exponential_opportunities()
    
    def _initialize_core_capabilities(self):
        """Initialize core technology capabilities detected in uvmgr."""
        
        # AI Capabilities
        self.capabilities["ai_dspy_reasoning"] = TechnologyCapability(
            domain=TechnologyDomain.AI,
            name="DSPy Reasoning",
            description="Advanced AI reasoning with DSPy framework",
            maturity_level=0.8,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.9
        )
        
        self.capabilities["ai_claude_integration"] = TechnologyCapability(
            domain=TechnologyDomain.AI,
            name="Claude AI Integration", 
            description="AI-powered development assistance",
            maturity_level=0.85,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.95
        )
        
        self.capabilities["ai_workflow_generation"] = TechnologyCapability(
            domain=TechnologyDomain.AI,
            name="AI Workflow Generation",
            description="Generate BPMN workflows from natural language",
            maturity_level=0.7,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.8
        )
        
        # Automation Capabilities
        self.capabilities["automation_spiff_workflows"] = TechnologyCapability(
            domain=TechnologyDomain.AUTOMATION,
            name="SpiffWorkflow Engine",
            description="BPMN workflow automation and orchestration",
            maturity_level=0.9,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.95
        )
        
        self.capabilities["automation_file_watching"] = TechnologyCapability(
            domain=TechnologyDomain.AUTOMATION,
            name="File System Automation",
            description="Event-driven automation based on file changes",
            maturity_level=0.8,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.85
        )
        
        self.capabilities["automation_ci_cd"] = TechnologyCapability(
            domain=TechnologyDomain.AUTOMATION,
            name="CI/CD Automation",
            description="Continuous integration and deployment workflows", 
            maturity_level=0.75,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.8
        )
        
        # Sensors/Telemetry Capabilities
        self.capabilities["telemetry_opentelemetry"] = TechnologyCapability(
            domain=TechnologyDomain.SENSORS,
            name="OpenTelemetry Integration",
            description="Comprehensive observability and telemetry",
            maturity_level=0.9,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.95
        )
        
        self.capabilities["telemetry_weaver_semconv"] = TechnologyCapability(
            domain=TechnologyDomain.SENSORS,
            name="Weaver Semantic Conventions",
            description="Standardized semantic observability",
            maturity_level=0.85,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.9
        )
        
        self.capabilities["telemetry_agi_reasoning"] = TechnologyCapability(
            domain=TechnologyDomain.SENSORS,
            name="AGI-Level Observability",
            description="Intelligent observation with causal reasoning",
            maturity_level=0.8,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.85
        )
        
        # Networks/Connectivity Capabilities
        self.capabilities["network_remote_execution"] = TechnologyCapability(
            domain=TechnologyDomain.NETWORKS,
            name="Remote Execution",
            description="Execute commands and workflows on remote systems",
            maturity_level=0.8,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.8
        )
        
        self.capabilities["network_mcp_protocol"] = TechnologyCapability(
            domain=TechnologyDomain.NETWORKS,
            name="Model Context Protocol",
            description="AI model communication and coordination",
            maturity_level=0.75,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.85
        )
        
        self.capabilities["network_api_interfaces"] = TechnologyCapability(
            domain=TechnologyDomain.NETWORKS,
            name="API Interfaces",
            description="RESTful and async API connectivity",
            maturity_level=0.85,
            usage_frequency=0,
            last_used=time.time(),
            convergence_readiness=0.9
        )
    
    def _initialize_known_convergences(self):
        """Initialize known convergence patterns."""
        
        # AI + Automation Convergence
        self.convergence_patterns["ai_automation_intelligent_workflows"] = ConvergencePattern(
            id="ai_automation_intelligent_workflows",
            name="Intelligent Workflow Automation",
            description="AI-powered workflows that adapt and improve themselves",
            primary_domains=[TechnologyDomain.AI, TechnologyDomain.AUTOMATION],
            convergence_level=ConvergenceLevel.ACTIVE,
            confidence_score=0.85,
            impact_multiplier=10.0,
            first_detected=time.time(),
            last_observed=time.time(),
            trend_direction="increasing",
            optimization_opportunities=[
                "AI-driven workflow optimization",
                "Self-healing workflow execution",
                "Predictive workflow scheduling"
            ]
        )
        
        # AI + Sensors Convergence
        self.convergence_patterns["ai_telemetry_intelligent_observability"] = ConvergencePattern(
            id="ai_telemetry_intelligent_observability",
            name="Intelligent Observability",
            description="AI-enhanced telemetry with causal reasoning and predictive insights",
            primary_domains=[TechnologyDomain.AI, TechnologyDomain.SENSORS],
            convergence_level=ConvergenceLevel.ACTIVE,
            confidence_score=0.9,
            impact_multiplier=8.0,
            first_detected=time.time(),
            last_observed=time.time(),
            trend_direction="increasing",
            optimization_opportunities=[
                "Predictive failure detection",
                "Automated root cause analysis",
                "Self-tuning observability"
            ]
        )
        
        # Automation + Sensors Convergence
        self.convergence_patterns["automation_telemetry_self_monitoring"] = ConvergencePattern(
            id="automation_telemetry_self_monitoring",
            name="Self-Monitoring Automation",
            description="Automated systems that monitor and adjust themselves",
            primary_domains=[TechnologyDomain.AUTOMATION, TechnologyDomain.SENSORS],
            convergence_level=ConvergenceLevel.ACTIVE,
            confidence_score=0.8,
            impact_multiplier=5.0,
            first_detected=time.time(),
            last_observed=time.time(),
            trend_direction="increasing"
        )
        
        # AI + Networks Convergence
        self.convergence_patterns["ai_network_distributed_intelligence"] = ConvergencePattern(
            id="ai_network_distributed_intelligence",
            name="Distributed AI Intelligence",
            description="Networked AI systems that share knowledge and capabilities",
            primary_domains=[TechnologyDomain.AI, TechnologyDomain.NETWORKS],
            convergence_level=ConvergenceLevel.EMERGING,
            confidence_score=0.7,
            impact_multiplier=15.0,
            first_detected=time.time(),
            last_observed=time.time(),
            trend_direction="increasing"
        )
    
    def _initialize_exponential_opportunities(self):
        """Initialize exponential opportunities from convergences."""
        
        self.exponential_opportunities["autonomous_development_system"] = ExponentialOpportunity(
            id="autonomous_development_system",
            name="Autonomous Development System",
            description="AI system that can develop, test, and deploy software autonomously",
            required_convergences=[
                "ai_automation_intelligent_workflows",
                "ai_telemetry_intelligent_observability"
            ],
            enabling_convergences=[
                "ai_network_distributed_intelligence"
            ],
            potential_impact=100.0,  # 100x impact
            implementation_effort=0.8,
            time_to_value="medium_term",
            readiness_score=0.6,
            implementation_steps=[
                "Enhance AI workflow generation capabilities",
                "Integrate autonomous testing and validation",
                "Implement self-improving deployment pipelines",
                "Add autonomous error detection and fixing",
                "Enable cross-system learning and adaptation"
            ]
        )
        
        self.exponential_opportunities["predictive_infrastructure"] = ExponentialOpportunity(
            id="predictive_infrastructure",
            name="Predictive Infrastructure Management",
            description="Infrastructure that predicts and prevents problems before they occur",
            required_convergences=[
                "ai_telemetry_intelligent_observability",
                "automation_telemetry_self_monitoring"
            ],
            potential_impact=25.0,  # 25x impact
            implementation_effort=0.6,
            time_to_value="short_term",
            readiness_score=0.8,
            implementation_steps=[
                "Enhance telemetry collection and analysis",
                "Implement predictive failure models",
                "Add automated remediation capabilities",
                "Enable proactive optimization"
            ]
        )
        
        self.exponential_opportunities["democratized_ai_development"] = ExponentialOpportunity(
            id="democratized_ai_development",
            name="Democratized AI Development",
            description="Enable anyone to build AI-powered applications without technical expertise",
            required_convergences=[
                "ai_automation_intelligent_workflows"
            ],
            enabling_convergences=[
                "ai_network_distributed_intelligence"
            ],
            potential_impact=50.0,  # 50x impact through democratization
            implementation_effort=0.7,
            time_to_value="medium_term",
            readiness_score=0.7,
            implementation_steps=[
                "Expand natural language to code generation",
                "Create intelligent template system",
                "Implement guided development workflows",
                "Add automated best practices enforcement"
            ]
        )
    
    def analyze_convergences(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze current state to detect convergences and opportunities.
        
        Returns comprehensive analysis of convergence state and opportunities.
        """
        context = context or {}
        analysis_start = time.time()
        
        # Update capability usage from recent activity
        self._update_capability_usage()
        
        # Detect new convergences
        new_convergences = self._detect_emerging_convergences()
        
        # Update existing convergence strengths
        self._update_convergence_strengths()
        
        # Identify exponential opportunities
        opportunities = self._identify_exponential_opportunities()
        
        # Generate recommendations
        recommendations = self._generate_convergence_recommendations()
        
        analysis_result = {
            "analysis_timestamp": analysis_start,
            "total_capabilities": len(self.capabilities),
            "active_convergences": len([c for c in self.convergence_patterns.values() 
                                      if c.convergence_level in [ConvergenceLevel.ACTIVE, ConvergenceLevel.MATURE]]),
            "emerging_convergences": len([c for c in self.convergence_patterns.values() 
                                        if c.convergence_level == ConvergenceLevel.EMERGING]),
            "exponential_opportunities": len(self.exponential_opportunities),
            "ready_opportunities": len([o for o in self.exponential_opportunities.values() 
                                      if o.readiness_score > 0.7]),
            "new_convergences_detected": len(new_convergences),
            "convergence_summary": self._generate_convergence_summary(),
            "top_opportunities": opportunities[:5],  # Top 5 opportunities
            "recommendations": recommendations,
            "convergence_score": self._calculate_overall_convergence_score()
        }
        
        # Store analysis
        self.last_analysis = analysis_start
        self.analysis_history.append(analysis_result)
        
        # Keep only last 50 analyses
        if len(self.analysis_history) > 50:
            self.analysis_history = self.analysis_history[-50:]
        
        # AGI reasoning observation
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "convergence_analysis",
                "convergences_detected": str(analysis_result["active_convergences"]),
                "opportunities_identified": str(analysis_result["exponential_opportunities"]),
                "convergence_score": str(analysis_result["convergence_score"])
            },
            context={
                "convergence_analysis": True,
                "exponential_technologies": True
            }
        )
        
        return analysis_result
    
    def _update_capability_usage(self):
        """Update capability usage based on system activity."""
        # This would integrate with telemetry data in a real implementation
        current_time = time.time()
        
        # Mock usage updates - in reality would come from OTEL data
        for capability in self.capabilities.values():
            # Update based on command usage patterns
            if "ai" in capability.name.lower():
                capability.usage_frequency += 1
                capability.last_used = current_time
            
            if "automation" in capability.name.lower():
                capability.usage_frequency += 1
                capability.last_used = current_time
    
    def _detect_emerging_convergences(self) -> List[ConvergencePattern]:
        """Detect new emerging convergence patterns."""
        new_convergences = []
        
        # Look for capability combinations that are being used together
        active_capabilities = [cap for cap in self.capabilities.values() 
                             if cap.usage_frequency > 0 and cap.convergence_readiness > 0.7]
        
        # Group by domain
        domain_groups = defaultdict(list)
        for cap in active_capabilities:
            domain_groups[cap.domain].append(cap)
        
        # Look for cross-domain activity patterns
        for domain1, caps1 in domain_groups.items():
            for domain2, caps2 in domain_groups.items():
                if domain1 != domain2:
                    convergence_id = f"{domain1.value}_{domain2.value}_emerging"
                    
                    # Check if this convergence already exists
                    if convergence_id not in self.convergence_patterns:
                        # Create new convergence pattern
                        new_convergence = ConvergencePattern(
                            id=convergence_id,
                            name=f"{domain1.value.replace('_', ' ').title()} + {domain2.value.replace('_', ' ').title()}",
                            description=f"Emerging convergence between {domain1.value} and {domain2.value}",
                            primary_domains=[domain1, domain2],
                            convergence_level=ConvergenceLevel.EMERGING,
                            confidence_score=0.6,
                            impact_multiplier=3.0,
                            first_detected=time.time(),
                            last_observed=time.time(),
                            trend_direction="increasing"
                        )
                        
                        self.convergence_patterns[convergence_id] = new_convergence
                        new_convergences.append(new_convergence)
        
        return new_convergences
    
    def _update_convergence_strengths(self):
        """Update the strength and level of existing convergences."""
        for convergence in self.convergence_patterns.values():
            # Calculate convergence strength based on usage patterns
            primary_caps = [cap for cap in self.capabilities.values() 
                          if cap.domain in convergence.primary_domains]
            
            if primary_caps:
                avg_usage = sum(cap.usage_frequency for cap in primary_caps) / len(primary_caps)
                avg_readiness = sum(cap.convergence_readiness for cap in primary_caps) / len(primary_caps)
                
                # Update convergence level based on usage and readiness
                convergence_strength = (avg_usage / 10.0 + avg_readiness) / 2.0  # Normalize
                
                if convergence_strength > 0.9:
                    convergence.convergence_level = ConvergenceLevel.EXPONENTIAL
                elif convergence_strength > 0.7:
                    convergence.convergence_level = ConvergenceLevel.MATURE
                elif convergence_strength > 0.5:
                    convergence.convergence_level = ConvergenceLevel.ACTIVE
                elif convergence_strength > 0.3:
                    convergence.convergence_level = ConvergenceLevel.EMERGING
                
                # Update confidence score
                convergence.confidence_score = min(1.0, convergence.confidence_score + 0.05)
                convergence.last_observed = time.time()
    
    def _identify_exponential_opportunities(self) -> List[Dict[str, Any]]:
        """Identify and rank exponential opportunities."""
        opportunities = []
        
        for opp in self.exponential_opportunities.values():
            # Calculate readiness based on required convergences
            required_convergences_ready = 0
            for conv_id in opp.required_convergences:
                conv = self.convergence_patterns.get(conv_id)
                if conv and conv.convergence_level in [ConvergenceLevel.ACTIVE, ConvergenceLevel.MATURE]:
                    required_convergences_ready += 1
            
            readiness_ratio = required_convergences_ready / len(opp.required_convergences)
            opp.readiness_score = readiness_ratio
            
            # Calculate priority score (impact vs effort vs readiness)
            priority_score = (opp.potential_impact * opp.readiness_score) / max(0.1, opp.implementation_effort)
            
            opportunities.append({
                "opportunity": opp,
                "priority_score": priority_score,
                "readiness_ratio": readiness_ratio,
                "required_convergences_ready": required_convergences_ready,
                "total_required": len(opp.required_convergences)
            })
        
        # Sort by priority score
        opportunities.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return opportunities
    
    def _generate_convergence_recommendations(self) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on convergence analysis."""
        recommendations = []
        
        # Recommendations based on strong convergences
        strong_convergences = [c for c in self.convergence_patterns.values() 
                             if c.convergence_level in [ConvergenceLevel.ACTIVE, ConvergenceLevel.MATURE]]
        
        for convergence in strong_convergences:
            if convergence.optimization_opportunities:
                recommendations.append({
                    "type": "optimization",
                    "title": f"Optimize {convergence.name}",
                    "description": f"Leverage the strong convergence in {convergence.name} for optimization",
                    "actions": convergence.optimization_opportunities[:3],
                    "impact": convergence.impact_multiplier,
                    "confidence": convergence.confidence_score
                })
        
        # Recommendations for emerging convergences
        emerging_convergences = [c for c in self.convergence_patterns.values() 
                               if c.convergence_level == ConvergenceLevel.EMERGING]
        
        for convergence in emerging_convergences:
            recommendations.append({
                "type": "development",
                "title": f"Develop {convergence.name}",
                "description": f"Nurture the emerging convergence in {convergence.name}",
                "actions": [
                    f"Increase usage of {domain.value} capabilities" 
                    for domain in convergence.primary_domains
                ],
                "impact": convergence.impact_multiplier,
                "confidence": convergence.confidence_score
            })
        
        # Recommendations for exponential opportunities
        ready_opportunities = [o for o in self.exponential_opportunities.values() 
                             if o.readiness_score > 0.6]
        
        for opportunity in ready_opportunities:
            recommendations.append({
                "type": "exponential_opportunity",
                "title": f"Pursue {opportunity.name}",
                "description": opportunity.description,
                "actions": opportunity.implementation_steps[:3],
                "impact": opportunity.potential_impact,
                "confidence": opportunity.readiness_score
            })
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _generate_convergence_summary(self) -> Dict[str, Any]:
        """Generate a summary of current convergence state."""
        return {
            "strongest_convergence": max(
                self.convergence_patterns.values(),
                key=lambda x: x.confidence_score,
                default=None
            ),
            "most_impactful_opportunity": max(
                self.exponential_opportunities.values(),
                key=lambda x: x.potential_impact,
                default=None
            ),
            "convergence_distribution": {
                level.value: len([c for c in self.convergence_patterns.values() 
                                if c.convergence_level == level])
                for level in ConvergenceLevel
            },
            "domain_activity": {
                domain.value: len([cap for cap in self.capabilities.values() 
                                 if cap.domain == domain and cap.usage_frequency > 0])
                for domain in TechnologyDomain
            }
        }
    
    def _calculate_overall_convergence_score(self) -> float:
        """Calculate overall convergence maturity score (0.0-1.0)."""
        if not self.convergence_patterns:
            return 0.0
        
        # Weight convergences by their level and confidence
        level_weights = {
            ConvergenceLevel.NONE: 0.0,
            ConvergenceLevel.EMERGING: 0.2,
            ConvergenceLevel.ACTIVE: 0.6,
            ConvergenceLevel.MATURE: 0.8,
            ConvergenceLevel.EXPONENTIAL: 1.0
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for convergence in self.convergence_patterns.values():
            weight = level_weights[convergence.convergence_level] * convergence.confidence_score
            total_score += weight
            total_weight += 1.0
        
        return total_score / max(1.0, total_weight)
    
    def get_convergence_status(self) -> Dict[str, Any]:
        """Get current convergence status without full analysis."""
        return {
            "total_capabilities": len(self.capabilities),
            "total_convergences": len(self.convergence_patterns),
            "active_convergences": len([c for c in self.convergence_patterns.values() 
                                      if c.convergence_level in [ConvergenceLevel.ACTIVE, ConvergenceLevel.MATURE]]),
            "exponential_opportunities": len(self.exponential_opportunities),
            "last_analysis": self.last_analysis,
            "convergence_score": self._calculate_overall_convergence_score()
        }
    
    def record_convergence_event(self, event_type: str, description: str, metadata: Dict[str, Any] = None):
        """Record a convergence-related event for analysis."""
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "description": description,
            "metadata": metadata or {}
        }
        
        self.convergence_events.append(event)
        
        # Keep only recent events
        if len(self.convergence_events) > 1000:
            self.convergence_events = self.convergence_events[-1000:]
    
    def get_exponential_opportunity(self, opportunity_id: str) -> Optional[ExponentialOpportunity]:
        """Get a specific exponential opportunity by ID."""
        return self.exponential_opportunities.get(opportunity_id)
    
    def get_convergence_pattern(self, pattern_id: str) -> Optional[ConvergencePattern]:
        """Get a specific convergence pattern by ID."""
        return self.convergence_patterns.get(pattern_id)


# Global convergence engine instance
_convergence_engine: Optional[ConvergenceEngine] = None

def get_convergence_engine() -> ConvergenceEngine:
    """Get the global convergence engine instance."""
    global _convergence_engine
    
    if _convergence_engine is None:
        _convergence_engine = ConvergenceEngine()
    
    return _convergence_engine

def analyze_convergences(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Analyze technology convergences in the current context."""
    engine = get_convergence_engine()
    return engine.analyze_convergences(context)

def get_convergence_recommendations() -> List[Dict[str, Any]]:
    """Get current convergence recommendations."""
    engine = get_convergence_engine()
    analysis = engine.analyze_convergences()
    return analysis.get("recommendations", [])

def record_convergence_activity(activity_type: str, description: str, metadata: Dict[str, Any] = None):
    """Record convergence-related activity for analysis."""
    engine = get_convergence_engine()
    engine.record_convergence_event(activity_type, description, metadata)