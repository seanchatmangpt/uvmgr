"""
AI Knowledge Management and Code Understanding
=============================================

This module addresses the critical AI integration gap by providing:

1. **Code Understanding**: Semantic analysis of project structure and patterns
2. **Knowledge Management**: Persistent learning and retrieval using ChromaDB
3. **Context Awareness**: Project-aware AI assistance and suggestions
4. **Semantic Search**: Find relevant code, docs, and patterns quickly
5. **Learning Integration**: Continuous learning from codebase changes

The 80/20 approach: 20% of AI features that provide 80% of intelligent assistance.
"""

from __future__ import annotations

import os
import ast
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import time

# Conditional imports for AI/ML dependencies
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    chromadb = None
    SentenceTransformer = None
    KNOWLEDGE_AVAILABLE = False

from uvmgr.core.semconv import CliAttributes, AIAttributes, ProjectAttributes
from uvmgr.core.agi_reasoning import observe_with_agi_reasoning, get_agi_insights
from uvmgr.core.workspace import get_workspace_config


@dataclass
class CodeElement:
    """Represents a code element (class, function, module) with semantic information."""
    
    id: str
    type: str  # "class", "function", "module", "variable", "import"
    name: str
    file_path: str
    line_number: int
    
    # Code content
    source_code: str
    docstring: Optional[str] = None
    
    # Semantic information
    dependencies: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    hash: str = ""


@dataclass
class ProjectKnowledge:
    """Aggregated knowledge about the project structure and patterns."""
    
    project_name: str
    project_type: str
    
    # Structure analysis
    total_files: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    
    # Code elements
    classes: List[CodeElement] = field(default_factory=list)
    functions: List[CodeElement] = field(default_factory=list)
    modules: List[CodeElement] = field(default_factory=list)
    
    # Patterns and insights
    architectural_patterns: List[str] = field(default_factory=list)
    common_imports: Dict[str, int] = field(default_factory=dict)
    complexity_hotspots: List[str] = field(default_factory=list)
    
    # AI insights
    ai_suggestions: List[str] = field(default_factory=list)
    learning_insights: List[str] = field(default_factory=list)
    
    # Metadata
    last_analyzed: str = field(default_factory=lambda: datetime.now().isoformat())
    knowledge_version: str = "1.0.0"


