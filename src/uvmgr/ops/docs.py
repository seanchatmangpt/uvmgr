#!/usr/bin/env python3
"""
Documentation operations layer with 8020 principles.

Business logic for multi-layered documentation generation:
- Executive/Business (20% effort, 80% stakeholder communication value)
- Solution Architecture (critical technical decision documentation) 
- Implementation (auto-generated from code with AI enhancement)
- Developer (onboarding and maintenance efficiency)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional, List
import time
from opentelemetry import trace

from ..runtime.docs import (
    create_executive_documentation,
    create_architecture_documentation,
    create_implementation_documentation,
    create_developer_documentation,
    analyze_project_structure,
    generate_documentation_metrics,
    publish_documentation_artifacts
)

tracer = trace.get_tracer(__name__)

# 8020 Documentation Layers with impact weighting
DOCUMENTATION_LAYERS = {
    "executive": {
        "weight": 0.30,  # High impact for stakeholder communication
        "priority": "critical",
        "audience": "business_stakeholders",
        "effort_multiplier": 0.2  # 20% effort for 80% stakeholder value
    },
    "architecture": {
        "weight": 0.30,  # High impact for technical decisions
        "priority": "critical", 
        "audience": "technical_leaders",
        "effort_multiplier": 0.3  # 30% effort for technical foundation
    },
    "implementation": {
        "weight": 0.25,  # Important for development efficiency
        "priority": "important",
        "audience": "developers",
        "effort_multiplier": 0.3  # 30% effort, mostly automated
    },
    "developer": {
        "weight": 0.15,  # Valuable for onboarding efficiency
        "priority": "important",
        "audience": "new_developers",
        "effort_multiplier": 0.2  # 20% effort for onboarding value
    }
}

DOCUMENTATION_TEMPLATES = {
    "startup": {
        "description": "Lean documentation for fast-moving startups",
        "focus_layers": ["executive", "developer"],
        "ai_enhancement": "high",
        "automation_level": "maximum"
    },
    "enterprise": {
        "description": "Comprehensive documentation for enterprise environments",
        "focus_layers": ["executive", "architecture", "implementation", "developer"],
        "ai_enhancement": "moderate",
        "automation_level": "balanced"
    },
    "technical": {
        "description": "Technical-first documentation for engineering teams",
        "focus_layers": ["architecture", "implementation"],
        "ai_enhancement": "moderate",
        "automation_level": "high"
    }
}

@tracer.start_as_current_span("docs.generate_complete_docs")
def generate_complete_docs(
    project_path: Path,
    layers: List[str],
    output_format: str = "markdown",
    ai_enhance: bool = True,
    auto_publish: bool = False,
    template: str = "enterprise"
) -> Dict[str, Any]:
    """
    Generate complete multi-layered documentation with 8020 optimization.
    
    Implements documentation strategy focused on maximum value:
    - Executive layer: 20% effort, 80% stakeholder communication value
    - Architecture layer: Critical technical foundation documentation
    - Implementation layer: Auto-generated with AI enhancement
    - Developer layer: Onboarding and maintenance efficiency
    
    Args:
        project_path: Path to project root
        layers: Documentation layers to generate
        output_format: Output format (markdown, html, pdf)
        ai_enhance: Use AI to enhance generated content
        auto_publish: Automatically publish to configured destinations
        template: Documentation template (startup, enterprise, technical)
        
    Returns:
        Dict with generation results and metadata
    """
    span = trace.get_current_span()
    span.set_attributes({
        "docs.layers": str(layers),
        "docs.output_format": output_format,
        "docs.ai_enhance": ai_enhance,
        "docs.auto_publish": auto_publish,
        "docs.template": template,
        "project.path": str(project_path)
    })
    
    start_time = time.time()
    
    try:
        # Analyze project structure first
        project_analysis = analyze_project_structure(
            project_path=project_path,
            include_dependencies=True,
            include_architecture=True
        )
        
        layers_generated = {}
        overall_coverage = 0.0
        total_weight = 0.0
        
        # Generate each requested layer
        for layer in layers:
            if layer not in DOCUMENTATION_LAYERS:
                continue
                
            layer_config = DOCUMENTATION_LAYERS[layer]
            layer_weight = layer_config["weight"]
            
            span.set_attribute(f"docs.layer.{layer}.generating", True)
            
            # Generate layer-specific documentation
            if layer == "executive":
                layer_result = generate_executive_docs(
                    project_path=project_path,
                    project_analysis=project_analysis,
                    output_format=output_format,
                    ai_enhance=ai_enhance
                )
            elif layer == "architecture":
                layer_result = generate_architecture_docs(
                    project_path=project_path,
                    project_analysis=project_analysis,
                    output_format=output_format,
                    include_diagrams=True
                )
            elif layer == "implementation":
                layer_result = generate_implementation_docs(
                    project_path=project_path,
                    project_analysis=project_analysis,
                    output_format=output_format,
                    auto_extract=True,
                    ai_enhance=ai_enhance
                )
            elif layer == "developer":
                layer_result = generate_developer_docs(
                    project_path=project_path,
                    project_analysis=project_analysis,
                    output_format=output_format,
                    include_setup=True
                )
            
            layers_generated[layer] = layer_result
            
            # Calculate weighted coverage
            layer_coverage = layer_result.get("coverage_score", 0.0)
            overall_coverage += layer_coverage * layer_weight
            total_weight += layer_weight
            
            span.set_attribute(f"docs.layer.{layer}.coverage", layer_coverage)
        
        # Calculate final metrics
        final_coverage = overall_coverage / total_weight if total_weight > 0 else 0.0
        generation_time = time.time() - start_time
        
        # Create output directory structure
        docs_dir = project_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Generate comprehensive metrics
        metrics_result = generate_documentation_metrics(
            project_path=project_path,
            layers_generated=layers_generated,
            overall_coverage=final_coverage
        )
        
        result = {
            "success": True,
            "layers_generated": layers_generated,
            "overall_coverage": final_coverage,
            "generation_time": generation_time,
            "output_directory": str(docs_dir),
            "metrics": metrics_result,
            "documentation_strategy": "8020_multilayer",
            "template_used": template
        }
        
        # Auto-publish if requested
        if auto_publish:
            publish_result = publish_documentation_artifacts(
                project_path=project_path,
                documentation_result=result
            )
            result["publishing_result"] = publish_result
        
        span.set_attributes({
            "docs.overall_coverage": final_coverage,
            "docs.generation_time": generation_time,
            "docs.layers_count": len(layers_generated)
        })
        
        return result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Documentation generation failed: {str(e)}",
            "generation_time": time.time() - start_time
        }

@tracer.start_as_current_span("docs.generate_executive_docs")
def generate_executive_docs(
    project_path: Path,
    project_analysis: Optional[Dict[str, Any]] = None,
    output_format: str = "markdown",
    include_metrics: bool = True,
    ai_enhance: bool = True
) -> Dict[str, Any]:
    """
    Generate executive/business documentation with maximum stakeholder value.
    
    Focuses on 20% effort that delivers 80% stakeholder communication value:
    - Project overview and business value proposition
    - Key metrics and success indicators
    - Strategic roadmap and milestones
    - Risk assessment and mitigation strategies
    - Resource requirements and ROI analysis
    
    Args:
        project_path: Path to project root
        project_analysis: Pre-analyzed project structure
        output_format: Output format for documentation
        include_metrics: Include business metrics and KPIs
        ai_enhance: Use AI to enhance business language and clarity
        
    Returns:
        Dict with executive documentation results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "docs.output_format": output_format,
        "docs.include_metrics": include_metrics,
        "docs.ai_enhance": ai_enhance,
        "project.path": str(project_path)
    })
    
    try:
        # Use project analysis or generate if not provided
        if project_analysis is None:
            project_analysis = analyze_project_structure(project_path)
        
        # Generate executive documentation using runtime layer
        exec_result = create_executive_documentation(
            project_path=project_path,
            project_analysis=project_analysis,
            output_format=output_format,
            include_metrics=include_metrics,
            ai_enhance=ai_enhance
        )
        
        # Calculate coverage based on executive needs
        sections_generated = exec_result.get("sections_generated", [])
        required_sections = ["overview", "business_value", "metrics", "roadmap", "risks"]
        coverage_score = (len(sections_generated) / len(required_sections)) * 100
        
        exec_result["coverage_score"] = coverage_score
        exec_result["layer"] = "executive"
        exec_result["audience"] = "business_stakeholders"
        
        span.set_attribute("docs.executive.coverage", coverage_score)
        
        return exec_result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Executive documentation generation failed: {str(e)}",
            "coverage_score": 0.0
        }

