"""
uvmgr.ops.infodesign - Information Design Operations with DSPy
============================================================

Business logic for intelligent information design using DSPy framework.
This module provides the core operations layer between commands and runtime.

This module implements DSPy-powered information processing including:
- Intelligent analysis of information structures
- AI-driven documentation generation
- Information architecture optimization
- Knowledge extraction and graph creation
- Template management and reuse

Key Features
-----------
• **DSPy Integration**: Leverages DSPy for structured AI operations
• **Information Analysis**: Deep analysis of content structure and patterns
• **Smart Generation**: AI-powered content and documentation generation
• **Architecture Optimization**: Intelligent structure optimization
• **Knowledge Graphs**: Entity extraction and relationship mapping
• **Template System**: Reusable information design patterns

Architecture
-----------
This operations layer focuses on business logic and DSPy coordination:
- No direct file I/O (delegated to runtime layer)
- DSPy signature definitions and program composition
- Business rule enforcement and validation
- Telemetry and observability integration
- Error handling and recovery logic

See Also
--------
- :mod:`uvmgr.runtime.infodesign` : Runtime implementation
- :mod:`uvmgr.commands.infodesign` : CLI interface
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
    # Fallback for when DSPy is not available
    HAS_DSPY = False
    print("DSPy not available - using mock implementations")


# DSPy Signatures for Information Design Tasks
if HAS_DSPY:
    class AnalyzeInformationStructure(Signature):
        """Analyze information structure and patterns in content."""
        content: str = InputField(desc="Content to analyze")
        analysis_type: str = InputField(desc="Type of analysis: code, docs, data, structure, content")
        depth: int = InputField(desc="Analysis depth level (1-5)")
        
        analysis: str = OutputField(desc="Detailed analysis of information structure")
        entities: str = OutputField(desc="JSON list of identified entities")
        relationships: str = OutputField(desc="JSON list of relationships between entities")
        complexity_score: float = OutputField(desc="Complexity score (0-10)")
        recommendations: str = OutputField(desc="JSON list of improvement recommendations")
    
    class GenerateDocumentation(Signature):
        """Generate comprehensive documentation from source content."""
        source_content: str = InputField(desc="Source content to document")
        doc_type: str = InputField(desc="Documentation type: api, user, technical, overview")
        template: str = InputField(desc="Template style to follow")
        audience: str = InputField(desc="Target audience level")
        
        documentation: str = OutputField(desc="Generated documentation in markdown format")
        sections: str = OutputField(desc="JSON list of document sections created")
        word_count: int = OutputField(desc="Approximate word count")
        completeness_score: float = OutputField(desc="Documentation completeness score (0-10)")
    
    class OptimizeInformationArchitecture(Signature):
        """Optimize information architecture for better usability."""
        current_structure: str = InputField(desc="Current information structure")
        target_pattern: str = InputField(desc="Target design pattern: hierarchical, network, linear, modular")
        audience: str = InputField(desc="Target audience characteristics")
        optimize_for: str = InputField(desc="Optimization goal: readability, navigation, comprehension")
        
        optimized_structure: str = OutputField(desc="Optimized information structure")
        changes: str = OutputField(desc="JSON list of proposed changes")
        improvement_score: float = OutputField(desc="Expected improvement score (0-10)")
        rationale: str = OutputField(desc="Explanation of optimization decisions")
    
    class ExtractKnowledge(Signature):
        """Extract knowledge entities and relationships from content."""
        content: str = InputField(desc="Content to extract knowledge from")
        extract_type: str = InputField(desc="Type: entities, concepts, relationships, all")
        domain: str = InputField(desc="Domain context for extraction")
        confidence_threshold: float = InputField(desc="Minimum confidence threshold (0-1)")
        
        extracted_items: str = OutputField(desc="JSON list of extracted knowledge items")
        confidence_scores: str = OutputField(desc="JSON dict of confidence scores")
        relationships: str = OutputField(desc="JSON list of identified relationships")
        summary: str = OutputField(desc="Summary of extraction results")
    
    class CreateKnowledgeGraph(Signature):
        """Create knowledge graph structure from extracted entities."""
        entities: str = InputField(desc="JSON list of entities")
        relationships: str = InputField(desc="JSON list of relationships")
        graph_type: str = InputField(desc="Graph type: semantic, dependency, flow, concept")
        layout_preference: str = InputField(desc="Layout algorithm preference")
        
        graph_structure: str = OutputField(desc="JSON graph structure with nodes and edges")
        layout_coordinates: str = OutputField(desc="JSON layout coordinates for visualization")
        clusters: str = OutputField(desc="JSON list of identified clusters")
        metrics: str = OutputField(desc="JSON dict of graph metrics (density, centrality, etc.)")


# DSPy Programs (Chain of Thought implementations)
if HAS_DSPY:
    class InformationAnalyzer(dspy.Module):
        def __init__(self):
            super().__init__()
            self.analyze = ChainOfThought(AnalyzeInformationStructure)
        
        def forward(self, content, analysis_type="structure", depth=3):
            return self.analyze(
                content=content,
                analysis_type=analysis_type,
                depth=depth
            )
    
    class DocumentationGenerator(dspy.Module):
        def __init__(self):
            super().__init__()
            self.generate = ChainOfThought(GenerateDocumentation)
        
        def forward(self, content, doc_type="comprehensive", template="default", audience="general"):
            return self.generate(
                source_content=content,
                doc_type=doc_type,
                template=template,
                audience=audience
            )
    
    class ArchitectureOptimizer(dspy.Module):
        def __init__(self):
            super().__init__()
            self.optimize = ChainOfThought(OptimizeInformationArchitecture)
        
        def forward(self, structure, pattern="hierarchical", audience="general", optimize_for="readability"):
            return self.optimize(
                current_structure=structure,
                target_pattern=pattern,
                audience=audience,
                optimize_for=optimize_for
            )
    
    class KnowledgeExtractor(dspy.Module):
        def __init__(self):
            super().__init__()
            self.extract = ChainOfThought(ExtractKnowledge)
        
        def forward(self, content, extract_type="entities", domain="general", confidence_threshold=0.7):
            return self.extract(
                content=content,
                extract_type=extract_type,
                domain=domain,
                confidence_threshold=confidence_threshold
            )
    
    class GraphCreator(dspy.Module):
        def __init__(self):
            super().__init__()
            self.create = ChainOfThought(CreateKnowledgeGraph)
        
        def forward(self, entities, relationships, graph_type="semantic", layout="force"):
            return self.create(
                entities=entities,
                relationships=relationships,
                graph_type=graph_type,
                layout_preference=layout
            )


@timed
def analyze_information_structure(
    source: Path,
    analysis_type: str = "structure",
    depth: int = 3,
    include_metrics: bool = True,
    output_format: str = "json",
) -> Dict[str, Any]:
    """Analyze information structure using DSPy."""
    with span("infodesign.analyze", source=str(source), type=analysis_type):
        add_span_attributes(**{
            "infodesign.source": str(source),
            "infodesign.type": analysis_type,
            "infodesign.depth": depth,
            "infodesign.metrics": include_metrics,
        })
        
        try:
            from uvmgr.runtime import infodesign as _rt
            
            # Load content from source
            content = _rt.load_content(source, analysis_type)
            
            if HAS_DSPY:
                # Use DSPy for intelligent analysis
                analyzer = InformationAnalyzer()
                result = analyzer(content, analysis_type, depth)
                
                # Parse DSPy outputs
                entities = json.loads(result.entities) if result.entities else []
                relationships = json.loads(result.relationships) if result.relationships else []
                recommendations = json.loads(result.recommendations) if result.recommendations else []
                
                analysis_result = {
                    "analysis": result.analysis,
                    "entities": entities,
                    "relationships": relationships,
                    "complexity_score": result.complexity_score,
                    "recommendations": recommendations,
                    "entities_count": len(entities),
                    "relationships_count": len(relationships),
                }
            else:
                # Fallback to basic analysis
                analysis_result = _rt.analyze_structure_basic(content, analysis_type, depth)
            
            # Add metrics if requested
            if include_metrics:
                metrics = _rt.calculate_information_metrics(content, analysis_result)
                analysis_result["metrics"] = metrics
                analysis_result["summary"] = _generate_analysis_summary(analysis_result)
            
            add_span_event("infodesign.analysis.completed", {
                "entities_found": analysis_result.get("entities_count", 0),
                "relationships_found": analysis_result.get("relationships_count", 0),
                "complexity": analysis_result.get("complexity_score", 0),
            })
            
            return analysis_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def generate_documentation(
    input_path: Path,
    output_path: Optional[Path] = None,
    doc_type: str = "comprehensive",
    template: Optional[str] = None,
    include_diagrams: bool = True,
    output_format: str = "markdown",
) -> Dict[str, Any]:
    """Generate documentation using DSPy."""
    with span("infodesign.generate", input=str(input_path), doc_type=doc_type):
        add_span_attributes(**{
            "infodesign.input": str(input_path),
            "infodesign.doc_type": doc_type,
            "infodesign.template": template or "default",
            "infodesign.diagrams": include_diagrams,
        })
        
        try:
            from uvmgr.runtime import infodesign as _rt
            
            # Load and preprocess content
            content = _rt.load_content(input_path, "documentation")
            
            if HAS_DSPY:
                # Use DSPy for intelligent generation
                generator = DocumentationGenerator()
                result = generator(
                    content, 
                    doc_type, 
                    template or "default", 
                    "general"
                )
                
                # Parse DSPy outputs
                sections = json.loads(result.sections) if result.sections else []
                
                generation_result = {
                    "documentation": result.documentation,
                    "sections": sections,
                    "word_count": result.word_count,
                    "completeness_score": result.completeness_score,
                    "sections_count": len(sections),
                }
            else:
                # Fallback to template-based generation
                generation_result = _rt.generate_documentation_basic(
                    content, doc_type, template, include_diagrams
                )
            
            # Save output if path specified
            if output_path:
                output_files = _rt.save_documentation(
                    generation_result, output_path, output_format, include_diagrams
                )
                generation_result["generated_files"] = output_files
                generation_result["output_path"] = str(output_path)
            
            # Add statistics
            generation_result["statistics"] = {
                "files_count": len(generation_result.get("generated_files", [])),
                "word_count": generation_result.get("word_count", 0),
                "sections_count": generation_result.get("sections_count", 0),
                "diagrams_count": generation_result.get("diagrams_count", 0),
            }
            
            add_span_event("infodesign.generation.completed", {
                "files_generated": len(generation_result.get("generated_files", [])),
                "words": generation_result.get("word_count", 0),
                "completeness": generation_result.get("completeness_score", 0),
            })
            
            return generation_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def optimize_information_structure(
    source: Path,
    pattern: str = "hierarchical",
    target_audience: str = "general",
    optimize_for: str = "readability",
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Optimize information structure using DSPy."""
    with span("infodesign.optimize", source=str(source), pattern=pattern):
        add_span_attributes(**{
            "infodesign.source": str(source),
            "infodesign.pattern": pattern,
            "infodesign.audience": target_audience,
            "infodesign.optimize_for": optimize_for,
            "infodesign.dry_run": dry_run,
        })
        
        try:
            from uvmgr.runtime import infodesign as _rt
            
            # Load current structure
            current_structure = _rt.load_structure(source)
            current_score = _rt.evaluate_structure(current_structure, optimize_for)
            
            if HAS_DSPY:
                # Use DSPy for intelligent optimization
                optimizer = ArchitectureOptimizer()
                result = optimizer(
                    json.dumps(current_structure),
                    pattern,
                    target_audience,
                    optimize_for
                )
                
                # Parse DSPy outputs
                optimized_structure = json.loads(result.optimized_structure)
                proposed_changes = json.loads(result.changes) if result.changes else []
                
                optimization_result = {
                    "current_structure": current_structure,
                    "optimized_structure": optimized_structure,
                    "proposed_changes": proposed_changes,
                    "current_score": current_score,
                    "optimized_score": current_score + result.improvement_score,
                    "improvement_score": result.improvement_score,
                    "rationale": result.rationale,
                }
            else:
                # Fallback to rule-based optimization
                optimization_result = _rt.optimize_structure_basic(
                    current_structure, pattern, target_audience, optimize_for
                )
                optimization_result["current_score"] = current_score
            
            # Apply changes if not dry run
            if not dry_run and optimization_result.get("proposed_changes"):
                applied_changes = _rt.apply_structure_changes(
                    source, optimization_result["proposed_changes"]
                )
                optimization_result["applied_changes"] = applied_changes
            
            # Generate recommendations
            optimization_result["recommendations"] = _generate_optimization_recommendations(
                optimization_result, pattern, optimize_for
            )
            
            add_span_event("infodesign.optimization.completed", {
                "changes_count": len(optimization_result.get("proposed_changes", [])),
                "improvement": optimization_result.get("improvement_score", 0),
                "applied": not dry_run,
            })
            
            return optimization_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def extract_knowledge(
    source: Path,
    extract_type: str = "entities",
    model: str = "gpt-3.5-turbo",
    confidence_threshold: float = 0.7,
    max_items: int = 100,
) -> Dict[str, Any]:
    """Extract knowledge using DSPy."""
    with span("infodesign.extract", source=str(source), type=extract_type):
        add_span_attributes(**{
            "infodesign.source": str(source),
            "infodesign.extract_type": extract_type,
            "infodesign.model": model,
            "infodesign.confidence": confidence_threshold,
            "infodesign.max_items": max_items,
        })
        
        try:
            from uvmgr.runtime import infodesign as _rt
            
            # Load and preprocess content
            content = _rt.load_content(source, "extraction")
            domain = _rt.detect_domain(content)
            
            if HAS_DSPY:
                # Configure DSPy model - only Qwen3
                lm = dspy.LM(model="ollama/qwen3")
                dspy.settings.configure(lm=lm)
                
                # Use DSPy for intelligent extraction
                extractor = KnowledgeExtractor()
                result = extractor(content, extract_type, domain, confidence_threshold)
                
                # Parse DSPy outputs
                extracted_items = json.loads(result.extracted_items) if result.extracted_items else []
                confidence_scores = json.loads(result.confidence_scores) if result.confidence_scores else {}
                relationships = json.loads(result.relationships) if result.relationships else []
                
                # Filter by confidence and limit
                filtered_items = [
                    item for item in extracted_items
                    if confidence_scores.get(item.get("id", ""), 0) >= confidence_threshold
                ][:max_items]
                
                extraction_result = {
                    "extracted_items": filtered_items,
                    "relationships": relationships,
                    "confidence_scores": confidence_scores,
                    "summary": result.summary,
                    "domain": domain,
                    "extract_type": extract_type,
                }
            else:
                # Fallback to pattern-based extraction
                extraction_result = _rt.extract_knowledge_basic(
                    content, extract_type, confidence_threshold, max_items
                )
                extraction_result["domain"] = domain
            
            # Calculate statistics
            items = extraction_result.get("extracted_items", [])
            confidences = extraction_result.get("confidence_scores", {})
            
            extraction_result["statistics"] = {
                "total_items": len(items),
                "high_confidence_items": len([
                    item for item in items
                    if confidences.get(item.get("id", ""), 0) >= 0.8
                ]),
                "average_confidence": sum(confidences.values()) / len(confidences) if confidences else 0,
                "processing_time": 0,  # Will be filled by runtime
            }
            
            add_span_event("infodesign.extraction.completed", {
                "items_count": len(items),
                "avg_confidence": extraction_result["statistics"]["average_confidence"],
                "domain": domain,
            })
            
            return extraction_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def create_knowledge_graph(
    source: Path,
    output: Optional[Path] = None,
    graph_type: str = "semantic",
    layout: str = "force",
    include_metadata: bool = True,
    output_format: str = "json",
) -> Dict[str, Any]:
    """Create knowledge graph using DSPy."""
    with span("infodesign.graph", source=str(source), type=graph_type):
        add_span_attributes(**{
            "infodesign.source": str(source),
            "infodesign.graph_type": graph_type,
            "infodesign.layout": layout,
            "infodesign.metadata": include_metadata,
        })
        
        try:
            from uvmgr.runtime import infodesign as _rt
            
            # First extract entities and relationships
            extraction_result = extract_knowledge(source, "all")
            entities = extraction_result.get("extracted_items", [])
            relationships = extraction_result.get("relationships", [])
            
            if HAS_DSPY:
                # Use DSPy for intelligent graph creation
                graph_creator = GraphCreator()
                result = graph_creator(
                    json.dumps(entities),
                    json.dumps(relationships),
                    graph_type,
                    layout
                )
                
                # Parse DSPy outputs
                graph_structure = json.loads(result.graph_structure)
                layout_coords = json.loads(result.layout_coordinates) if result.layout_coordinates else {}
                clusters = json.loads(result.clusters) if result.clusters else []
                metrics = json.loads(result.metrics) if result.metrics else {}
                
                graph_result = {
                    "graph_structure": graph_structure,
                    "layout_coordinates": layout_coords,
                    "clusters": clusters,
                    "metrics": metrics,
                    "nodes_count": len(graph_structure.get("nodes", [])),
                    "edges_count": len(graph_structure.get("edges", [])),
                    "graph_density": metrics.get("density", 0),
                    "clusters_count": len(clusters),
                }
            else:
                # Fallback to basic graph creation
                graph_result = _rt.create_graph_basic(
                    entities, relationships, graph_type, layout, include_metadata
                )
            
            # Calculate additional graph metrics
            graph_metrics = _rt.calculate_graph_metrics(graph_result["graph_structure"])
            graph_result["metrics"].update(graph_metrics)
            
            # Find top nodes by centrality
            graph_result["top_nodes"] = _rt.find_central_nodes(
                graph_result["graph_structure"], limit=10
            )
            
            # Save output if specified
            if output:
                output_path = _rt.save_graph(graph_result, output, output_format)
                graph_result["output_path"] = str(output_path)
            
            add_span_event("infodesign.graph.completed", {
                "nodes": graph_result.get("nodes_count", 0),
                "edges": graph_result.get("edges_count", 0),
                "density": graph_result.get("graph_density", 0),
                "clusters": graph_result.get("clusters_count", 0),
            })
            
            return graph_result
            
        except Exception as e:
            record_exception(e)
            raise


