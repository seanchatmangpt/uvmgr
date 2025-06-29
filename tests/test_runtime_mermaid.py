"""
Unit tests for runtime/mermaid.py module.

Tests the actual implementation of Mermaid diagram processing functions,
including file I/O operations, template processing, and error handling.
"""

from __future__ import annotations

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from uvmgr.runtime.mermaid import (
    load_diagram_source,
    extract_weaver_data,
    generate_diagram_template,
    detect_mermaid_type,
    validate_mermaid_syntax,
    calculate_diagram_statistics,
    _generate_flowchart_template,
    _generate_sequence_template,
    _extract_nodes_from_mermaid,
    _extract_relationships_from_mermaid
)


class TestLoadDiagramSource:
    """Test diagram source loading functions."""
    
    def test_load_diagram_source_from_file(self):
        """Test loading diagram content from a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "diagram.mmd"
            source_content = """
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
"""
            source_file.write_text(source_content)
            
            result = load_diagram_source(source_file, "file")
            
            assert "flowchart TD" in result
            assert "A[Start]" in result
            assert "B[Process]" in result
            
    def test_load_diagram_source_nonexistent_file(self):
        """Test error handling for nonexistent files."""
        nonexistent_file = Path("/nonexistent/diagram.mmd")
        
        with pytest.raises(FileNotFoundError):
            load_diagram_source(nonexistent_file, "file")
            
    def test_load_diagram_source_empty_file(self):
        """Test loading empty diagram file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_file = Path(temp_dir) / "empty.mmd"
            empty_file.write_text("")
            
            result = load_diagram_source(empty_file, "file")
            
            assert result == ""


class TestWeaverDataExtraction:
    """Test Weaver data extraction functions."""
    
    def test_extract_weaver_data_basic(self):
        """Test basic Weaver data extraction."""
        result = extract_weaver_data()
        
        assert "services" in result
        assert "dependencies" in result
        assert "spans_count" in result
        assert "conventions_count" in result
        assert "timestamp" in result
        
        # Verify data structure
        assert isinstance(result["services"], list)
        assert isinstance(result["dependencies"], list)
        assert isinstance(result["spans_count"], int)
        assert isinstance(result["conventions_count"], int)
        
    def test_extract_weaver_data_services(self):
        """Test that basic services are extracted."""
        result = extract_weaver_data()
        
        services = result["services"]
        assert len(services) >= 3
        assert "uvmgr-cli" in services
        assert "uvmgr-ops" in services
        assert "uvmgr-runtime" in services
        
    def test_extract_weaver_data_dependencies(self):
        """Test that service dependencies are extracted."""
        result = extract_weaver_data()
        
        dependencies = result["dependencies"]
        assert len(dependencies) >= 2
        
        # Check dependency structure
        for dep in dependencies:
            assert "from" in dep
            assert "to" in dep
            assert "type" in dep


class TestDiagramTemplateGeneration:
    """Test diagram template generation functions."""
    
    def test_generate_diagram_template_flowchart(self):
        """Test flowchart template generation."""
        content = "User authentication process with login validation"
        
        result = generate_diagram_template(
            content=content,
            diagram_type="flowchart",
            title="Authentication Flow"
        )
        
        assert "mermaid_code" in result
        assert "nodes" in result
        assert "relationships" in result
        assert "confidence_score" in result
        
        mermaid_code = result["mermaid_code"]
        assert "flowchart" in mermaid_code.lower()
        assert "Authentication Flow" in mermaid_code
        
    def test_generate_diagram_template_sequence(self):
        """Test sequence diagram template generation."""
        content = "User sends request to API server which queries database"
        
        result = generate_diagram_template(
            content=content,
            diagram_type="sequence",
            title="API Request Flow"
        )
        
        assert "mermaid_code" in result
        mermaid_code = result["mermaid_code"]
        assert "sequenceDiagram" in mermaid_code
        assert "API Request Flow" in mermaid_code
        
    def test_generate_diagram_template_class(self):
        """Test class diagram template generation."""
        content = "User class with name and email properties, Account class with balance"
        
        result = generate_diagram_template(
            content=content,
            diagram_type="class",
            title="Domain Model"
        )
        
        assert "mermaid_code" in result
        mermaid_code = result["mermaid_code"]
        assert "classDiagram" in mermaid_code
        assert "Domain Model" in mermaid_code


class TestMermaidTypeDetection:
    """Test Mermaid diagram type detection."""
    
    def test_detect_mermaid_type_flowchart(self):
        """Test detection of flowchart diagrams."""
        flowchart_code = """
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
"""
        result = detect_mermaid_type(flowchart_code)
        assert result == "flowchart"
        
    def test_detect_mermaid_type_sequence(self):
        """Test detection of sequence diagrams."""
        sequence_code = """
sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello Bob
    B-->>A: Hello Alice
"""
        result = detect_mermaid_type(sequence_code)
        assert result == "sequence"
        
    def test_detect_mermaid_type_class(self):
        """Test detection of class diagrams."""
        class_code = """
classDiagram
    class Animal
    class Dog
    Animal <|-- Dog
"""
        result = detect_mermaid_type(class_code)
        assert result == "class"
        
    def test_detect_mermaid_type_unknown(self):
        """Test detection of unknown diagram types."""
        unknown_code = "This is not a valid Mermaid diagram"
        result = detect_mermaid_type(unknown_code)
        assert result == "unknown"


