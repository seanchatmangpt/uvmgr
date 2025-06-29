"""
Definition of Done (DoD) Automation System
==========================================

The DoD module provides enterprise-grade Definition of Done automation
through the Weaver Forge exoskeleton architecture. This system wraps around
entire projects to provide structural integrity, automated validation,
and continuous evolution of quality standards.

Key Components:
- Weaver Forge Compiler: Transforms declarative DoD specs into executable pipelines
- DoD Exoskeleton: Wraps projects with continuous compliance enforcement  
- Evolution Engine: Self-improving DoD rules based on validation patterns
- Enterprise Integration: DevOps, CI/CD, and end-to-end automation

Usage:
    from uvmgr.dod import wrap_project_with_dod, validate_dod
    
    # Wrap project with DoD exoskeleton
    await wrap_project_with_dod(project_path, "enterprise")
    
    # Validate project compliance
    results = await validate_dod(project_path, fix_issues=True)
"""

from .weaver_forge_compiler import (
    DoDExoskeleton,
    WeaverForgeCompiler,
    DoDSpecification,
    DoDRule,
    DoDValidationResult,
    ValidationLevel,
    DoDCategory,
    get_dod_exoskeleton,
    wrap_project_with_dod,
    validate_dod,
)

__all__ = [
    "DoDExoskeleton",
    "WeaverForgeCompiler", 
    "DoDSpecification",
    "DoDRule",
    "DoDValidationResult",
    "ValidationLevel",
    "DoDCategory",
    "get_dod_exoskeleton",
    "wrap_project_with_dod",
    "validate_dod",
]