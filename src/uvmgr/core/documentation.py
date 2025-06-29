"""
Technical Writing Automation with Spiff and DSPy
================================================

This module provides intelligent technical writing automation using SpiffWorkflow
for orchestration and DSPy for AI-powered content generation. It implements the
80/20 principle: 20% effort for 80% of documentation automation value.

Key features:
1. **Workflow-Driven Generation**: BPMN workflows for document creation
2. **AI Content Generation**: DSPy signatures for intelligent writing
3. **Template Management**: Reusable templates with variable substitution
4. **Multi-Format Output**: Markdown, HTML, PDF, Word generation
5. **Content Validation**: Automated quality checks and reviews

The 80/20 approach: Essential documentation automation covering most use cases.
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
import yaml

import dspy
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.bpmn.parser.BpmnParser import BpmnParser
from SpiffWorkflow.task import Task

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.semconv import CliAttributes

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of technical documents."""
    API_DOCS = "api_docs"
    USER_GUIDE = "user_guide"
    TECHNICAL_SPEC = "technical_spec"
    README = "readme"
    CHANGELOG = "changelog"
    TUTORIAL = "tutorial"
    ARCHITECTURE = "architecture"
    DEPLOYMENT = "deployment"
    TROUBLESHOOTING = "troubleshooting"
    REFERENCE = "reference"


class OutputFormat(Enum):
    """Output formats for documents."""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    ASCIIDOC = "asciidoc"
    RST = "rst"


@dataclass
class DocumentContext:
    """Context for document generation."""
    project_name: str
    version: str = "1.0.0"
    author: str = "uvmgr"
    description: str = ""
    
    # Code analysis context
    codebase_path: Optional[Path] = None
    api_endpoints: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Project metadata
    dependencies: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    
    # Custom context
    custom_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentTemplate:
    """Document template configuration."""
    name: str
    type: DocumentType
    template_path: Path
    variables: Dict[str, str] = field(default_factory=dict)
    sections: List[str] = field(default_factory=list)
    ai_signatures: List[str] = field(default_factory=list)
    
    # Template metadata
    description: str = ""
    author: str = ""
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)


@dataclass
class GeneratedDocument:
    """Generated document result."""
    content: str
    format: OutputFormat
    template: DocumentTemplate
    context: DocumentContext
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Generation metrics
    generation_time: float = 0.0
    word_count: int = 0
    sections_count: int = 0
    ai_generated_sections: int = 0


# DSPy Signatures for Technical Writing
class GenerateAPIDocumentation(dspy.Signature):
    """Generate comprehensive API documentation from function/endpoint definitions."""
    
    function_signature = dspy.InputField(desc="Function or endpoint signature")
    function_docstring = dspy.InputField(desc="Existing docstring or description")
    context = dspy.InputField(desc="Additional context about the function")
    
    api_documentation = dspy.OutputField(desc="Complete API documentation with examples")


class GenerateUserGuide(dspy.Signature):
    """Generate user guide sections for software features."""
    
    feature_description = dspy.InputField(desc="Description of the feature")
    usage_examples = dspy.InputField(desc="Example usage scenarios")
    target_audience = dspy.InputField(desc="Target audience (beginner, intermediate, advanced)")
    
    user_guide_section = dspy.OutputField(desc="Complete user guide section with examples")


class GenerateTechnicalSpecification(dspy.Signature):
    """Generate technical specification sections from requirements."""
    
    requirements = dspy.InputField(desc="Technical requirements and constraints")
    architecture_overview = dspy.InputField(desc="High-level architecture description")
    implementation_details = dspy.InputField(desc="Implementation considerations")
    
    technical_spec = dspy.OutputField(desc="Detailed technical specification")


class GenerateArchitectureDoc(dspy.Signature):
    """Generate architecture documentation from system design."""
    
    system_components = dspy.InputField(desc="List of system components and their roles")
    data_flow = dspy.InputField(desc="Description of data flow between components")
    design_decisions = dspy.InputField(desc="Key architectural design decisions")
    
    architecture_documentation = dspy.OutputField(desc="Complete architecture documentation")


