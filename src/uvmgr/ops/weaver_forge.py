"""
uvmgr.ops.weaver_forge - Weaver Forge Operations
===============================================

Weaver Forge operations for template-based code generation with Hygen-like
capabilities and DSPy-powered intelligent generation.

This module provides the core operations for Weaver Forge, including:
- Template management and creation
- Code generation from templates
- Project scaffolding
- Interactive prompt-based generation
- Template validation using Lean Six Sigma principles
- DSPy integration for intelligent decision making

Key Features
-----------
• **Template Engine**: Hygen-like template processing with EJS syntax
• **DSPy Integration**: Intelligent template selection and customization
• **Lean Six Sigma**: Systematic template validation and improvement
• **OpenTelemetry**: Comprehensive instrumentation and monitoring
• **Interactive Generation**: Guided template creation and customization
• **Project Scaffolding**: Complete project structure generation

Template Structure
-----------------
Templates follow Hygen-like structure:
```
templates/
├── component/
│   ├── _templates/
│   │   ├── component.ejs.t
│   │   └── component.test.ejs.t
│   └── index.js
├── api/
│   ├── _templates/
│   │   ├── endpoint.ejs.t
│   │   └── service.ejs.t
│   └── index.js
└── ...
```

See Also
--------
- :mod:`uvmgr.commands.weaver_forge` : Weaver Forge CLI commands
- :mod:`uvmgr.core.agi_reasoning` : AGI reasoning capabilities
- :mod:`uvmgr.core.instrumentation` : Instrumentation utilities
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import yaml
from jinja2 import Environment, FileSystemLoader, Template
from rich.console import Console

from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import span, metric_counter, metric_histogram, record_exception
from uvmgr.core.agi_reasoning import dspy_reasoning_chain
from uvmgr.core.lean_six_sigma import validate_template_quality

console = Console()


@dataclass
class TemplateInfo:
    """Template information."""
    name: str
    type: str
    description: str
    path: Path
    parameters: Dict[str, Any]
    usage_count: int = 0
    last_used: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class GenerationResult:
    """Code generation result."""
    template_used: str
    files: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    duration: float
    success: bool
    errors: List[str] = None


@dataclass
class ValidationIssue:
    """Template validation issue."""
    template: str
    severity: str
    description: str
    line_number: Optional[int] = None
    fix_suggestion: Optional[str] = None


class WeaverForgeError(Exception):
    """Weaver Forge specific error."""
    pass


class TemplateNotFoundError(WeaverForgeError):
    """Template not found error."""
    pass


class TemplateValidationError(WeaverForgeError):
    """Template validation error."""
    pass


def init_weaver_forge(
    project_path: Optional[Path] = None,
    template_source: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Initialize Weaver Forge in project.
    
    Args:
        project_path: Project path for initialization
        template_source: Template source repository
        force: Force reinitialization
        
    Returns:
        Initialization result with project path and created templates
    """
    with span("weaver_forge.init", attributes={
        "project_path": str(project_path) if project_path else None,
        "template_source": template_source,
        "force": force
    }) as current_span:
        
        start_time = time.time()
        
        # Determine project path
        if project_path is None:
            project_path = Path.cwd()
        
        # Create Weaver Forge directory structure
        weaver_forge_path = project_path / ".weaver-forge"
        templates_path = weaver_forge_path / "templates"
        scaffolds_path = weaver_forge_path / "scaffolds"
        config_path = weaver_forge_path / "config.yaml"
        
        # Check if already initialized
        if weaver_forge_path.exists() and not force:
            raise WeaverForgeError("Weaver Forge already initialized. Use --force to reinitialize.")
        
        # Create directory structure
        templates_path.mkdir(parents=True, exist_ok=True)
        scaffolds_path.mkdir(parents=True, exist_ok=True)
        
        # Create default configuration
        config = {
            "version": "1.0.0",
            "templates_path": str(templates_path),
            "scaffolds_path": str(scaffolds_path),
            "default_parameters": {},
            "ai_enabled": True,
            "validation_enabled": True,
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Create default templates
        default_templates = _create_default_templates(templates_path)
        
        # Create default scaffolds
        default_scaffolds = _create_default_scaffolds(scaffolds_path)
        
        # Load templates from source if provided
        if template_source:
            _load_templates_from_source(templates_path, template_source)
        
        duration = time.time() - start_time
        
        add_span_event("weaver_forge.initialized", {
            "project_path": str(project_path),
            "templates_created": len(default_templates),
            "scaffolds_created": len(default_scaffolds),
        })
        
        return {
            "project_path": project_path,
            "templates_created": len(default_templates),
            "scaffolds_created": len(default_scaffolds),
            "templates": default_templates,
            "scaffolds": default_scaffolds,
            "duration": duration,
            "config_path": str(config_path),
        }


def generate_from_template(
    template_name: str,
    name: str,
    output_path: Optional[Path] = None,
    parameters: Optional[Dict[str, Any]] = None,
    interactive: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generate code from template.
    
    Args:
        template_name: Name of template to use
        name: Name for the generated item
        output_path: Output path for generated files
        parameters: Template parameters
        interactive: Interactive parameter input
        dry_run: Show what would be generated without creating files
        
    Returns:
        Generation result with files and metadata
    """
    with span("weaver_forge.generate", attributes={
        "template_name": template_name,
        "name": name,
        "interactive": interactive,
        "dry_run": dry_run
    }) as current_span:
        
        start_time = time.time()
        
        # Get template info
        template_info = _get_template_info(template_name)
        if not template_info:
            raise TemplateNotFoundError(f"Template '{template_name}' not found")
        
        # Merge parameters
        if parameters is None:
            parameters = {}
        
        # Add default parameters
        default_params = template_info.parameters.copy()
        default_params.update(parameters)
        parameters = default_params
        
        # Add common parameters
        parameters.update({
            "name": name,
            "Name": name.title(),
            "NAME": name.upper(),
            "name_lower": name.lower(),
            "name_kebab": name.replace("_", "-").replace(" ", "-").lower(),
            "name_snake": name.replace(" ", "_").lower(),
            "name_camel": "".join(word.title() for word in name.split()),
        })
        
        # Interactive parameter input
        if interactive:
            parameters = _interactive_parameter_input(parameters, template_info)
        
        # Use DSPy for intelligent parameter enhancement
        if _is_ai_enabled():
            enhanced_params = _enhance_parameters_with_dspy(template_name, name, parameters)
            parameters.update(enhanced_params)
        
        # Determine output path
        if output_path is None:
            output_path = Path.cwd()
        
        # Generate files
        generated_files = []
        errors = []
        
        try:
            template_files = _get_template_files(template_info.path)
            
            for template_file in template_files:
                try:
                    file_result = _generate_file_from_template(
                        template_file,
                        parameters,
                        output_path,
                        dry_run
                    )
                    if file_result:
                        generated_files.append(file_result)
                except Exception as e:
                    error_msg = f"Error generating {template_file}: {e}"
                    errors.append(error_msg)
                    record_exception(e)
            
            # Update template usage statistics
            _update_template_usage(template_name)
            
        except Exception as e:
            record_exception(e)
            errors.append(f"Generation failed: {e}")
        
        duration = time.time() - start_time
        
        add_span_event("weaver_forge.generated", {
            "template": template_name,
            "name": name,
            "files_created": len(generated_files),
            "errors": len(errors),
        })
        
        return {
            "template_used": template_name,
            "files": generated_files,
            "parameters": parameters,
            "duration": duration,
            "success": len(errors) == 0,
            "errors": errors,
        }


def create_template(
    template_name: str,
    template_type: str,
    description: Optional[str] = None,
    interactive: bool = True,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Create new template.
    
    Args:
        template_name: Name of the template
        template_type: Type of template
        description: Template description
        interactive: Interactive template creation
        output_dir: Output directory for template
        
    Returns:
        Template creation result
    """
    with span("weaver_forge.create_template", attributes={
        "template_name": template_name,
        "template_type": template_type,
        "interactive": interactive
    }) as current_span:
        
        start_time = time.time()
        
        # Determine output directory
        if output_dir is None:
            weaver_forge_path = _find_weaver_forge_path()
            output_dir = weaver_forge_path / "templates" / template_name
        
        # Create template directory
        template_path = output_dir
        templates_dir = template_path / "_templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Get template structure based on type
        template_structure = _get_template_structure(template_type)
        
        # Interactive template creation
        if interactive:
            template_structure = _interactive_template_creation(template_name, template_structure)
        
        # Use DSPy for intelligent template enhancement
        if _is_ai_enabled():
            enhanced_structure = _enhance_template_with_dspy(template_name, template_type, template_structure)
            template_structure.update(enhanced_structure)
        
        # Create template files
        created_files = []
        for file_path, content in template_structure.items():
            full_path = templates_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            created_files.append({
                "path": str(full_path),
                "size": len(content),
                "type": "template"
            })
        
        # Create template index
        index_content = _create_template_index(template_name, template_type, description)
        index_path = template_path / "index.js"
        with open(index_path, 'w') as f:
            f.write(index_content)
        
        created_files.append({
            "path": str(index_path),
            "size": len(index_content),
            "type": "index"
        })
        
        duration = time.time() - start_time
        
        add_span_event("weaver_forge.template_created", {
            "template_name": template_name,
            "template_type": template_type,
            "files_created": len(created_files),
        })
        
        return {
            "name": template_name,
            "type": template_type,
            "description": description,
            "output_path": template_path,
            "files": created_files,
            "duration": duration,
        }


def list_templates(
    template_type: Optional[str] = None,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    List available templates.
    
    Args:
        template_type: Filter by template type
        detailed: Show detailed template information
        
    Returns:
        Templates list with metadata
    """
    with span("weaver_forge.list_templates", attributes={
        "template_type": template_type,
        "detailed": detailed
    }) as current_span:
        
        weaver_forge_path = _find_weaver_forge_path()
        templates_path = weaver_forge_path / "templates"
        
        if not templates_path.exists():
            return {"templates": []}
        
        templates = []
        
        for template_dir in templates_path.iterdir():
            if not template_dir.is_dir():
                continue
            
            template_name = template_dir.name
            
            # Filter by type if specified
            if template_type and not _template_matches_type(template_dir, template_type):
                continue
            
            template_info = _get_template_info_from_path(template_dir)
            if template_info:
                templates.append(template_info.__dict__)
        
        # Sort by usage count
        templates.sort(key=lambda x: x.get("usage_count", 0), reverse=True)
        
        add_span_event("weaver_forge.templates_listed", {
            "templates_count": len(templates),
            "template_type": template_type or "all",
        })
        
        return {
            "templates": templates,
            "total_count": len(templates),
            "filtered_by_type": template_type is not None,
        }


def validate_templates(
    template_name: Optional[str] = None,
    fix_issues: bool = False
) -> Dict[str, Any]:
    """
    Validate templates using Lean Six Sigma principles.
    
    Args:
        template_name: Specific template to validate
        fix_issues: Automatically fix validation issues
        
    Returns:
        Validation results with issues and fixes
    """
    with span("weaver_forge.validate_templates", attributes={
        "template_name": template_name,
        "fix_issues": fix_issues
    }) as current_span:
        
        start_time = time.time()
        
        weaver_forge_path = _find_weaver_forge_path()
        templates_path = weaver_forge_path / "templates"
        
        if not templates_path.exists():
            return {
                "templates_validated": 0,
                "valid_templates": 0,
                "issues": [],
                "fixes_applied": [],
                "duration": 0,
            }
        
        issues = []
        fixes_applied = []
        templates_validated = 0
        valid_templates = 0
        
        # Get templates to validate
        if template_name:
            template_dirs = [templates_path / template_name]
        else:
            template_dirs = [d for d in templates_path.iterdir() if d.is_dir()]
        
        for template_dir in template_dirs:
            if not template_dir.exists():
                continue
            
            templates_validated += 1
            
            # Validate template
            template_issues = _validate_single_template(template_dir)
            
            if template_issues:
                issues.extend(template_issues)
                
                # Apply fixes if requested
                if fix_issues:
                    template_fixes = _apply_template_fixes(template_dir, template_issues)
                    fixes_applied.extend(template_fixes)
            else:
                valid_templates += 1
        
        duration = time.time() - start_time
        
        add_span_event("weaver_forge.templates_validated", {
            "templates_validated": templates_validated,
            "valid_templates": valid_templates,
            "issues_found": len(issues),
            "fixes_applied": len(fixes_applied),
        })
        
        return {
            "templates_validated": templates_validated,
            "valid_templates": valid_templates,
            "issues": issues,
            "fixes_applied": fixes_applied,
            "duration": duration,
        }


def create_scaffold(
    scaffold_type: str,
    project_name: str,
    output_path: Optional[Path] = None,
    parameters: Optional[Dict[str, Any]] = None,
    interactive: bool = True
) -> Dict[str, Any]:
    """
    Create project scaffold.
    
    Args:
        scaffold_type: Type of scaffold to create
        project_name: Name of the project
        output_path: Output path for scaffold
        parameters: Scaffold parameters
        interactive: Interactive scaffold creation
        
    Returns:
        Scaffold creation result
    """
    with span("weaver_forge.create_scaffold", attributes={
        "scaffold_type": scaffold_type,
        "project_name": project_name,
        "interactive": interactive
    }) as current_span:
        
        start_time = time.time()
        
        # Determine output path
        if output_path is None:
            output_path = Path.cwd() / project_name
        
        # Get scaffold template
        scaffold_template = _get_scaffold_template(scaffold_type)
        if not scaffold_template:
            raise WeaverForgeError(f"Scaffold type '{scaffold_type}' not found")
        
        # Merge parameters
        if parameters is None:
            parameters = {}
        
        # Add common parameters
        parameters.update({
            "project_name": project_name,
            "ProjectName": project_name.title(),
            "PROJECT_NAME": project_name.upper(),
            "project_name_lower": project_name.lower(),
            "project_name_kebab": project_name.replace("_", "-").replace(" ", "-").lower(),
            "project_name_snake": project_name.replace(" ", "_").lower(),
        })
        
        # Interactive parameter input
        if interactive:
            parameters = _interactive_scaffold_parameters(parameters, scaffold_template)
        
        # Use DSPy for intelligent scaffold enhancement
        if _is_ai_enabled():
            enhanced_params = _enhance_scaffold_with_dspy(scaffold_type, project_name, parameters)
            parameters.update(enhanced_params)
        
        # Create scaffold
        created_files = []
        
        try:
            for file_info in scaffold_template["files"]:
                file_result = _create_scaffold_file(
                    file_info,
                    parameters,
                    output_path
                )
                if file_result:
                    created_files.append(file_result)
        except Exception as e:
            record_exception(e)
            raise WeaverForgeError(f"Scaffold creation failed: {e}")
        
        duration = time.time() - start_time
        
        add_span_event("weaver_forge.scaffold_created", {
            "scaffold_type": scaffold_type,
            "project_name": project_name,
            "files_created": len(created_files),
        })
        
        return {
            "scaffold_type": scaffold_type,
            "project_name": project_name,
            "output_path": output_path,
            "files": created_files,
            "parameters": parameters,
            "duration": duration,
        }


def interactive_prompt_generation(
    description: str,
    output_path: Optional[Path] = None,
    template_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Interactive prompt-based generation.
    
    Args:
        description: Description of what to generate
        output_path: Output path for generated files
        template_hint: Hint for template type
        output_path: Output path for generated files
        
    Returns:
        Generation result with files and AI insights
    """
    with span("weaver_forge.interactive_prompt", attributes={
        "description": description,
        "template_hint": template_hint
    }) as current_span:
        
        start_time = time.time()
        
        # Use DSPy for intelligent analysis
        if _is_ai_enabled():
            analysis_result = _analyze_generation_request_with_dspy(description, template_hint)
            
            template_name = analysis_result.get("template_name")
            parameters = analysis_result.get("parameters", {})
            ai_insights = analysis_result.get("insights", [])
        else:
            # Fallback to basic analysis
            template_name = _basic_template_selection(description, template_hint)
            parameters = _basic_parameter_extraction(description)
            ai_insights = []
        
        # Generate code
        generation_result = generate_from_template(
            template_name=template_name,
            name=parameters.get("name", "Generated"),
            output_path=output_path,
            parameters=parameters,
            interactive=False,
            dry_run=False
        )
        
        duration = time.time() - start_time
        
        add_span_event("weaver_forge.prompt_generated", {
            "description": description,
            "template_used": template_name,
            "ai_analysis": _is_ai_enabled(),
        })
        
        return {
            "template_used": template_name,
            "files": generation_result.get("files", []),
            "parameters": generation_result.get("parameters", {}),
            "ai_insights": ai_insights,
            "duration": duration,
        }


def get_weaver_forge_status(
    detailed: bool = False,
    include_metrics: bool = True
) -> Dict[str, Any]:
    """
    Get Weaver Forge status and metrics.
    
    Args:
        detailed: Show detailed status information
        include_metrics: Include performance metrics
        
    Returns:
        Status information with metrics
    """
    with span("weaver_forge.get_status", attributes={
        "detailed": detailed,
        "include_metrics": include_metrics
    }) as current_span:
        
        weaver_forge_path = _find_weaver_forge_path()
        
        # Basic status
        status = {
            "initialized": weaver_forge_path.exists(),
            "templates_count": 0,
            "scaffolds_count": 0,
            "last_generation": "Never",
        }
        
        if weaver_forge_path.exists():
            templates_path = weaver_forge_path / "templates"
            scaffolds_path = weaver_forge_path / "scaffolds"
            
            if templates_path.exists():
                status["templates_count"] = len([d for d in templates_path.iterdir() if d.is_dir()])
            
            if scaffolds_path.exists():
                status["scaffolds_count"] = len([d for d in scaffolds_path.iterdir() if d.is_dir()])
        
        # Detailed information
        if detailed:
            status["templates"] = _get_detailed_template_stats()
        
        # Metrics
        if include_metrics:
            status["metrics"] = _get_weaver_forge_metrics()
        
        add_span_event("weaver_forge.status.retrieved", {
            "initialized": status["initialized"],
            "templates_count": status["templates_count"],
        })
        
        return status


# Helper functions

def _create_default_templates(templates_path: Path) -> List[str]:
    """Create default templates."""
    default_templates = []
    
    # Component template
    component_template = templates_path / "component"
    component_templates_dir = component_template / "_templates"
    component_templates_dir.mkdir(parents=True, exist_ok=True)
    
    component_content = """import React from 'react';

interface <%= Name %>Props {
  // Add your props here
}

export const <%= Name %>: React.FC<<%= Name %>Props> = ({}) => {
  return (
    <div className="<%= name_kebab %>">
      <h2><%= Name %></h2>
      {/* Add your component content here */}
    </div>
  );
};

export default <%= Name %>;
"""
    
    with open(component_templates_dir / "component.tsx.ejs.t", 'w') as f:
        f.write(component_content)
    
    # Test template
    test_content = """import { render, screen } from '@testing-library/react';
import { <%= Name %> } from './<%= Name %>';

describe('<%= Name %>', () => {
  it('renders correctly', () => {
    render(<<%= Name %> />);
    expect(screen.getByText('<%= Name %>')).toBeInTheDocument();
  });
});
"""
    
    with open(component_templates_dir / "component.test.tsx.ejs.t", 'w') as f:
        f.write(test_content)
    
    # Index file
    index_content = """module.exports = {
  description: 'React component template',
  parameters: {
    name: {
      type: 'string',
      description: 'Component name',
      required: true
    }
  }
};
"""
    
    with open(component_template / "index.js", 'w') as f:
        f.write(index_content)
    
    default_templates.append("component")
    
    # API template
    api_template = templates_path / "api"
    api_templates_dir = api_template / "_templates"
    api_templates_dir.mkdir(parents=True, exist_ok=True)
    
    api_content = """import express from 'express';

const router = express.Router();

// GET /<%= name_kebab %>
router.get('/', async (req, res) => {
  try {
    // Add your logic here
    res.json({ message: '<%= Name %> endpoint' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /<%= name_kebab %>
router.post('/', async (req, res) => {
  try {
    // Add your logic here
    res.status(201).json({ message: '<%= Name %> created' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
"""
    
    with open(api_templates_dir / "endpoint.ts.ejs.t", 'w') as f:
        f.write(api_content)
    
    # API index
    api_index_content = """module.exports = {
  description: 'API endpoint template',
  parameters: {
    name: {
      type: 'string',
      description: 'Endpoint name',
      required: true
    }
  }
};
"""
    
    with open(api_template / "index.js", 'w') as f:
        f.write(api_index_content)
    
    default_templates.append("api")
    
    return default_templates


def _create_default_scaffolds(scaffolds_path: Path) -> List[str]:
    """Create default scaffolds."""
    default_scaffolds = []
    
    # React app scaffold
    react_scaffold = scaffolds_path / "react-app"
    react_scaffold.mkdir(parents=True, exist_ok=True)
    
    react_config = {
        "description": "React application scaffold",
        "files": [
            {
                "path": "package.json",
                "template": """{
  "name": "<%= project_name_kebab %>",
  "version": "1.0.0",
  "description": "<%= project_name %>",
  "main": "index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-scripts": "5.0.1"
  }
}"""
            },
            {
                "path": "src/App.tsx",
                "template": """import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1><%= project_name %></h1>
        <p>Welcome to your new React app!</p>
      </header>
    </div>
  );
}

export default App;
"""
            }
        ]
    }
    
    with open(react_scaffold / "config.json", 'w') as f:
        json.dump(react_config, f, indent=2)
    
    default_scaffolds.append("react-app")
    
    return default_scaffolds


def _load_templates_from_source(templates_path: Path, source: str):
    """Load templates from source repository."""
    # Implementation for loading templates from external source
    pass


def _get_template_info(template_name: str) -> Optional[TemplateInfo]:
    """Get template information."""
    weaver_forge_path = _find_weaver_forge_path()
    template_path = weaver_forge_path / "templates" / template_name
    
    if not template_path.exists():
        return None
    
    return _get_template_info_from_path(template_path)


def _get_template_info_from_path(template_path: Path) -> Optional[TemplateInfo]:
    """Get template information from path."""
    index_path = template_path / "index.js"
    
    if not index_path.exists():
        return None
    
    # Load template configuration
    # This is a simplified implementation
    # In a real implementation, you'd properly load and execute the index.js
    
    return TemplateInfo(
        name=template_path.name,
        type="custom",  # Would be determined from config
        description="Template description",  # Would be loaded from config
        path=template_path,
        parameters={},  # Would be loaded from config
        usage_count=0,  # Would be loaded from usage tracking
    )


def _interactive_parameter_input(parameters: Dict[str, Any], template_info: TemplateInfo) -> Dict[str, Any]:
    """Interactive parameter input."""
    # Implementation for interactive parameter input
    return parameters


def _enhance_parameters_with_dspy(template_name: str, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance parameters using DSPy."""
    try:
        prompt = f"""
        Analyze the template '{template_name}' for generating '{name}' with current parameters: {parameters}
        
        Suggest additional intelligent parameters that would improve the generated code.
        Consider:
        - Best practices for the template type
        - Common patterns and conventions
        - Code quality improvements
        - Maintainability enhancements
        
        Return only a JSON object with additional parameters.
        """
        
        result = dspy_reasoning_chain(prompt)
        
        # Parse result as JSON
        try:
            enhanced_params = json.loads(result)
            return enhanced_params
        except json.JSONDecodeError:
            return {}
            
    except Exception as e:
        record_exception(e)
        return {}


def _get_template_files(template_path: Path) -> List[Path]:
    """Get template files."""
    templates_dir = template_path / "_templates"
    if not templates_dir.exists():
        return []
    
    template_files = []
    for file_path in templates_dir.rglob("*.ejs.t"):
        template_files.append(file_path)
    
    return template_files


def _generate_file_from_template(
    template_file: Path,
    parameters: Dict[str, Any],
    output_path: Path,
    dry_run: bool
) -> Optional[Dict[str, Any]]:
    """Generate file from template."""
    # Read template content
    with open(template_file, 'r') as f:
        template_content = f.read()
    
    # Process template with EJS-like syntax
    processed_content = _process_ejs_template(template_content, parameters)
    
    # Determine output file path
    relative_path = template_file.relative_to(template_file.parents[1])
    output_file_name = relative_path.name.replace(".ejs.t", "")
    output_file_path = output_path / output_file_name
    
    if dry_run:
        return {
            "path": str(output_file_path),
            "size": len(processed_content),
            "content": processed_content,
            "type": "would_create"
        }
    
    # Create output file
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file_path, 'w') as f:
        f.write(processed_content)
    
    return {
        "path": str(output_file_path),
        "size": len(processed_content),
        "type": "created"
    }


def _process_ejs_template(content: str, parameters: Dict[str, Any]) -> str:
    """Process EJS-like template."""
    # Simple EJS-like template processing
    # In a real implementation, you'd use a proper EJS engine
    
    processed_content = content
    
    for key, value in parameters.items():
        placeholder = f"<%= {key} %>"
        processed_content = processed_content.replace(placeholder, str(value))
    
    return processed_content


def _update_template_usage(template_name: str):
    """Update template usage statistics."""
    # Implementation for updating usage statistics
    pass


def _get_template_structure(template_type: str) -> Dict[str, str]:
    """Get template structure based on type."""
    structures = {
        "component": {
            "component.tsx.ejs.t": """import React from 'react';

interface <%= Name %>Props {
  // Add your props here
}

export const <%= Name %>: React.FC<<%= Name %>Props> = ({}) => {
  return (
    <div className="<%= name_kebab %>">
      <h2><%= Name %></h2>
      {/* Add your component content here */}
    </div>
  );
};

export default <%= Name %>;
""",
            "component.test.tsx.ejs.t": """import { render, screen } from '@testing-library/react';
import { <%= Name %> } from './<%= Name %>';

describe('<%= Name %>', () => {
  it('renders correctly', () => {
    render(<<%= Name %> />);
    expect(screen.getByText('<%= Name %>')).toBeInTheDocument();
  });
});
"""
        },
        "api": {
            "endpoint.ts.ejs.t": """import express from 'express';

const router = express.Router();

// GET /<%= name_kebab %>
router.get('/', async (req, res) => {
  try {
    // Add your logic here
    res.json({ message: '<%= Name %> endpoint' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /<%= name_kebab %>
router.post('/', async (req, res) => {
  try {
    // Add your logic here
    res.status(201).json({ message: '<%= Name %> created' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
"""
        }
    }
    
    return structures.get(template_type, {})


def _interactive_template_creation(template_name: str, template_structure: Dict[str, str]) -> Dict[str, str]:
    """Interactive template creation."""
    # Implementation for interactive template creation
    return template_structure


def _enhance_template_with_dspy(template_name: str, template_type: str, template_structure: Dict[str, str]) -> Dict[str, str]:
    """Enhance template with DSPy."""
    try:
        prompt = f"""
        Analyze the template '{template_name}' of type '{template_type}' with current structure: {list(template_structure.keys())}
        
        Suggest additional template files that would improve the template.
        Consider:
        - Best practices for the template type
        - Common patterns and conventions
        - Code quality improvements
        - Maintainability enhancements
        
        Return only a JSON object with additional template files and their content.
        """
        
        result = dspy_reasoning_chain(prompt)
        
        # Parse result as JSON
        try:
            enhanced_structure = json.loads(result)
            return enhanced_structure
        except json.JSONDecodeError:
            return {}
            
    except Exception as e:
        record_exception(e)
        return {}


def _create_template_index(template_name: str, template_type: str, description: Optional[str]) -> str:
    """Create template index file."""
    return f"""module.exports = {{
  description: '{description or f"{template_type} template"}',
  parameters: {{
    name: {{
      type: 'string',
      description: 'Name for the generated item',
      required: true
    }}
  }}
}};
"""


def _template_matches_type(template_dir: Path, template_type: str) -> bool:
    """Check if template matches type."""
    # Implementation for type matching
    return True


def _validate_single_template(template_dir: Path) -> List[Dict[str, Any]]:
    """Validate single template."""
    issues = []
    
    # Check template structure
    templates_dir = template_dir / "_templates"
    if not templates_dir.exists():
        issues.append({
            "template": template_dir.name,
            "severity": "error",
            "description": "Missing _templates directory"
        })
    
    # Check for template files
    template_files = list(templates_dir.glob("*.ejs.t")) if templates_dir.exists() else []
    if not template_files:
        issues.append({
            "template": template_dir.name,
            "severity": "error",
            "description": "No template files found"
        })
    
    # Validate individual template files
    for template_file in template_files:
        file_issues = _validate_template_file(template_file)
        issues.extend(file_issues)
    
    return issues


def _validate_template_file(template_file: Path) -> List[Dict[str, Any]]:
    """Validate template file."""
    issues = []
    
    try:
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Check for basic EJS syntax
        if "<%=" in content and "%>" not in content:
            issues.append({
                "template": template_file.name,
                "severity": "warning",
                "description": "Incomplete EJS syntax",
                "line_number": content.count("\n") + 1
            })
        
        # Check for common issues
        if "TODO" in content or "FIXME" in content:
            issues.append({
                "template": template_file.name,
                "severity": "warning",
                "description": "Contains TODO or FIXME comments",
                "line_number": content.find("TODO") // 80 + 1  # Approximate line number
            })
        
    except Exception as e:
        issues.append({
            "template": template_file.name,
            "severity": "error",
            "description": f"Error reading template file: {e}"
        })
    
    return issues


def _apply_template_fixes(template_dir: Path, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply fixes to template issues."""
    fixes_applied = []
    
    for issue in issues:
        if issue.get("severity") == "error":
            # Apply automatic fixes for errors
            fix_description = f"Applied fix for {issue['description']}"
            fixes_applied.append({
                "template": issue["template"],
                "description": fix_description
            })
    
    return fixes_applied


def _get_scaffold_template(scaffold_type: str) -> Optional[Dict[str, Any]]:
    """Get scaffold template."""
    weaver_forge_path = _find_weaver_forge_path()
    scaffold_path = weaver_forge_path / "scaffolds" / scaffold_type
    
    if not scaffold_path.exists():
        return None
    
    config_path = scaffold_path / "config.json"
    if not config_path.exists():
        return None
    
    with open(config_path, 'r') as f:
        return json.load(f)


def _interactive_scaffold_parameters(parameters: Dict[str, Any], scaffold_template: Dict[str, Any]) -> Dict[str, Any]:
    """Interactive scaffold parameter input."""
    # Implementation for interactive scaffold parameters
    return parameters


def _enhance_scaffold_with_dspy(scaffold_type: str, project_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance scaffold with DSPy."""
    try:
        prompt = f"""
        Analyze the scaffold '{scaffold_type}' for project '{project_name}' with current parameters: {parameters}
        
        Suggest additional intelligent parameters that would improve the scaffold.
        Consider:
        - Best practices for the scaffold type
        - Common patterns and conventions
        - Project structure improvements
        - Development workflow enhancements
        
        Return only a JSON object with additional parameters.
        """
        
        result = dspy_reasoning_chain(prompt)
        
        # Parse result as JSON
        try:
            enhanced_params = json.loads(result)
            return enhanced_params
        except json.JSONDecodeError:
            return {}
            
    except Exception as e:
        record_exception(e)
        return {}


def _create_scaffold_file(file_info: Dict[str, Any], parameters: Dict[str, Any], output_path: Path) -> Optional[Dict[str, Any]]:
    """Create scaffold file."""
    file_path = output_path / file_info["path"]
    template_content = file_info["template"]
    
    # Process template
    processed_content = _process_ejs_template(template_content, parameters)
    
    # Create file
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(processed_content)
    
    return {
        "path": str(file_path),
        "size": len(processed_content),
        "type": "scaffold"
    }


def _analyze_generation_request_with_dspy(description: str, template_hint: Optional[str]) -> Dict[str, Any]:
    """Analyze generation request with DSPy."""
    try:
        prompt = f"""
        Analyze the generation request: "{description}"
        Template hint: {template_hint or "None"}
        
        Determine:
        1. The most appropriate template to use
        2. Parameters that should be extracted from the description
        3. Additional insights for improving the generation
        
        Return a JSON object with:
        - template_name: the template to use
        - parameters: extracted parameters
        - insights: list of insights for improvement
        """
        
        result = dspy_reasoning_chain(prompt)
        
        # Parse result as JSON
        try:
            analysis = json.loads(result)
            return analysis
        except json.JSONDecodeError:
            return {
                "template_name": "component",
                "parameters": {"name": "Generated"},
                "insights": []
            }
            
    except Exception as e:
        record_exception(e)
        return {
            "template_name": "component",
            "parameters": {"name": "Generated"},
            "insights": []
        }


def _basic_template_selection(description: str, template_hint: Optional[str]) -> str:
    """Basic template selection without AI."""
    if template_hint:
        return template_hint
    
    # Simple keyword-based selection
    description_lower = description.lower()
    
    if any(word in description_lower for word in ["component", "react", "ui", "frontend"]):
        return "component"
    elif any(word in description_lower for word in ["api", "endpoint", "service", "backend"]):
        return "api"
    else:
        return "component"


def _basic_parameter_extraction(description: str) -> Dict[str, Any]:
    """Basic parameter extraction without AI."""
    # Simple parameter extraction
    words = description.split()
    if words:
        return {"name": words[0].title()}
    return {"name": "Generated"}


def _find_weaver_forge_path() -> Path:
    """Find Weaver Forge path."""
    current_path = Path.cwd()
    
    # Look for .weaver-forge in current directory and parents
    while current_path != current_path.parent:
        weaver_forge_path = current_path / ".weaver-forge"
        if weaver_forge_path.exists():
            return weaver_forge_path
        current_path = current_path.parent
    
    # If not found, use current directory
    return Path.cwd() / ".weaver-forge"


def _is_ai_enabled() -> bool:
    """Check if AI is enabled."""
    weaver_forge_path = _find_weaver_forge_path()
    config_path = weaver_forge_path / "config.yaml"
    
    if not config_path.exists():
        return True  # Default to enabled
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get("ai_enabled", True)
    except Exception:
        return True


def _get_detailed_template_stats() -> Dict[str, Any]:
    """Get detailed template statistics."""
    # Implementation for detailed template statistics
    return {}


def _get_weaver_forge_metrics() -> Dict[str, Any]:
    """Get Weaver Forge metrics."""
    # Implementation for metrics collection
    return {
        "total_generations": 0,
        "successful_generations": 0,
        "average_generation_time": 0.0,
        "most_used_template": "component",
        "templates_created": 0,
    }


def generate_bulk_from_templates(
    generation_specs: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
    parallel: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generate multiple items from templates in bulk.
    
    Args:
        generation_specs: List of generation specifications
        output_path: Base output path for all generations
        parallel: Whether to run generations in parallel
        dry_run: Show what would be generated without creating files
        
    Returns:
        Bulk generation result with summary and individual results
    """
    with span("weaver_forge.bulk_generate", attributes={
        "specs_count": len(generation_specs),
        "parallel": parallel,
        "dry_run": dry_run
    }) as current_span:
        
        start_time = time.time()
        
        if output_path is None:
            output_path = Path.cwd()
        
        results = []
        errors = []
        total_files = 0
        
        if parallel:
            # Parallel generation using asyncio
            async def _generate_parallel():
                tasks = []
                for spec in generation_specs:
                    task = asyncio.create_task(_generate_single_async(spec, output_path, dry_run))
                    tasks.append(task)
                
                return await asyncio.gather(*tasks, return_exceptions=True)
            
            # Run parallel generation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                parallel_results = loop.run_until_complete(_generate_parallel())
                for result in parallel_results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                    else:
                        results.append(result)
                        total_files += len(result.get("files", []))
            finally:
                loop.close()
        else:
            # Sequential generation
            for spec in generation_specs:
                try:
                    result = generate_from_template(
                        template_name=spec["template"],
                        name=spec["name"],
                        output_path=output_path / spec.get("subdir", ""),
                        parameters=spec.get("parameters", {}),
                        interactive=False,
                        dry_run=dry_run
                    )
                    results.append(result)
                    total_files += len(result.get("files", []))
                except Exception as e:
                    error_msg = f"Error generating {spec.get('template', 'unknown')} {spec.get('name', 'unknown')}: {e}"
                    errors.append(error_msg)
                    record_exception(e)
        
        duration = time.time() - start_time
        
        # Calculate success rate
        success_count = len([r for r in results if r.get("success", False)])
        success_rate = (success_count / len(generation_specs)) * 100 if generation_specs else 0
        
        add_span_event("weaver_forge.bulk_generated", {
            "total_specs": len(generation_specs),
            "successful": success_count,
            "failed": len(errors),
            "total_files": total_files,
            "success_rate": success_rate,
        })
        
        return {
            "total_specs": len(generation_specs),
            "successful": success_count,
            "failed": len(errors),
            "success_rate": success_rate,
            "total_files": total_files,
            "duration": duration,
            "results": results,
            "errors": errors,
            "parallel": parallel,
            "dry_run": dry_run
        }


async def _generate_single_async(spec: Dict[str, Any], output_path: Path, dry_run: bool) -> Dict[str, Any]:
    """Generate a single item asynchronously."""
    return generate_from_template(
        template_name=spec["template"],
        name=spec["name"],
        output_path=output_path / spec.get("subdir", ""),
        parameters=spec.get("parameters", {}),
        interactive=False,
        dry_run=dry_run
    )


def generate_bulk_scaffolds(
    scaffold_specs: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
    parallel: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generate multiple project scaffolds in bulk.
    
    Args:
        scaffold_specs: List of scaffold specifications
        output_path: Base output path for all scaffolds
        parallel: Whether to run scaffold generation in parallel
        dry_run: Show what would be generated without creating files
        
    Returns:
        Bulk scaffold generation result
    """
    with span("weaver_forge.bulk_scaffold", attributes={
        "scaffolds_count": len(scaffold_specs),
        "parallel": parallel,
        "dry_run": dry_run
    }) as current_span:
        
        start_time = time.time()
        
        if output_path is None:
            output_path = Path.cwd()
        
        results = []
        errors = []
        total_files = 0
        
        for spec in scaffold_specs:
            try:
                result = create_scaffold(
                    scaffold_type=spec["type"],
                    project_name=spec["name"],
                    output_path=output_path / spec.get("subdir", spec["name"]),
                    parameters=spec.get("parameters", {}),
                    interactive=False
                )
                results.append(result)
                total_files += len(result.get("files", []))
            except Exception as e:
                error_msg = f"Error creating scaffold {spec.get('type', 'unknown')} {spec.get('name', 'unknown')}: {e}"
                errors.append(error_msg)
                record_exception(e)
        
        duration = time.time() - start_time
        
        # Calculate success rate
        success_count = len([r for r in results if r.get("success", False)])
        success_rate = (success_count / len(scaffold_specs)) * 100 if scaffold_specs else 0
        
        add_span_event("weaver_forge.bulk_scaffolded", {
            "total_scaffolds": len(scaffold_specs),
            "successful": success_count,
            "failed": len(errors),
            "total_files": total_files,
            "success_rate": success_rate,
        })
        
        return {
            "total_scaffolds": len(scaffold_specs),
            "successful": success_count,
            "failed": len(errors),
            "success_rate": success_rate,
            "total_files": total_files,
            "duration": duration,
            "results": results,
            "errors": errors,
            "parallel": parallel,
            "dry_run": dry_run
        }


def generate_from_batch_file(
    batch_file: Path,
    output_path: Optional[Path] = None,
    parallel: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generate from a batch specification file (JSON/YAML).
    
    Args:
        batch_file: Path to batch specification file
        output_path: Base output path for generations
        parallel: Whether to run generations in parallel
        dry_run: Show what would be generated without creating files
        
    Returns:
        Batch generation result
    """
    with span("weaver_forge.batch_file_generate", attributes={
        "batch_file": str(batch_file),
        "parallel": parallel,
        "dry_run": dry_run
    }) as current_span:
        
        start_time = time.time()
        
        if not batch_file.exists():
            raise WeaverForgeError(f"Batch file not found: {batch_file}")
        
        # Load batch specification
        try:
            with open(batch_file, 'r') as f:
                if batch_file.suffix.lower() in ['.yaml', '.yml']:
                    batch_spec = yaml.safe_load(f)
                else:
                    batch_spec = json.load(f)
        except Exception as e:
            raise WeaverForgeError(f"Failed to load batch file: {e}")
        
        # Extract generation specifications
        generation_specs = batch_spec.get("generations", [])
        scaffold_specs = batch_spec.get("scaffolds", [])
        
        results = {
            "batch_file": str(batch_file),
            "generations": {},
            "scaffolds": {},
            "total_duration": 0,
            "total_files": 0,
            "total_errors": 0
        }
        
        # Generate from templates
        if generation_specs:
            gen_result = generate_bulk_from_templates(
                generation_specs=generation_specs,
                output_path=output_path,
                parallel=parallel,
                dry_run=dry_run
            )
            results["generations"] = gen_result
            results["total_files"] += gen_result.get("total_files", 0)
            results["total_errors"] += len(gen_result.get("errors", []))
        
        # Generate scaffolds
        if scaffold_specs:
            scaffold_result = generate_bulk_scaffolds(
                scaffold_specs=scaffold_specs,
                output_path=output_path,
                parallel=parallel,
                dry_run=dry_run
            )
            results["scaffolds"] = scaffold_result
            results["total_files"] += scaffold_result.get("total_files", 0)
            results["total_errors"] += len(scaffold_result.get("errors", []))
        
        results["total_duration"] = time.time() - start_time
        
        add_span_event("weaver_forge.batch_file_completed", {
            "batch_file": str(batch_file),
            "total_files": results["total_files"],
            "total_errors": results["total_errors"],
        })
        
        return results


def create_bulk_template(
    template_specs: List[Dict[str, Any]],
    output_dir: Optional[Path] = None,
    interactive: bool = False
) -> Dict[str, Any]:
    """
    Create multiple templates in bulk.
    
    Args:
        template_specs: List of template specifications
        output_dir: Output directory for templates
        interactive: Whether to use interactive mode
        
    Returns:
        Bulk template creation result
    """
    with span("weaver_forge.bulk_create_templates", attributes={
        "templates_count": len(template_specs),
        "interactive": interactive
    }) as current_span:
        
        start_time = time.time()
        
        if output_dir is None:
            output_dir = _find_weaver_forge_path() / "templates"
        
        results = []
        errors = []
        
        for spec in template_specs:
            try:
                result = create_template(
                    template_name=spec["name"],
                    template_type=spec["type"],
                    description=spec.get("description"),
                    interactive=interactive,
                    output_dir=output_dir
                )
                results.append(result)
            except Exception as e:
                error_msg = f"Error creating template {spec.get('name', 'unknown')}: {e}"
                errors.append(error_msg)
                record_exception(e)
        
        duration = time.time() - start_time
        
        # Calculate success rate
        success_count = len([r for r in results if r.get("name")])
        success_rate = (success_count / len(template_specs)) * 100 if template_specs else 0
        
        add_span_event("weaver_forge.bulk_templates_created", {
            "total_templates": len(template_specs),
            "successful": success_count,
            "failed": len(errors),
            "success_rate": success_rate,
        })
        
        return {
            "total_templates": len(template_specs),
            "successful": success_count,
            "failed": len(errors),
            "success_rate": success_rate,
            "duration": duration,
            "results": results,
            "errors": errors
        }


def validate_bulk_templates(
    template_names: Optional[List[str]] = None,
    fix_issues: bool = False,
    output_report: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Validate multiple templates in bulk.
    
    Args:
        template_names: List of template names to validate (None for all)
        fix_issues: Whether to automatically fix validation issues
        output_report: Path to output validation report
        
    Returns:
        Bulk validation result
    """
    with span("weaver_forge.bulk_validate", attributes={
        "templates_count": len(template_names) if template_names else "all",
        "fix_issues": fix_issues
    }) as current_span:
        
        start_time = time.time()
        
        weaver_forge_path = _find_weaver_forge_path()
        templates_path = weaver_forge_path / "templates"
        
        if not templates_path.exists():
            return {
                "success": False,
                "error": "Templates directory not found",
                "duration": time.time() - start_time
            }
        
        # Get templates to validate
        if template_names:
            templates_to_validate = [templates_path / name for name in template_names]
        else:
            templates_to_validate = [d for d in templates_path.iterdir() if d.is_dir()]
        
        results = []
        total_issues = 0
        fixed_issues = 0
        
        for template_path in templates_to_validate:
            try:
                validation_result = _validate_single_template(template_path)
                results.append({
                    "template": template_path.name,
                    "issues": validation_result,
                    "issue_count": len(validation_result)
                })
                total_issues += len(validation_result)
                
                # Fix issues if requested
                if fix_issues and validation_result:
                    fixed_result = _apply_template_fixes(template_path, validation_result)
                    fixed_issues += len(fixed_result)
            except Exception as e:
                results.append({
                    "template": template_path.name,
                    "error": str(e),
                    "issues": [],
                    "issue_count": 0
                })
        
        duration = time.time() - start_time
        
        # Generate summary
        summary = {
            "total_templates": len(templates_to_validate),
            "templates_with_issues": len([r for r in results if r.get("issue_count", 0) > 0]),
            "total_issues": total_issues,
            "fixed_issues": fixed_issues,
            "success_rate": ((len(templates_to_validate) - len([r for r in results if r.get("error")])) / len(templates_to_validate)) * 100 if templates_to_validate else 0,
            "duration": duration,
            "results": results
        }
        
        # Output report if requested
        if output_report:
            try:
                with open(output_report, 'w') as f:
                    if output_report.suffix.lower() in ['.yaml', '.yml']:
                        yaml.dump(summary, f, default_flow_style=False)
                    else:
                        json.dump(summary, f, indent=2)
            except Exception as e:
                summary["report_error"] = str(e)
        
        add_span_event("weaver_forge.bulk_validated", {
            "total_templates": len(templates_to_validate),
            "total_issues": total_issues,
            "fixed_issues": fixed_issues,
        })
        
        return summary 