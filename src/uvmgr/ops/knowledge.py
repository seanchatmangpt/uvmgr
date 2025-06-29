"""
Knowledge management operations for uvmgr.

This module provides business logic for AI-powered knowledge management,
code understanding, and intelligent documentation. It follows the 80/20
principle by focusing on the most valuable knowledge operations.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, span
from uvmgr.core.semconv import AIAttributes
from uvmgr.runtime import knowledge as knowledge_runtime


def analyze_codebase(
    path: Optional[Path] = None,
    include_dependencies: bool = True,
    generate_embeddings: bool = True,
    analysis_depth: str = "standard"
) -> Dict[str, Any]:
    """
    Perform comprehensive codebase analysis.
    
    Parameters
    ----------
    path : Optional[Path]
        Path to analyze (current directory if None)
    include_dependencies : bool
        Whether to analyze dependencies
    generate_embeddings : bool
        Whether to generate semantic embeddings
    analysis_depth : str
        Depth of analysis (quick, standard, deep)
        
    Returns
    -------
    Dict[str, Any]
        Codebase analysis results
    """
    with span("knowledge.analyze_codebase") as current_span:
        start_time = time.time()
        
        add_span_attributes(**{
            AIAttributes.OPERATION: "analyze",
            "knowledge.path": str(path) if path else ".",
            "knowledge.include_dependencies": include_dependencies,
            "knowledge.generate_embeddings": generate_embeddings,
            "knowledge.analysis_depth": analysis_depth,
        })
        
        # Delegate to runtime
        result = knowledge_runtime.analyze_project_structure(
            project_path=path,
            include_deps=include_dependencies,
            generate_embeddings=generate_embeddings,
            depth=analysis_depth
        )
        
        analysis_time = time.time() - start_time
        add_span_attributes(**{
            "knowledge.analysis_success": result.get("success", False),
            "knowledge.analysis_time": analysis_time,
            "knowledge.files_analyzed": result.get("files_analyzed", 0),
            "knowledge.functions_found": result.get("functions_found", 0),
            "knowledge.classes_found": result.get("classes_found", 0),
        })
        
        return result


def ask_question(
    question: str,
    context_path: Optional[Path] = None,
    include_code: bool = True,
    include_docs: bool = True,
    max_context_files: int = 10
) -> Dict[str, Any]:
    """
    Ask a question about the codebase using AI.
    
    Parameters
    ----------
    question : str
        Question to ask about the code
    context_path : Optional[Path]
        Specific path to focus the question on
    include_code : bool
        Whether to include source code in context
    include_docs : bool
        Whether to include documentation in context
    max_context_files : int
        Maximum number of files to include in context
        
    Returns
    -------
    Dict[str, Any]
        AI response with answer and sources
    """
    with span("knowledge.ask_question") as current_span:
        add_span_attributes(**{
            AIAttributes.OPERATION: "ask",
            "knowledge.question": question[:100],  # Truncate for privacy
            "knowledge.context_path": str(context_path) if context_path else None,
            "knowledge.include_code": include_code,
            "knowledge.include_docs": include_docs,
            "knowledge.max_context_files": max_context_files,
        })
        
        # Delegate to runtime
        result = knowledge_runtime.ask_ai_question(
            question=question,
            context_path=context_path,
            include_code=include_code,
            include_docs=include_docs,
            max_context_files=max_context_files
        )
        
        add_span_attributes(**{
            "knowledge.question_success": result.get("success", False),
            "knowledge.sources_used": len(result.get("sources", [])),
            AIAttributes.TOKENS_INPUT: result.get("tokens_input", 0),
            AIAttributes.TOKENS_OUTPUT: result.get("tokens_output", 0),
        })
        
        return result


def generate_documentation(
    path: Optional[Path] = None,
    doc_type: str = "api",
    output_format: str = "markdown",
    include_examples: bool = True
) -> Dict[str, Any]:
    """
    Generate intelligent documentation for code.
    
    Parameters
    ----------
    path : Optional[Path]
        Path to generate docs for
    doc_type : str
        Type of documentation (api, guide, tutorial)
    output_format : str
        Output format (markdown, html, rst)
    include_examples : bool
        Whether to include usage examples
        
    Returns
    -------
    Dict[str, Any]
        Documentation generation results
    """
    with span("knowledge.generate_docs") as current_span:
        add_span_attributes(**{
            AIAttributes.OPERATION: "generate_docs",
            "knowledge.path": str(path) if path else ".",
            "knowledge.doc_type": doc_type,
            "knowledge.output_format": output_format,
            "knowledge.include_examples": include_examples,
        })
        
        # Delegate to runtime
        result = knowledge_runtime.generate_intelligent_docs(
            source_path=path,
            doc_type=doc_type,
            output_format=output_format,
            include_examples=include_examples
        )
        
        add_span_attributes(**{
            "knowledge.docs_success": result.get("success", False),
            "knowledge.docs_generated": len(result.get("generated_files", [])),
            "knowledge.total_sections": result.get("total_sections", 0),
        })
        
        return result


def explain_code(
    file_path: Path,
    function_name: Optional[str] = None,
    line_range: Optional[tuple] = None,
    explanation_level: str = "detailed"
) -> Dict[str, Any]:
    """
    Generate AI explanations for specific code.
    
    Parameters
    ----------
    file_path : Path
        Path to the file to explain
    function_name : Optional[str]
        Specific function to explain
    line_range : Optional[tuple]
        Specific line range to explain (start, end)
    explanation_level : str
        Level of explanation (basic, detailed, expert)
        
    Returns
    -------
    Dict[str, Any]
        Code explanation results
    """
    with span("knowledge.explain_code") as current_span:
        add_span_attributes(**{
            AIAttributes.OPERATION: "explain",
            "knowledge.file_path": str(file_path),
            "knowledge.function_name": function_name,
            "knowledge.line_range": str(line_range) if line_range else None,
            "knowledge.explanation_level": explanation_level,
        })
        
        # Delegate to runtime
        result = knowledge_runtime.explain_code_section(
            file_path=file_path,
            function_name=function_name,
            line_range=line_range,
            explanation_level=explanation_level
        )
        
        add_span_attributes(**{
            "knowledge.explanation_success": result.get("success", False),
            "knowledge.explanation_length": len(result.get("explanation", "")),
            AIAttributes.TOKENS_INPUT: result.get("tokens_input", 0),
            AIAttributes.TOKENS_OUTPUT: result.get("tokens_output", 0),
        })
        
        return result


def find_similar_code(
    query: str,
    similarity_threshold: float = 0.7,
    max_results: int = 10,
    search_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Find semantically similar code using embeddings.
    
    Parameters
    ----------
    query : str
        Code pattern or description to search for
    similarity_threshold : float
        Minimum similarity score (0.0 to 1.0)
    max_results : int
        Maximum number of results to return
    search_path : Optional[Path]
        Path to search within
        
    Returns
    -------
    Dict[str, Any]
        Similar code search results
    """
    with span("knowledge.find_similar") as current_span:
        add_span_attributes(**{
            AIAttributes.OPERATION: "similarity_search",
            "knowledge.query": query[:100],  # Truncate for privacy
            "knowledge.similarity_threshold": similarity_threshold,
            "knowledge.max_results": max_results,
            "knowledge.search_path": str(search_path) if search_path else None,
        })
        
        # Delegate to runtime
        result = knowledge_runtime.semantic_code_search(
            query=query,
            similarity_threshold=similarity_threshold,
            max_results=max_results,
            search_path=search_path
        )
        
        add_span_attributes(**{
            "knowledge.search_success": result.get("success", False),
            "knowledge.results_found": len(result.get("results", [])),
            "knowledge.avg_similarity": result.get("avg_similarity", 0.0),
        })
        
        return result


