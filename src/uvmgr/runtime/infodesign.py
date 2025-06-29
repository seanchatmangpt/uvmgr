"""
uvmgr.runtime.infodesign - Information Design Runtime Implementation
==================================================================

Runtime layer for information design operations providing file I/O,
data processing, and format conversion capabilities.

This module handles the actual implementation of information design operations
including file system operations, content processing, template management,
and output generation.

Key Responsibilities
------------------
• **File Operations**: Read/write content from various sources
• **Content Processing**: Parse and analyze different file formats
• **Format Conversion**: Convert between formats (MD, JSON, HTML, etc.)
• **Template Management**: Store and apply information templates
• **Graph Processing**: Create and manipulate knowledge graphs
• **Metrics Calculation**: Compute information quality metrics

Architecture
-----------
This runtime layer focuses on concrete implementation:
- Direct file system operations and I/O
- Content parsing and format detection
- Data structure manipulation
- External tool integration
- Performance optimizations
- Error handling and recovery

File Format Support
------------------
- **Text**: .txt, .md, .rst
- **Code**: .py, .js, .ts, .java, .cpp, .rs
- **Data**: .json, .yaml, .toml, .csv
- **Documentation**: .md, .html, .pdf
- **Archives**: .zip, .tar.gz

See Also
--------
- :mod:`uvmgr.ops.infodesign` : Business logic layer
- :mod:`uvmgr.commands.infodesign` : CLI interface
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
import hashlib

# Standard library imports for content processing
import ast
import tokenize
from io import StringIO


def load_content(source: Path, analysis_type: str = "structure") -> str:
    """Load content from various source types."""
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    
    if source.is_file():
        return _load_file_content(source, analysis_type)
    elif source.is_dir():
        return _load_directory_content(source, analysis_type)
    else:
        raise ValueError(f"Invalid source type: {source}")


def _load_file_content(file_path: Path, analysis_type: str) -> str:
    """Load content from a single file."""
    try:
        # Detect encoding
        encoding = _detect_encoding(file_path)
        
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        # Add metadata
        metadata = {
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix,
            "analysis_type": analysis_type,
            "encoding": encoding,
        }
        
        # Prepend metadata as comments
        metadata_header = f"# FILE_METADATA: {json.dumps(metadata)}\n\n"
        return metadata_header + content
        
    except Exception as e:
        raise RuntimeError(f"Failed to load file {file_path}: {e}")


def _load_directory_content(dir_path: Path, analysis_type: str) -> str:
    """Load aggregated content from directory."""
    content_parts = []
    file_count = 0
    total_size = 0
    
    # File patterns to include based on analysis type
    if analysis_type == "code":
        patterns = ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.rs", "*.go"]
    elif analysis_type == "docs":
        patterns = ["*.md", "*.rst", "*.txt", "*.html"]
    elif analysis_type == "data":
        patterns = ["*.json", "*.yaml", "*.yml", "*.toml", "*.csv"]
    else:
        patterns = ["*.py", "*.js", "*.md", "*.txt", "*.json", "*.yaml"]
    
    # Collect files
    for pattern in patterns:
        for file_path in dir_path.rglob(pattern):
            if file_path.is_file() and not _should_ignore_file(file_path):
                try:
                    file_content = _load_file_content(file_path, analysis_type)
                    content_parts.append(f"\n\n# === FILE: {file_path.relative_to(dir_path)} ===\n")
                    content_parts.append(file_content)
                    file_count += 1
                    total_size += file_path.stat().st_size
                except Exception as e:
                    content_parts.append(f"\n# ERROR loading {file_path}: {e}\n")
    
    # Add directory metadata
    metadata = {
        "directory_path": str(dir_path),
        "files_processed": file_count,
        "total_size": total_size,
        "analysis_type": analysis_type,
        "patterns": patterns,
    }
    
    metadata_header = f"# DIRECTORY_METADATA: {json.dumps(metadata)}\n\n"
    return metadata_header + "".join(content_parts)


def _detect_encoding(file_path: Path) -> str:
    """Detect file encoding."""
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return 'utf-8'
    except UnicodeDecodeError:
        # Fall back to latin-1 which accepts any byte sequence
        return 'latin-1'


def _should_ignore_file(file_path: Path) -> bool:
    """Check if file should be ignored."""
    ignore_patterns = [
        "__pycache__", ".git", ".pytest_cache", "node_modules",
        ".venv", "venv", ".env", "build", "dist", ".mypy_cache"
    ]
    
    # Check if any parent directory matches ignore patterns
    for part in file_path.parts:
        if part in ignore_patterns:
            return True
    
    # Check file extensions to ignore
    ignore_extensions = {".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe"}
    if file_path.suffix in ignore_extensions:
        return True
    
    return False


def analyze_structure_basic(content: str, analysis_type: str, depth: int) -> Dict[str, Any]:
    """Basic fallback analysis when DSPy is not available."""
    entities = []
    relationships = []
    
    if analysis_type == "code":
        entities, relationships = _analyze_code_structure(content, depth)
    elif analysis_type == "docs":
        entities, relationships = _analyze_doc_structure(content, depth)
    elif analysis_type == "data":
        entities, relationships = _analyze_data_structure(content, depth)
    else:
        entities, relationships = _analyze_generic_structure(content, depth)
    
    complexity_score = _calculate_complexity_score(entities, relationships)
    recommendations = _generate_basic_recommendations(entities, relationships, analysis_type)
    
    return {
        "analysis": f"Basic {analysis_type} analysis completed",
        "entities": entities,
        "relationships": relationships,
        "complexity_score": complexity_score,
        "recommendations": recommendations,
        "entities_count": len(entities),
        "relationships_count": len(relationships),
    }


def _analyze_code_structure(content: str, depth: int) -> Tuple[List[Dict], List[Dict]]:
    """Analyze code structure for entities and relationships."""
    entities = []
    relationships = []
    
    # Simple regex-based analysis
    # Find classes
    class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
    for match in re.finditer(class_pattern, content):
        entities.append({
            "id": f"class_{match.group(1)}",
            "name": match.group(1),
            "type": "class",
            "line": content[:match.start()].count('\n') + 1,
        })
    
    # Find functions
    function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
    for match in re.finditer(function_pattern, content):
        entities.append({
            "id": f"function_{match.group(1)}",
            "name": match.group(1),
            "type": "function",
            "line": content[:match.start()].count('\n') + 1,
        })
    
    # Find imports
    import_pattern = r'(?:from\s+(\w+(?:\.\w+)*)\s+)?import\s+([^#\n]+)'
    for match in re.finditer(import_pattern, content):
        module = match.group(1) or match.group(2).split(',')[0].strip()
        entities.append({
            "id": f"import_{module}",
            "name": module,
            "type": "import",
            "line": content[:match.start()].count('\n') + 1,
        })
    
    # Create relationships (basic)
    for i, entity in enumerate(entities):
        for j, other in enumerate(entities[i+1:], i+1):
            if _entities_related(entity, other, content):
                relationships.append({
                    "source": entity["id"],
                    "target": other["id"],
                    "type": "references",
                    "confidence": 0.8,
                })
    
    return entities, relationships


def _analyze_doc_structure(content: str, depth: int) -> Tuple[List[Dict], List[Dict]]:
    """Analyze documentation structure."""
    entities = []
    relationships = []
    
    # Find headings
    heading_pattern = r'^(#{1,6})\s+(.+)$'
    for match in re.finditer(heading_pattern, content, re.MULTILINE):
        level = len(match.group(1))
        title = match.group(2).strip()
        entities.append({
            "id": f"heading_{hashlib.md5(title.encode()).hexdigest()[:8]}",
            "name": title,
            "type": "heading",
            "level": level,
            "line": content[:match.start()].count('\n') + 1,
        })
    
    # Find links
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, content):
        link_text = match.group(1)
        link_url = match.group(2)
        entities.append({
            "id": f"link_{hashlib.md5(link_url.encode()).hexdigest()[:8]}",
            "name": link_text,
            "type": "link",
            "url": link_url,
            "line": content[:match.start()].count('\n') + 1,
        })
    
    # Create hierarchical relationships for headings
    headings = [e for e in entities if e["type"] == "heading"]
    for i, heading in enumerate(headings):
        for j in range(i-1, -1, -1):
            parent = headings[j]
            if parent["level"] < heading["level"]:
                relationships.append({
                    "source": parent["id"],
                    "target": heading["id"],
                    "type": "contains",
                    "confidence": 0.9,
                })
                break
    
    return entities, relationships


def _analyze_data_structure(content: str, depth: int) -> Tuple[List[Dict], List[Dict]]:
    """Analyze data structure (JSON, YAML, etc.)."""
    entities = []
    relationships = []
    
    try:
        # Try to parse as JSON
        data = json.loads(content)
        entities, relationships = _extract_json_entities(data, "root")
    except json.JSONDecodeError:
        # Fallback to text analysis
        entities, relationships = _analyze_generic_structure(content, depth)
    
    return entities, relationships


def _extract_json_entities(data: Any, path: str, entities=None, relationships=None) -> Tuple[List[Dict], List[Dict]]:
    """Extract entities from JSON data structure."""
    if entities is None:
        entities = []
    if relationships is None:
        relationships = []
    
    entity_id = f"json_{hashlib.md5(path.encode()).hexdigest()[:8]}"
    
    if isinstance(data, dict):
        entities.append({
            "id": entity_id,
            "name": path.split('.')[-1] if '.' in path else path,
            "type": "object",
            "path": path,
            "size": len(data),
        })
        
        for key, value in data.items():
            child_path = f"{path}.{key}"
            child_entities, child_relationships = _extract_json_entities(value, child_path, [], [])
            entities.extend(child_entities)
            relationships.extend(child_relationships)
            
            if child_entities:
                relationships.append({
                    "source": entity_id,
                    "target": child_entities[0]["id"],
                    "type": "contains",
                    "confidence": 1.0,
                })
    
    elif isinstance(data, list):
        entities.append({
            "id": entity_id,
            "name": path.split('.')[-1] if '.' in path else path,
            "type": "array",
            "path": path,
            "size": len(data),
        })
        
        for i, item in enumerate(data[:5]):  # Limit to first 5 items
            child_path = f"{path}[{i}]"
            child_entities, child_relationships = _extract_json_entities(item, child_path, [], [])
            entities.extend(child_entities)
            relationships.extend(child_relationships)
    
    else:
        entities.append({
            "id": entity_id,
            "name": path.split('.')[-1] if '.' in path else path,
            "type": "value",
            "path": path,
            "value_type": type(data).__name__,
            "value": str(data)[:100],  # Truncate long values
        })
    
    return entities, relationships


def _analyze_generic_structure(content: str, depth: int) -> Tuple[List[Dict], List[Dict]]:
    """Generic text analysis fallback."""
    entities = []
    relationships = []
    
    # Find words and phrases
    words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', content)  # CamelCase
    word_counts = Counter(words)
    
    # Create entities for common words
    for word, count in word_counts.most_common(20):
        entities.append({
            "id": f"word_{word.lower()}",
            "name": word,
            "type": "concept",
            "frequency": count,
        })
    
    # Simple co-occurrence relationships
    sentences = re.split(r'[.!?]+', content)
    for sentence in sentences[:50]:  # Limit processing
        sentence_words = [w for w in words if w in sentence]
        for i, word1 in enumerate(sentence_words):
            for word2 in sentence_words[i+1:]:
                if word1 != word2:
                    relationships.append({
                        "source": f"word_{word1.lower()}",
                        "target": f"word_{word2.lower()}",
                        "type": "co-occurs",
                        "confidence": 0.5,
                    })
    
    return entities, relationships


def _entities_related(entity1: Dict, entity2: Dict, content: str) -> bool:
    """Check if two entities are related in the content."""
    # Simple heuristic: if they appear in the same line or nearby lines
    line_diff = abs(entity1.get("line", 0) - entity2.get("line", 0))
    return line_diff <= 5


def _calculate_complexity_score(entities: List[Dict], relationships: List[Dict]) -> float:
    """Calculate complexity score based on entities and relationships."""
    if not entities:
        return 0.0
    
    # Factors: entity count, relationship density, type diversity
    entity_count = len(entities)
    relationship_count = len(relationships)
    
    # Relationship density
    max_relationships = entity_count * (entity_count - 1) / 2
    density = relationship_count / max_relationships if max_relationships > 0 else 0
    
    # Type diversity
    entity_types = set(e.get("type", "unknown") for e in entities)
    type_diversity = len(entity_types)
    
    # Combine factors (scale 0-10)
    complexity = min(10, (
        (entity_count / 10) * 3 +  # Entity count contributes 30%
        (density * 10) * 4 +       # Density contributes 40%
        (type_diversity / 5) * 3   # Diversity contributes 30%
    ))
    
    return round(complexity, 2)


def _generate_basic_recommendations(entities: List[Dict], relationships: List[Dict], analysis_type: str) -> List[str]:
    """Generate basic recommendations."""
    recommendations = []
    
    entity_count = len(entities)
    relationship_count = len(relationships)
    
    if entity_count == 0:
        recommendations.append("No entities found - content may be too simple or parsing failed")
    elif entity_count > 100:
        recommendations.append("High entity count - consider breaking into smaller modules")
    
    if relationship_count == 0:
        recommendations.append("No relationships found - structure may be too isolated")
    elif relationship_count / max(entity_count, 1) > 3:
        recommendations.append("High relationship density - consider simplifying connections")
    
    if analysis_type == "code":
        recommendations.append("Consider adding more documentation and comments")
        recommendations.append("Ensure proper function and class naming conventions")
    elif analysis_type == "docs":
        recommendations.append("Add cross-references between related sections")
        recommendations.append("Ensure consistent heading hierarchy")
    
    return recommendations


def calculate_information_metrics(content: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate detailed information quality metrics."""
    metrics = {}
    
    # Basic content metrics
    word_count = len(content.split())
    line_count = content.count('\n')
    char_count = len(content)
    
    # Readability metrics (simplified)
    sentences = len(re.split(r'[.!?]+', content))
    avg_words_per_sentence = word_count / max(sentences, 1)
    
    # Structure metrics
    entities = analysis_result.get("entities", [])
    relationships = analysis_result.get("relationships", [])
    
    entity_types = Counter(e.get("type", "unknown") for e in entities)
    relationship_types = Counter(r.get("type", "unknown") for r in relationships)
    
    metrics = {
        "content": {
            "word_count": word_count,
            "line_count": line_count,
            "character_count": char_count,
            "average_words_per_sentence": round(avg_words_per_sentence, 2),
        },
        "structure": {
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "entity_types": dict(entity_types),
            "relationship_types": dict(relationship_types),
            "type_diversity": len(entity_types),
        },
        "quality": {
            "information_density": len(entities) / max(word_count / 100, 1),
            "connectivity": len(relationships) / max(len(entities), 1),
            "complexity_score": analysis_result.get("complexity_score", 0),
        }
    }
    
    return metrics