@timed
def manage_templates(
    action: str,
    template_name: Optional[str] = None,
    source: Optional[Path] = None,
    target: Optional[Path] = None,
    template_type: str = "documentation",
) -> Dict[str, Any]:
    """Manage information design templates."""
    with span("infodesign.template", action=action, template=template_name or ""):
        add_span_attributes(**{
            "infodesign.action": action,
            "infodesign.template_name": template_name or "",
            "infodesign.template_type": template_type,
        })
        
        try:
            from uvmgr.runtime import infodesign as _rt
            
            if action == "list":
                templates = _rt.list_templates()
                return {"templates": templates}
            
            elif action == "create":
                if not template_name or not source:
                    raise ValueError("Template name and source required for creation")
                
                template_path = _rt.create_template(
                    template_name, source, template_type
                )
                return {
                    "template_name": template_name,
                    "template_path": str(template_path),
                    "template_type": template_type,
                }
            
            elif action == "apply":
                if not template_name or not target:
                    raise ValueError("Template name and target required for application")
                
                generated_files = _rt.apply_template(
                    template_name, target, template_type
                )
                return {
                    "template_name": template_name,
                    "target": str(target),
                    "generated_files": generated_files,
                }
            
            elif action == "delete":
                if not template_name:
                    raise ValueError("Template name required for deletion")
                
                _rt.delete_template(template_name)
                return {"template_name": template_name, "deleted": True}
            
            else:
                raise ValueError(f"Unknown action: {action}")
            
        except Exception as e:
            record_exception(e)
            raise


