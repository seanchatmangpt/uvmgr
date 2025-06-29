"""
uvmgr.ops.mermaid - Mermaid Operations with Weaver Forge + DSPy
==============================================================

Business logic for Mermaid diagram generation using 80/20 principles
with Weaver Forge semantic conventions and DSPy intelligent processing.

This module provides the core operations layer for Mermaid diagram generation,
integrating with Weaver Forge for telemetry-driven diagrams and DSPy for
intelligent content processing.

Key Features
-----------
• **80/20 Prioritized Diagrams**: Focus on highest-value diagram types
• **Weaver Forge Integration**: Generate diagrams from OTEL data
• **DSPy Intelligence**: AI-powered diagram generation and optimization
• **Template System**: Reusable diagram patterns
• **Validation & Analysis**: Comprehensive diagram quality assessment
• **Export Pipeline**: Multi-format output support

Architecture Integration
----------------------
- **Commands Layer**: Rich CLI interface with Typer
- **Operations Layer**: This module - DSPy coordination and business logic
- **Runtime Layer**: File operations, parsing, export processing

Weaver Forge Features
-------------------
• Service dependency mapping from traces
• Telemetry flow visualization
• Semantic convention validation
• Architecture diagram auto-generation

DSPy Capabilities
----------------
• Intelligent diagram type selection
• Content-aware layout optimization
• Entity relationship inference
• Smart label generation

See Also
--------
- :mod:`uvmgr.runtime.mermaid` : Runtime implementation
- :mod:`uvmgr.commands.mermaid` : CLI interface
- :mod:`uvmgr.core.weaver` : Weaver Forge integration
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from uvmgr.core.shell import timed
from uvmgr.core.telemetry import span, record_exception
from uvmgr.core.instrumentation import add_span_attributes, add_span_event

# DSPy imports (with graceful fallback)
try:
    import dspy
    from dspy import Signature, InputField, OutputField, ChainOfThought
    HAS_DSPY = True
except ImportError:
    HAS_DSPY = False
    print("DSPy not available - using fallback implementations")


# DSPy Signatures for Mermaid Generation
if HAS_DSPY:
    class GenerateMermaidDiagram(Signature):
        """Generate Mermaid diagram code from input content."""
        content: str = InputField(desc="Source content to convert to diagram")
        diagram_type: str = InputField(desc="Type of Mermaid diagram: flowchart, sequence, class, etc.")
        title: str = InputField(desc="Diagram title")
        complexity_preference: str = InputField(desc="Complexity preference: simple, medium, detailed")
        
        mermaid_code: str = OutputField(desc="Generated Mermaid diagram code")
        nodes_identified: str = OutputField(desc="JSON list of identified nodes/entities")
        relationships: str = OutputField(desc="JSON list of relationships between entities")
        confidence_score: float = OutputField(desc="Confidence in generation quality (0-1)")
        suggestions: str = OutputField(desc="JSON list of improvement suggestions")
    
    class OptimizeMermaidLayout(Signature):
        """Optimize Mermaid diagram layout and structure."""
        mermaid_code: str = InputField(desc="Current Mermaid diagram code")
        optimization_goal: str = InputField(desc="Goal: readability, compactness, aesthetics, flow")
        diagram_type: str = InputField(desc="Type of diagram being optimized")
        
        optimized_code: str = OutputField(desc="Optimized Mermaid diagram code")
        improvements: str = OutputField(desc="JSON list of improvements made")
        layout_score: float = OutputField(desc="Layout quality score (0-10)")
        rationale: str = OutputField(desc="Explanation of optimization decisions")
    
    class AnalyzeDiagramComplexity(Signature):
        """Analyze Mermaid diagram complexity and suggest simplifications."""
        mermaid_code: str = InputField(desc="Mermaid diagram code to analyze")
        target_audience: str = InputField(desc="Target audience: technical, business, general")
        
        complexity_score: float = OutputField(desc="Complexity score (0-10)")
        readability_score: float = OutputField(desc="Readability score (0-10)")
        recommendations: str = OutputField(desc="JSON list of simplification recommendations")
        metrics: str = OutputField(desc="JSON dict of complexity metrics")
    
    class GenerateWeaverDiagram(Signature):
        """Generate architecture diagrams from Weaver Forge telemetry data."""
        telemetry_data: str = InputField(desc="JSON telemetry data from OTEL/Weaver")
        diagram_type: str = InputField(desc="Architecture diagram type: service-map, sequence, flow")
        focus_area: str = InputField(desc="Focus area: services, traces, dependencies")
        
        architecture_diagram: str = OutputField(desc="Generated Mermaid architecture diagram")
        services_identified: str = OutputField(desc="JSON list of identified services")
        dependencies: str = OutputField(desc="JSON list of service dependencies")
        insights: str = OutputField(desc="Key architectural insights discovered")


# DSPy Programs
if HAS_DSPY:
    class MermaidGenerator(dspy.Module):
        def __init__(self):
            super().__init__()
            self.generate = ChainOfThought(GenerateMermaidDiagram)
        
        def forward(self, content, diagram_type="flowchart", title="Diagram", complexity="medium"):
            return self.generate(
                content=content,
                diagram_type=diagram_type,
                title=title,
                complexity_preference=complexity
            )
    
    class MermaidOptimizer(dspy.Module):
        def __init__(self):
            super().__init__()
            self.optimize = ChainOfThought(OptimizeMermaidLayout)
        
        def forward(self, mermaid_code, goal="readability", diagram_type="flowchart"):
            return self.optimize(
                mermaid_code=mermaid_code,
                optimization_goal=goal,
                diagram_type=diagram_type
            )
    
    class ComplexityAnalyzer(dspy.Module):
        def __init__(self):
            super().__init__()
            self.analyze = ChainOfThought(AnalyzeDiagramComplexity)
        
        def forward(self, mermaid_code, audience="technical"):
            return self.analyze(
                mermaid_code=mermaid_code,
                target_audience=audience
            )
    
    class WeaverDiagramGenerator(dspy.Module):
        def __init__(self):
            super().__init__()
            self.generate = ChainOfThought(GenerateWeaverDiagram)
        
        def forward(self, telemetry_data, diagram_type="service-map", focus="services"):
            return self.generate(
                telemetry_data=telemetry_data,
                diagram_type=diagram_type,
                focus_area=focus
            )


@timed
def generate_mermaid_diagram(
    diagram_type: str,
    source: Optional[Path] = None,
    input_text: Optional[str] = None,
    source_type: str = "auto",
    title: Optional[str] = None,
    use_dspy: bool = True,
    weaver_integration: bool = False,
) -> Dict[str, Any]:
    """Generate Mermaid diagram using DSPy intelligence."""
    with span("mermaid.generate", diagram_type=diagram_type, source_type=source_type):
        add_span_attributes(**{
            "mermaid.diagram_type": diagram_type,
            "mermaid.source_type": source_type,
            "mermaid.use_dspy": use_dspy,
            "mermaid.weaver_integration": weaver_integration,
        })
        
        try:
            from uvmgr.runtime import mermaid as _rt
            
            # Load and process content
            if source:
                content = _rt.load_diagram_source(source, source_type)
            elif input_text:
                content = input_text
            else:
                raise ValueError("Either source file or input text must be provided")
            
            # Weaver Forge integration for architecture diagrams
            if weaver_integration:
                telemetry_data = _rt.extract_weaver_data()
                content = f"TELEMETRY_DATA:\n{json.dumps(telemetry_data)}\n\nCONTENT:\n{content}"
            
            if HAS_DSPY and use_dspy:
                try:
                    # Use DSPy for intelligent generation
                    generator = MermaidGenerator()
                    result = generator(
                        content,
                        diagram_type,
                        title or f"Generated {diagram_type.title()} Diagram",
                        "medium"
                    )
                except Exception as dspy_error:
                    # Fallback to template if DSPy fails (e.g., no LM configured)
                    print(f"DSPy generation failed ({dspy_error}), using template fallback")
                    generation_result = _rt.generate_diagram_template(
                        content, diagram_type, title, source_type
                    )
                    generation_result["generation_method"] = "template_fallback"
                    
                    # Calculate statistics and add missing fields
                    stats = _rt.calculate_diagram_statistics(generation_result["mermaid_code"])
                    generation_result["statistics"] = stats
                    generation_result["nodes_count"] = len(generation_result.get("nodes", []))
                    generation_result["edges_count"] = len(generation_result.get("relationships", []))
                    generation_result["complexity_score"] = stats.get("complexity_score", 0)
                    
                    add_span_event("mermaid.generation.completed", {
                        "diagram_type": diagram_type,
                        "nodes_count": generation_result["nodes_count"],
                        "edges_count": generation_result["edges_count"],
                        "generation_method": generation_result["generation_method"],
                        "confidence": generation_result.get("confidence_score", 0),
                    })
                    
                    return generation_result
                
                # Parse DSPy outputs
                nodes = json.loads(result.nodes_identified) if result.nodes_identified else []
                relationships = json.loads(result.relationships) if result.relationships else []
                suggestions = json.loads(result.suggestions) if result.suggestions else []
                
                generation_result = {
                    "mermaid_code": result.mermaid_code,
                    "nodes": nodes,
                    "relationships": relationships,
                    "confidence_score": result.confidence_score,
                    "suggestions": suggestions,
                    "generation_method": "dspy",
                }
            else:
                # Fallback to template-based generation
                generation_result = _rt.generate_diagram_template(
                    content, diagram_type, title, source_type
                )
                generation_result["generation_method"] = "template"
            
            # Calculate statistics
            stats = _rt.calculate_diagram_statistics(generation_result["mermaid_code"])
            generation_result["statistics"] = stats
            
            # Add nodes/edges counts for telemetry
            generation_result["nodes_count"] = len(generation_result.get("nodes", []))
            generation_result["edges_count"] = len(generation_result.get("relationships", []))
            generation_result["complexity_score"] = stats.get("complexity_score", 0)
            
            add_span_event("mermaid.generation.completed", {
                "diagram_type": diagram_type,
                "nodes_count": generation_result["nodes_count"],
                "edges_count": generation_result["edges_count"],
                "generation_method": generation_result["generation_method"],
                "confidence": generation_result.get("confidence_score", 0),
            })
            
            return generation_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def generate_weaver_diagram(
    diagram_type: str = "architecture",
    service_map: bool = False,
    telemetry_flow: bool = False,
    semantic_conventions: bool = False,
    trace_analysis: bool = False,
) -> Dict[str, Any]:
    """Generate diagrams from Weaver Forge and OTEL data."""
    with span("mermaid.weaver_generate", diagram_type=diagram_type):
        add_span_attributes(**{
            "mermaid.diagram_type": diagram_type,
            "mermaid.service_map": service_map,
            "mermaid.telemetry_flow": telemetry_flow,
            "mermaid.semantic_conventions": semantic_conventions,
            "mermaid.trace_analysis": trace_analysis,
        })
        
        try:
            from uvmgr.runtime import mermaid as _rt
            
            # Extract Weaver Forge data
            weaver_data = _rt.extract_weaver_telemetry_data(
                service_map=service_map,
                telemetry_flow=telemetry_flow,
                semantic_conventions=semantic_conventions,
                trace_analysis=trace_analysis,
            )
            
            if HAS_DSPY:
                try:
                    # Use DSPy for intelligent Weaver diagram generation
                    weaver_generator = WeaverDiagramGenerator()
                    result = weaver_generator(
                        json.dumps(weaver_data),
                        diagram_type,
                        "services" if service_map else "traces"
                    )
                except Exception as dspy_error:
                    # Fallback to template if DSPy fails (e.g., no LM configured)
                    print(f"DSPy generation failed ({dspy_error}), using template fallback")
                    generation_result = _rt.generate_weaver_diagram_template(
                        weaver_data, diagram_type, service_map, telemetry_flow
                    )
                    generation_result["generation_method"] = "template_weaver_fallback"
                    
                    generation_result["services_count"] = len(generation_result.get("services", []))
                    generation_result["spans_count"] = weaver_data.get("spans_count", 0)
                    generation_result["conventions_count"] = weaver_data.get("conventions_count", 0)
                    
                    add_span_event("mermaid.weaver.completed", {
                        "diagram_type": diagram_type,
                        "services_count": generation_result["services_count"],
                        "spans_analyzed": generation_result["spans_count"],
                        "conventions_used": generation_result["conventions_count"],
                    })
                    
                    return generation_result
                
                # Parse DSPy outputs
                services = json.loads(result.services_identified) if result.services_identified else []
                dependencies = json.loads(result.dependencies) if result.dependencies else []
                
                generation_result = {
                    "mermaid_code": result.architecture_diagram,
                    "services": services,
                    "dependencies": dependencies,
                    "insights": result.insights,
                    "weaver_analysis": weaver_data,
                    "generation_method": "dspy_weaver",
                }
            else:
                # Fallback to template-based Weaver generation
                generation_result = _rt.generate_weaver_diagram_template(
                    weaver_data, diagram_type, service_map, telemetry_flow
                )
                generation_result["generation_method"] = "template_weaver"
            
            # Add analysis statistics
            generation_result["services_count"] = len(generation_result.get("services", []))
            generation_result["spans_count"] = weaver_data.get("spans_count", 0)
            generation_result["conventions_count"] = weaver_data.get("conventions_count", 0)
            
            add_span_event("mermaid.weaver.completed", {
                "diagram_type": diagram_type,
                "services_count": generation_result["services_count"],
                "spans_analyzed": generation_result["spans_count"],
                "conventions_used": generation_result["conventions_count"],
            })
            
            return generation_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def validate_mermaid_diagram(
    mermaid_code: str,
    strict: bool = False,
    check_syntax: bool = True,
    check_semantics: bool = True,
    suggest_improvements: bool = True,
) -> Dict[str, Any]:
    """Validate Mermaid diagram syntax and semantics."""
    with span("mermaid.validate"):
        add_span_attributes(**{
            "mermaid.strict": strict,
            "mermaid.check_syntax": check_syntax,
            "mermaid.check_semantics": check_semantics,
            "mermaid.suggest_improvements": suggest_improvements,
        })
        
        try:
            from uvmgr.runtime import mermaid as _rt
            
            validation_result = {
                "is_valid": True,
                "syntax_errors": [],
                "semantic_errors": [],
                "suggestions": [],
                "statistics": {},
            }
            
            # Syntax validation
            if check_syntax:
                syntax_errors = _rt.validate_mermaid_syntax(mermaid_code, strict)
                validation_result["syntax_errors"] = syntax_errors
                if syntax_errors:
                    validation_result["is_valid"] = False
            
            # Semantic validation
            if check_semantics:
                semantic_errors = _rt.validate_mermaid_semantics(mermaid_code)
                validation_result["semantic_errors"] = semantic_errors
                if semantic_errors and strict:
                    validation_result["is_valid"] = False
            
            # Generate improvement suggestions
            if suggest_improvements:
                if HAS_DSPY:
                    try:
                        analyzer = ComplexityAnalyzer()
                        analysis = analyzer(mermaid_code, "technical")
                        suggestions = json.loads(analysis.recommendations) if analysis.recommendations else []
                        validation_result["suggestions"] = suggestions
                        validation_result["complexity_analysis"] = {
                            "complexity_score": analysis.complexity_score,
                            "readability_score": analysis.readability_score,
                        }
                    except Exception as dspy_error:
                        # Fallback to template suggestions if DSPy fails
                        print(f"DSPy analysis failed ({dspy_error}), using template suggestions")
                        suggestions = _rt.generate_improvement_suggestions(mermaid_code)
                        validation_result["suggestions"] = suggestions
                else:
                    suggestions = _rt.generate_improvement_suggestions(mermaid_code)
                    validation_result["suggestions"] = suggestions
            
            # Calculate diagram statistics
            stats = _rt.calculate_diagram_statistics(mermaid_code)
            validation_result["statistics"] = stats
            
            add_span_event("mermaid.validation.completed", {
                "is_valid": validation_result["is_valid"],
                "syntax_errors": len(validation_result["syntax_errors"]),
                "semantic_errors": len(validation_result["semantic_errors"]),
                "suggestions_count": len(validation_result["suggestions"]),
            })
            
            return validation_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def export_diagram(
    mermaid_code: str,
    output_path: Path,
    export_format: str = "png",
    width: int = 1920,
    height: int = 1080,
    theme: str = "default",
    background: str = "white",
) -> Dict[str, Any]:
    """Export Mermaid diagram to various formats."""
    with span("mermaid.export", format=export_format):
        add_span_attributes(**{
            "mermaid.export_format": export_format,
            "mermaid.width": width,
            "mermaid.height": height,
            "mermaid.theme": theme,
        })
        
        try:
            from uvmgr.runtime import mermaid as _rt
            
            export_result = _rt.export_mermaid_diagram(
                mermaid_code=mermaid_code,
                output_path=output_path,
                export_format=export_format,
                width=width,
                height=height,
                theme=theme,
                background=background,
            )
            
            add_span_event("mermaid.export.completed", {
                "format": export_format,
                "output_size": export_result.get("file_size", 0),
                "export_time": export_result.get("export_time", 0),
            })
            
            return export_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def preview_diagram(
    mermaid_code: str,
    browser: bool = True,
    theme: str = "default",
    port: int = 8080,
) -> Dict[str, Any]:
    """Preview Mermaid diagram in browser or terminal."""
    with span("mermaid.preview", browser=browser):
        add_span_attributes(**{
            "mermaid.browser": browser,
            "mermaid.theme": theme,
            "mermaid.port": port,
        })
        
        try:
            from uvmgr.runtime import mermaid as _rt
            
            if browser:
                preview_result = _rt.launch_browser_preview(mermaid_code, theme, port)
            else:
                preview_result = _rt.generate_terminal_preview(mermaid_code)
            
            add_span_event("mermaid.preview.completed", {
                "browser": browser,
                "preview_method": preview_result.get("preview_method", "unknown"),
            })
            
            return preview_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def manage_mermaid_templates(
    action: str,
    template_name: Optional[str] = None,
    diagram_type: Optional[str] = None,
    source: Optional[Path] = None,
) -> Dict[str, Any]:
    """Manage reusable Mermaid diagram templates."""
    with span("mermaid.templates", action=action):
        add_span_attributes(**{
            "mermaid.action": action,
            "mermaid.template_name": template_name or "",
            "mermaid.diagram_type": diagram_type or "",
        })
        
        try:
            from uvmgr.runtime import mermaid as _rt
            
            if action == "list":
                templates = _rt.list_mermaid_templates()
                return {"templates": templates}
            
            elif action == "create":
                if not template_name or not source:
                    raise ValueError("Template name and source required for creation")
                
                template_path = _rt.create_mermaid_template(
                    template_name, source, diagram_type
                )
                return {
                    "template_name": template_name,
                    "template_path": str(template_path),
                    "diagram_type": diagram_type,
                }
            
            elif action == "apply":
                if not template_name:
                    raise ValueError("Template name required for application")
                
                output_file = _rt.apply_mermaid_template(template_name, diagram_type)
                return {
                    "template_name": template_name,
                    "output_file": str(output_file),
                }
            
            elif action == "delete":
                if not template_name:
                    raise ValueError("Template name required for deletion")
                
                _rt.delete_mermaid_template(template_name)
                return {"template_name": template_name, "deleted": True}
            
            else:
                raise ValueError(f"Unknown action: {action}")
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def analyze_mermaid_diagram(
    mermaid_code: str,
    complexity_analysis: bool = True,
    layout_analysis: bool = True,
    accessibility_check: bool = False,
    performance_check: bool = False,
) -> Dict[str, Any]:
    """Analyze Mermaid diagram and suggest improvements."""
    with span("mermaid.analyze"):
        add_span_attributes(**{
            "mermaid.complexity": complexity_analysis,
            "mermaid.layout": layout_analysis,
            "mermaid.accessibility": accessibility_check,
            "mermaid.performance": performance_check,
        })
        
        try:
            from uvmgr.runtime import mermaid as _rt
            
            analysis_result = {}
            
            # Complexity analysis
            if complexity_analysis:
                if HAS_DSPY:
                    try:
                        analyzer = ComplexityAnalyzer()
                        complexity = analyzer(mermaid_code, "technical")
                        analysis_result["complexity_analysis"] = {
                            "score": complexity.complexity_score,
                            "readability_score": complexity.readability_score,
                            "recommendations": json.loads(complexity.recommendations) if complexity.recommendations else [],
                            "metrics": json.loads(complexity.metrics) if complexity.metrics else {},
                        }
                    except Exception as dspy_error:
                        # Fallback to template analysis if DSPy fails
                        print(f"DSPy complexity analysis failed ({dspy_error}), using template analysis")
                        complexity = _rt.analyze_diagram_complexity(mermaid_code)
                        analysis_result["complexity_analysis"] = complexity
                else:
                    complexity = _rt.analyze_diagram_complexity(mermaid_code)
                    analysis_result["complexity_analysis"] = complexity
                
                # Add basic statistics
                stats = _rt.calculate_diagram_statistics(mermaid_code)
                analysis_result["complexity_analysis"].update(stats)
            
            # Layout analysis
            if layout_analysis:
                layout = _rt.analyze_diagram_layout(mermaid_code)
                analysis_result["layout_analysis"] = layout
            
            # Accessibility check
            if accessibility_check:
                accessibility = _rt.check_diagram_accessibility(mermaid_code)
                analysis_result["accessibility_analysis"] = accessibility
            
            # Performance analysis
            if performance_check:
                performance = _rt.analyze_diagram_performance(mermaid_code)
                analysis_result["performance_analysis"] = performance
            
            # Generate comprehensive recommendations
            recommendations = []
            if complexity_analysis and analysis_result.get("complexity_analysis", {}).get("recommendations"):
                recommendations.extend(analysis_result["complexity_analysis"]["recommendations"])
            
            if layout_analysis and analysis_result.get("layout_analysis", {}).get("recommendations"):
                recommendations.extend(analysis_result["layout_analysis"].get("recommendations", []))
            
            analysis_result["recommendations"] = recommendations
            
            # Overall scores
            analysis_result["complexity_score"] = analysis_result.get("complexity_analysis", {}).get("score", 0)
            analysis_result["layout_score"] = analysis_result.get("layout_analysis", {}).get("score", 0)
            
            add_span_event("mermaid.analysis.completed", {
                "complexity_score": analysis_result.get("complexity_score", 0),
                "layout_score": analysis_result.get("layout_score", 0),
                "recommendations_count": len(recommendations),
            })
            
            return analysis_result
            
        except Exception as e:
            record_exception(e)
            raise


# 80/20 Priority mapping for diagram types
DIAGRAM_PRIORITY_MAP = {
    # Priority 1: Most commonly used (40% of use cases)
    "flowchart": {"priority": 1, "complexity": "medium", "business_value": "high"},
    
    # Priority 2: High business value (30% of use cases)
    "sequence": {"priority": 2, "complexity": "medium", "business_value": "high"},
    
    # Priority 3: Development workflows (15% of use cases)
    "class": {"priority": 3, "complexity": "high", "business_value": "medium"},
    "gitgraph": {"priority": 3, "complexity": "low", "business_value": "medium"},
    
    # Priority 4: Architecture and system design (10% of use cases)
    "architecture": {"priority": 4, "complexity": "high", "business_value": "high"},
    "c4context": {"priority": 4, "complexity": "high", "business_value": "high"},
    
    # Priority 5: Specialized diagrams (5% of use cases)
    "state": {"priority": 5, "complexity": "medium", "business_value": "low"},
    "er": {"priority": 5, "complexity": "medium", "business_value": "low"},
    "journey": {"priority": 5, "complexity": "low", "business_value": "low"},
    "gantt": {"priority": 5, "complexity": "low", "business_value": "medium"},
    "pie": {"priority": 5, "complexity": "low", "business_value": "low"},
    "requirement": {"priority": 5, "complexity": "medium", "business_value": "low"},
    "mindmap": {"priority": 5, "complexity": "low", "business_value": "low"},
    "timeline": {"priority": 5, "complexity": "low", "business_value": "low"},
    "sankey": {"priority": 5, "complexity": "high", "business_value": "low"},
    "block": {"priority": 5, "complexity": "medium", "business_value": "low"},
}


def get_diagram_priority(diagram_type: str) -> int:
    """Get 80/20 priority for diagram type."""
    return DIAGRAM_PRIORITY_MAP.get(diagram_type, {"priority": 5})["priority"]


def get_recommended_diagrams(use_case: str) -> List[str]:
    """Get recommended diagram types for specific use cases."""
    use_case_mapping = {
        "process": ["flowchart", "sequence"],
        "architecture": ["architecture", "c4context", "class"],
        "workflow": ["flowchart", "gitgraph", "sequence"],
        "data": ["er", "class", "flowchart"],
        "user_experience": ["journey", "sequence", "flowchart"],
        "planning": ["gantt", "timeline", "mindmap"],
        "analysis": ["pie", "sankey", "requirement"],
    }
    
    return use_case_mapping.get(use_case.lower(), ["flowchart"])


def optimize_diagram_for_priority(mermaid_code: str, diagram_type: str) -> Dict[str, Any]:
    """Optimize diagram based on 80/20 priority principles."""
    priority_info = DIAGRAM_PRIORITY_MAP.get(diagram_type, {"priority": 5, "complexity": "medium"})
    
    if priority_info["priority"] <= 2:
        # High priority - optimize for clarity and business value
        optimization_goals = ["readability", "business_clarity", "simplified_layout"]
    elif priority_info["priority"] <= 4:
        # Medium priority - balance detail and clarity
        optimization_goals = ["completeness", "technical_accuracy", "balanced_layout"]
    else:
        # Lower priority - maintain functionality but don't over-optimize
        optimization_goals = ["basic_readability", "functional_layout"]
    
    return {
        "priority": priority_info["priority"],
        "optimization_goals": optimization_goals,
        "business_value": priority_info.get("business_value", "medium"),
        "recommended_complexity": priority_info.get("complexity", "medium"),
    }