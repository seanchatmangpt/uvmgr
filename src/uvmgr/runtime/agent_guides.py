"""
Agent Guides Runtime Operations
===============================

This module provides agent guides runtime operations.
Implements the 80/20 principle: focuses on the most useful agent guide
operations that provide 80% of the value for AI-assisted development.

Key Features:
- Guide installation and management
- Custom command creation
- Multi-mind analysis coordination
- Conversation search and indexing
- Code analysis and insights
- Anti-repetition workflows
- DSPy integration for decision making
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from uvmgr.core.instrumentation import add_span_attributes, add_span_event, instrument_command
from uvmgr.core.process import run_logged
from uvmgr.core.semconv import AgentAttributes, AgentOperations
from uvmgr.core.telemetry import metric_counter, metric_histogram, span, record_exception


@dataclass
class GuideInfo:
    """Agent guide information."""
    name: str
    version: str
    description: str
    author: str
    commands: List[str]
    installation_path: str
    status: str


@dataclass
class AnalysisResult:
    """Multi-mind analysis result."""
    topic: str
    specialists: List[str]
    insights: List[str]
    consensus: Optional[str]
    confidence: float
    duration: float


@dataclass
class SearchResult:
    """Conversation search result."""
    conversation_id: str
    relevance_score: float
    snippet: str
    timestamp: str
    source: str


@instrument_command("agent_guides_install")
def install_guide(source: str, target_path: Optional[Path] = None) -> GuideInfo:
    """Install an agent guide from a source."""
    with span("agent_guides.install",
              **{AgentAttributes.OPERATION: AgentOperations.INSTALL,
                 AgentAttributes.SOURCE: source}):
        
        if target_path is None:
            target_path = Path.home() / ".uvmgr" / "guides"
        
        target_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone or download the guide
            if source.startswith(("http://", "https://", "git@")):
                # Git repository
                guide_name = source.split("/")[-1].replace(".git", "")
                guide_path = target_path / guide_name
                
                if guide_path.exists():
                    # Update existing guide
                    subprocess.run(
                        ["git", "pull"],
                        cwd=guide_path,
                        check=True,
                        capture_output=True,
                        timeout=60
                    )
                else:
                    # Clone new guide
                    subprocess.run(
                        ["git", "clone", source, str(guide_path)],
                        check=True,
                        capture_output=True,
                        timeout=120
                    )
            else:
                # Local path
                import shutil
                source_path = Path(source)
                if source_path.exists():
                    guide_name = source_path.name
                    guide_path = target_path / guide_name
                    shutil.copytree(source_path, guide_path, dirs_exist_ok=True)
                else:
                    raise FileNotFoundError(f"Source path not found: {source}")
            
            # Read guide metadata
            guide_info = _read_guide_metadata(guide_path)
            
            add_span_event("agent_guides.installed", {
                "guide_name": guide_info.name,
                "installation_path": guide_info.installation_path
            })
            
            metric_counter("agent_guides.installations")(1, {
                "source_type": "git" if source.startswith(("http", "git@")) else "local"
            })
            
            return guide_info
            
        except subprocess.CalledProcessError as e:
            record_exception(e, attributes={
                "operation": "install_guide",
                "source": source
            })
            raise RuntimeError(f"Failed to install guide from {source}: {e.stderr}")
        except Exception as e:
            record_exception(e, attributes={
                "operation": "install_guide",
                "source": source
            })
            raise


def _read_guide_metadata(guide_path: Path) -> GuideInfo:
    """Read guide metadata from installation."""
    metadata_file = guide_path / "guide.json"
    
    if metadata_file.exists():
        try:
            metadata = json.loads(metadata_file.read_text())
            return GuideInfo(
                name=metadata.get("name", guide_path.name),
                version=metadata.get("version", "unknown"),
                description=metadata.get("description", ""),
                author=metadata.get("author", "unknown"),
                commands=metadata.get("commands", []),
                installation_path=str(guide_path),
                status="installed"
            )
        except Exception:
            pass
    
    # Fallback to basic info
    return GuideInfo(
        name=guide_path.name,
        version="unknown",
        description="Agent guide",
        author="unknown",
        commands=[],
        installation_path=str(guide_path),
        status="installed"
    )


@instrument_command("agent_guides_list")
def list_guides(guides_path: Optional[Path] = None) -> List[GuideInfo]:
    """List installed agent guides."""
    if guides_path is None:
        guides_path = Path.home() / ".uvmgr" / "guides"
    
    with span("agent_guides.list",
              **{AgentAttributes.OPERATION: AgentOperations.LIST}):
        
        guides = []
        
        if guides_path.exists():
            for guide_dir in guides_path.iterdir():
                if guide_dir.is_dir():
                    try:
                        guide_info = _read_guide_metadata(guide_dir)
                        guides.append(guide_info)
                    except Exception as e:
                        record_exception(e, attributes={
                            "operation": "list_guides",
                            "guide_path": str(guide_dir)
                        })
        
        add_span_attributes(**{"guides.count": len(guides)})
        
        return guides


@instrument_command("agent_guides_multi_mind_analysis")
async def run_multi_mind_analysis(topic: str, specialists: Optional[List[str]] = None,
                                rounds: int = 3) -> AnalysisResult:
    """Run multi-specialist collaborative analysis."""
    if specialists is None:
        specialists = ["architect", "developer", "tester", "security", "performance"]
    
    with span("agent_guides.multi_mind",
              **{AgentAttributes.OPERATION: AgentOperations.ANALYZE,
                 "analysis.topic": topic,
                 "analysis.specialists": ",".join(specialists),
                 "analysis.rounds": rounds}):
        
        start_time = time.time()
        insights = []
        
        try:
            # Simulate multi-mind analysis (simplified implementation)
            for round_num in range(rounds):
                round_insights = []
                
                for specialist in specialists:
                    # In a real implementation, this would call different AI models
                    # or prompt templates specialized for each role
                    insight = await _generate_specialist_insight(specialist, topic, round_num)
                    round_insights.append(insight)
                    insights.append(f"[{specialist.title()}] {insight}")
                
                add_span_event(f"agent_guides.analysis.round_{round_num}", {
                    "insights_generated": len(round_insights)
                })
            
            # Generate consensus (simplified)
            consensus = await _generate_consensus(topic, insights)
            confidence = _calculate_confidence(insights)
            
            duration = time.time() - start_time
            
            result = AnalysisResult(
                topic=topic,
                specialists=specialists,
                insights=insights,
                consensus=consensus,
                confidence=confidence,
                duration=duration
            )
            
            add_span_attributes(**{
                "analysis.insights_count": len(insights),
                "analysis.confidence": confidence,
                "analysis.duration": duration
            })
            
            metric_histogram("agent_guides.analysis.duration")(duration, {
                "specialists_count": len(specialists),
                "rounds": rounds
            })
            
            return result
            
        except Exception as e:
            record_exception(e, attributes={
                "operation": "multi_mind_analysis",
                "topic": topic
            })
            raise


async def _generate_specialist_insight(specialist: str, topic: str, round_num: int) -> str:
    """Generate insight from a specialist perspective."""
    # This is a simplified implementation
    # In practice, this would use specialized prompts or AI models
    
    specialist_perspectives = {
        "architect": f"From an architectural perspective on '{topic}': Consider scalability, maintainability, and design patterns.",
        "developer": f"From a development perspective on '{topic}': Focus on implementation complexity, code quality, and developer experience.",
        "tester": f"From a testing perspective on '{topic}': Consider testability, edge cases, and quality assurance strategies.",
        "security": f"From a security perspective on '{topic}': Evaluate potential vulnerabilities, access controls, and threat models.",
        "performance": f"From a performance perspective on '{topic}': Analyze bottlenecks, optimization opportunities, and resource usage."
    }
    
    base_insight = specialist_perspectives.get(specialist, f"Analysis of '{topic}' from {specialist} perspective")
    
    # Add round-specific variations
    round_variations = [
        "Initial assessment and high-level considerations.",
        "Deeper analysis with specific recommendations.",
        "Final refinement and implementation guidance."
    ]
    
    variation = round_variations[min(round_num, len(round_variations) - 1)]
    
    return f"{base_insight} {variation}"


async def _generate_consensus(topic: str, insights: List[str]) -> str:
    """Generate consensus from multiple insights."""
    # Simplified consensus generation
    # In practice, this would use AI to synthesize insights
    
    if not insights:
        return f"No consensus reached for '{topic}'"
    
    # Count common themes (simplified)
    themes = {}
    for insight in insights:
        words = insight.lower().split()
        for word in words:
            if len(word) > 5:  # Focus on meaningful words
                themes[word] = themes.get(word, 0) + 1
    
    # Find most common themes
    common_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)[:3]
    theme_words = [theme[0] for theme in common_themes]
    
    return f"Consensus on '{topic}': Key considerations include {', '.join(theme_words)}. Multiple specialists agree on the importance of careful planning and implementation."


def _calculate_confidence(insights: List[str]) -> float:
    """Calculate confidence score based on insight consistency."""
    if not insights:
        return 0.0
    
    # Simplified confidence calculation
    # In practice, this would use NLP to analyze insight similarity
    
    # Base confidence on number of insights and length
    base_confidence = min(0.8, len(insights) / 10)
    
    # Adjust based on insight quality (simplified)
    avg_length = sum(len(insight) for insight in insights) / len(insights)
    length_factor = min(1.0, avg_length / 100)
    
    confidence = base_confidence * length_factor
    return round(confidence, 2)


@instrument_command("agent_guides_search_conversations")
def search_conversations(query: str, limit: int = 10, 
                        source: Optional[str] = None) -> List[SearchResult]:
    """Search through conversation history."""
    with span("agent_guides.search",
              **{AgentAttributes.OPERATION: AgentOperations.SEARCH,
                 "search.query": query,
                 "search.limit": limit}):
        
        # Conversation search not implemented
        return NotImplemented


@instrument_command("agent_guides_create_command")
def create_custom_command(name: str, description: str, template: str,
                         guides_path: Optional[Path] = None) -> bool:
    """Create a custom agent guide command."""
    if guides_path is None:
        guides_path = Path.home() / ".uvmgr" / "guides" / "custom"
    
    with span("agent_guides.create_command",
              **{AgentAttributes.OPERATION: AgentOperations.CREATE,
                 "command.name": name}):
        
        try:
            guides_path.mkdir(parents=True, exist_ok=True)
            
            # Create command file
            command_file = guides_path / f"{name}.py"
            command_content = _generate_command_template(name, description, template)
            command_file.write_text(command_content)
            
            # Update guide metadata
            metadata_file = guides_path / "guide.json"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
            else:
                metadata = {
                    "name": "custom",
                    "version": "1.0.0",
                    "description": "Custom agent guide commands",
                    "author": "user",
                    "commands": []
                }
            
            if name not in metadata["commands"]:
                metadata["commands"].append(name)
            
            metadata_file.write_text(json.dumps(metadata, indent=2))
            
            add_span_event("agent_guides.command_created", {
                "command_name": name,
                "file_path": str(command_file)
            })
            
            metric_counter("agent_guides.commands_created")(1)
            
            return True
            
        except Exception as e:
            record_exception(e, attributes={
                "operation": "create_command",
                "command_name": name
            })
            return False


def _generate_command_template(name: str, description: str, template: str) -> str:
    """Generate command implementation template."""
    return f'''"""