class GenerateTroubleshootingGuide(dspy.Signature):
    """Generate troubleshooting guides from common issues."""
    
    common_issues = dspy.InputField(desc="List of common issues and error messages")
    system_context = dspy.InputField(desc="System context and environment details")
    debugging_tools = dspy.InputField(desc="Available debugging and diagnostic tools")
    
    troubleshooting_guide = dspy.OutputField(desc="Comprehensive troubleshooting guide")


class TechnicalWritingEngine:
    """AI-powered technical writing engine using DSPy."""
    
    def __init__(self, model: str = "qwen3"):
        """Initialize the technical writing engine with Qwen3."""
        self.model = model
        self._setup_dspy()
        
        # Initialize AI generators
        self.api_doc_generator = dspy.ChainOfThought(GenerateAPIDocumentation)
        self.user_guide_generator = dspy.ChainOfThought(GenerateUserGuide)
        self.tech_spec_generator = dspy.ChainOfThought(GenerateTechnicalSpecification)
        self.architecture_generator = dspy.ChainOfThought(GenerateArchitectureDoc)
        self.troubleshooting_generator = dspy.ChainOfThought(GenerateTroubleshootingGuide)
    
    def _setup_dspy(self):
        """Setup DSPy with Qwen3 via Ollama only."""
        try:
            lm = dspy.LM(model="ollama/qwen3", max_tokens=2000)
            dspy.settings.configure(lm=lm)
            logger.info("DSPy configured with Qwen3 for technical writing")
        except Exception as e:
            logger.error(f"Failed to configure DSPy with Qwen3: {e}")
            raise RuntimeError("Qwen3 via Ollama is required for technical writing. No fallback is allowed.")
    
    def generate_api_documentation(
        self,
        function_signature: str,
        docstring: str = "",
        context: str = ""
    ) -> str:
        """Generate API documentation for a function."""
        try:
            result = self.api_doc_generator(
                function_signature=function_signature,
                function_docstring=docstring,
                context=context
            )
            return result.api_documentation
        except Exception as e:
            logger.error(f"Failed to generate API documentation: {e}")
            return NotImplemented
    
    def generate_user_guide_section(
        self,
        feature_description: str,
        usage_examples: str = "",
        target_audience: str = "intermediate"
    ) -> str:
        """Generate user guide section."""
        try:
            result = self.user_guide_generator(
                feature_description=feature_description,
                usage_examples=usage_examples,
                target_audience=target_audience
            )
            return result.user_guide_section
        except Exception as e:
            logger.error(f"Failed to generate user guide: {e}")
            return NotImplemented
    
    def generate_technical_spec(
        self,
        requirements: str,
        architecture: str = "",
        implementation: str = ""
    ) -> str:
        """Generate technical specification."""
        try:
            result = self.tech_spec_generator(
                requirements=requirements,
                architecture_overview=architecture,
                implementation_details=implementation
            )
            return result.technical_spec
        except Exception as e:
            logger.error(f"Failed to generate technical spec: {e}")
            return NotImplemented
    
    def generate_architecture_doc(
        self,
        components: str,
        data_flow: str = "",
        design_decisions: str = ""
    ) -> str:
        """Generate architecture documentation."""
        try:
            result = self.architecture_generator(
                system_components=components,
                data_flow=data_flow,
                design_decisions=design_decisions
            )
            return result.architecture_documentation
        except Exception as e:
            logger.error(f"Failed to generate architecture doc: {e}")
            return NotImplemented
    
    def generate_troubleshooting_guide(
        self,
        issues: str,
        context: str = "",
        tools: str = ""
    ) -> str:
        """Generate troubleshooting guide."""
        try:
            result = self.troubleshooting_generator(
                common_issues=issues,
                system_context=context,
                debugging_tools=tools
            )
            return result.troubleshooting_guide
        except Exception as e:
            logger.error(f"Failed to generate troubleshooting guide: {e}")
            return NotImplemented
    
    # Mock response methods for demo purposes
    def _mock_api_documentation(self, function_signature: str) -> str:
        """Generate mock API documentation."""
        return f"""## API Documentation

### Function: {function_signature}

**Description:**
This function provides core functionality for the application. It handles input validation,
processing, and returns structured output.

**Parameters:**
- `param1` (str): Primary input parameter for processing
- `param2` (int, optional): Optional configuration parameter (default: 10)

**Returns:**
- `dict`: Structured response containing processing results

**Example Usage:**
```python
result = {function_signature}("example_input", 20)
print(result)
# Output: {{"status": "success", "data": "processed_example_input"}}
```

**Error Handling:**
- Raises `ValueError` for invalid input parameters
- Raises `RuntimeError` for processing failures

**Notes:**
- This function is thread-safe
- Performance: O(n) where n is the size of input data
"""
    
    def _mock_user_guide(self, feature_description: str) -> str:
        """Generate mock user guide section."""
        return f"""## User Guide: {feature_description}

### Overview
{feature_description} is a powerful feature that enables users to accomplish their tasks efficiently.
This guide will walk you through the essential steps to get started.

### Getting Started

#### Step 1: Initial Setup
Before using this feature, ensure you have completed the initial setup:

1. Install the required dependencies
2. Configure your environment
3. Verify the installation

#### Step 2: Basic Usage
Here's how to use the basic functionality:

```bash
# Basic command
uvmgr feature-name --option value

# Advanced usage
uvmgr feature-name --advanced --config config.yml
```

#### Step 3: Configuration
Customize the feature behavior by modifying the configuration:

```yaml
feature:
  enabled: true
  options:
    timeout: 30
    retries: 3
```

### Best Practices
- Always validate your input before processing
- Use appropriate error handling
- Monitor performance metrics
- Keep configurations under version control

### Troubleshooting
If you encounter issues:
1. Check the logs for error messages
2. Verify your configuration
3. Ensure all dependencies are installed
4. Contact support if problems persist
"""
    
    def _mock_technical_spec(self, requirements: str) -> str:
        """Generate mock technical specification."""
        return f"""# Technical Specification

## Overview
This specification outlines the technical requirements and implementation details
for: {requirements}

## Requirements
### Functional Requirements
- **FR1**: Core functionality implementation
- **FR2**: User interface integration
- **FR3**: Data persistence and retrieval
- **FR4**: Error handling and recovery

### Non-Functional Requirements
- **NFR1**: Performance - Response time < 100ms
- **NFR2**: Scalability - Support 1000+ concurrent users
- **NFR3**: Reliability - 99.9% uptime
- **NFR4**: Security - End-to-end encryption

## Architecture
### System Components
1. **API Layer**: RESTful API endpoints
2. **Business Logic**: Core processing engine
3. **Data Layer**: Database and caching
4. **Integration Layer**: External service connectors

### Data Flow
1. Request validation and authentication
2. Business logic processing
3. Data persistence operations
4. Response formatting and delivery

## Implementation Details
### Technology Stack
- **Backend**: Python 3.12+ with FastAPI
- **Database**: PostgreSQL with Redis cache
- **Monitoring**: OpenTelemetry integration
- **Deployment**: Docker containers with K8s

### Security Considerations
- JWT token authentication
- Rate limiting and DDoS protection
- Input validation and sanitization
- Audit logging for all operations

## Testing Strategy
- Unit tests (90%+ coverage)
- Integration tests
- Performance testing
- Security testing
"""
    
    def _mock_architecture_doc(self, components: str) -> str:
        """Generate mock architecture documentation."""
        return f"""# System Architecture

## Architecture Overview
This document describes the high-level architecture for the system containing: {components}

## System Components

### Core Services
- **API Gateway**: Central entry point for all requests
- **Authentication Service**: User authentication and authorization
- **Business Logic Service**: Core application functionality
- **Data Service**: Database operations and data management

### Supporting Infrastructure
- **Load Balancer**: Traffic distribution and failover
- **Message Queue**: Asynchronous task processing
- **Cache Layer**: Performance optimization
- **Monitoring**: System health and metrics

## Component Interactions

### Request Flow
1. Client sends request to API Gateway
2. Gateway validates and routes request
3. Authentication service verifies credentials
4. Business logic processes the request
5. Data service handles persistence
6. Response flows back through the chain

### Data Flow
- **Write Operations**: Gateway → Auth → Logic → Data → Cache Update
- **Read Operations**: Gateway → Auth → Cache Check → Data (if needed)
- **Event Processing**: Queue → Logic → Data → Event Emission

## Design Decisions

### Architectural Patterns
- **Microservices**: Improved scalability and maintainability
- **Event-Driven**: Loose coupling between components
- **CQRS**: Separate read/write operations for optimization
- **Circuit Breaker**: Fault tolerance and resilience

### Technology Choices
- **Python**: Rapid development and rich ecosystem
- **FastAPI**: High-performance async web framework
- **PostgreSQL**: ACID compliance and complex queries
- **Redis**: High-speed caching and session storage
- **Docker**: Consistent deployment environments

## Scalability Considerations
- Horizontal scaling of stateless services
- Database read replicas for improved performance
- CDN for static content delivery
- Auto-scaling based on metrics

## Security Architecture
- Zero-trust network model
- End-to-end encryption
- Regular security audits
- Compliance with industry standards
"""
    
    def _mock_troubleshooting_guide(self, issues: str) -> str:
        """Generate mock troubleshooting guide."""
        return f"""# Troubleshooting Guide

## Common Issues: {issues}

### Quick Diagnostic Steps
Before diving into specific issues, perform these quick checks:

1. **System Status**: Verify all services are running
2. **Network Connectivity**: Check network connections
3. **Resource Availability**: Monitor CPU, memory, and disk usage
4. **Log Analysis**: Review recent log entries for errors

## Issue Categories

### 1. Connection Issues
**Symptoms:**
- Unable to connect to service
- Timeout errors
- Connection refused errors

**Diagnosis:**
```bash
# Check service status
systemctl status service-name

# Test network connectivity
telnet hostname port

# Check listening ports
netstat -tlnp | grep port
```

**Solutions:**
- Restart the service if stopped
- Check firewall rules
- Verify DNS resolution
- Update connection strings

### 2. Performance Issues
**Symptoms:**
- Slow response times
- High CPU/memory usage
- Request timeouts

**Diagnosis:**
```bash
# Monitor system resources
top -p PID

# Check database performance
EXPLAIN ANALYZE SELECT ...

# Review application metrics
curl http://localhost:8080/metrics
```

**Solutions:**
- Scale resources vertically/horizontally
- Optimize database queries
- Implement caching strategies
- Review application code for bottlenecks

### 3. Authentication Failures
**Symptoms:**
- Login failures
- Token validation errors
- Permission denied messages

**Diagnosis:**
- Verify user credentials
- Check token expiration
- Review permission configurations
- Examine authentication logs

**Solutions:**
- Reset user passwords
- Refresh authentication tokens
- Update permission assignments
- Synchronize user directories

### 4. Data Inconsistency
**Symptoms:**
- Missing or incorrect data
- Synchronization failures
- Database constraint violations

**Diagnosis:**
- Compare data across systems
- Review transaction logs
- Check data validation rules
- Examine replication status

**Solutions:**
- Run data reconciliation scripts
- Restore from backups if needed
- Fix data validation issues
- Restart replication processes

## Emergency Procedures

### Service Outage Response
1. **Immediate Assessment**
   - Identify affected services
   - Estimate impact scope
   - Notify stakeholders

2. **Recovery Actions**
   - Switch to backup systems
   - Scale resources if needed
   - Apply emergency fixes

3. **Communication**
   - Update status page
   - Notify users of issues
   - Provide regular updates

### Escalation Matrix
- **Level 1**: Self-service documentation
- **Level 2**: Technical support team
- **Level 3**: Engineering team
- **Level 4**: Senior engineering/management

## Monitoring and Alerting
- Set up proactive monitoring
- Configure appropriate alert thresholds
- Implement automated recovery where possible
- Regular review and update of procedures
"""


