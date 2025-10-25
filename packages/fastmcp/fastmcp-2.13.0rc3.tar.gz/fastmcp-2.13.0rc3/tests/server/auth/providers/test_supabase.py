"""Tests for Supabase Auth provider."""

import os
from collections.abc import Generator
from unittest.mock import patch

import httpx
import pytest

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.server.auth.providers.supabase import SupabaseProvider
from fastmcp.utilities.tests import HeadlessOAuth, run_server_in_process


class TestSupabaseProvider:
    """Test Supabase Auth provider functionality."""

    def test_init_with_explicit_params(self):
        """Test SupabaseProvider initialization with explicit parameters."""
        provider = SupabaseProvider(
            project_url="https://abc123.supabase.co",
            base_url="https://myserver.com",
        )

        assert provider.project_url == "https://abc123.supabase.co"
        assert str(provider.base_url) == "https://myserver.com/"

    @pytest.mark.parametrize(
        "scopes_env",
        [
            "openid,email",
            '["openid", "email"]',
        ],
    )
    def test_init_with_env_vars(self, scopes_env):
        """Test SupabaseProvider initialization from environment variables."""
        with patch.dict(
            os.environ,
            {
                "FASTMCP_SERVER_AUTH_SUPABASE_PROJECT_URL": "https://env123.supabase.co",
                "FASTMCP_SERVER_AUTH_SUPABASE_BASE_URL": "https://envserver.com",
            },
        ):
            provider = SupabaseProvider()

            assert provider.project_url == "https://env123.supabase.co"
            assert str(provider.base_url) == "https://envserver.com/"

    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        provider = SupabaseProvider(
            project_url="https://env123.supabase.co",
            base_url="http://env-server.com",
        )

        assert provider.project_url == "https://env123.supabase.co"
        assert str(provider.base_url) == "http://env-server.com/"

    def test_project_url_normalization(self):
        """Test that project_url handles trailing slashes correctly."""
        # Without trailing slash
        provider1 = SupabaseProvider(
            project_url="https://abc123.supabase.co",
            base_url="https://myserver.com",
        )
        assert provider1.project_url == "https://abc123.supabase.co"

        # With trailing slash - should be stripped
        provider2 = SupabaseProvider(
            project_url="https://abc123.supabase.co/",
            base_url="https://myserver.com",
        )
        assert provider2.project_url == "https://abc123.supabase.co"

    def test_jwt_verifier_configured_correctly(self):
        """Test that JWT verifier is configured correctly."""
        provider = SupabaseProvider(
            project_url="https://abc123.supabase.co",
            base_url="https://myserver.com",
        )

        # Check that JWT verifier uses the correct endpoints
        assert (
            provider.token_verifier.jwks_uri  # type: ignore[attr-defined]
            == "https://abc123.supabase.co/auth/v1/.well-known/jwks.json"
        )
        assert (
            provider.token_verifier.issuer == "https://abc123.supabase.co/auth/v1"  # type: ignore[attr-defined]
        )
        assert provider.token_verifier.algorithm == "ES256"  # type: ignore[attr-defined]

    def test_jwt_verifier_with_required_scopes(self):
        """Test that JWT verifier respects required_scopes."""
        provider = SupabaseProvider(
            project_url="https://abc123.supabase.co",
            base_url="https://myserver.com",
            required_scopes=["openid", "email"],
        )

        assert provider.token_verifier.required_scopes == ["openid", "email"]  # type: ignore[attr-defined]

    def test_authorization_servers_configured(self):
        """Test that authorization servers list is configured correctly."""
        provider = SupabaseProvider(
            project_url="https://abc123.supabase.co",
            base_url="https://myserver.com",
        )

        assert len(provider.authorization_servers) == 1
        assert (
            str(provider.authorization_servers[0])
            == "https://abc123.supabase.co/auth/v1"
        )


def run_mcp_server(host: str, port: int) -> None:
    mcp = FastMCP(
        auth=SupabaseProvider(
            project_url="https://test123.supabase.co",
            base_url="http://localhost:4321",
        )
    )

    @mcp.tool
    def add(a: int, b: int) -> int:
        return a + b

    mcp.run(host=host, port=port, transport="http")


@pytest.fixture
def mcp_server_url() -> Generator[str]:
    with run_server_in_process(run_mcp_server) as url:
        yield f"{url}/mcp"


@pytest.fixture()
def client_with_headless_oauth(
    mcp_server_url: str,
) -> Generator[Client, None, None]:
    """Client with headless OAuth that bypasses browser interaction."""
    client = Client(
        transport=StreamableHttpTransport(mcp_server_url),
        auth=HeadlessOAuth(mcp_url=mcp_server_url),
    )
    yield client


class TestSupabaseProviderIntegration:
    async def test_unauthorized_access(self, mcp_server_url: str):
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            async with Client(mcp_server_url) as client:
                tools = await client.list_tools()  # noqa: F841

        assert isinstance(exc_info.value, httpx.HTTPStatusError)
        assert exc_info.value.response.status_code == 401
        assert "tools" not in locals()

    # async def test_authorized_access(self, client_with_headless_oauth: Client):
    #     async with client_with_headless_oauth:
    #         tools = await client_with_headless_oauth.list_tools()
    #     assert tools is not None
    #     assert len(tools) > 0
    #     assert "add" in tools