class TestMermaidSyntaxValidation:
    """Test Mermaid syntax validation functions."""
    
    def test_validate_mermaid_syntax_valid_flowchart(self):
        """Test validation of valid flowchart syntax."""
        valid_flowchart = """
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
"""
        result = validate_mermaid_syntax(valid_flowchart)
        
        # Should return empty list for valid syntax
        assert isinstance(result, list)
        # Allow for some warnings but no critical errors
        critical_errors = [error for error in result if error.get("severity") == "error"]
        assert len(critical_errors) == 0
        
    def test_validate_mermaid_syntax_invalid_syntax(self):
        """Test validation of invalid Mermaid syntax."""
        invalid_syntax = """
flowchart TD
    A[Start] -> B[Process]  # Invalid arrow
    B --> C[End
    D[Orphan]
"""
        result = validate_mermaid_syntax(invalid_syntax, strict=True)
        
        assert isinstance(result, list)
        assert len(result) > 0  # Should find syntax issues
        
        # Check that errors contain relevant information
        error_messages = [error.get("message", "") for error in result]
        assert any("syntax" in msg.lower() or "arrow" in msg.lower() for msg in error_messages)
        
    def test_validate_mermaid_syntax_empty_input(self):
        """Test validation of empty input."""
        result = validate_mermaid_syntax("")
        
        assert isinstance(result, list)
        assert len(result) >= 1  # Should report empty diagram issue
        assert any("empty" in error.get("message", "").lower() for error in result)


class TestDiagramStatistics:
    """Test diagram statistics calculation functions."""
    
    def test_calculate_diagram_statistics_flowchart(self):
        """Test statistics calculation for flowchart."""
        flowchart_code = """
flowchart TD
    A[Start] --> B[Process]
    B --> C[Decision]
    C -->|Yes| D[Action1]
    C -->|No| E[Action2]
    D --> F[End]
    E --> F[End]
"""
        result = calculate_diagram_statistics(flowchart_code)
        
        assert "nodes_count" in result
        assert "edges_count" in result
        assert "diagram_type" in result
        assert "complexity_score" in result
        assert "lines_count" in result
        
        assert result["diagram_type"] == "flowchart"
        assert result["nodes_count"] >= 5  # A, B, C, D, E, F
        assert result["edges_count"] >= 6  # All the arrows
        assert isinstance(result["complexity_score"], (int, float))
        
    def test_calculate_diagram_statistics_sequence(self):
        """Test statistics calculation for sequence diagram."""
        sequence_code = """
sequenceDiagram
    participant A as Alice
    participant B as Bob
    participant C as Charlie
    A->>B: Message 1
    B->>C: Message 2
    C-->>B: Reply 1
    B-->>A: Reply 2
"""
        result = calculate_diagram_statistics(sequence_code)
        
        assert result["diagram_type"] == "sequence"
        assert result["nodes_count"] >= 3  # Alice, Bob, Charlie
        assert result["edges_count"] >= 4  # All the messages
        
    def test_calculate_diagram_statistics_empty(self):
        """Test statistics calculation for empty diagram."""
        result = calculate_diagram_statistics("")
        
        assert result["nodes_count"] == 0
        assert result["edges_count"] == 0
        assert result["diagram_type"] == "unknown"
        assert result["complexity_score"] == 0


class TestDiagramTemplateHelpers:
    """Test diagram template helper functions."""
    
    def test_generate_flowchart_template_basic(self):
        """Test basic flowchart template generation."""
        content = "Process user registration with validation"
        title = "User Registration"
        
        result = _generate_flowchart_template(content, title)
        
        assert "flowchart TD" in result
        assert "User Registration" in result
        assert isinstance(result, str)
        assert len(result) > 50  # Should generate substantial content
        
    def test_generate_sequence_template_basic(self):
        """Test basic sequence template generation."""
        content = "User sends request to server which processes data"
        title = "Request Processing"
        
        result = _generate_sequence_template(content, title)
        
        assert "sequenceDiagram" in result
        assert "Request Processing" in result
        assert "participant" in result
        assert isinstance(result, str)
        
    def test_extract_nodes_from_mermaid_flowchart(self):
        """Test node extraction from flowchart."""
        mermaid_code = """
flowchart TD
    A[Start Process]
    B[Validate Input]
    C{Decision Point}
    D[Process Data]
    E[End]
"""
        result = _extract_nodes_from_mermaid(mermaid_code, "flowchart")
        
        assert isinstance(result, list)
        assert len(result) >= 5
        
        # Check node structure
        for node in result:
            assert "id" in node
            assert "label" in node
            assert "type" in node
            
        # Verify specific nodes
        node_ids = [node["id"] for node in result]
        assert "A" in node_ids
        assert "B" in node_ids
        assert "C" in node_ids
        
    def test_extract_relationships_from_mermaid_flowchart(self):
        """Test relationship extraction from flowchart."""
        mermaid_code = """
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
    A -.-> D[Optional]
"""
        result = _extract_relationships_from_mermaid(mermaid_code, "flowchart")
        
        assert isinstance(result, list)
        assert len(result) >= 3
        
        # Check relationship structure
        for rel in result:
            assert "source" in rel
            assert "target" in rel
            assert "type" in rel
            
        # Verify specific relationships
        sources = [rel["source"] for rel in result]
        targets = [rel["target"] for rel in result]
        assert "A" in sources
        assert "B" in sources
        assert "B" in targets
        assert "C" in targets


