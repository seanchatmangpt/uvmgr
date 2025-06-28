"""Test weavership_agi imports and basic functionality."""

import weavership_agi


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(weavership_agi.__name__, str)
    assert weavership_agi.__version__ == "2.0.0"


def test_core_agi_components() -> None:
    """Test that core AGI components are available."""
    # Test MetaAgent is available
    assert hasattr(weavership_agi, 'MetaAgent')
    assert hasattr(weavership_agi, 'SelfEvolvingPlatform')
    assert hasattr(weavership_agi, 'SelfUpdatingTemplate')
    
    # Test instances are created
    assert hasattr(weavership_agi, 'platform')
    assert hasattr(weavership_agi, 'meta_agent')
    
    # Test telemetry is configured
    assert hasattr(weavership_agi, 'tracer')
    assert hasattr(weavership_agi, 'meter')


def test_agi_platform_initialization() -> None:
    """Test that AGI platform initializes correctly."""
    platform = weavership_agi.platform
    assert platform.maturity_level >= 0
    assert isinstance(platform.startup_hooks, list)
    assert isinstance(platform.evolution_hooks, list)


def test_meta_agent_initialization() -> None:
    """Test that meta-agent initializes correctly."""
    meta_agent = weavership_agi.meta_agent
    assert meta_agent.target_system == "weavership"
    assert meta_agent.safety_level == "high"
    assert isinstance(meta_agent.improvement_queue, list)
    assert meta_agent.maturity_level >= 0