class CodeAnalyzer:
    """Analyzes Python code to extract semantic information."""
    
    @staticmethod
    def analyze_file(file_path: Path) -> List[CodeElement]:
        """Analyze a Python file and extract code elements."""
        
        if not file_path.suffix == '.py' or not file_path.exists():
            return []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except Exception:
            return []
        
        elements = []
        
        for node in ast.walk(tree):
            element = None
            
            if isinstance(node, ast.ClassDef):
                element = CodeElement(
                    id=f"class:{file_path}:{node.name}",
                    type="class",
                    name=node.name,
                    file_path=str(file_path),
                    line_number=node.lineno,
                    source_code=ast.get_source_segment(content, node) or "",
                    docstring=ast.get_docstring(node),
                    complexity_score=CodeAnalyzer._calculate_complexity(node)
                )
                
            elif isinstance(node, ast.FunctionDef):
                element = CodeElement(
                    id=f"function:{file_path}:{node.name}",
                    type="function", 
                    name=node.name,
                    file_path=str(file_path),
                    line_number=node.lineno,
                    source_code=ast.get_source_segment(content, node) or "",
                    docstring=ast.get_docstring(node),
                    complexity_score=CodeAnalyzer._calculate_complexity(node)
                )
            
            if element:
                # Calculate hash for change detection
                element.hash = hashlib.md5(element.source_code.encode()).hexdigest()
                
                # Extract dependencies
                element.dependencies = CodeAnalyzer._extract_dependencies(node)
                
                # Generate tags
                element.tags = CodeAnalyzer._generate_tags(element)
                
                elements.append(element)
        
        return elements
    
    @staticmethod
    def _calculate_complexity(node: ast.AST) -> float:
        """Calculate cyclomatic complexity score."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    @staticmethod
    def _extract_dependencies(node: ast.AST) -> List[str]:
        """Extract dependencies from a code node."""
        dependencies = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                dependencies.append(child.id)
            elif isinstance(child, ast.Attribute):
                dependencies.append(child.attr)
        
        # Remove duplicates and common built-ins
        builtins = {'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple'}
        return list(set(dependencies) - builtins)
    
    @staticmethod
    def _generate_tags(element: CodeElement) -> List[str]:
        """Generate semantic tags for a code element."""
        tags = []
        
        # Type-based tags
        tags.append(element.type)
        
        # Complexity tags
        if element.complexity_score > 10:
            tags.append("complex")
        elif element.complexity_score < 3:
            tags.append("simple")
        
        # Name-based patterns
        name_lower = element.name.lower()
        if "test" in name_lower:
            tags.append("test")
        if "util" in name_lower or "helper" in name_lower:
            tags.append("utility")
        if "config" in name_lower:
            tags.append("configuration")
        if "api" in name_lower or "endpoint" in name_lower:
            tags.append("api")
        
        # Docstring analysis
        if element.docstring:
            tags.append("documented")
            if "TODO" in element.docstring or "FIXME" in element.docstring:
                tags.append("needs_attention")
        
        return tags


class KnowledgeBase:
    """
    AI-powered knowledge base using ChromaDB for semantic search and learning.
    
    Provides intelligent code understanding and context-aware assistance.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.knowledge_dir = self.workspace_root / ".uvmgr" / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[Any] = None
        self.embeddings_model: Optional[SentenceTransformer] = None
        
        self.project_knowledge: Optional[ProjectKnowledge] = None
        
        if KNOWLEDGE_AVAILABLE:
            self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize ChromaDB and embeddings model."""
        try:
            # Initialize ChromaDB
            self.client = chromadb.PersistentClient(path=str(self.knowledge_dir / "chroma"))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="uvmgr_code_knowledge",
                metadata={"description": "uvmgr code understanding and knowledge base"}
            )
            
            # Initialize embeddings model
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            
        except Exception as e:
            print(f"Warning: Failed to initialize knowledge base: {e}")
            KNOWLEDGE_AVAILABLE = False
    
    def analyze_project(self, force_reanalysis: bool = False) -> ProjectKnowledge:
        """Analyze the entire project and build knowledge base."""
        
        workspace_config = get_workspace_config()
        
        # Check if analysis is needed
        knowledge_file = self.knowledge_dir / "project_knowledge.json"
        if knowledge_file.exists() and not force_reanalysis:
            try:
                with open(knowledge_file, 'r') as f:
                    data = json.load(f)
                    self.project_knowledge = ProjectKnowledge(**data)
                    return self.project_knowledge
            except Exception:
                pass  # Fall through to re-analysis
        
        # Observe analysis start
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "knowledge_analyze",
                ProjectAttributes.NAME: workspace_config.project_name,
                AIAttributes.OPERATION: "analyze",
                "scope": "project"
            },
            context={
                "ai_knowledge_management": True,
                "code_understanding": True,
                "force_reanalysis": force_reanalysis
            }
        )
        
        knowledge = ProjectKnowledge(
            project_name=workspace_config.project_name,
            project_type=workspace_config.project_type
        )
        
        # Find all Python files
        python_files = list(self.workspace_root.rglob("*.py"))
        # Filter out common ignore patterns
        ignore_patterns = {'.venv', '__pycache__', '.git', 'node_modules', '.pytest_cache'}
        python_files = [f for f in python_files if not any(pattern in str(f) for pattern in ignore_patterns)]
        
        knowledge.total_files = len(python_files)
        knowledge.languages["python"] = len(python_files)
        
        # Analyze each file
        all_elements = []
        total_lines = 0
        
        for file_path in python_files:
            try:
                # Count lines
                content = file_path.read_text(encoding='utf-8')
                total_lines += len(content.splitlines())
                
                # Analyze code elements
                elements = CodeAnalyzer.analyze_file(file_path)
                all_elements.extend(elements)
                
            except Exception as e:
                continue  # Skip problematic files
        
        knowledge.total_lines = total_lines
        
        # Categorize elements
        for element in all_elements:
            if element.type == "class":
                knowledge.classes.append(element)
            elif element.type == "function":
                knowledge.functions.append(element)
            elif element.type == "module":
                knowledge.modules.append(element)
        
        # Extract patterns and insights
        knowledge.common_imports = self._extract_common_imports(python_files)
        knowledge.architectural_patterns = self._detect_architectural_patterns(knowledge)
        knowledge.complexity_hotspots = self._identify_complexity_hotspots(knowledge)
        
        # Generate AI insights
        knowledge.ai_suggestions = self._generate_ai_suggestions(knowledge)
        knowledge.learning_insights = self._extract_learning_insights(knowledge)
        
        # Store in vector database
        if KNOWLEDGE_AVAILABLE and self.collection:
            self._store_elements_in_knowledge_base(all_elements)
        
        # Save knowledge
        self.project_knowledge = knowledge
        self._save_project_knowledge(knowledge)
        
        # Observe analysis completion
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "knowledge_analyzed",
                "elements_count": str(len(all_elements)),
                "classes_count": str(len(knowledge.classes)),
                "functions_count": str(len(knowledge.functions)),
                "complexity_hotspots": str(len(knowledge.complexity_hotspots))
            },
            context={
                "ai_knowledge_management": True,
                "analysis_complete": True
            }
        )
        
        return knowledge
    
    def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search across the codebase."""
        
        if not KNOWLEDGE_AVAILABLE or not self.collection:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings_model.encode([query])
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=limit
            )
            
            # Format results
            search_results = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    search_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1.0 - distance,  # Convert distance to relevance
                        "file_path": metadata.get("file_path", ""),
                        "element_type": metadata.get("type", ""),
                        "name": metadata.get("name", "")
                    })
            
            # Observe search
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "knowledge_search",
                    AIAttributes.OPERATION: "search",
                    "query": query,
                    "results_count": str(len(search_results))
                },
                context={
                    "semantic_search": True,
                    "ai_knowledge_management": True
                }
            )
            
            return search_results
            
        except Exception as e:
            return []
    
    def get_context_for_ai(self, scope: str = "current_file") -> Dict[str, Any]:
        """Get relevant context for AI assistance."""
        
        if not self.project_knowledge:
            self.analyze_project()
        
        context = {
            "project_overview": {
                "name": self.project_knowledge.project_name,
                "type": self.project_knowledge.project_type,
                "total_files": self.project_knowledge.total_files,
                "total_lines": self.project_knowledge.total_lines,
                "languages": self.project_knowledge.languages
            },
            "architectural_patterns": self.project_knowledge.architectural_patterns,
            "common_imports": dict(list(self.project_knowledge.common_imports.items())[:10]),
            "complexity_hotspots": self.project_knowledge.complexity_hotspots[:5],
            "ai_suggestions": self.project_knowledge.ai_suggestions[:3],
            "recent_insights": self.project_knowledge.learning_insights[:3]
        }
        
        return context
    
    def learn_from_changes(self, changed_files: List[str]):
        """Learn from code changes and update knowledge base."""
        
        if not changed_files:
            return
        
        # Re-analyze changed files
        updated_elements = []
        for file_path_str in changed_files:
            file_path = Path(file_path_str)
            if file_path.suffix == '.py' and file_path.exists():
                elements = CodeAnalyzer.analyze_file(file_path)
                updated_elements.extend(elements)
        
        # Update knowledge base
        if KNOWLEDGE_AVAILABLE and self.collection and updated_elements:
            self._update_elements_in_knowledge_base(updated_elements)
        
        # Update project knowledge
        if self.project_knowledge:
            # Simple update - in practice, this would be more sophisticated
            for element in updated_elements:
                if element.type == "class":
                    # Update or add class
                    existing = next((c for c in self.project_knowledge.classes if c.id == element.id), None)
                    if existing:
                        existing = element
                    else:
                        self.project_knowledge.classes.append(element)
        
        # Observe learning
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "knowledge_learn",
                AIAttributes.OPERATION: "learn",
                "changed_files_count": str(len(changed_files)),
                "updated_elements": str(len(updated_elements))
            },
            context={
                "continuous_learning": True,
                "ai_knowledge_management": True
            }
        )
    
    def _extract_common_imports(self, python_files: List[Path]) -> Dict[str, int]:
        """Extract most common imports across the project."""
        
        import_counts = {}
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_counts[alias.name] = import_counts.get(alias.name, 0) + 1
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        import_counts[node.module] = import_counts.get(node.module, 0) + 1
                        
            except Exception:
                continue
        
        # Return top 20 most common imports
        return dict(sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:20])
    
    def _detect_architectural_patterns(self, knowledge: ProjectKnowledge) -> List[str]:
        """Detect architectural patterns in the codebase."""
        
        patterns = []
        
        # Check for common patterns based on structure
        class_names = [c.name for c in knowledge.classes]
        function_names = [f.name for f in knowledge.functions]
        
        # MVC pattern
        if any("Controller" in name for name in class_names) and any("Model" in name for name in class_names):
            patterns.append("MVC")
        
        # Repository pattern
        if any("Repository" in name for name in class_names):
            patterns.append("Repository")
        
        # Factory pattern
        if any("Factory" in name for name in class_names):
            patterns.append("Factory")
        
        # Command pattern
        if any("Command" in name for name in class_names):
            patterns.append("Command")
        
        # Observer pattern
        if any("Observer" in name or "Listener" in name for name in class_names):
            patterns.append("Observer")
        
        # Strategy pattern
        if any("Strategy" in name for name in class_names):
            patterns.append("Strategy")
        
        # API/Web patterns
        if any("app" in name or "router" in name for name in function_names):
            patterns.append("Web API")
        
        # CLI pattern
        if any("cli" in name or "command" in name for name in function_names):
            patterns.append("CLI Application")
        
        return patterns
    
    def _identify_complexity_hotspots(self, knowledge: ProjectKnowledge) -> List[str]:
        """Identify code complexity hotspots."""
        
        hotspots = []
        
        # Find high-complexity functions and classes
        all_elements = knowledge.classes + knowledge.functions
        high_complexity = [e for e in all_elements if e.complexity_score > 10]
        
        for element in sorted(high_complexity, key=lambda x: x.complexity_score, reverse=True)[:5]:
            hotspots.append(f"{element.file_path}:{element.name} (complexity: {element.complexity_score})")
        
        return hotspots
    
    def _generate_ai_suggestions(self, knowledge: ProjectKnowledge) -> List[str]:
        """Generate AI-powered suggestions for code improvement."""
        
        suggestions = []
        
        # Analyze patterns and suggest improvements
        if len(knowledge.complexity_hotspots) > 0:
            suggestions.append("Consider refactoring high-complexity functions to improve maintainability")
        
        if len([c for c in knowledge.classes if not c.docstring]) > len(knowledge.classes) * 0.5:
            suggestions.append("Add docstrings to classes to improve code documentation")
        
        if len([f for f in knowledge.functions if not f.docstring]) > len(knowledge.functions) * 0.7:
            suggestions.append("Add docstrings to functions to improve code documentation")
        
        # Test coverage suggestions
        test_functions = [f for f in knowledge.functions if "test" in f.name.lower()]
        if len(test_functions) < len(knowledge.functions) * 0.3:
            suggestions.append("Consider adding more unit tests to improve code coverage")
        
        # Architecture suggestions
        if "MVC" not in knowledge.architectural_patterns and len(knowledge.classes) > 10:
            suggestions.append("Consider adopting MVC pattern for better code organization")
        
        return suggestions
    
    def _extract_learning_insights(self, knowledge: ProjectKnowledge) -> List[str]:
        """Extract learning insights from AGI reasoning engine."""
        
        # Get AGI insights
        agi_insights = get_agi_insights()
        
        insights = []
        
        # Code understanding insights
        if agi_insights["understanding_confidence"] > 0.8:
            insights.append("High code understanding confidence - AGI ready for autonomous assistance")
        
        if len(agi_insights["improvement_suggestions"]) > 0:
            insights.append(f"AGI identified {len(agi_insights['improvement_suggestions'])} improvement opportunities")
        
        # Pattern recognition insights
        if agi_insights["cross_domain_patterns"] > 2:
            insights.append("Strong cross-domain patterns detected - good for knowledge transfer")
        
        return insights
    
    def _store_elements_in_knowledge_base(self, elements: List[CodeElement]):
        """Store code elements in ChromaDB for semantic search."""
        
        if not self.collection or not self.embeddings_model:
            return
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for element in elements:
            # Create document text for embedding
            doc_text = f"{element.name}\n{element.docstring or ''}\n{element.source_code}"
            documents.append(doc_text)
            
            # Metadata
            metadata = {
                "id": element.id,
                "type": element.type,
                "name": element.name,
                "file_path": element.file_path,
                "line_number": element.line_number,
                "complexity_score": element.complexity_score,
                "tags": ",".join(element.tags),
                "last_modified": element.last_modified
            }
            metadatas.append(metadata)
            ids.append(element.id)
        
        # Generate embeddings
        embeddings = self.embeddings_model.encode(documents)
        
        # Store in ChromaDB (upsert to handle updates)
        try:
            self.collection.upsert(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(f"Warning: Failed to store elements in knowledge base: {e}")
    
    def _update_elements_in_knowledge_base(self, elements: List[CodeElement]):
        """Update existing elements in the knowledge base."""
        # For now, just use the same method as storing
        self._store_elements_in_knowledge_base(elements)
    
    def _save_project_knowledge(self, knowledge: ProjectKnowledge):
        """Save project knowledge to disk."""
        
        knowledge_file = self.knowledge_dir / "project_knowledge.json"
        
        # Convert to dict (handle nested dataclasses)
        def to_dict(obj):
            if hasattr(obj, '__dict__'):
                result = {}
                for key, value in obj.__dict__.items():
                    if isinstance(value, list):
                        result[key] = [to_dict(item) if hasattr(item, '__dict__') else item for item in value]
                    elif hasattr(value, '__dict__'):
                        result[key] = to_dict(value)
                    else:
                        result[key] = value
                return result
            return obj
        
        try:
            with open(knowledge_file, 'w') as f:
                json.dump(to_dict(knowledge), f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save project knowledge: {e}")


# Global knowledge base instance
_knowledge_base: Optional[KnowledgeBase] = None

def get_knowledge_base(workspace_root: Optional[Path] = None) -> KnowledgeBase:
    """Get the global knowledge base instance."""
    global _knowledge_base
    
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase(workspace_root)
    
    return _knowledge_base

def analyze_project_knowledge(force_reanalysis: bool = False) -> ProjectKnowledge:
    """Analyze project and build knowledge base."""
    return get_knowledge_base().analyze_project(force_reanalysis)

def search_codebase(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Perform semantic search across the codebase."""
    return get_knowledge_base().semantic_search(query, limit)

def get_ai_context(scope: str = "current_file") -> Dict[str, Any]:
    """Get relevant context for AI assistance."""
    return get_knowledge_base().get_context_for_ai(scope)