def generate_documentation_basic(
    content: str,
    doc_type: str,
    template: Optional[str],
    include_diagrams: bool,
) -> Dict[str, Any]:
    """Basic documentation generation fallback."""
    sections = []
    
    # Extract structure for documentation
    lines = content.split('\n')
    
    # Find sections based on content type
    if any(keyword in content.lower() for keyword in ['class', 'def', 'function']):
        sections = _generate_code_documentation(content)
    else:
        sections = _generate_generic_documentation(content)
    
    # Generate markdown content
    documentation = _format_as_markdown(sections, doc_type, include_diagrams)
    
    word_count = len(documentation.split())
    completeness_score = min(10.0, len(sections) * 1.5)
    
    return {
        "documentation": documentation,
        "sections": sections,
        "word_count": word_count,
        "completeness_score": completeness_score,
        "sections_count": len(sections),
    }


def _generate_code_documentation(content: str) -> List[Dict[str, Any]]:
    """Generate documentation sections for code."""
    sections = []
    
    # Overview section
    sections.append({
        "title": "Overview",
        "type": "overview",
        "content": "Auto-generated documentation from code analysis.",
    })
    
    # Find classes
    class_matches = re.finditer(r'class\s+(\w+)(?:\([^)]*\))?:', content)
    for match in class_matches:
        class_name = match.group(1)
        sections.append({
            "title": f"Class: {class_name}",
            "type": "class",
            "content": f"Documentation for the {class_name} class.",
            "class_name": class_name,
        })
    
    # Find functions
    function_matches = re.finditer(r'def\s+(\w+)\s*\([^)]*\):', content)
    for match in function_matches:
        function_name = match.group(1)
        sections.append({
            "title": f"Function: {function_name}",
            "type": "function",
            "content": f"Documentation for the {function_name} function.",
            "function_name": function_name,
        })
    
    return sections