# Helper functions

def _generate_analysis_summary(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of analysis results."""
    entities_count = analysis_result.get("entities_count", 0)
    relationships_count = analysis_result.get("relationships_count", 0)
    complexity = analysis_result.get("complexity_score", 0)
    
    return {
        "information_density": {
            "value": entities_count + relationships_count,
            "score": min(10, (entities_count + relationships_count) / 10),
        },
        "structural_complexity": {
            "value": complexity,
            "score": complexity,
        },
        "relationship_richness": {
            "value": relationships_count / max(entities_count, 1),
            "score": min(10, (relationships_count / max(entities_count, 1)) * 5),
        },
        "organization_quality": {
            "value": 10 - complexity + (relationships_count / max(entities_count, 1)),
            "score": max(0, min(10, 10 - complexity + (relationships_count / max(entities_count, 1)))),
        },
    }


def _generate_optimization_recommendations(
    optimization_result: Dict[str, Any],
    pattern: str,
    optimize_for: str,
) -> List[str]:
    """Generate optimization recommendations."""
    recommendations = []
    
    improvement = optimization_result.get("improvement_score", 0)
    changes_count = len(optimization_result.get("proposed_changes", []))
    
    if improvement < 2:
        recommendations.append("Consider a different design pattern for better results")
    
    if changes_count > 20:
        recommendations.append("Large number of changes - consider incremental optimization")
    
    if pattern == "hierarchical":
        recommendations.append("Ensure clear parent-child relationships in structure")
    elif pattern == "network":
        recommendations.append("Focus on interconnection quality between nodes")
    elif pattern == "modular":
        recommendations.append("Maintain clear module boundaries and interfaces")
    
    if optimize_for == "readability":
        recommendations.append("Use consistent formatting and clear headings")
    elif optimize_for == "navigation":
        recommendations.append("Add cross-references and navigation aids")
    elif optimize_for == "comprehension":
        recommendations.append("Include examples and explanatory content")
    
    return recommendations