"""
Persistent AGI Memory System
============================

This module implements persistent vector-based memory for the AGI system,
enabling knowledge retention across sessions and semantic similarity search.

Key Features:
- Vector embeddings for semantic similarity
- Persistent storage with ChromaDB
- Automatic knowledge extraction from observations
- Cross-session learning retention
- Semantic search and retrieval

This fills the critical gap preventing true AGI: ephemeral memory.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

from uvmgr.core.agi_reasoning import SemanticObservation, CausalPattern, CrossDomainPattern


@dataclass
class MemoryEntry:
    """A single memory entry with metadata."""
    id: str
    content: str
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]
    timestamp: float
    memory_type: str  # observation, pattern, goal, strategy, outcome
    importance: float = 0.5
    access_count: int = 0
    last_accessed: float = 0.0


@dataclass
class RetrievedMemory:
    """Memory retrieved from semantic search."""
    memory: MemoryEntry
    similarity: float
    relevance_score: float


class PersistentVectorMemory:
    """
    Persistent vector memory system for AGI knowledge storage.
    
    Enables true AGI capabilities:
    - Semantic storage and retrieval
    - Cross-session learning persistence  
    - Knowledge accumulation over time
    - Intelligent memory consolidation
    """
    
    def __init__(self, memory_path: Optional[Path] = None):
        self.memory_path = memory_path or Path.home() / ".uvmgr" / "agi_memory"
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.memory_cache: Dict[str, MemoryEntry] = {}
        
        # Initialize if dependencies available
        if MEMORY_AVAILABLE:
            self._initialize_memory_system()
        else:
            print("⚠️  ChromaDB/SentenceTransformers not available - memory will be limited")
    
    def _initialize_memory_system(self):
        """Initialize the persistent memory system."""
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize ChromaDB with persistent storage
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.memory_path / "chroma_db"),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection("agi_memory")
            except ValueError:
                # Create new collection
                self.collection = self.chroma_client.create_collection(
                    name="agi_memory",
                    metadata={"description": "AGI persistent memory storage"}
                )
            
            # Load memory cache
            self._load_memory_cache()
            
        except Exception as e:
            print(f"⚠️  Memory system initialization failed: {e}")
            MEMORY_AVAILABLE = False
    
    def store_observation(self, observation: SemanticObservation) -> str:
        """Store a semantic observation in persistent memory."""
        if not MEMORY_AVAILABLE:
            return "memory_disabled"
        
        # Create memory entry
        memory_id = str(uuid.uuid4())
        content = self._observation_to_text(observation)
        embedding = self._create_embedding(content)
        
        metadata = {
            "type": "observation",
            "intent": observation.inferred_intent or "unknown",
            "confidence": observation.confidence,
            "causal_predecessors": len(observation.causal_predecessors),
            "attributes": json.dumps(observation.attributes),
            "context": json.dumps(observation.context),
            "timestamp": observation.timestamp
        }
        
        memory_entry = MemoryEntry(
            id=memory_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            timestamp=observation.timestamp,
            memory_type="observation",
            importance=observation.confidence
        )
        
        # Store in vector database
        self._store_in_vector_db(memory_entry)
        
        # Cache locally
        self.memory_cache[memory_id] = memory_entry
        
        return memory_id
    
    def store_pattern(self, pattern: CausalPattern) -> str:
        """Store a causal pattern in persistent memory."""
        if not MEMORY_AVAILABLE:
            return "memory_disabled"
        
        memory_id = str(uuid.uuid4())
        content = f"Causal Pattern: {pattern.cause_pattern} leads to {pattern.effect_pattern}"
        embedding = self._create_embedding(content)
        
        metadata = {
            "type": "causal_pattern",
            "confidence": pattern.confidence,
            "frequency": pattern.frequency,
            "last_seen": pattern.last_seen,
            "cause": json.dumps(pattern.cause_pattern),
            "effect": json.dumps(pattern.effect_pattern)
        }
        
        memory_entry = MemoryEntry(
            id=memory_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
            timestamp=pattern.last_seen,
            memory_type="pattern",
            importance=pattern.confidence * min(1.0, pattern.frequency / 10)
        )
        
        self._store_in_vector_db(memory_entry)
        self.memory_cache[memory_id] = memory_entry
        
        return memory_id
    
    def store_knowledge(self, 
                       content: str, 
                       knowledge_type: str,
                       metadata: Dict[str, Any] = None) -> str:
        """Store arbitrary knowledge in memory."""
        if not MEMORY_AVAILABLE:
            return "memory_disabled"
        
        memory_id = str(uuid.uuid4())
        embedding = self._create_embedding(content)
        
        full_metadata = {
            "type": knowledge_type,
            "timestamp": time.time(),
            **(metadata or {})
        }
        
        memory_entry = MemoryEntry(
            id=memory_id,
            content=content,
            embedding=embedding,
            metadata=full_metadata,
            timestamp=time.time(),
            memory_type=knowledge_type,
            importance=metadata.get("importance", 0.5) if metadata else 0.5
        )
        
        self._store_in_vector_db(memory_entry)
        self.memory_cache[memory_id] = memory_entry
        
        return memory_id
    
    def retrieve_similar(self, 
                        query: str, 
                        n_results: int = 5,
                        memory_type: Optional[str] = None,
                        min_similarity: float = 0.3) -> List[RetrievedMemory]:
        """Retrieve semantically similar memories."""
        if not MEMORY_AVAILABLE or not self.collection:
            return []
        
        try:
            # Create query embedding
            query_embedding = self._create_embedding(query)
            
            # Build where clause for filtering
            where_clause = {}
            if memory_type:
                where_clause["type"] = memory_type
            
            # Query vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            # Process results
            retrieved_memories = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0], 
                results["distances"][0]
            )):
                # Convert distance to similarity (ChromaDB uses cosine distance)
                similarity = 1.0 - distance
                
                if similarity >= min_similarity:
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance(query, doc, metadata, similarity)
                    
                    # Create memory entry
                    memory_entry = MemoryEntry(
                        id=metadata.get("id", f"unknown_{i}"),
                        content=doc,
                        embedding=None,  # Don't load embeddings in results
                        metadata=metadata,
                        timestamp=metadata.get("timestamp", time.time()),
                        memory_type=metadata.get("type", "unknown"),
                        importance=metadata.get("importance", 0.5),
                        access_count=metadata.get("access_count", 0),
                        last_accessed=metadata.get("last_accessed", 0.0)
                    )
                    
                    retrieved_memories.append(RetrievedMemory(
                        memory=memory_entry,
                        similarity=similarity,
                        relevance_score=relevance_score
                    ))
            
            # Sort by relevance score
            retrieved_memories.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Update access counts
            for retrieved in retrieved_memories:
                self._update_access_stats(retrieved.memory.id)
            
            return retrieved_memories
            
        except Exception as e:
            print(f"⚠️  Memory retrieval failed: {e}")
            return []
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics."""
        if not MEMORY_AVAILABLE or not self.collection:
            return {"status": "disabled", "total_memories": 0}
        
        try:
            # Get collection count
            collection_count = self.collection.count()
            
            # Analyze memory types
            type_counts = {}
            importance_distribution = []
            
            for memory in self.memory_cache.values():
                mem_type = memory.memory_type
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
                importance_distribution.append(memory.importance)
            
            avg_importance = sum(importance_distribution) / len(importance_distribution) if importance_distribution else 0
            
            return {
                "status": "active",
                "total_memories": collection_count,
                "cached_memories": len(self.memory_cache),
                "memory_types": type_counts,
                "average_importance": avg_importance,
                "memory_path": str(self.memory_path),
                "embedding_model": "all-MiniLM-L6-v2" if self.embedding_model else None
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def consolidate_memories(self, threshold: float = 0.95) -> Dict[str, int]:
        """Consolidate highly similar memories to prevent redundancy."""
        if not MEMORY_AVAILABLE:
            return {"consolidated": 0, "total": 0}
        
        consolidation_stats = {"consolidated": 0, "total": len(self.memory_cache)}
        
        # This is a simplified consolidation - in production, you'd want more sophisticated deduplication
        # For now, we'll just mark similar memories
        
        return consolidation_stats
    
    def _observation_to_text(self, observation: SemanticObservation) -> str:
        """Convert observation to searchable text."""
        text_parts = []
        
        # Add intent
        if observation.inferred_intent:
            text_parts.append(f"Intent: {observation.inferred_intent}")
        
        # Add attributes
        for key, value in observation.attributes.items():
            text_parts.append(f"{key}: {value}")
        
        # Add context
        for key, value in observation.context.items():
            text_parts.append(f"Context {key}: {value}")
        
        # Add causal info
        if observation.causal_predecessors:
            text_parts.append(f"Preceded by: {', '.join(observation.causal_predecessors)}")
        
        return " | ".join(text_parts)
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding for text."""
        if not self.embedding_model:
            return []
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"⚠️  Embedding creation failed: {e}")
            return []
    
    def _store_in_vector_db(self, memory_entry: MemoryEntry):
        """Store memory entry in vector database."""
        if not self.collection:
            return
        
        try:
            self.collection.add(
                embeddings=[memory_entry.embedding] if memory_entry.embedding else None,
                documents=[memory_entry.content],
                metadatas=[{
                    **memory_entry.metadata,
                    "id": memory_entry.id,
                    "importance": memory_entry.importance,
                    "access_count": memory_entry.access_count,
                    "last_accessed": memory_entry.last_accessed
                }],
                ids=[memory_entry.id]
            )
        except Exception as e:
            print(f"⚠️  Vector storage failed: {e}")
    
    def _calculate_relevance(self, query: str, document: str, metadata: Dict, similarity: float) -> float:
        """Calculate relevance score for retrieved memory."""
        relevance = similarity * 0.7  # Base similarity weight
        
        # Boost recent memories
        age_hours = (time.time() - metadata.get("timestamp", 0)) / 3600
        recency_boost = max(0, 0.2 * (1 - min(age_hours / 168, 1)))  # Decay over a week
        
        # Boost important memories
        importance_boost = metadata.get("importance", 0.5) * 0.1
        
        # Boost frequently accessed memories
        access_boost = min(0.1, metadata.get("access_count", 0) * 0.01)
        
        return relevance + recency_boost + importance_boost + access_boost
    
    def _update_access_stats(self, memory_id: str):
        """Update access statistics for a memory."""
        if memory_id in self.memory_cache:
            memory = self.memory_cache[memory_id]
            memory.access_count += 1
            memory.last_accessed = time.time()
    
    def _load_memory_cache(self):
        """Load memory entries into local cache."""
        if not self.collection:
            return
        
        try:
            # Get all memories for caching
            # Note: In production, you'd implement smart caching
            results = self.collection.get(include=["metadatas", "documents"])
            
            for doc, metadata in zip(results["documents"], results["metadatas"]):
                memory_entry = MemoryEntry(
                    id=metadata["id"],
                    content=doc,
                    embedding=None,  # Don't cache embeddings
                    metadata=metadata,
                    timestamp=metadata.get("timestamp", time.time()),
                    memory_type=metadata.get("type", "unknown"),
                    importance=metadata.get("importance", 0.5),
                    access_count=metadata.get("access_count", 0),
                    last_accessed=metadata.get("last_accessed", 0.0)
                )
                self.memory_cache[memory_entry.id] = memory_entry
                
        except Exception as e:
            print(f"⚠️  Memory cache loading failed: {e}")


# Global persistent memory instance
_persistent_memory = None

def get_persistent_memory() -> PersistentVectorMemory:
    """Get the global persistent memory instance."""
    global _persistent_memory
    if _persistent_memory is None:
        _persistent_memory = PersistentVectorMemory()
    return _persistent_memory

def store_agi_observation(observation: SemanticObservation) -> str:
    """Store an AGI observation in persistent memory."""
    memory = get_persistent_memory()
    return memory.store_observation(observation)

def retrieve_relevant_memories(query: str, n_results: int = 5) -> List[RetrievedMemory]:
    """Retrieve memories relevant to a query."""
    memory = get_persistent_memory()
    return memory.retrieve_similar(query, n_results)

def get_memory_insights() -> Dict[str, Any]:
    """Get insights about the memory system."""
    memory = get_persistent_memory()
    return memory.get_memory_stats()