"""Tests for ADK integration classes."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from agentsts.core import TokenType
from google.adk.tools.mcp_tool import MCPTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

from agentsts.adk import (
    ADKSTSIntegration,
    ADKTokenPropagationPlugin,
)
from agentsts.adk._base import HEADERS_KEY
from agentsts.adk._base import _extract_jwt_from_headers as extract_jwt_from_headers


class TestADKTokenPropagationPlugin:
    """Test cases for ADKTokenPropagationPlugin."""

    def test_init(self):
        """Test plugin initialization."""
        mock_sts_integration = Mock()
        plugin = ADKTokenPropagationPlugin(mock_sts_integration)

        assert plugin.name == "ADKTokenPropagationPlugin"
        assert plugin.sts_integration == mock_sts_integration

    @pytest.mark.asyncio
    async def test_before_tool_callback_with_mcp_tool(self):
        """Test before_tool_callback with MCPTool."""
        mock_sts_integration = Mock()
        mock_credential = Mock()
        mock_sts_integration.get_auth_credential = AsyncMock(return_value=mock_credential)

        plugin = ADKTokenPropagationPlugin(mock_sts_integration)

        # Create mock MCPTool
        mock_tool = Mock(spec=MCPTool)
        mock_tool.name = "test-mcp-tool"
        mock_tool._run_async_impl = AsyncMock(return_value="tool_result")

        # Create mock tool context with session state
        mock_tool_context = Mock()
        mock_tool_context._invocation_context.session.state = {
            HEADERS_KEY: {"Authorization": "Bearer subject-token-123"}
        }

        tool_args = {"arg1": "value1"}

        result = await plugin.before_tool_callback(tool=mock_tool, tool_args=tool_args, tool_context=mock_tool_context)

        mock_sts_integration.get_auth_credential.assert_called_once_with(subject_token="subject-token-123")
        mock_tool._run_async_impl.assert_called_once_with(
            args=tool_args, tool_context=mock_tool_context, credential=mock_credential
        )
        assert result == "tool_result"

    @pytest.mark.asyncio
    async def test_before_tool_callback_with_non_mcp_tool(self):
        """Test before_tool_callback with non-MCPTool."""
        mock_sts_integration = Mock()
        plugin = ADKTokenPropagationPlugin(mock_sts_integration)

        # Create mock non-MCPTool
        mock_tool = Mock()
        mock_tool.name = "test-tool"

        mock_tool_context = Mock()
        tool_args = {"arg1": "value1"}

        result = await plugin.before_tool_callback(tool=mock_tool, tool_args=tool_args, tool_context=mock_tool_context)

        mock_sts_integration.get_auth_credential.assert_not_called()
        assert result is None

    @pytest.mark.asyncio
    async def test_before_tool_callback_no_subject_token(self):
        """Test before_tool_callback when no subject token in session state."""
        mock_sts_integration = Mock()
        mock_sts_integration.get_auth_credential = AsyncMock(return_value=None)

        plugin = ADKTokenPropagationPlugin(mock_sts_integration)

        mock_tool = Mock(spec=MCPTool)
        mock_tool.name = "test-mcp-tool"
        mock_tool._run_async_impl = AsyncMock()

        mock_tool_context = Mock()
        mock_tool_context._invocation_context.session.state = {}  # No headers

        tool_args = {"arg1": "value1"}

        with patch("agentsts.adk._base.logger") as mock_logger:
            result = await plugin.before_tool_callback(
                tool=mock_tool, tool_args=tool_args, tool_context=mock_tool_context
            )

            mock_logger.warning.assert_called_once_with("No headers provided for JWT extraction")
            assert result is None

    @pytest.mark.asyncio
    async def test_before_run_callback_with_headers(self):
        """Test before_run_callback with headers in session state."""
        mock_sts_integration = Mock()
        mock_sts_integration.exchange_token = AsyncMock(return_value="access-token-123")
        mock_sts_integration._actor_token = "actor-token"

        plugin = ADKTokenPropagationPlugin(mock_sts_integration)

        # Create mock invocation context with session state containing headers
        mock_invocation_context = Mock()
        mock_invocation_context.session.state = {HEADERS_KEY: {"Authorization": "Bearer subject-token-123"}}

        # Create mock agent with MCPToolset
        mock_tool = Mock(spec=MCPToolset)
        mock_tool._connection_params = Mock()
        mock_tool._connection_params.headers = {}
        mock_invocation_context.agent.tools = [mock_tool]

        result = await plugin.before_run_callback(invocation_context=mock_invocation_context)

        mock_sts_integration.exchange_token.assert_called_once_with(
            "subject-token-123",
            TokenType.JWT,
            actor_token="actor-token",
            actor_token_type=TokenType.JWT,
        )
        assert mock_tool._connection_params.headers["Authorization"] == "Bearer access-token-123"
        assert result is None

    @pytest.mark.asyncio
    async def test_before_run_callback_no_headers(self):
        """Test before_run_callback when no headers in session state."""
        mock_sts_integration = Mock()
        plugin = ADKTokenPropagationPlugin(mock_sts_integration)

        # Create mock invocation context with empty session state
        mock_invocation_context = Mock()
        mock_invocation_context.session.state = {}

        with patch("agentsts.adk._base.logger") as mock_logger:
            result = await plugin.before_run_callback(invocation_context=mock_invocation_context)

            mock_logger.debug.assert_called_once_with(
                "No subject token available to be propagated to tool connection params"
            )
            assert result is None

    def test_extract_jwt_from_headers_success(self):
        """Test successful JWT extraction from headers."""
        headers = {"Authorization": "Bearer jwt-token-123"}

        with patch("agentsts.adk._base.logger") as mock_logger:
            result = extract_jwt_from_headers(headers)

            assert result == "jwt-token-123"
            mock_logger.debug.assert_called_once()

    def test_extract_jwt_from_headers_no_headers(self):
        """Test JWT extraction with no headers."""
        with patch("agentsts.adk._base.logger") as mock_logger:
            result = extract_jwt_from_headers({})

            assert result is None
            mock_logger.warning.assert_called_once_with("No headers provided for JWT extraction")

    def test_extract_jwt_from_headers_no_auth_header(self):
        """Test JWT extraction with no Authorization header."""
        headers = {"Other-Header": "value"}

        with patch("agentsts.adk._base.logger") as mock_logger:
            result = extract_jwt_from_headers(headers)

            assert result is None
            mock_logger.warning.assert_called_once_with("No Authorization header found in request")

    def test_extract_jwt_from_headers_invalid_bearer(self):
        """Test JWT extraction with invalid Bearer format."""
        headers = {"Authorization": "Basic jwt-token-123"}

        with patch("agentsts.adk._base.logger") as mock_logger:
            result = extract_jwt_from_headers(headers)

            assert result is None
            mock_logger.warning.assert_called_once_with("Authorization header must start with Bearer")

    def test_extract_jwt_from_headers_empty_token(self):
        """Test JWT extraction with empty token."""
        headers = {"Authorization": "Bearer "}

        with patch("agentsts.adk._base.logger") as mock_logger:
            result = extract_jwt_from_headers(headers)

            assert result is None
            mock_logger.warning.assert_called_once_with("Empty JWT token found in Authorization header")

    def test_extract_jwt_from_headers_whitespace_token(self):
        """Test JWT extraction with whitespace-only token."""
        headers = {"Authorization": "Bearer   \n\t  "}

        with patch("agentsts.adk._base.logger") as mock_logger:
            result = extract_jwt_from_headers(headers)

            assert result is None
            mock_logger.warning.assert_called_once_with("Empty JWT token found in Authorization header")

    def test_extract_jwt_from_headers_stripped_token(self):
        """Test JWT extraction with token that has whitespace."""
        headers = {"Authorization": "Bearer  jwt-token-123  \n"}

        with patch("agentsts.adk._base.logger") as mock_logger:
            result = extract_jwt_from_headers(headers)

            assert result == "jwt-token-123"
            mock_logger.debug.assert_called_once()


class TestADKSTSIntegration:
    """Test cases for ADKSTSIntegration."""

    @pytest.mark.asyncio
    async def test_get_auth_credential_with_actor_token(self):
        """Test that get_auth_credential calls exchange_token with actor token."""

        adk_integration = ADKSTSIntegration("https://example.com/.well-known/oauth-authorization-server")

        adk_integration._actor_token = "system:serviceaccount:default:example-agent"
        adk_integration.exchange_token = AsyncMock(return_value="mock-delegation-token")
        adk_integration.create_auth_credential = Mock(return_value="mock-auth-credential")

        result = await adk_integration.get_auth_credential("mock-subject-token")

        # Verify exchange_token was called with actor token
        adk_integration.exchange_token.assert_called_once_with(
            "mock-subject-token",
            TokenType.JWT,
            actor_token="system:serviceaccount:default:example-agent",
            actor_token_type=TokenType.JWT,
        )

        # Verify create_auth_credential was called with the returned access token
        adk_integration.create_auth_credential.assert_called_once_with("mock-delegation-token")

        assert result == "mock-auth-credential"

    @pytest.mark.asyncio
    async def test_get_auth_credential_without_actor_token(self):
        """Test that get_auth_credential calls exchange_token without actor token when none is set."""

        # Create ADKSTSIntegration instance without actor token
        adk_integration = ADKSTSIntegration("https://example.com/.well-known/oauth-authorization-server")

        # Manually set the actor token to None and mock the methods
        adk_integration._actor_token = None
        adk_integration.exchange_token = AsyncMock(return_value="mock-impersonation-token")
        adk_integration.create_auth_credential = Mock(return_value="mock-auth-credential")

        result = await adk_integration.get_auth_credential("mock-subject-token")

        # Verify exchange_token was called without actor token
        adk_integration.exchange_token.assert_called_once_with(
            "mock-subject-token", TokenType.JWT, actor_token=None, actor_token_type=None
        )

        # Verify create_auth_credential was called with the returned access token
        adk_integration.create_auth_credential.assert_called_once_with("mock-impersonation-token")

        assert result == "mock-auth-credential"