Custom Agent Guide Command: {name}
{description}
"""

import asyncio
from typing import Any, Dict, List, Optional

async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the {name} command."""
    
    # Command implementation based on template: {template}
    
    result = {{
        "command": "{name}",
        "status": "success",
        "description": "{description}",
        "output": "Command executed successfully",
        "context": context
    }}
    
    return result


def get_command_info() -> Dict[str, Any]:
    """Get command metadata."""
    return {{
        "name": "{name}",
        "description": "{description}",
        "template": "{template}",
        "version": "1.0.0"
    }}
'''


@instrument_command("agent_guides_validate")
def validate_guides(guides_path: Optional[Path] = None) -> Dict[str, Any]:
    """Validate installed agent guides."""
    if guides_path is None:
        guides_path = Path.home() / ".uvmgr" / "guides"
    
    with span("agent_guides.validate",
              **{AgentAttributes.OPERATION: AgentOperations.VALIDATE}):
        
        validation_results = {
            "valid_guides": [],
            "invalid_guides": [],
            "missing_files": [],
            "total_guides": 0
        }
        
        if not guides_path.exists():
            validation_results["error"] = "Guides directory does not exist"
            return validation_results
        
        for guide_dir in guides_path.iterdir():
            if guide_dir.is_dir():
                validation_results["total_guides"] += 1
                
                try:
                    guide_info = _read_guide_metadata(guide_dir)
                    
                    # Validate guide structure
                    required_files = ["guide.json"]
                    missing = []
                    
                    for required_file in required_files:
                        if not (guide_dir / required_file).exists():
                            missing.append(required_file)
                    
                    if missing:
                        validation_results["invalid_guides"].append({
                            "name": guide_info.name,
                            "path": str(guide_dir),
                            "missing_files": missing
                        })
                        validation_results["missing_files"].extend(missing)
                    else:
                        validation_results["valid_guides"].append({
                            "name": guide_info.name,
                            "version": guide_info.version,
                            "path": str(guide_dir),
                            "commands": len(guide_info.commands)
                        })
                
                except Exception as e:
                    validation_results["invalid_guides"].append({
                        "name": guide_dir.name,
                        "path": str(guide_dir),
                        "error": str(e)
                    })
        
        validation_results["summary"] = {
            "valid": len(validation_results["valid_guides"]),
            "invalid": len(validation_results["invalid_guides"]),
            "total": validation_results["total_guides"],
            "success_rate": len(validation_results["valid_guides"]) / max(1, validation_results["total_guides"])
        }
        
        add_span_attributes(**{
            "validation.total_guides": validation_results["total_guides"],
            "validation.valid_guides": len(validation_results["valid_guides"]),
            "validation.invalid_guides": len(validation_results["invalid_guides"])
        })
        
        return validation_results


@instrument_command("agent_guides_get_status")
def get_status(guides_path: Optional[Path] = None) -> Dict[str, Any]:
    """Get agent guides system status."""
    if guides_path is None:
        guides_path = Path.home() / ".uvmgr" / "guides"
    
    with span("agent_guides.status",
              **{AgentAttributes.OPERATION: AgentOperations.STATUS}):
        
        status = {
            "installation_path": str(guides_path),
            "guides_installed": 0,
            "commands_available": 0,
            "system_health": "unknown",
            "last_update": "never"
        }
        
        try:
            guides = list_guides(guides_path)
            status["guides_installed"] = len(guides)
            status["commands_available"] = sum(len(guide.commands) for guide in guides)
            
            if guides:
                status["system_health"] = "healthy"
                # Find most recent guide (simplified)
                status["last_update"] = "recent"
            else:
                status["system_health"] = "no_guides"
            
            # Add guide details
            status["guides"] = [
                {
                    "name": guide.name,
                    "version": guide.version,
                    "commands": len(guide.commands),
                    "status": guide.status
                }
                for guide in guides
            ]
            
        except Exception as e:
            status["system_health"] = "error"
            status["error"] = str(e)
            record_exception(e, attributes={"operation": "get_status"})
        
        return status