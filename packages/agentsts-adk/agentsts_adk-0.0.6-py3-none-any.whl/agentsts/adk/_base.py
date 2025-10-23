"""Google ADK-specific STS integration."""

import logging
from typing import Any, Dict, Optional

from agentsts.core import STSIntegrationBase, TokenType
from google.adk.agents.invocation_context import InvocationContext
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, HttpAuth, HttpCredentials
from google.adk.events.event import Event
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService
from google.adk.sessions.session import Session
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.mcp_tool import MCPTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.tool_context import ToolContext
from typing_extensions import override

logger = logging.getLogger(__name__)

HEADERS_KEY = "headers"


class ADKSTSIntegration(STSIntegrationBase):
    """Google ADK-specific STS integration."""

    def __init__(
        self,
        well_known_uri: str,
        service_account_token_path: Optional[str] = None,
        timeout: int = 5,
        verify_ssl: bool = True,
        additional_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(well_known_uri, service_account_token_path, timeout, verify_ssl, additional_config)

    def create_auth_credential(self, access_token: str) -> AuthCredential:
        return _create_adk_auth_credential(access_token)

    async def get_auth_credential(
        self,
        subject_token: str,
        subject_token_type: TokenType = TokenType.JWT,
    ) -> AuthCredential:
        access_token = await self.exchange_token(
            subject_token,
            subject_token_type,
            actor_token=self._actor_token,
            actor_token_type=TokenType.JWT if self._actor_token else None,
        )
        return self.create_auth_credential(access_token)


class ADKTokenPropagationPlugin(BasePlugin):
    """Plugin for propagating STS tokens to ADK tools."""

    def __init__(self, sts_integration: Optional[ADKSTSIntegration] = None):
        """Initialize the token propagation plugin.

        Args:
            sts_integration: The ADK STS integration instance
        """
        super().__init__("ADKTokenPropagationPlugin")
        self.sts_integration = sts_integration

    @override
    async def before_run_callback(
        self,
        *,
        invocation_context: InvocationContext,
    ) -> Optional[dict]:
        """Propagate token to model before execution."""
        headers = invocation_context.session.state.get(HEADERS_KEY, None)
        subject_token = _extract_jwt_from_headers(headers)
        agent = invocation_context.agent
        if subject_token and self.sts_integration is not None:
            try:
                access_token = await self.sts_integration.exchange_token(
                    subject_token,
                    TokenType.JWT,
                    actor_token=self.sts_integration._actor_token,
                    actor_token_type=TokenType.JWT if self.sts_integration._actor_token else None,
                )
                logger.debug(f"Got Access token from STS server with length: {len(access_token)}")
                for tool in agent.tools:
                    if isinstance(tool, MCPToolset):
                        if tool._connection_params.headers is None:
                            tool._connection_params.headers = {}
                        tool._connection_params.headers["Authorization"] = f"Bearer {access_token}"
                        logger.debug("Updated tool connection params to include access token from STS server")
            except Exception as e:
                logger.warning(f"Token exchange failed for tool: {e}")
                return None
        else:
            logger.debug("No subject token available to be propagated to tool connection params")

        return None

    @override
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> Optional[dict]:
        """Propagate token to MCP tools before execution.

        Args:
            tool: The tool being executed
            tool_args: Arguments for the tool
            tool_context: Context for the tool execution

        Returns:
            Modified tool arguments with credential if applicable
        """
        if isinstance(tool, MCPTool):
            headers = tool_context._invocation_context.session.state.get(HEADERS_KEY, None)
            subject_token = _extract_jwt_from_headers(headers)
            if subject_token and self.sts_integration is not None:
                try:
                    credential = await self.sts_integration.get_auth_credential(subject_token=subject_token)
                    logger.debug("Propagating STS token in ADK tool call: %s", tool.name)
                    return await tool._run_async_impl(args=tool_args, tool_context=tool_context, credential=credential)
                except Exception as e:
                    logger.error(f"Token exchange failed for tool {tool.name}: {e}")
                    return None

        return None


def _create_adk_auth_credential(access_token: str) -> AuthCredential:
    credential = AuthCredential(
        auth_type=AuthCredentialTypes.HTTP,
        http=HttpAuth(
            scheme="bearer",
            credentials=HttpCredentials(token=access_token),
        ),
    )

    return credential


def _extract_jwt_from_headers(headers: dict[str, str]) -> Optional[str]:
    """Extract JWT from request headers for STS token exchange.

    Args:
        headers: Dictionary of request headers

    Returns:
        JWT token string if found in Authorization header, None otherwise
    """
    if not headers:
        logger.warning("No headers provided for JWT extraction")
        return None

    auth_header = headers.get("Authorization") or headers.get("authorization")
    if not auth_header:
        logger.warning("No Authorization header found in request")
        return None

    if not auth_header.startswith("Bearer "):
        logger.warning("Authorization header must start with Bearer")
        return None

    jwt_token = auth_header.removeprefix("Bearer ").strip()
    if not jwt_token:
        logger.warning("Empty JWT token found in Authorization header")
        return None

    logger.debug(f"Successfully extracted JWT token (length: {len(jwt_token)})")
    return jwt_token