class TestMermaidErrorHandling:
    """Test error handling in Mermaid functions."""
    
    def test_load_diagram_source_permission_error(self):
        """Test handling of permission errors."""
        # Try to read from a restricted location
        restricted_path = Path("/root/restricted.mmd")
        
        with pytest.raises((FileNotFoundError, PermissionError)):
            load_diagram_source(restricted_path, "file")
            
    def test_generate_diagram_template_invalid_type(self):
        """Test handling of invalid diagram types."""
        result = generate_diagram_template(
            content="Test content",
            diagram_type="invalid_type",
            title="Test"
        )
        
        # Should handle gracefully with generic template
        assert "mermaid_code" in result
        assert isinstance(result["mermaid_code"], str)
        
    def test_validate_mermaid_syntax_malformed_input(self):
        """Test validation with severely malformed input."""
        malformed_input = "!@#$%^&*()_+"
        
        result = validate_mermaid_syntax(malformed_input)
        
        assert isinstance(result, list)
        assert len(result) > 0  # Should report errors
        
    def test_calculate_diagram_statistics_malformed_input(self):
        """Test statistics calculation with malformed input."""
        malformed_input = "This is not a diagram at all"
        
        result = calculate_diagram_statistics(malformed_input)
        
        # Should handle gracefully
        assert "nodes_count" in result
        assert "edges_count" in result
        assert "diagram_type" in result
        assert result["diagram_type"] == "unknown"


class TestMermaidIntegration:
    """Integration tests for Mermaid workflow."""
    
    def test_full_mermaid_workflow(self):
        """Test complete Mermaid diagram processing workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Create a diagram file
            diagram_file = Path(temp_dir) / "workflow.mmd"
            diagram_content = """
flowchart TD
    A[User Request] --> B[Validation]
    B --> C{Valid?}
    C -->|Yes| D[Process]
    C -->|No| E[Error]
    D --> F[Response]
    E --> F[Response]
"""
            diagram_file.write_text(diagram_content)
            
            # Step 2: Load diagram source
            loaded_content = load_diagram_source(diagram_file, "file")
            assert "flowchart TD" in loaded_content
            
            # Step 3: Detect diagram type
            diagram_type = detect_mermaid_type(loaded_content)
            assert diagram_type == "flowchart"
            
            # Step 4: Validate syntax
            validation_errors = validate_mermaid_syntax(loaded_content)
            critical_errors = [e for e in validation_errors if e.get("severity") == "error"]
            assert len(critical_errors) == 0
            
            # Step 5: Calculate statistics
            stats = calculate_diagram_statistics(loaded_content)
            assert stats["diagram_type"] == "flowchart"
            assert stats["nodes_count"] >= 6
            assert stats["edges_count"] >= 6
            
            # Step 6: Extract Weaver data
            weaver_data = extract_weaver_data()
            assert "services" in weaver_data
            assert len(weaver_data["services"]) >= 3
            
    def test_mermaid_template_generation_workflow(self):
        """Test template generation and processing workflow."""
        # Step 1: Generate template from content
        content = "User authentication system with login, validation, and session management"
        template_result = generate_diagram_template(
            content=content,
            diagram_type="flowchart",
            title="Authentication System"
        )
        
        assert "mermaid_code" in template_result
        generated_code = template_result["mermaid_code"]
        
        # Step 2: Validate generated template
        validation_errors = validate_mermaid_syntax(generated_code)
        critical_errors = [e for e in validation_errors if e.get("severity") == "error"]
        assert len(critical_errors) == 0
        
        # Step 3: Calculate statistics on generated template
        stats = calculate_diagram_statistics(generated_code)
        assert stats["diagram_type"] == "flowchart"
        assert stats["nodes_count"] > 0
        
        # Step 4: Verify template contains expected elements
        assert "Authentication System" in generated_code
        assert "flowchart" in generated_code.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])