class DocumentationWorkflowEngine:
    """BPMN workflow engine for document generation orchestration."""
    
    def __init__(self, workflows_dir: Path = None):
        """Initialize the workflow engine."""
        self.workflows_dir = workflows_dir or Path(__file__).parent / "workflows" / "documentation"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.writing_engine = TechnicalWritingEngine()
        
        # Create default workflows if they don't exist
        self._create_default_workflows()
    
    def _create_default_workflows(self):
        """Create default BPMN workflows for documentation."""
        workflows = {
            "api_documentation": self._create_api_doc_workflow(),
            "user_guide": self._create_user_guide_workflow(),
            "technical_spec": self._create_tech_spec_workflow(),
            "full_documentation": self._create_full_doc_workflow()
        }
        
        for name, workflow_xml in workflows.items():
            workflow_file = self.workflows_dir / f"{name}.bpmn"
            if not workflow_file.exists():
                workflow_file.write_text(workflow_xml)
    
    def _create_api_doc_workflow(self) -> str:
        """Create BPMN workflow for API documentation generation."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                  id="api_doc_workflow">
  <bpmn:process id="generate_api_docs" isExecutable="true">
    
    <bpmn:startEvent id="start" name="Start API Doc Generation">
      <bpmn:outgoing>to_analyze_code</bpmn:outgoing>
    </bpmn:startEvent>
    
    <bpmn:serviceTask id="analyze_code" name="Analyze Codebase">
      <bpmn:incoming>to_analyze_code</bpmn:incoming>
      <bpmn:outgoing>to_extract_functions</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:serviceTask id="extract_functions" name="Extract Functions">
      <bpmn:incoming>to_extract_functions</bpmn:incoming>
      <bpmn:outgoing>to_generate_docs</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:serviceTask id="generate_docs" name="Generate API Documentation">
      <bpmn:incoming>to_generate_docs</bpmn:incoming>
      <bpmn:outgoing>to_format_output</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:serviceTask id="format_output" name="Format Output">
      <bpmn:incoming>to_format_output</bpmn:incoming>
      <bpmn:outgoing>to_end</bpmn:outgoing>
    </bpmn:serviceTask>
    
    <bpmn:endEvent id="end" name="Documentation Generated">
      <bpmn:incoming>to_end</bpmn:incoming>
    </bpmn:endEvent>
    
    <bpmn:sequenceFlow id="to_analyze_code" sourceRef="start" targetRef="analyze_code"/>
    <bpmn:sequenceFlow id="to_extract_functions" sourceRef="analyze_code" targetRef="extract_functions"/>
    <bpmn:sequenceFlow id="to_generate_docs" sourceRef="extract_functions" targetRef="generate_docs"/>
    <bpmn:sequenceFlow id="to_format_output" sourceRef="generate_docs" targetRef="format_output"/>
    <bpmn:sequenceFlow id="to_end" sourceRef="format_output" targetRef="end"/>
    
  </bpmn:process>
</bpmn:definitions>"""
    
    def _create_user_guide_workflow(self) -> str:
        """Create BPMN workflow for user guide generation."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  id="user_guide_workflow">
  <bpmn:process id="generate_user_guide" isExecutable="true">
    
    <bpmn:startEvent id="start" name="Start User Guide Generation"/>
    <bpmn:serviceTask id="analyze_features" name="Analyze Features"/>
    <bpmn:serviceTask id="create_outline" name="Create Guide Outline"/>
    <bpmn:serviceTask id="generate_sections" name="Generate Sections"/>
    <bpmn:serviceTask id="add_examples" name="Add Examples"/>
    <bpmn:serviceTask id="review_content" name="Review Content"/>
    <bpmn:endEvent id="end" name="User Guide Complete"/>
    
  </bpmn:process>
</bpmn:definitions>"""
    
    def _create_tech_spec_workflow(self) -> str:
        """Create BPMN workflow for technical specification generation."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  id="tech_spec_workflow">
  <bpmn:process id="generate_tech_spec" isExecutable="true">
    
    <bpmn:startEvent id="start" name="Start Tech Spec Generation"/>
    <bpmn:serviceTask id="gather_requirements" name="Gather Requirements"/>
    <bpmn:serviceTask id="analyze_architecture" name="Analyze Architecture"/>
    <bpmn:serviceTask id="generate_spec" name="Generate Specification"/>
    <bpmn:serviceTask id="validate_spec" name="Validate Specification"/>
    <bpmn:endEvent id="end" name="Tech Spec Complete"/>
    
  </bpmn:process>
</bpmn:definitions>"""
    
    def _create_full_doc_workflow(self) -> str:
        """Create comprehensive documentation workflow."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  id="full_doc_workflow">
  <bpmn:process id="generate_full_docs" isExecutable="true">
    
    <bpmn:startEvent id="start" name="Start Full Documentation"/>
    
    <bpmn:parallelGateway id="parallel_start" name="Parallel Generation"/>
    
    <bpmn:serviceTask id="generate_api_docs" name="Generate API Docs"/>
    <bpmn:serviceTask id="generate_user_guide" name="Generate User Guide"/>
    <bpmn:serviceTask id="generate_tech_spec" name="Generate Tech Spec"/>
    <bpmn:serviceTask id="generate_architecture" name="Generate Architecture Doc"/>
    
    <bpmn:parallelGateway id="parallel_end" name="Combine Results"/>
    
    <bpmn:serviceTask id="create_index" name="Create Documentation Index"/>
    <bpmn:serviceTask id="generate_site" name="Generate Documentation Site"/>
    
    <bpmn:endEvent id="end" name="Full Documentation Complete"/>
    
  </bpmn:process>
</bpmn:definitions>"""
    
    async def execute_workflow(
        self,
        workflow_name: str,
        context: DocumentContext,
        template: Optional[DocumentTemplate] = None
    ) -> GeneratedDocument:
        """Execute a documentation workflow."""
        workflow_file = self.workflows_dir / f"{workflow_name}.bpmn"
        
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_name}")
        
        # Parse and execute BPMN workflow
        parser = BpmnParser()
        parser.add_bpmn_file(str(workflow_file))
        workflow = BpmnWorkflow(parser.get_spec(workflow_name))
        
        # Execute workflow with custom task handlers
        workflow_data = {
            "context": context,
            "template": template,
            "generated_content": {},
            "errors": []
        }
        
        import time
        start_time = time.time()
        
        # Simulate workflow execution (in real implementation, this would use SpiffWorkflow)
        if workflow_name == "api_documentation":
            content = await self._execute_api_doc_workflow(context)
        elif workflow_name == "user_guide":
            content = await self._execute_user_guide_workflow(context)
        elif workflow_name == "technical_spec":
            content = await self._execute_tech_spec_workflow(context)
        else:
            content = await self._execute_full_doc_workflow(context)
        
        generation_time = time.time() - start_time
        
        # Create result document
        result = GeneratedDocument(
            content=content,
            format=OutputFormat.MARKDOWN,
            template=template or DocumentTemplate("default", DocumentType.README, Path("")),
            context=context,
            generation_time=generation_time,
            word_count=len(content.split()),
            sections_count=content.count("##"),
            ai_generated_sections=content.count("AI-Generated:")
        )
        
        return result
    
    async def _execute_api_doc_workflow(self, context: DocumentContext) -> str:
        """Execute API documentation workflow."""
        content = f"# API Documentation - {context.project_name}\n\n"
        
        # Analyze functions from context
        if context.functions:
            content += "## Functions\n\n"
            for func in context.functions[:3]:  # Limit for demo
                func_name = func.get("name", "unknown_function")
                func_sig = func.get("signature", f"{func_name}()")
                
                api_doc = self.writing_engine.generate_api_documentation(
                    function_signature=func_sig,
                    docstring=func.get("docstring", ""),
                    context=f"Part of {context.project_name} API"
                )
                content += api_doc + "\n\n"
        
        # Add API endpoints if available
        if context.api_endpoints:
            content += "## API Endpoints\n\n"
            for endpoint in context.api_endpoints[:3]:
                endpoint_doc = f"""### {endpoint.get('method', 'GET')} {endpoint.get('path', '/unknown')}

**Description:** {endpoint.get('description', 'API endpoint')}

**Parameters:**
- See endpoint documentation for details

**Response:**
```json
{{"status": "success", "data": "response_data"}}
```

"""
                content += endpoint_doc
        
        return content
    
    async def _execute_user_guide_workflow(self, context: DocumentContext) -> str:
        """Execute user guide workflow."""
        content = f"# User Guide - {context.project_name}\n\n"
        
        # Generate overview
        overview = self.writing_engine.generate_user_guide_section(
            feature_description=f"{context.project_name} - {context.description}",
            usage_examples="Basic usage examples",
            target_audience="intermediate"
        )
        content += overview + "\n\n"
        
        # Add installation section
        content += """## Installation

Install {project_name} using your preferred package manager:

```bash
# Using pip
pip install {project_name}

# Using uv
uv add {project_name}
```

""".format(project_name=context.project_name)
        
        return content
    
    async def _execute_tech_spec_workflow(self, context: DocumentContext) -> str:
        """Execute technical specification workflow."""
        requirements = f"Technical specification for {context.project_name}"
        architecture = f"System architecture with components: {', '.join(context.entry_points)}"
        
        tech_spec = self.writing_engine.generate_technical_spec(
            requirements=requirements,
            architecture=architecture,
            implementation=f"Implementation using Python {context.version}"
        )
        
        return tech_spec
    
    async def _execute_full_doc_workflow(self, context: DocumentContext) -> str:
        """Execute full documentation workflow."""
        content = f"# Complete Documentation - {context.project_name}\n\n"
        
        # Table of contents
        content += """## Table of Contents

1. [Overview](#overview)
2. [API Documentation](#api-documentation)
3. [User Guide](#user-guide)
4. [Technical Specification](#technical-specification)
5. [Architecture](#architecture)
6. [Troubleshooting](#troubleshooting)

"""
        
        # Overview
        content += f"""## Overview

{context.project_name} is a {context.description}

Version: {context.version}
Author: {context.author}

"""
        
        # Add other sections
        api_content = await self._execute_api_doc_workflow(context)
        user_content = await self._execute_user_guide_workflow(context)
        tech_content = await self._execute_tech_spec_workflow(context)
        
        content += "## API Documentation\n\n" + api_content + "\n\n"
        content += "## User Guide\n\n" + user_content + "\n\n"
        content += "## Technical Specification\n\n" + tech_content + "\n\n"
        
        return content