@tracer.start_as_current_span("docs.generate_architecture_docs")
def generate_architecture_docs(
    project_path: Path,
    project_analysis: Optional[Dict[str, Any]] = None,
    output_format: str = "markdown",
    include_diagrams: bool = True,
    detail_level: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Generate solution architecture documentation for technical decisions.
    
    Critical technical foundation documentation including:
    - System architecture and component design
    - Technology stack and architectural decisions
    - Integration patterns and data flow
    - Security architecture and compliance
    - Scalability and performance considerations
    - Deployment and infrastructure architecture
    
    Args:
        project_path: Path to project root
        project_analysis: Pre-analyzed project structure
        output_format: Output format for documentation
        include_diagrams: Generate architectural diagrams
        detail_level: Level of architectural detail
        
    Returns:
        Dict with architecture documentation results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "docs.output_format": output_format,
        "docs.include_diagrams": include_diagrams,
        "docs.detail_level": detail_level,
        "project.path": str(project_path)
    })
    
    try:
        # Use project analysis or generate if not provided
        if project_analysis is None:
            project_analysis = analyze_project_structure(project_path)
        
        # Generate architecture documentation using runtime layer
        arch_result = create_architecture_documentation(
            project_path=project_path,
            project_analysis=project_analysis,
            output_format=output_format,
            include_diagrams=include_diagrams,
            detail_level=detail_level
        )
        
        # Calculate coverage based on architecture completeness
        components = arch_result.get("architecture_components", [])
        required_components = ["system_design", "tech_stack", "integrations", "security", "scalability", "deployment"]
        coverage_score = (len(components) / len(required_components)) * 100
        
        arch_result["coverage_score"] = coverage_score
        arch_result["layer"] = "architecture"
        arch_result["audience"] = "technical_leaders"
        
        span.set_attribute("docs.architecture.coverage", coverage_score)
        
        return arch_result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Architecture documentation generation failed: {str(e)}",
            "coverage_score": 0.0
        }

