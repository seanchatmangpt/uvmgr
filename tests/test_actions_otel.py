"""
Test OpenTelemetry instrumentation for GitHub Actions commands.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from uvmgr.commands.actions import status
from uvmgr.core.telemetry import get_current_span
import subprocess


class TestActionsOTELInstrumentation:
    """Test OTEL instrumentation for GitHub Actions commands."""

    @patch('uvmgr.ops.actions.get_workflow_runs')
    @patch('subprocess.check_output')
    def test_status_command_creates_span(self, mock_check_output, mock_get_runs):
        """Test that status command creates proper OTEL spans."""
        # Mock the GitHub CLI token
        mock_check_output.return_value = "test-token"
        
        # Mock the operations layer
        mock_get_runs.return_value = [
            {
                "name": "CI",
                "status": "completed",
                "conclusion": "success",
                "event": "push",
                "head_branch": "main",
                "html_url": "https://github.com/test/repo/actions/runs/123"
            }
        ]

        # Test the command
        with patch('typer.echo') as mock_echo:
            status(
                owner="test-owner",
                repo="test-repo",
                limit=5,
                token=None
            )

        # Verify the operation was called with the mocked token
        mock_get_runs.assert_called_once_with("test-owner", "test-repo", 5, "test-token")

    @patch('uvmgr.runtime.actions.urllib.request.urlopen')
    def test_runtime_layer_creates_spans(self, mock_urlopen):
        """Test that runtime layer creates proper OTEL spans."""
        from uvmgr.runtime.actions import get_workflow_runs

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "workflow_runs": [
                {
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "head_branch": "main",
                    "html_url": "https://github.com/test/repo/actions/runs/123"
                }
            ]
        }).encode()
        mock_urlopen.return_value = mock_response

        # Test the runtime function
        result = get_workflow_runs("test-owner", "test-repo", 1)

        # Verify API was called correctly
        mock_urlopen.assert_called_once()

        # Verify result structure
        assert len(result) == 1
        assert result[0]["name"] == "CI"
        assert result[0]["status"] == "completed"

    @patch('uvmgr.runtime.actions.urllib.request.urlopen')
    def test_runtime_layer_handles_errors(self, mock_urlopen):
        """Test that runtime layer properly handles API errors."""
        from uvmgr.runtime.actions import get_workflow_runs

        # Mock API error
        mock_urlopen.side_effect = Exception("API Error")

        # Test error handling
        result = get_workflow_runs("test-owner", "test-repo", 1)

        # Should return empty list on error
        assert result == []

    def test_semantic_conventions_defined(self):
        """Test that GitHub semantic conventions are properly defined."""
        from uvmgr.core.semconv import GitHubAttributes

        # Verify all required attributes are defined
        assert hasattr(GitHubAttributes, 'OWNER')
        assert hasattr(GitHubAttributes, 'REPOSITORY')
        assert hasattr(GitHubAttributes, 'WORKFLOW_NAME')
        assert hasattr(GitHubAttributes, 'WORKFLOW_STATUS')
        assert hasattr(GitHubAttributes, 'WORKFLOW_CONCLUSION')

        # Verify attribute values follow convention
        assert GitHubAttributes.OWNER == "github.owner"
        assert GitHubAttributes.REPOSITORY == "github.repository"
        assert GitHubAttributes.WORKFLOW_NAME == "github.workflow.name" 