def _generate_generic_documentation(content: str) -> List[Dict[str, Any]]:
    """Generate documentation sections for generic content."""
    sections = []
    
    # Split content into paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    for i, paragraph in enumerate(paragraphs[:10]):  # Limit to 10 paragraphs
        if len(paragraph) > 50:  # Only substantial paragraphs
            sections.append({
                "title": f"Section {i+1}",
                "type": "content",
                "content": paragraph[:500] + "..." if len(paragraph) > 500 else paragraph,
            })
    
    return sections


def _format_as_markdown(sections: List[Dict], doc_type: str, include_diagrams: bool) -> str:
    """Format sections as markdown documentation."""
    lines = []
    
    # Title
    lines.append(f"# Documentation - {doc_type.title()}")
    lines.append("")
    lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")
    
    # Table of contents
    if len(sections) > 3:
        lines.append("## Table of Contents")
        lines.append("")
        for section in sections:
            lines.append(f"- [{section['title']}](#{section['title'].lower().replace(' ', '-')})")
        lines.append("")
    
    # Sections
    for section in sections:
        lines.append(f"## {section['title']}")
        lines.append("")
        lines.append(section['content'])
        lines.append("")
        
        # Add diagrams if requested
        if include_diagrams and section.get('type') == 'class':
            lines.append("```mermaid")
            lines.append("classDiagram")
            lines.append(f"    class {section.get('class_name', 'Unknown')}")
            lines.append("```")
            lines.append("")
    
    return "\n".join(lines)