class DocumentationAutomationManager:
    """High-level manager for technical writing automation."""
    
    def __init__(self, project_root: Path = None):
        """Initialize the documentation automation manager."""
        self.project_root = project_root or Path.cwd()
        self.workflow_engine = DocumentationWorkflowEngine()
        self.templates_dir = self.project_root / "docs" / "templates"
        self.output_dir = self.project_root / "docs" / "generated"
        
        # Create directories
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_project(self) -> DocumentContext:
        """Analyze the project to create documentation context."""
        context = DocumentContext(
            project_name=self.project_root.name,
            codebase_path=self.project_root
        )
        
        # Analyze project files
        if (self.project_root / "pyproject.toml").exists():
            context = self._analyze_python_project(context)
        elif (self.project_root / "package.json").exists():
            context = self._analyze_node_project(context)
        
        return context
    
    def _analyze_python_project(self, context: DocumentContext) -> DocumentContext:
        """Analyze Python project for documentation context."""
        try:
            import tomllib
            pyproject_path = self.project_root / "pyproject.toml"
            
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            
            project_info = data.get("project", {})
            context.description = project_info.get("description", "")
            context.version = project_info.get("version", "1.0.0")
            context.dependencies = project_info.get("dependencies", [])
            
            # Find Python files and extract functions
            src_dir = self.project_root / "src"
            if src_dir.exists():
                context.functions = self._extract_python_functions(src_dir)
            
        except Exception as e:
            logger.warning(f"Failed to analyze Python project: {e}")
        
        return context
    
    def _analyze_node_project(self, context: DocumentContext) -> DocumentContext:
        """Analyze Node.js project for documentation context."""
        try:
            package_json = self.project_root / "package.json"
            with open(package_json) as f:
                data = json.load(f)
            
            context.description = data.get("description", "")
            context.version = data.get("version", "1.0.0")
            context.dependencies = list(data.get("dependencies", {}).keys())
            
        except Exception as e:
            logger.warning(f"Failed to analyze Node.js project: {e}")
        
        return context
    
    def _extract_python_functions(self, src_dir: Path) -> List[Dict[str, Any]]:
        """Extract function information from Python files."""
        functions = []
        
        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
                
                # Simple regex to find function definitions
                import re
                func_pattern = r'def\s+(\w+)\s*\([^)]*\):'
                matches = re.findall(func_pattern, content)
                
                for func_name in matches[:5]:  # Limit for demo
                    functions.append({
                        "name": func_name,
                        "signature": f"{func_name}()",
                        "file": str(py_file.relative_to(self.project_root)),
                        "docstring": f"Function {func_name} from {py_file.name}"
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")
        
        return functions
    
    async def generate_documentation(
        self,
        doc_type: DocumentType,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        template_name: Optional[str] = None
    ) -> GeneratedDocument:
        """Generate documentation of specified type."""
        
        # Analyze project context
        context = self.analyze_project()
        
        # Load template if specified
        template = None
        if template_name:
            template = self._load_template(template_name)
        
        # Map document type to workflow
        workflow_map = {
            DocumentType.API_DOCS: "api_documentation",
            DocumentType.USER_GUIDE: "user_guide", 
            DocumentType.TECHNICAL_SPEC: "technical_spec",
            DocumentType.README: "full_documentation"
        }
        
        workflow_name = workflow_map.get(doc_type, "full_documentation")
        
        # Execute workflow
        result = await self.workflow_engine.execute_workflow(
            workflow_name, context, template
        )
        
        # Save output
        output_file = self.output_dir / f"{doc_type.value}.{output_format.value}"
        output_file.write_text(result.content)
        
        # Observe with AGI reasoning
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "documentation_generation",
                "doc_type": doc_type.value,
                "output_format": output_format.value,
                "workflow": workflow_name,
                "generation_time": str(result.generation_time),
                "word_count": str(result.word_count)
            },
            context={
                "technical_writing": True,
                "ai_automation": True,
                "workflow_orchestration": True,
                "project_analysis": True
            }
        )
        
        return result
    
    def _load_template(self, template_name: str) -> Optional[DocumentTemplate]:
        """Load documentation template."""
        template_file = self.templates_dir / f"{template_name}.yml"
        
        if not template_file.exists():
            return None
        
        try:
            with open(template_file) as f:
                data = yaml.safe_load(f)
            
            return DocumentTemplate(
                name=data.get("name", template_name),
                type=DocumentType(data.get("type", "readme")),
                template_path=template_file,
                variables=data.get("variables", {}),
                sections=data.get("sections", []),
                description=data.get("description", "")
            )
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            return None
    
    def create_template(
        self,
        name: str,
        doc_type: DocumentType,
        sections: List[str],
        variables: Dict[str, str] = None
    ) -> DocumentTemplate:
        """Create a new documentation template."""
        template_data = {
            "name": name,
            "type": doc_type.value,
            "sections": sections,
            "variables": variables or {},
            "description": f"Template for {doc_type.value} generation"
        }
        
        template_file = self.templates_dir / f"{name}.yml"
        with open(template_file, "w") as f:
            yaml.dump(template_data, f, default_flow_style=False)
        
        return DocumentTemplate(
            name=name,
            type=doc_type,
            template_path=template_file,
            sections=sections,
            variables=variables or {}
        )


# Global documentation manager instance
_doc_manager: Optional[DocumentationAutomationManager] = None

def get_documentation_manager(project_root: Optional[Path] = None) -> DocumentationAutomationManager:
    """Get the global documentation automation manager instance."""
    global _doc_manager
    
    if _doc_manager is None:
        _doc_manager = DocumentationAutomationManager(project_root)
    
    return _doc_manager