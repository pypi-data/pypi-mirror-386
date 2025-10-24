"""httpx.Auth adapter that acquires tokens via TokenManager."""

from __future__ import annotations

import httpx

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_agent.oauth.manager import TokenManager
    from mcp_agent.core.context import Context
    from mcp_agent.oauth.identity import OAuthUserIdentity


class OAuthHttpxAuth(httpx.Auth):
    requires_request_body = True

    def __init__(
        self,
        *,
        token_manager: "TokenManager",
        context: "Context",
        server_name: str,
        server_config,
        scopes=None,
        identity_resolver: Callable[[], "OAuthUserIdentity | None"] | None = None,
    ) -> None:
        self._token_manager = token_manager
        self._context = context
        self._server_name = server_name
        self._server_config = server_config
        self._scopes = list(scopes) if scopes is not None else None
        self._identity_resolver = identity_resolver

    async def async_auth_flow(self, request: httpx.Request):
        identity = None
        if self._identity_resolver is not None:
            identity = self._identity_resolver()
        else:
            try:
                from mcp_agent.server import app_server

                identity = app_server.get_current_identity()
            except Exception:
                identity = None

        try:
            token_record = await self._token_manager.ensure_access_token(
                context=self._context,
                server_name=self._server_name,
                server_config=self._server_config,
                scopes=self._scopes,
                identity=identity,
            )
        except Exception:
            raise
        request.headers["Authorization"] = (
            f"{token_record.token_type} {token_record.access_token}"
        )
        response = yield request

        if response.status_code != 401:
            return

        if identity is None:
            try:
                from mcp_agent.server import app_server

                identity = app_server.get_current_identity()
            except Exception:
                identity = None
        if identity is None:
            from mcp_agent.oauth.identity import DEFAULT_PRECONFIGURED_IDENTITY

            identity = DEFAULT_PRECONFIGURED_IDENTITY
        if identity is None:
            return

        await self._token_manager.invalidate(
            identity=identity,
            resource=token_record.resource or "",
            authorization_server=token_record.authorization_server,
            scopes=token_record.scopes,
        )

        refreshed_record = await self._token_manager.ensure_access_token(
            context=self._context,
            server_name=self._server_name,
            server_config=self._server_config,
            scopes=self._scopes,
            identity=identity,
        )

        # Create a new request with the refreshed token. Using copy() preserves the original body.
        retry_request = request.copy()
        retry_request.headers["Authorization"] = (
            f"{refreshed_record.token_type} {refreshed_record.access_token}"
        )
        yield retry_request