def save_documentation(
    generation_result: Dict[str, Any],
    output_path: Path,
    output_format: str,
    include_diagrams: bool,
) -> List[Dict[str, Any]]:
    """Save generated documentation to files."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    documentation = generation_result.get("documentation", "")
    
    if output_format == "markdown":
        file_path = output_path.with_suffix('.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        generated_files.append({
            "name": file_path.name,
            "path": str(file_path),
            "size": f"{len(documentation)} chars",
            "type": "markdown",
        })
    
    elif output_format == "html":
        # Convert markdown to HTML (basic conversion)
        html_content = _markdown_to_html(documentation)
        file_path = output_path.with_suffix('.html')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        generated_files.append({
            "name": file_path.name,
            "path": str(file_path),
            "size": f"{len(html_content)} chars",
            "type": "html",
        })
    
    elif output_format == "json":
        file_path = output_path.with_suffix('.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(generation_result, f, indent=2)
        
        generated_files.append({
            "name": file_path.name,
            "path": str(file_path),
            "size": f"{file_path.stat().st_size} bytes",
            "type": "json",
        })
    
    return generated_files


def _markdown_to_html(markdown_content: str) -> str:
    """Basic markdown to HTML conversion."""
    html_lines = ["<!DOCTYPE html>", "<html>", "<head>", 
                  "<title>Generated Documentation</title>", "</head>", "<body>"]
    
    for line in markdown_content.split('\n'):
        if line.startswith('# '):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith('## '):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith('### '):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.strip() == '':
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p>{line}</p>")
    
    html_lines.extend(["</body>", "</html>"])
    return "\n".join(html_lines)


def load_structure(source: Path) -> Dict[str, Any]:
    """Load current information structure."""
    if source.is_file():
        content = load_content(source)
        return _parse_file_structure(content)
    elif source.is_dir():
        return _parse_directory_structure(source)
    else:
        raise ValueError(f"Invalid source: {source}")


def _parse_file_structure(content: str) -> Dict[str, Any]:
    """Parse structure from file content."""
    lines = content.split('\n')
    
    structure = {
        "type": "file",
        "sections": [],
        "metadata": {},
    }
    
    # Find headings and sections
    current_section = None
    for i, line in enumerate(lines):
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            
            section = {
                "title": title,
                "level": level,
                "line": i + 1,
                "content_lines": 0,
            }
            
            if current_section:
                current_section["content_lines"] = i - current_section["line"]
            
            structure["sections"].append(section)
            current_section = section
    
    # Set content lines for last section
    if current_section:
        current_section["content_lines"] = len(lines) - current_section["line"]
    
    return structure


def _parse_directory_structure(dir_path: Path) -> Dict[str, Any]:
    """Parse structure from directory layout."""
    structure = {
        "type": "directory",
        "path": str(dir_path),
        "files": [],
        "subdirectories": [],
        "total_files": 0,
        "total_size": 0,
    }
    
    for item in dir_path.rglob('*'):
        if _should_ignore_file(item):
            continue
        
        if item.is_file():
            relative_path = item.relative_to(dir_path)
            structure["files"].append({
                "path": str(relative_path),
                "name": item.name,
                "size": item.stat().st_size,
                "type": item.suffix,
                "depth": len(relative_path.parts),
            })
            structure["total_files"] += 1
            structure["total_size"] += item.stat().st_size
        elif item.is_dir():
            relative_path = item.relative_to(dir_path)
            if len(relative_path.parts) <= 3:  # Limit depth
                structure["subdirectories"].append({
                    "path": str(relative_path),
                    "name": item.name,
                    "depth": len(relative_path.parts),
                })
    
    return structure


def evaluate_structure(structure: Dict[str, Any], optimize_for: str) -> float:
    """Evaluate current structure quality."""
    if structure["type"] == "file":
        return _evaluate_file_structure(structure, optimize_for)
    elif structure["type"] == "directory":
        return _evaluate_directory_structure(structure, optimize_for)
    else:
        return 5.0  # Default neutral score


def _evaluate_file_structure(structure: Dict[str, Any], optimize_for: str) -> float:
    """Evaluate file structure quality."""
    sections = structure.get("sections", [])
    
    if not sections:
        return 2.0  # Low score for unstructured content
    
    # Check heading hierarchy
    levels = [s["level"] for s in sections]
    hierarchy_score = 10.0
    
    for i in range(1, len(levels)):
        if levels[i] > levels[i-1] + 1:  # Skip levels
            hierarchy_score -= 1.0
    
    # Check section balance
    content_lines = [s.get("content_lines", 0) for s in sections]
    avg_content = sum(content_lines) / len(content_lines) if content_lines else 0
    
    balance_score = 10.0
    for lines in content_lines:
        if lines > avg_content * 3:  # Section too long
            balance_score -= 0.5
        elif lines < avg_content * 0.3:  # Section too short
            balance_score -= 0.5
    
    # Combine scores based on optimization target
    if optimize_for == "readability":
        return (hierarchy_score * 0.6 + balance_score * 0.4)
    elif optimize_for == "navigation":
        return (hierarchy_score * 0.8 + balance_score * 0.2)
    else:
        return (hierarchy_score * 0.5 + balance_score * 0.5)


def _evaluate_directory_structure(structure: Dict[str, Any], optimize_for: str) -> float:
    """Evaluate directory structure quality."""
    files = structure.get("files", [])
    subdirs = structure.get("subdirectories", [])
    
    if not files and not subdirs:
        return 1.0
    
    # Check depth distribution
    file_depths = [f["depth"] for f in files]
    max_depth = max(file_depths) if file_depths else 0
    avg_depth = sum(file_depths) / len(file_depths) if file_depths else 0
    
    depth_score = 10.0
    if max_depth > 5:  # Too deep
        depth_score -= (max_depth - 5) * 1.0
    if avg_depth > 3:  # Average too deep
        depth_score -= (avg_depth - 3) * 0.5
    
    # Check file organization
    file_types = Counter(f["type"] for f in files)
    type_diversity = len(file_types)
    
    organization_score = min(10.0, type_diversity * 2)  # Reward type diversity
    
    # Combine scores
    if optimize_for == "navigation":
        return (depth_score * 0.7 + organization_score * 0.3)
    elif optimize_for == "readability":
        return (depth_score * 0.5 + organization_score * 0.5)
    else:
        return (depth_score * 0.6 + organization_score * 0.4)


def optimize_structure_basic(
    current_structure: Dict[str, Any],
    pattern: str,
    target_audience: str,
    optimize_for: str,
) -> Dict[str, Any]:
    """Basic structure optimization fallback."""
    proposed_changes = []
    
    if current_structure["type"] == "file":
        changes = _optimize_file_structure(current_structure, pattern, optimize_for)
        proposed_changes.extend(changes)
    elif current_structure["type"] == "directory":
        changes = _optimize_directory_structure(current_structure, pattern, optimize_for)
        proposed_changes.extend(changes)
    
    # Calculate improvement score
    improvement_score = len(proposed_changes) * 0.5  # Rough estimate
    
    return {
        "current_structure": current_structure,
        "optimized_structure": current_structure,  # Would need actual optimization
        "proposed_changes": proposed_changes,
        "improvement_score": min(improvement_score, 5.0),
        "rationale": f"Applied {pattern} pattern optimization for {optimize_for}",
    }


def _optimize_file_structure(structure: Dict[str, Any], pattern: str, optimize_for: str) -> List[Dict]:
    """Generate optimization changes for file structure."""
    changes = []
    sections = structure.get("sections", [])
    
    if not sections:
        changes.append({
            "type": "add_structure",
            "target": "document",
            "description": "Add headings to structure the content",
            "impact_score": 3.0,
        })
        return changes
    
    # Check for hierarchy issues
    levels = [s["level"] for s in sections]
    for i in range(1, len(levels)):
        if levels[i] > levels[i-1] + 1:
            changes.append({
                "type": "fix_hierarchy",
                "target": sections[i]["title"],
                "description": f"Adjust heading level from H{levels[i]} to H{levels[i-1]+1}",
                "impact_score": 1.5,
            })
    
    # Check for unbalanced sections
    content_lines = [s.get("content_lines", 0) for s in sections]
    avg_content = sum(content_lines) / len(content_lines) if content_lines else 0
    
    for section in sections:
        lines = section.get("content_lines", 0)
        if lines > avg_content * 3:
            changes.append({
                "type": "split_section",
                "target": section["title"],
                "description": "Split large section into smaller subsections",
                "impact_score": 2.0,
            })
        elif lines < avg_content * 0.2 and lines > 0:
            changes.append({
                "type": "merge_section",
                "target": section["title"],
                "description": "Consider merging with adjacent section",
                "impact_score": 1.0,
            })
    
    return changes


def _optimize_directory_structure(structure: Dict[str, Any], pattern: str, optimize_for: str) -> List[Dict]:
    """Generate optimization changes for directory structure."""
    changes = []
    files = structure.get("files", [])
    
    # Group files by type
    files_by_type = defaultdict(list)
    for file_info in files:
        files_by_type[file_info["type"]].append(file_info)
    
    # Suggest grouping by type if pattern is modular
    if pattern == "modular":
        for file_type, type_files in files_by_type.items():
            if len(type_files) > 3:  # Multiple files of same type
                changes.append({
                    "type": "group_by_type",
                    "target": f"{file_type} files",
                    "description": f"Group {len(type_files)} {file_type} files into a subdirectory",
                    "impact_score": 1.5,
                })
    
    # Check for deep nesting
    deep_files = [f for f in files if f["depth"] > 4]
    if deep_files:
        changes.append({
            "type": "reduce_depth",
            "target": "deeply nested files",
            "description": f"Reduce nesting depth for {len(deep_files)} files",
            "impact_score": 2.0,
        })
    
    return changes


def apply_structure_changes(source: Path, proposed_changes: List[Dict]) -> List[Dict]:
    """Apply structure changes (dry run implementation)."""
    applied_changes = []
    
    for change in proposed_changes:
        # For this basic implementation, just log what would be done
        applied_changes.append({
            "change_id": change.get("type", "unknown"),
            "target": change.get("target", ""),
            "status": "simulated",  # Would be "applied" in real implementation
            "description": change.get("description", ""),
        })
    
    return applied_changes


def extract_knowledge_basic(
    content: str,
    extract_type: str,
    confidence_threshold: float,
    max_items: int,
) -> Dict[str, Any]:
    """Basic knowledge extraction fallback."""
    extracted_items = []
    
    if extract_type == "entities":
        # Extract named entities using simple patterns
        # Capitalized words
        entities = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', content)
        entity_counts = Counter(entities)
        
        for entity, count in entity_counts.most_common(max_items):
            confidence = min(1.0, count / 10)  # Simple confidence based on frequency
            if confidence >= confidence_threshold:
                extracted_items.append({
                    "id": f"entity_{entity.lower()}",
                    "name": entity,
                    "type": "named_entity",
                    "frequency": count,
                    "confidence": confidence,
                })
    
    elif extract_type == "concepts":
        # Extract concepts using keyword patterns
        concept_patterns = [
            r'\b(algorithm|method|approach|technique|strategy)\b',
            r'\b(principle|rule|law|theorem|concept)\b',
            r'\b(pattern|design|architecture|structure)\b',
        ]
        
        for pattern in concept_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                concept = match.group(1)
                extracted_items.append({
                    "id": f"concept_{concept.lower()}",
                    "name": concept,
                    "type": "concept",
                    "confidence": 0.8,
                    "context": content[max(0, match.start()-50):match.end()+50],
                })
    
    # Create confidence scores dict
    confidence_scores = {item["id"]: item["confidence"] for item in extracted_items}
    
    return {
        "extracted_items": extracted_items[:max_items],
        "relationships": [],  # Would need more sophisticated analysis
        "confidence_scores": confidence_scores,
        "summary": f"Extracted {len(extracted_items)} {extract_type} using basic patterns",
    }


def detect_domain(content: str) -> str:
    """Detect content domain."""
    # Simple keyword-based domain detection
    domains = {
        "software": ["code", "function", "class", "import", "def", "python", "javascript"],
        "science": ["research", "experiment", "hypothesis", "data", "analysis", "study"],
        "business": ["revenue", "profit", "customer", "market", "strategy", "sales"],
        "education": ["learn", "teach", "course", "student", "lesson", "curriculum"],
        "technical": ["system", "process", "method", "procedure", "implementation"],
    }
    
    content_lower = content.lower()
    domain_scores = {}
    
    for domain, keywords in domains.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        domain_scores[domain] = score
    
    # Return domain with highest score, or "general" if no clear winner
    if domain_scores:
        max_domain = max(domain_scores.items(), key=lambda x: x[1])
        return max_domain[0] if max_domain[1] > 2 else "general"
    
    return "general"


def create_graph_basic(
    entities: List[Dict],
    relationships: List[Dict],
    graph_type: str,
    layout: str,
    include_metadata: bool,
) -> Dict[str, Any]:
    """Basic graph creation fallback."""
    # Create nodes
    nodes = []
    for entity in entities:
        node = {
            "id": entity["id"],
            "label": entity.get("name", entity["id"]),
            "type": entity.get("type", "unknown"),
        }
        if include_metadata:
            node["metadata"] = {k: v for k, v in entity.items() if k not in ["id", "name"]}
        nodes.append(node)
    
    # Create edges
    edges = []
    for relationship in relationships:
        edge = {
            "source": relationship["source"],
            "target": relationship["target"],
            "type": relationship.get("type", "related"),
            "weight": relationship.get("confidence", 1.0),
        }
        edges.append(edge)
    
    # Basic layout coordinates (simple circle layout)
    import math
    node_count = len(nodes)
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / max(node_count, 1)
        radius = 100
        node["x"] = radius * math.cos(angle)
        node["y"] = radius * math.sin(angle)
    
    # Simple clustering (group by type)
    clusters = []
    node_types = defaultdict(list)
    for node in nodes:
        node_types[node["type"]].append(node)
    
    for node_type, type_nodes in node_types.items():
        if len(type_nodes) > 1:
            clusters.append({
                "name": f"{node_type.title()} Cluster",
                "type": node_type,
                "size": len(type_nodes),
                "nodes": [n["id"] for n in type_nodes],
            })
    
    graph_structure = {
        "nodes": nodes,
        "edges": edges,
    }
    
    return {
        "graph_structure": graph_structure,
        "layout_coordinates": {},  # Coordinates embedded in nodes
        "clusters": clusters,
        "metrics": {
            "density": len(edges) / max(len(nodes) * (len(nodes) - 1) / 2, 1),
            "average_degree": 2 * len(edges) / max(len(nodes), 1),
        },
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "graph_density": len(edges) / max(len(nodes) * (len(nodes) - 1) / 2, 1),
        "clusters_count": len(clusters),
    }


def calculate_graph_metrics(graph_structure: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate detailed graph metrics."""
    nodes = graph_structure.get("nodes", [])
    edges = graph_structure.get("edges", [])
    
    node_count = len(nodes)
    edge_count = len(edges)
    
    # Calculate degree distribution
    degree_count = defaultdict(int)
    for edge in edges:
        degree_count[edge["source"]] += 1
        degree_count[edge["target"]] += 1
    
    degrees = list(degree_count.values())
    avg_degree = sum(degrees) / max(len(degrees), 1)
    max_degree = max(degrees) if degrees else 0
    
    # Calculate density
    max_possible_edges = node_count * (node_count - 1) / 2
    density = edge_count / max_possible_edges if max_possible_edges > 0 else 0
    
    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "density": density,
        "average_degree": avg_degree,
        "max_degree": max_degree,
        "clustering_coefficient": 0.0,  # Would need more complex calculation
    }


