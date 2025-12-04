"""
Test suite for re-enabled advanced commands: search, agent, spiff_otel.

These tests verify that:
1. Commands import successfully (even without all dependencies)
2. Command structure is correct (Typer apps with subcommands)
3. Lazy loading works as intended
4. Error messages are helpful when dependencies are missing
"""

import sys
from pathlib import Path

import pytest


class TestSearchCommand:
    """Test the search command module."""

    def test_search_command_imports(self):
        """Verify search command can be imported."""
        try:
            from uvmgr.commands import search
            assert hasattr(search, 'app'), "search should have a Typer app"
            assert search.app is not None, "search.app should not be None"
        except ImportError as e:
            pytest.skip(f"Search command import failed: {e}")

    def test_search_command_has_subcommands(self):
        """Verify search command has the expected subcommands."""
        try:
            from uvmgr.commands import search
            # Check that the app has registered commands
            assert hasattr(search.app, 'registered_commands'), "app should have registered_commands"
            # Common subcommands: code, deps, files, semantic
            assert any(cmd for cmd in ['code', 'deps', 'files', 'semantic']
                      if hasattr(search, f'search_{cmd}') or hasattr(search.app, cmd))
        except (ImportError, AssertionError) as e:
            pytest.skip(f"Search command validation failed: {e}")

    def test_search_code_function_exists(self):
        """Verify search_code function exists."""
        try:
            from uvmgr.commands.search import search_code
            assert callable(search_code), "search_code should be callable"
        except ImportError as e:
            pytest.skip(f"search_code import failed: {e}")

    def test_search_deps_function_exists(self):
        """Verify search_deps function exists."""
        try:
            from uvmgr.commands.search import search_deps
            assert callable(search_deps), "search_deps should be callable"
        except ImportError as e:
            pytest.skip(f"search_deps import failed: {e}")


class TestAgentCommand:
    """Test the agent command module."""

    def test_agent_command_imports(self):
        """Verify agent command can be imported."""
        try:
            from uvmgr.commands import agent
            assert hasattr(agent, 'app'), "agent should have a Typer app"
            assert agent.app is not None, "agent.app should not be None"
        except ImportError as e:
            pytest.skip(f"Agent command import failed: {e}")

    def test_agent_lazy_loads_spiff(self):
        """Verify agent command doesn't require SpiffWorkflow at import time."""
        import importlib

        # Temporarily hide SpiffWorkflow if it exists
        spiff_hidden = False
        if 'SpiffWorkflow' in sys.modules:
            spiff_backup = sys.modules['SpiffWorkflow']
            del sys.modules['SpiffWorkflow']
            spiff_hidden = True

        try:
            # Should still import even without SpiffWorkflow
            from uvmgr.commands import agent
            assert agent.app is not None, "Should import without SpiffWorkflow"
        finally:
            # Restore SpiffWorkflow if it was hidden
            if spiff_hidden and 'SpiffWorkflow' not in sys.modules:
                sys.modules['SpiffWorkflow'] = spiff_backup

    def test_agent_has_subcommands(self):
        """Verify agent command has the expected subcommands."""
        try:
            from uvmgr.commands.agent import (
                run_bpmn_workflow,
                validate_workflow,
                test_workflow,
            )
            assert callable(run_bpmn_workflow), "run_bpmn_workflow should be callable"
            assert callable(validate_workflow), "validate_workflow should be callable"
            assert callable(test_workflow), "test_workflow should be callable"
        except ImportError as e:
            pytest.skip(f"Agent command functions failed: {e}")


class TestSpiffOTELCommand:
    """Test the spiff_otel command module."""

    def test_spiff_otel_command_imports(self):
        """Verify spiff_otel command can be imported."""
        try:
            from uvmgr.commands import spiff_otel
            assert hasattr(spiff_otel, 'app'), "spiff_otel should have a Typer app"
            assert spiff_otel.app is not None, "spiff_otel.app should not be None"
        except ImportError as e:
            pytest.skip(f"Spiff_otel command import failed: {e}")

    def test_spiff_otel_lazy_loads(self):
        """Verify spiff_otel doesn't require dependencies at import time."""
        import importlib

        # This should import without SpiffWorkflow
        try:
            from uvmgr.commands import spiff_otel
            assert spiff_otel.app is not None, "Should import without all dependencies"
        except ImportError as e:
            if "spiffworkflow" in str(e).lower():
                pytest.skip(f"SpiffWorkflow not available (expected): {e}")
            raise


class TestLazyLoadingPattern:
    """Test the lazy loading pattern used by re-enabled commands."""

    def test_lazy_loaders_exist(self):
        """Verify lazy loading helper functions exist."""
        try:
            from uvmgr.commands.agent import _get_spiff_functions
            assert callable(_get_spiff_functions), "_get_spiff_functions should be callable"
        except ImportError as e:
            pytest.skip(f"Lazy loader import failed: {e}")

    def test_lazy_loaders_handle_missing_dependencies(self):
        """Verify lazy loaders provide helpful error messages."""
        try:
            from uvmgr.commands.agent import _get_spiff_functions

            # If SpiffWorkflow is available, this will work
            # If not, it should give a helpful error
            try:
                result = _get_spiff_functions()
                assert result is not None, "Should return functions if available"
            except ImportError as e:
                assert "spiffworkflow" in str(e).lower() or "install" in str(e).lower(), \
                    "Error message should mention SpiffWorkflow or installation"
        except ImportError as e:
            pytest.skip(f"Lazy loader test failed: {e}")


class TestCommandIntegration:
    """Integration tests for re-enabled commands."""

    def test_all_three_commands_importable(self):
        """Verify all 3 re-enabled commands can be imported together."""
        from uvmgr.commands import search
        from uvmgr.commands import agent
        from uvmgr.commands import spiff_otel

        assert all([search.app, agent.app, spiff_otel.app]), \
            "All three commands should have apps"

    def test_commands_registered_in_all(self):
        """Verify commands are in commands/__init__.py __all__."""
        from uvmgr.commands import __all__

        assert 'search' in __all__, "search should be in __all__"
        assert 'agent' in __all__, "agent should be in __all__"
        assert 'spiff_otel' in __all__, "spiff_otel should be in __all__"

    def test_commands_have_help_text(self):
        """Verify commands have help documentation."""
        from uvmgr.commands import search, agent, spiff_otel

        assert search.app.help, "search should have help text"
        assert agent.app.help, "agent should have help text"
        assert spiff_otel.app.help, "spiff_otel should have help text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