@tracer.start_as_current_span("docs.generate_implementation_docs")
def generate_implementation_docs(
    project_path: Path,
    project_analysis: Optional[Dict[str, Any]] = None,
    output_format: str = "markdown",
    auto_extract: bool = True,
    include_examples: bool = True,
    ai_enhance: bool = True
) -> Dict[str, Any]:
    """
    Generate implementation documentation from code with AI enhancement.
    
    Auto-generated developer-focused documentation including:
    - API reference and endpoint documentation
    - Code module structure and dependencies
    - Configuration and environment setup
    - Usage examples and code snippets
    - Testing patterns and procedures
    - Troubleshooting guides and common issues
    
    Args:
        project_path: Path to project root
        project_analysis: Pre-analyzed project structure
        output_format: Output format for documentation
        auto_extract: Automatically extract from code
        include_examples: Include usage examples
        ai_enhance: Use AI to improve documentation quality
        
    Returns:
        Dict with implementation documentation results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "docs.output_format": output_format,
        "docs.auto_extract": auto_extract,
        "docs.include_examples": include_examples,
        "docs.ai_enhance": ai_enhance,
        "project.path": str(project_path)
    })
    
    try:
        # Use project analysis or generate if not provided
        if project_analysis is None:
            project_analysis = analyze_project_structure(project_path)
        
        # Generate implementation documentation using runtime layer
        impl_result = create_implementation_documentation(
            project_path=project_path,
            project_analysis=project_analysis,
            output_format=output_format,
            auto_extract=auto_extract,
            include_examples=include_examples,
            ai_enhance=ai_enhance
        )
        
        # Calculate API coverage
        modules_documented = impl_result.get("modules_documented", [])
        total_modules = project_analysis.get("total_modules", 1)
        api_coverage = (len(modules_documented) / total_modules) * 100
        
        impl_result["api_coverage"] = api_coverage
        impl_result["coverage_score"] = api_coverage
        impl_result["layer"] = "implementation"
        impl_result["audience"] = "developers"
        
        span.set_attribute("docs.implementation.coverage", api_coverage)
        
        return impl_result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Implementation documentation generation failed: {str(e)}",
            "coverage_score": 0.0
        }

@tracer.start_as_current_span("docs.generate_developer_docs")
def generate_developer_docs(
    project_path: Path,
    project_analysis: Optional[Dict[str, Any]] = None,
    output_format: str = "markdown",
    include_setup: bool = True,
    include_workflows: bool = True
) -> Dict[str, Any]:
    """
    Generate developer onboarding and maintenance documentation.
    
    Developer efficiency-focused documentation including:
    - Quick start guide and local development setup
    - Development workflows and best practices
    - Contributing guidelines and code standards
    - Testing and debugging procedures
    - Release and deployment processes
    - Maintenance and monitoring guides
    
    Args:
        project_path: Path to project root
        project_analysis: Pre-analyzed project structure
        output_format: Output format for documentation
        include_setup: Include development setup instructions
        include_workflows: Include development workflow guides
        
    Returns:
        Dict with developer documentation results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "docs.output_format": output_format,
        "docs.include_setup": include_setup,
        "docs.include_workflows": include_workflows,
        "project.path": str(project_path)
    })
    
    try:
        # Use project analysis or generate if not provided
        if project_analysis is None:
            project_analysis = analyze_project_structure(project_path)
        
        # Generate developer documentation using runtime layer
        dev_result = create_developer_documentation(
            project_path=project_path,
            project_analysis=project_analysis,
            output_format=output_format,
            include_setup=include_setup,
            include_workflows=include_workflows
        )
        
        # Calculate coverage based on developer needs
        guide_sections = dev_result.get("guide_sections", [])
        required_sections = ["quickstart", "setup", "workflows", "contributing", "testing", "deployment"]
        coverage_score = (len(guide_sections) / len(required_sections)) * 100
        
        dev_result["coverage_score"] = coverage_score
        dev_result["layer"] = "developer"
        dev_result["audience"] = "new_developers"
        
        span.set_attribute("docs.developer.coverage", coverage_score)
        
        return dev_result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Developer documentation generation failed: {str(e)}",
            "coverage_score": 0.0
        }