def find_central_nodes(graph_structure: Dict[str, Any], limit: int = 10) -> List[Dict]:
    """Find most central nodes in graph."""
    nodes = graph_structure.get("nodes", [])
    edges = graph_structure.get("edges", [])
    
    # Calculate degree centrality (simple)
    degree_count = defaultdict(int)
    for edge in edges:
        degree_count[edge["source"]] += 1
        degree_count[edge["target"]] += 1
    
    # Create centrality list
    central_nodes = []
    for node in nodes:
        centrality = degree_count.get(node["id"], 0) / max(len(nodes) - 1, 1)
        central_nodes.append({
            "id": node["id"],
            "name": node.get("label", node["id"]),
            "type": node.get("type", "unknown"),
            "centrality": centrality,
            "degree": degree_count.get(node["id"], 0),
        })
    
    # Sort by centrality and return top nodes
    central_nodes.sort(key=lambda x: x["centrality"], reverse=True)
    return central_nodes[:limit]


def save_graph(graph_result: Dict[str, Any], output: Path, output_format: str) -> Path:
    """Save graph to file."""
    output.parent.mkdir(parents=True, exist_ok=True)
    
    if output_format == "json":
        output_file = output.with_suffix('.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_result, f, indent=2)
    
    elif output_format == "gml":
        # Basic GML format
        output_file = output.with_suffix('.gml')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("graph [\n")
            f.write("  directed 0\n")
            
            # Write nodes
            for node in graph_result["graph_structure"]["nodes"]:
                f.write("  node [\n")
                f.write(f"    id {node['id']}\n")
                f.write(f"    label \"{node.get('label', node['id'])}\"\n")
                f.write("  ]\n")
            
            # Write edges
            for edge in graph_result["graph_structure"]["edges"]:
                f.write("  edge [\n")
                f.write(f"    source {edge['source']}\n")
                f.write(f"    target {edge['target']}\n")
                f.write("  ]\n")
            
            f.write("]\n")
    
    elif output_format == "dot":
        # Graphviz DOT format
        output_file = output.with_suffix('.dot')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("graph G {\n")
            
            # Write nodes
            for node in graph_result["graph_structure"]["nodes"]:
                label = node.get('label', node['id'])
                f.write(f"  \"{node['id']}\" [label=\"{label}\"];\n")
            
            # Write edges
            for edge in graph_result["graph_structure"]["edges"]:
                f.write(f"  \"{edge['source']}\" -- \"{edge['target']}\";\n")
            
            f.write("}\n")
    
    else:
        # Default to JSON
        output_file = output.with_suffix('.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_result, f, indent=2)
    
    return output_file


def list_templates() -> List[Dict[str, Any]]:
    """List available information design templates."""
    templates_dir = Path.home() / ".uvmgr" / "templates" / "infodesign"
    templates = []
    
    if templates_dir.exists():
        for template_file in templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                templates.append({
                    "name": template_data.get("name", template_file.stem),
                    "type": template_data.get("type", "unknown"),
                    "created": template_data.get("created", "unknown"),
                    "usage_count": template_data.get("usage_count", 0),
                    "description": template_data.get("description", ""),
                })
            except Exception:
                # Skip invalid template files
                continue
    
    return templates


def create_template(template_name: str, source: Path, template_type: str) -> Path:
    """Create a new information design template."""
    templates_dir = Path.home() / ".uvmgr" / "templates" / "infodesign"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract template structure from source
    if source.is_file():
        content = load_content(source)
        structure = _parse_file_structure(content)
    else:
        structure = _parse_directory_structure(source)
    
    # Create template data
    template_data = {
        "name": template_name,
        "type": template_type,
        "created": datetime.now().isoformat(),
        "usage_count": 0,
        "source": str(source),
        "structure": structure,
        "description": f"Template created from {source}",
    }
    
    # Save template
    template_file = templates_dir / f"{template_name}.json"
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, indent=2)
    
    return template_file


def apply_template(template_name: str, target: Path, template_type: str) -> List[str]:
    """Apply an information design template."""
    templates_dir = Path.home() / ".uvmgr" / "templates" / "infodesign"
    template_file = templates_dir / f"{template_name}.json"
    
    if not template_file.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    with open(template_file, 'r', encoding='utf-8') as f:
        template_data = json.load(f)
    
    # For this basic implementation, create placeholder files based on template structure
    generated_files = []
    target.mkdir(parents=True, exist_ok=True)
    
    structure = template_data.get("structure", {})
    
    if structure.get("type") == "file":
        # Create documentation file based on template sections
        sections = structure.get("sections", [])
        content_lines = ["# Documentation"]
        content_lines.append(f"*Generated from template: {template_name}*")
        content_lines.append("")
        
        for section in sections:
            content_lines.append(f"## {section['title']}")
            content_lines.append("")
            content_lines.append("<!-- Content goes here -->")
            content_lines.append("")
        
        output_file = target / "README.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(content_lines))
        
        generated_files.append(str(output_file))
    
    elif structure.get("type") == "directory":
        # Create directory structure based on template
        subdirs = structure.get("subdirectories", [])
        for subdir_info in subdirs[:5]:  # Limit to prevent excessive creation
            subdir_path = target / subdir_info["name"]
            subdir_path.mkdir(exist_ok=True)
            
            # Create placeholder README in each subdirectory
            readme_file = subdir_path / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"# {subdir_info['name']}\n\nContent for {subdir_info['name']} directory.\n")
            
            generated_files.append(str(readme_file))
    
    # Update template usage count
    template_data["usage_count"] = template_data.get("usage_count", 0) + 1
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, indent=2)
    
    return generated_files


def delete_template(template_name: str) -> None:
    """Delete an information design template."""
    templates_dir = Path.home() / ".uvmgr" / "templates" / "infodesign"
    template_file = templates_dir / f"{template_name}.json"
    
    if not template_file.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    template_file.unlink()