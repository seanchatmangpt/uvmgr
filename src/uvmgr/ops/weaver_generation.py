"""
uvmgr.ops.weaver_generation
============================

Unified code generation for Weaver Forge with 80/20 optimization.

This module consolidates all code generation logic into a single, 
efficient pipeline that handles 80% of use cases with 20% of the code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Environment = FileSystemLoader = Template = None
from uvmgr.core.instrumentation import add_span_attributes, add_span_event
from uvmgr.core.telemetry import span


class WeaverGenerator:
    """Unified generator for semantic conventions with 80/20 optimization."""
    
    def __init__(self, registry_path: Path, template_path: Optional[Path] = None):
        self.registry_path = registry_path
        self.template_path = template_path or Path(__file__).parent.parent / "templates"
        self._setup_jinja_env()
        
    def _setup_jinja_env(self):
        """Initialize Jinja2 environment with custom filters."""
        if JINJA2_AVAILABLE and self.template_path.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_path)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            # Add custom filters for semantic conventions
            self.env.filters["to_python_const"] = self._to_python_const
            self.env.filters["to_python_type"] = self._to_python_type
            self.env.filters["groupby"] = self._groupby_filter
            self.env.filters["selectattr"] = self._selectattr_filter
            self.env.filters["unique"] = self._unique_filter
        else:
            self.env = None
            
    @staticmethod
    def _to_python_const(name: str) -> str:
        """Convert semantic convention name to Python constant."""
        # e.g., "http.request.method" -> "HTTP_REQUEST_METHOD"
        return name.upper().replace(".", "_").replace("-", "_")
        
    @staticmethod  
    def _to_python_type(type_str: str) -> str:
        """Convert OTEL type to Python type annotation."""
        type_map = {
            "string": "str",
            "int": "int", 
            "double": "float",
            "boolean": "bool",
            "string[]": "List[str]",
            "int[]": "List[int]",
        }
        return type_map.get(type_str, "Any")
        
    @staticmethod
    def _groupby_filter(items, attribute):
        """Group items by attribute (simplified for 80/20)."""
        groups = {}
        for item in items:
            if hasattr(item, attribute):
                key = getattr(item, attribute)
            elif isinstance(item, dict):
                key = item.get(attribute, "unknown")
            else:
                key = "unknown"
                
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups.items()
        
    @staticmethod
    def _selectattr_filter(items, attribute):
        """Select items that have attribute (simplified for 80/20)."""
        result = []
        for item in items:
            if hasattr(item, attribute):
                if getattr(item, attribute):
                    result.append(item)
            elif isinstance(item, dict) and item.get(attribute):
                result.append(item)
        return result
        
    @staticmethod
    def _unique_filter(items):
        """Return unique items (simplified for 80/20)."""
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
        
    def generate_python(self, output_path: Path, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Python constants file with 80/20 approach.
        
        This focuses on the most common use case: generating type-safe
        attribute constants for OpenTelemetry instrumentation.
        """
        with span("ops.weaver.generate_python"):
            add_span_attributes(
                output_path=str(output_path),
                attribute_count=len(attributes),
            )
            
            # Use template if available, fallback to simple generation
            if self.env and (self.template_path / "python_constants.j2").exists():
                template = self.env.get_template("python_constants.j2")
                content = template.render(
                    attributes=attributes,
                    imports=self._get_python_imports(attributes),
                )
            else:
                # 80/20 fallback - simple but effective
                content = self._generate_simple_python(attributes)
                
            # Write output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
            
            add_span_event("python_generation_complete", {
                "output_path": str(output_path),
                "lines": len(content.splitlines()),
            })
            
            return {
                "status": "success",
                "output_path": str(output_path),
                "attributes_generated": len(attributes),
                "template_used": self.env is not None,
            }
            
    def _generate_simple_python(self, attributes: Dict[str, Any]) -> str:
        """Generate simple Python constants without templates (80/20 fallback)."""
        lines = [
            '"""Auto-generated semantic convention constants."""',
            "",
            "from typing import Final",
            "",
        ]
        
        # Group attributes by namespace
        namespaces = {}
        for attr_name, attr_info in attributes.items():
            namespace = attr_name.split(".")[0]
            if namespace not in namespaces:
                namespaces[namespace] = []
            namespaces[namespace].append((attr_name, attr_info))
            
        # Generate classes for each namespace
        for namespace, attrs in sorted(namespaces.items()):
            class_name = f"{namespace.title()}Attributes"
            lines.extend([
                f"class {class_name}:",
                f'    """{namespace.title()} operation attributes"""',
                "",
            ])
            
            for attr_name, attr_info in sorted(attrs):
                const_name = self._to_python_const(attr_name)
                description = attr_info.get("brief", "").replace('"', "'")
                lines.append(
                    f'    {const_name}: Final[str] = "{attr_name}"  # {description}'
                )
                
            lines.append("")
            
        # Add __all__ export
        lines.extend([
            "# Export all classes",
            "__all__ = [",
        ])
        for namespace in sorted(namespaces.keys()):
            lines.append(f'    "{namespace.title()}Attributes",')
        lines.append("]")
        
        return "\n".join(lines)
        
    def _get_python_imports(self, attributes: Dict[str, Any]) -> List[str]:
        """Determine required imports based on attributes."""
        imports = ["from typing import Final"]
        
        # Check if we need List type
        for attr_info in attributes.values():
            if attr_info.get("type", "").endswith("[]"):
                imports.append("from typing import List")
                break
                
        return imports
        
    def validate_before_generate(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration before generation (80/20 approach).
        
        Only validates the critical 20% that prevents 80% of errors.
        """
        with span("ops.weaver.validate_config"):
            # Critical validations only
            if not self.registry_path.exists():
                add_span_event("validation_failed", {"reason": "registry_not_found"})
                return False
                
            if "attributes" not in config or not config["attributes"]:
                add_span_event("validation_failed", {"reason": "no_attributes"})
                return False
                
            add_span_event("validation_passed", {
                "attribute_count": len(config.get("attributes", {}))
            })
            return True


def consolidate_generation(
    registry_path: Path,
    output_path: Path, 
    language: str = "python",
    template_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Main entry point for consolidated code generation.
    
    This implements the 80/20 principle by focusing on Python generation
    which covers 80% of use cases with minimal configuration.
    """
    with span("ops.weaver.consolidate_generation"):
        generator = WeaverGenerator(registry_path, template_path)
        
        # Load attributes from registry
        attributes = {}
        
        try:
            import yaml
        except ImportError:
            # Fallback for environments without PyYAML
            import json
            yaml = None
        
        for yaml_file in registry_path.glob("**/*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    if yaml:
                        # Use PyYAML if available
                        yaml_content = yaml.safe_load(f)
                    else:
                        # Fallback: try to parse as JSON-like YAML
                        content = f.read()
                        # Simple YAML-to-JSON conversion for basic cases
                        content = content.replace(':', ': ').replace('- ', '"- "')
                        try:
                            yaml_content = json.loads(content)
                        except:
                            # Skip malformed files
                            continue
                
                # Extract semantic convention attributes
                if isinstance(yaml_content, dict):
                    # Look for semantic convention patterns
                    for key, value in yaml_content.items():
                        if key.startswith('attribute_') or 'semantic_conventions' in str(key).lower():
                            if isinstance(value, dict):
                                attributes.update(value)
                            elif isinstance(value, list):
                                # Handle list of attributes
                                for item in value:
                                    if isinstance(item, dict) and 'id' in item:
                                        attributes[item['id']] = item
                
                add_span_event("yaml_file_parsed", {
                    "file": str(yaml_file),
                    "attributes_found": len(attributes)
                })
                
            except Exception as e:
                add_span_event("yaml_parsing_failed", {
                    "file": str(yaml_file),
                    "error": str(e)
                })
                # Continue processing other files
                continue
            
        # Validate
        config = {"attributes": attributes}
        if not generator.validate_before_generate(config):
            return {"status": "validation_failed"}
            
        # Generate based on language
        if language == "python":
            return generator.generate_python(output_path, attributes)
        else:
            # 80/20: Python is primary, others can be added later
            return {"status": "unsupported_language", "language": language}