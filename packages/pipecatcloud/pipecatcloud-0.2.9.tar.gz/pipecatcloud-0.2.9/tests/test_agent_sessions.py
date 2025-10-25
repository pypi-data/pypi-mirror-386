"""
Unit tests for the 'pcc agent sessions' command.

Tests focus on core behaviors and edge cases, not implementation details.
"""

import pytest
from unittest.mock import patch
import typer

# Import the function under test from local source
from src.pipecatcloud.cli.commands.agent import sessions

# Test constants
TEST_ORG = "test-org"
TEST_AGENT = "test-agent"


class TestAgentSessionsCommand:
    """Test the 'pcc agent sessions' command behaviors."""

    @pytest.fixture
    def mock_api(self):
        """Mock the underlying API agent_sessions method."""
        with patch('src.pipecatcloud.cli.commands.agent.API._agent_sessions') as mock_api:
            yield mock_api

    def test_handles_zero_sessions_without_crash(self, mock_api):
        """Agent with zero sessions should not cause ZeroDivisionError."""
        # Arrange: API returns empty sessions list
        empty_sessions_response = {"sessions": []}
        mock_api.return_value = empty_sessions_response
        
        # Act & Assert: Should complete without ZeroDivisionError
        sessions(
            deploy_config=None,
            agent_name=TEST_AGENT,
            session_id=None, 
            organization=TEST_ORG
        )

    def test_handles_api_error_gracefully(self, mock_api):
        """API errors should be handled without crashing.""" 
        # Arrange: _agent_sessions raises exception (API error)
        mock_api.side_effect = Exception("Agent not found")
        
        # Act: Call with API error  
        result = sessions(
            deploy_config=None,
            agent_name="nonexistent-agent",
            session_id=None,
            organization=TEST_ORG
        )
        
        # Assert: Should return typer.Exit on error
        assert isinstance(result, type(typer.Exit()))

    def test_handles_missing_agent_name_gracefully(self):
        """Command should exit gracefully when no agent name is provided."""
        # Act: Call with no agent name from either source
        result = sessions(
            deploy_config=None,  # No deploy config
            agent_name=None,     # No agent name argument
            session_id=None,
            organization=TEST_ORG
        )
        
        # Assert: Should return typer.Exit(1) with error message
        assert isinstance(result, type(typer.Exit()))
        assert result.exit_code == 1