@tracer.start_as_current_span("docs.analyze_documentation_coverage")
def analyze_documentation_coverage(
    project_path: Path,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    Analyze documentation coverage and quality across all layers.
    
    Comprehensive analysis including:
    - Layer-by-layer coverage assessment
    - Documentation quality metrics
    - Content freshness and accuracy
    - Stakeholder alignment analysis
    - Coverage gap identification
    - Improvement recommendations
    
    Args:
        project_path: Path to project root
        detailed: Include detailed analysis per layer
        
    Returns:
        Dict with coverage analysis results
    """
    span = trace.get_current_span()
    span.set_attributes({
        "docs.detailed": detailed,
        "project.path": str(project_path)
    })
    
    try:
        # Analyze each documentation layer
        layer_coverage = {}
        total_coverage = 0.0
        total_weight = 0.0
        
        for layer_name, layer_config in DOCUMENTATION_LAYERS.items():
            # Check if documentation exists for this layer
            layer_weight = layer_config["weight"]
            
            # Analyze actual documentation coverage
            return NotImplemented
            
            layer_coverage[layer_name] = {
                "coverage": coverage,
                "quality": quality,
                "weight": layer_weight,
                "audience": layer_config["audience"],
                "priority": layer_config["priority"]
            }
            
            # Calculate weighted coverage
            total_coverage += coverage * layer_weight
            total_weight += layer_weight
        
        overall_coverage = total_coverage / total_weight if total_weight > 0 else 0.0
        
        # Calculate overall quality score
        quality_scores = [layer["quality"] for layer in layer_coverage.values()]
        quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Identify coverage gaps
        coverage_gaps = []
        for layer_name, layer_data in layer_coverage.items():
            if layer_data["coverage"] < 80.0 and layer_data["priority"] == "critical":
                coverage_gaps.append(f"{layer_name.title()} documentation needs improvement")
            elif layer_data["coverage"] < 70.0:
                coverage_gaps.append(f"{layer_name.title()} documentation is incomplete")
        
        result = {
            "success": True,
            "overall_coverage": overall_coverage,
            "quality_score": quality_score,
            "layer_coverage": layer_coverage,
            "layers_analyzed": list(DOCUMENTATION_LAYERS.keys()),
            "coverage_gaps": coverage_gaps,
            "analysis_strategy": "8020_weighted"
        }
        
        span.set_attributes({
            "docs.overall_coverage": overall_coverage,
            "docs.quality_score": quality_score,
            "docs.gaps_count": len(coverage_gaps)
        })
        
        return result
        
    except Exception as e:
        span.record_exception(e)
        return {
            "success": False,
            "error": f"Coverage analysis failed: {str(e)}",
            "overall_coverage": 0.0
        }

# Helper functions

def _calculate_weighted_coverage(layer_results: Dict[str, Any]) -> float:
    """Calculate weighted documentation coverage using 8020 principles."""
    total_weight = 0.0
    weighted_coverage = 0.0
    
    for layer_name, layer_result in layer_results.items():
        if layer_name not in DOCUMENTATION_LAYERS:
            continue
            
        layer_weight = DOCUMENTATION_LAYERS[layer_name]["weight"]
        layer_coverage = layer_result.get("coverage_score", 0.0)
        
        weighted_coverage += layer_coverage * layer_weight
        total_weight += layer_weight
    
    return weighted_coverage / total_weight if total_weight > 0 else 0.0

def _get_documentation_priorities(template: str) -> List[str]:
    """Get prioritized list of documentation layers based on template."""
    template_config = DOCUMENTATION_TEMPLATES.get(template, DOCUMENTATION_TEMPLATES["enterprise"])
    return template_config.get("focus_layers", list(DOCUMENTATION_LAYERS.keys()))
