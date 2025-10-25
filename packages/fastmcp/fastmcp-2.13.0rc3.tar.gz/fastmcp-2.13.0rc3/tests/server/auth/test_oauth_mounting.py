"""Tests for OAuth .well-known routes when FastMCP apps are mounted in parent ASGI apps.

This test file validates the fix for issue #2077 where .well-known/oauth-protected-resource
returns 404 at root level when a FastMCP app is mounted under a path prefix.

The fix uses MCP SDK 1.17+ which implements RFC 9728 path-scoped well-known URLs.
"""

import httpx
import pytest
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.routing import Mount

from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier


@pytest.fixture
def test_tokens():
    """Standard test tokens fixture."""
    return {
        "test_token": {
            "client_id": "test-client",
            "scopes": ["read", "write"],
        }
    }


class TestOAuthMounting:
    """Test OAuth .well-known routes with mounted FastMCP apps."""

    async def test_well_known_with_direct_deployment(self, test_tokens):
        """Test that .well-known routes work when app is deployed directly (not mounted).

        This is the baseline - it should work as expected.
        Per RFC 9728, if the resource is at /mcp, the well-known endpoint is at
        /.well-known/oauth-protected-resource/mcp (path-scoped).
        """
        token_verifier = StaticTokenVerifier(tokens=test_tokens)
        auth_provider = RemoteAuthProvider(
            token_verifier=token_verifier,
            authorization_servers=[AnyHttpUrl("https://auth.example.com")],
            base_url="https://api.example.com",
        )

        mcp = FastMCP("test-server", auth=auth_provider)
        mcp_app = mcp.http_app()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=mcp_app),
            base_url="https://api.example.com",
        ) as client:
            # RFC 9728: path-scoped well-known URL
            # Resource is at /mcp, so well-known should be at /.well-known/oauth-protected-resource/mcp
            response = await client.get("/.well-known/oauth-protected-resource/mcp")
            assert response.status_code == 200

            data = response.json()
            assert data["resource"] == "https://api.example.com/mcp"
            assert data["authorization_servers"] == ["https://auth.example.com/"]

    async def test_well_known_with_mounted_app(self, test_tokens):
        """Test that .well-known routes work when explicitly mounted at root.

        This test uses the CANONICAL pattern for mounting:
        - base_url includes the mount prefix ("/api")
        - mcp_path is just the internal MCP path ("/mcp")
        - These combine: base_url + mcp_path = actual URL

        The well-known routes are mounted at root level for RFC 9728 compliance.
        """
        token_verifier = StaticTokenVerifier(tokens=test_tokens)
        # CANONICAL PATTERN: base_url includes the mount prefix
        auth_provider = RemoteAuthProvider(
            token_verifier=token_verifier,
            authorization_servers=[AnyHttpUrl("https://auth.example.com")],
            base_url="https://api.example.com/api",  # Includes /api mount prefix
        )

        mcp = FastMCP("test-server", auth=auth_provider)
        mcp_app = mcp.http_app(path="/mcp")

        # Pass just the internal mcp_path, NOT the full mount path
        # The auth provider will combine base_url + mcp_path internally
        well_known_routes = auth_provider.get_well_known_routes(mcp_path="/mcp")

        parent_app = Starlette(
            routes=[
                *well_known_routes,  # Well-known routes at root level
                Mount("/api", app=mcp_app),  # MCP app under /api
            ],
            lifespan=mcp_app.lifespan,
        )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=parent_app),
            base_url="https://api.example.com",
        ) as client:
            # The CORRECT RFC 9728 path-scoped well-known URL at root
            # Resource is at /api/mcp, so well-known is at /.well-known/oauth-protected-resource/api/mcp
            response = await client.get("/.well-known/oauth-protected-resource/api/mcp")
            assert response.status_code == 200

            data = response.json()
            assert data["resource"] == "https://api.example.com/api/mcp"
            assert data["authorization_servers"] == ["https://auth.example.com/"]

            # There will also be an extra route at /api/.well-known/oauth-protected-resource/mcp
            # (from the mounted MCP app), but we don't care about that as long as the correct one exists

    async def test_mcp_endpoint_with_mounted_app(self, test_tokens):
        """Test that MCP endpoint works correctly when mounted.

        This confirms the MCP functionality itself works with mounting.
        """
        token_verifier = StaticTokenVerifier(tokens=test_tokens)
        auth_provider = RemoteAuthProvider(
            token_verifier=token_verifier,
            authorization_servers=[AnyHttpUrl("https://auth.example.com")],
            base_url="https://api.example.com",
        )

        mcp = FastMCP("test-server", auth=auth_provider)

        @mcp.tool
        def test_tool(message: str) -> str:
            return f"Echo: {message}"

        mcp_app = mcp.http_app(path="/mcp")

        # Mount the MCP app under /api prefix
        parent_app = Starlette(
            routes=[
                Mount("/api", app=mcp_app),
            ],
            lifespan=mcp_app.lifespan,
        )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=parent_app),
            base_url="https://api.example.com",
        ) as client:
            # The MCP endpoint should work at /api/mcp (mounted correctly)
            # This is a basic connectivity test
            response = await client.get("/api/mcp")

            # We expect either 200 (if no auth required for GET) or 401 (if auth required)
            # The key is that it's NOT 404
            assert response.status_code in [200, 401, 405]

    async def test_nested_mounting(self, test_tokens):
        """Test .well-known routes with deeply nested mounts.

        Uses CANONICAL pattern: base_url includes all mount prefixes.
        """
        token_verifier = StaticTokenVerifier(tokens=test_tokens)
        # CANONICAL PATTERN: base_url includes full mount path /outer/inner
        auth_provider = RemoteAuthProvider(
            token_verifier=token_verifier,
            authorization_servers=[AnyHttpUrl("https://auth.example.com")],
            base_url="https://api.example.com/outer/inner",  # Includes nested mount path
        )

        mcp = FastMCP("test-server", auth=auth_provider)
        mcp_app = mcp.http_app(path="/mcp")

        # Pass just the internal mcp_path
        well_known_routes = auth_provider.get_well_known_routes(mcp_path="/mcp")

        # Create nested mounts
        inner_app = Starlette(
            routes=[Mount("/inner", app=mcp_app)],
        )
        outer_app = Starlette(
            routes=[
                *well_known_routes,  # Well-known routes at root level
                Mount("/outer", app=inner_app),
            ],
            lifespan=mcp_app.lifespan,
        )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=outer_app),
            base_url="https://api.example.com",
        ) as client:
            # RFC 9728: path-scoped well-known URL for nested mounting
            # Resource is at /outer/inner/mcp, so well-known is at /.well-known/oauth-protected-resource/outer/inner/mcp
            response = await client.get(
                "/.well-known/oauth-protected-resource/outer/inner/mcp"
            )
            assert response.status_code == 200

            data = response.json()
            assert data["resource"] == "https://api.example.com/outer/inner/mcp"