def update_knowledge_base(
    path: Optional[Path] = None,
    incremental: bool = True,
    rebuild_embeddings: bool = False
) -> Dict[str, Any]:
    """
    Update the knowledge base with latest code changes.
    
    Parameters
    ----------
    path : Optional[Path]
        Path to update knowledge base for
    incremental : bool
        Whether to perform incremental updates only
    rebuild_embeddings : bool
        Whether to rebuild all embeddings
        
    Returns
    -------
    Dict[str, Any]
        Knowledge base update results
    """
    with span("knowledge.update_kb") as current_span:
        start_time = time.time()
        
        add_span_attributes(**{
            AIAttributes.OPERATION: "update_knowledge_base",
            "knowledge.path": str(path) if path else ".",
            "knowledge.incremental": incremental,
            "knowledge.rebuild_embeddings": rebuild_embeddings,
        })
        
        # Delegate to runtime
        result = knowledge_runtime.update_knowledge_base(
            project_path=path,
            incremental=incremental,
            rebuild_embeddings=rebuild_embeddings
        )
        
        update_time = time.time() - start_time
        add_span_attributes(**{
            "knowledge.update_success": result.get("success", False),
            "knowledge.update_time": update_time,
            "knowledge.files_updated": result.get("files_updated", 0),
            "knowledge.embeddings_updated": result.get("embeddings_updated", 0),
        })
        
        return result


def get_code_insights(
    path: Optional[Path] = None,
    insight_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get AI-powered insights about the codebase.
    
    Parameters
    ----------
    path : Optional[Path]
        Path to analyze for insights
    insight_types : Optional[List[str]]
        Types of insights to generate (complexity, patterns, improvements)
        
    Returns
    -------
    Dict[str, Any]
        Code insights and recommendations
    """
    with span("knowledge.code_insights") as current_span:
        add_span_attributes(**{
            AIAttributes.OPERATION: "generate_insights",
            "knowledge.path": str(path) if path else ".",
            "knowledge.insight_types": ",".join(insight_types or []),
        })
        
        # Delegate to runtime
        result = knowledge_runtime.generate_code_insights(
            project_path=path,
            insight_types=insight_types or ["complexity", "patterns", "improvements"]
        )
        
        add_span_attributes(**{
            "knowledge.insights_success": result.get("success", False),
            "knowledge.insights_count": len(result.get("insights", [])),
            "knowledge.recommendations_count": len(result.get("recommendations", [])),
        })
        
        return result