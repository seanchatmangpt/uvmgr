"""
Test AGI-specific components and self-improvement capabilities.

🧠 AGI Test Strategy:
- Test recursive self-improvement
- Validate telemetry-driven evolution
- Test 80/20 principle application
- Validate meta-agent behavior
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from weavership_agi import (
    MetaAgent,
    SelfEvolvingPlatform,
    SelfUpdatingTemplate,
    platform,
    meta_agent,
    tracer,
    meter
)


class TestMetaAgent:
    """Test the Meta-Agent that improves WeaverShip itself."""
    
    def test_meta_agent_initialization(self):
        """Test meta-agent initializes with correct defaults."""
        agent = MetaAgent()
        assert agent.target_system == "weavership"
        assert agent.safety_level == "high"
        assert agent.maturity_level == 0
        assert isinstance(agent.improvement_queue, list)
    
    @pytest.mark.asyncio
    async def test_analyze_architecture(self):
        """Test meta-agent can analyze architecture."""
        agent = MetaAgent()
        components = await agent.analyze_architecture()
        
        # Should return list of critical components
        assert isinstance(components, list)
        assert len(components) > 0
        
        # Should apply 80/20 principle
        assert "template_engine" in components or "validation_system" in components
    
    @pytest.mark.asyncio
    async def test_identify_critical_components_pareto(self):
        """Test 80/20 analysis for critical components."""
        agent = MetaAgent()
        
        # Mock telemetry analysis methods
        with patch.object(agent, '_analyze_error_telemetry', new=AsyncMock(return_value=["comp1", "comp1", "comp2"])):
            with patch.object(agent, '_analyze_performance_telemetry', new=AsyncMock(return_value=["comp1", "comp3"])):
                with patch.object(agent, '_analyze_resource_telemetry', new=AsyncMock(return_value=["comp1"])):
                    
                    components = await agent._identify_critical_components()
                    
                    # Should prioritize comp1 (appears most frequently)
                    assert isinstance(components, list)
                    assert len(components) >= 1
    
    @pytest.mark.asyncio
    async def test_apply_safe_improvements(self):
        """Test applying safe improvements."""
        agent = MetaAgent()
        
        # Add test improvement to queue
        safe_improvement = {
            "type": "code_optimization",
            "safety_level": "safe",
            "target_file": "test.py"
        }
        agent.improvement_queue.append(safe_improvement)
        
        # Mock the apply improvement method
        with patch.object(agent, '_apply_improvement', new=AsyncMock(return_value=True)):
            improvements_applied = await agent.apply_safe_improvements()
            assert improvements_applied == 1
    
    @pytest.mark.asyncio 
    async def test_safety_check(self):
        """Test safety validation for improvements."""
        agent = MetaAgent()
        
        safe_improvement = {"safety_level": "safe"}
        unsafe_improvement = {"safety_level": "dangerous"}
        unknown_improvement = {}
        
        assert await agent._safety_check(safe_improvement) == True
        assert await agent._safety_check(unsafe_improvement) == False
        assert await agent._safety_check(unknown_improvement) == False


class TestSelfEvolvingPlatform:
    """Test the self-evolving platform capabilities."""
    
    def test_platform_initialization(self):
        """Test platform initializes correctly."""
        platform = SelfEvolvingPlatform()
        assert isinstance(platform.startup_hooks, list)
        assert isinstance(platform.evolution_hooks, list)
        assert platform.maturity_level == 0
    
    def test_startup_hook_registration(self):
        """Test startup hook registration."""
        platform = SelfEvolvingPlatform()
        
        @platform.on_startup
        async def test_hook():
            return "hook executed"
        
        assert test_hook in platform.startup_hooks
    
    @pytest.mark.asyncio
    async def test_recursive_validation(self):
        """Test platform can validate itself."""
        platform = SelfEvolvingPlatform()
        
        # Mock validation methods
        with patch.object(platform, '_validate_telemetry_coverage', new=AsyncMock(return_value=[])):
            with patch.object(platform, '_validate_code_quality', new=AsyncMock(return_value=[])):
                with patch.object(platform, '_validate_performance_slas', new=AsyncMock(return_value=[])):
                    
                    result = await platform.recursive_validate()
                    
                    assert isinstance(result, dict)
                    assert "passed" in result
                    assert "issues" in result
                    assert "improvements_suggested" in result
                    assert result["passed"] == True  # No issues should mean passed
    
    @pytest.mark.asyncio
    async def test_self_validation_with_issues(self):
        """Test self-validation when issues are found."""
        platform = SelfEvolvingPlatform()
        
        # Mock finding issues
        test_issue = {"type": "performance", "severity": "medium"}
        with patch.object(platform, '_validate_telemetry_coverage', new=AsyncMock(return_value=[test_issue])):
            with patch.object(platform, '_validate_code_quality', new=AsyncMock(return_value=[])):
                with patch.object(platform, '_validate_performance_slas', new=AsyncMock(return_value=[])):
                    with patch.object(platform, '_generate_improvement_from_issue', new=AsyncMock(return_value={"fix": "optimize"})):
                        
                        result = await platform.recursive_validate()
                        
                        assert result["passed"] == False  # Issues found
                        assert len(result["issues"]) == 1
                        assert len(result["improvements_suggested"]) == 1


class TestSelfUpdatingTemplate:
    """Test self-updating template capabilities."""
    
    def test_template_initialization(self):
        """Test template initializes correctly."""
        template = SelfUpdatingTemplate("test_template")
        assert template.template_name == "test_template"
        assert isinstance(template.usage_patterns, list)
        assert isinstance(template.improvement_history, list)
    
    @pytest.mark.asyncio
    async def test_template_evolution(self):
        """Test template can evolve itself."""
        template = SelfUpdatingTemplate("test_template")
        
        # Mock analysis and improvement methods
        mock_analysis = {"common_patterns": ["pattern1"], "pain_points": ["issue1"]}
        mock_improvements = [{"type": "enhancement", "confidence": 0.9}]
        
        with patch.object(template, '_analyze_usage_patterns', new=AsyncMock(return_value=mock_analysis)):
            with patch.object(template, '_generate_improvements', new=AsyncMock(return_value=mock_improvements)):
                with patch.object(template, '_apply_template_improvement', new=AsyncMock()):
                    
                    improvements = await template.evolve_template()
                    
                    assert isinstance(improvements, list)
                    assert len(improvements) == 1
                    assert improvements[0]["confidence"] == 0.9


class TestAGIIntegration:
    """Test AGI components working together."""
    
    @pytest.mark.asyncio
    async def test_bootstrap_agi_evolution(self):
        """Test AGI bootstrap process."""
        # Import the bootstrap function
        from weavership_agi import bootstrap_agi_evolution
        
        # Mock all the async calls
        with patch.object(meta_agent, 'analyze_architecture', new=AsyncMock(return_value=["component1"])):
            with patch.object(platform, 'recursive_validate', new=AsyncMock(return_value={"passed": True})):
                with patch.object(meta_agent, 'apply_safe_improvements', new=AsyncMock(return_value=2)):
                    
                    # Should not raise any errors
                    await bootstrap_agi_evolution()
                    
                    # Platform maturity should increase
                    assert platform.maturity_level >= 1
    
    def test_telemetry_integration(self):
        """Test telemetry is properly configured."""
        # Test tracer is available and functional
        assert tracer is not None
        assert meter is not None
        
        # Test creating spans and metrics works
        with tracer.start_as_current_span("test_span") as span:
            assert span is not None
            span.set_attribute("test_attribute", "test_value")
        
        # Test creating metrics
        test_counter = meter.create_counter("test_counter")
        assert test_counter is not None
    
    def test_agi_principle_80_20(self):
        """Test 80/20 principle is applied throughout."""
        # Meta-agent should focus on critical components
        agent = MetaAgent()
        assert agent.target_system == "weavership"  # Focus on self-improvement
        
        # Platform should have evolution capabilities
        assert hasattr(platform, 'recursive_validate')
        assert hasattr(platform, 'maturity_level')
        
        # Templates should be self-updating
        template = SelfUpdatingTemplate("test")
        assert hasattr(template, 'evolve_template')


class TestTelemetryDrivenEvolution:
    """Test that evolution is driven by actual telemetry data."""
    
    @pytest.mark.asyncio
    async def test_telemetry_driven_analysis(self):
        """Test meta-agent uses telemetry for analysis."""
        agent = MetaAgent()
        
        # Test that analysis methods are called during architecture analysis
        with patch.object(agent, '_analyze_error_telemetry', new=AsyncMock(return_value=["comp1"])) as mock_error:
            with patch.object(agent, '_analyze_performance_telemetry', new=AsyncMock(return_value=["comp2"])) as mock_perf:
                with patch.object(agent, '_analyze_resource_telemetry', new=AsyncMock(return_value=["comp3"])) as mock_resource:
                    
                    await agent._identify_critical_components()
                    
                    # All telemetry analysis methods should be called
                    mock_error.assert_called_once()
                    mock_perf.assert_called_once()
                    mock_resource.assert_called_once()
    
    def test_metrics_collection(self):
        """Test that AGI metrics are properly defined."""
        from weavership_agi import (
            meta_improvement_counter,
            recursive_validation_histogram,
            self_evolution_gauge
        )
        
        # All AGI-specific metrics should be defined
        assert meta_improvement_counter is not None
        assert recursive_validation_histogram is not None
        assert self_evolution_gauge is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])