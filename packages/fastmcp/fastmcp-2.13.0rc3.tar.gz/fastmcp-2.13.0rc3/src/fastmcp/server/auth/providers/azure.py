"""Azure (Microsoft Entra) OAuth provider for FastMCP.

This provider implements Azure/Microsoft Entra ID OAuth authentication
using the OAuth Proxy pattern for non-DCR OAuth flows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from key_value.aio.protocols import AsyncKeyValue
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastmcp.server.auth.oauth_proxy import OAuthProxy
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.settings import ENV_FILE
from fastmcp.utilities.auth import parse_scopes
from fastmcp.utilities.logging import get_logger
from fastmcp.utilities.types import NotSet, NotSetT

if TYPE_CHECKING:
    from mcp.server.auth.provider import AuthorizationParams
    from mcp.shared.auth import OAuthClientInformationFull

logger = get_logger(__name__)


class AzureProviderSettings(BaseSettings):
    """Settings for Azure OAuth provider."""

    model_config = SettingsConfigDict(
        env_prefix="FASTMCP_SERVER_AUTH_AZURE_",
        env_file=ENV_FILE,
        extra="ignore",
    )

    client_id: str | None = None
    client_secret: SecretStr | None = None
    tenant_id: str | None = None
    identifier_uri: str | None = None
    base_url: str | None = None
    issuer_url: str | None = None
    redirect_path: str | None = None
    required_scopes: list[str] | None = None
    additional_authorize_scopes: list[str] | None = None
    allowed_client_redirect_uris: list[str] | None = None
    jwt_signing_key: str | None = None

    @field_validator("required_scopes", mode="before")
    @classmethod
    def _parse_scopes(cls, v: object) -> list[str] | None:
        return parse_scopes(v)

    @field_validator("additional_authorize_scopes", mode="before")
    @classmethod
    def _parse_additional_authorize_scopes(cls, v: object) -> list[str] | None:
        return parse_scopes(v)


class AzureProvider(OAuthProxy):
    """Azure (Microsoft Entra) OAuth provider for FastMCP.

    This provider implements Azure/Microsoft Entra ID authentication using the
    OAuth Proxy pattern. It supports both organizational accounts and personal
    Microsoft accounts depending on the tenant configuration.

    Scope Handling:
    - required_scopes: Provide unprefixed scope names (e.g., ["read", "write"])
      → Automatically prefixed with identifier_uri during initialization
      → Validated on all tokens and advertised to MCP clients
    - additional_authorize_scopes: Provide full format (e.g., ["User.Read"])
      → NOT prefixed, NOT validated, NOT advertised to clients
      → Used to request Microsoft Graph or other upstream API permissions

    Features:
    - OAuth proxy to Azure/Microsoft identity platform
    - JWT validation using tenant issuer and JWKS
    - Supports tenant configurations: specific tenant ID, "organizations", or "consumers"
    - Custom API scopes and Microsoft Graph scopes in a single provider

    Setup:
    1. Create an App registration in Azure Portal
    2. Configure Web platform redirect URI: http://localhost:8000/auth/callback (or your custom path)
    3. Add an Application ID URI under "Expose an API" (defaults to api://{client_id})
    4. Add custom scopes (e.g., "read", "write") under "Expose an API"
    5. Set access token version to 2 in the App manifest: "requestedAccessTokenVersion": 2
    6. Create a client secret
    7. Get Application (client) ID, Directory (tenant) ID, and client secret

    Example:
        ```python
        from fastmcp import FastMCP
        from fastmcp.server.auth.providers.azure import AzureProvider

        auth = AzureProvider(
            client_id="your-client-id",
            client_secret="your-client-secret",
            tenant_id="your-tenant-id",
            required_scopes=["read", "write"],  # Unprefixed scope names
            additional_authorize_scopes=["User.Read", "Mail.Read"],  # Optional Graph scopes
            base_url="http://localhost:8000",
            # identifier_uri defaults to api://{client_id}
        )

        mcp = FastMCP("My App", auth=auth)
        ```
    """

    def __init__(
        self,
        *,
        client_id: str | NotSetT = NotSet,
        client_secret: str | NotSetT = NotSet,
        tenant_id: str | NotSetT = NotSet,
        identifier_uri: str | None | NotSetT = NotSet,
        base_url: str | NotSetT = NotSet,
        issuer_url: str | NotSetT = NotSet,
        redirect_path: str | NotSetT = NotSet,
        required_scopes: list[str] | None | NotSetT = NotSet,
        additional_authorize_scopes: list[str] | None | NotSetT = NotSet,
        allowed_client_redirect_uris: list[str] | NotSetT = NotSet,
        client_storage: AsyncKeyValue | None = None,
        jwt_signing_key: str | bytes | NotSetT = NotSet,
        require_authorization_consent: bool = True,
    ) -> None:
        """Initialize Azure OAuth provider.

        Args:
            client_id: Azure application (client) ID from your App registration
            client_secret: Azure client secret from your App registration
            tenant_id: Azure tenant ID (specific tenant GUID, "organizations", or "consumers")
            identifier_uri: Optional Application ID URI for your custom API (defaults to api://{client_id}).
                This URI is automatically prefixed to all required_scopes during initialization.
                Example: identifier_uri="api://my-api" + required_scopes=["read"]
                → tokens validated for "api://my-api/read"
            base_url: Public URL where OAuth endpoints will be accessible (includes any mount path)
            issuer_url: Issuer URL for OAuth metadata (defaults to base_url). Use root-level URL
                to avoid 404s during discovery when mounting under a path.
            redirect_path: Redirect path configured in Azure App registration (defaults to "/auth/callback")
            required_scopes: Custom API scope names WITHOUT prefix (e.g., ["read", "write"]).
                - Automatically prefixed with identifier_uri during initialization
                - Validated on all tokens
                - Advertised in Protected Resource Metadata
                - Must match scope names defined in Azure Portal under "Expose an API"
                Example: ["read", "write"] → validates tokens containing ["api://xxx/read", "api://xxx/write"]
            additional_authorize_scopes: Microsoft Graph or other upstream scopes in full format.
                - NOT prefixed with identifier_uri
                - NOT validated on tokens
                - NOT advertised to MCP clients
                - Used to request additional permissions from Azure (e.g., Graph API access)
                Example: ["User.Read", "Mail.Read", "offline_access"]
                These scopes allow your FastMCP server to call Microsoft Graph APIs using the
                upstream Azure token, but MCP clients are unaware of them.
            allowed_client_redirect_uris: List of allowed redirect URI patterns for MCP clients.
                If None (default), all URIs are allowed. If empty list, no URIs are allowed.
            client_storage: Storage backend for OAuth state (client registrations, encrypted tokens).
                If None, a DiskStore will be created in the data directory (derived from `platformdirs`). The
                disk store will be encrypted using a key derived from the JWT Signing Key.
            jwt_signing_key: Secret for signing FastMCP JWT tokens (any string or bytes). If bytes are provided,
                they will be used as is. If a string is provided, it will be derived into a 32-byte key. If not
                provided, the upstream client secret will be used to derive a 32-byte key using PBKDF2.
            require_authorization_consent: Whether to require user consent before authorizing clients (default True).
                When True, users see a consent screen before being redirected to Azure.
                When False, authorization proceeds directly without user confirmation.
                SECURITY WARNING: Only disable for local development or testing environments.
        """
        settings = AzureProviderSettings.model_validate(
            {
                k: v
                for k, v in {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "tenant_id": tenant_id,
                    "identifier_uri": identifier_uri,
                    "base_url": base_url,
                    "issuer_url": issuer_url,
                    "redirect_path": redirect_path,
                    "required_scopes": required_scopes,
                    "additional_authorize_scopes": additional_authorize_scopes,
                    "allowed_client_redirect_uris": allowed_client_redirect_uris,
                    "jwt_signing_key": jwt_signing_key,
                }.items()
                if v is not NotSet
            }
        )

        # Validate required settings
        if not settings.client_id:
            msg = "client_id is required - set via parameter or FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID"
            raise ValueError(msg)
        if not settings.client_secret:
            msg = "client_secret is required - set via parameter or FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET"
            raise ValueError(msg)

        # Validate tenant_id is provided
        if not settings.tenant_id:
            msg = (
                "tenant_id is required - set via parameter or "
                "FASTMCP_SERVER_AUTH_AZURE_TENANT_ID. Use your Azure tenant ID "
                "(found in Azure Portal), 'organizations', or 'consumers'"
            )
            raise ValueError(msg)

        if not settings.required_scopes:
            raise ValueError("required_scopes is required")

        # Apply defaults
        self.identifier_uri = settings.identifier_uri or f"api://{settings.client_id}"
        self.additional_authorize_scopes = settings.additional_authorize_scopes or []
        tenant_id_final = settings.tenant_id

        # Prefix required scopes with identifier_uri for Azure
        # Azure returns scopes as full URIs (e.g., "api://xxx/read") in tokens
        prefixed_required_scopes = [
            f"{self.identifier_uri}/{scope}" for scope in settings.required_scopes
        ]

        # Always validate tokens against the app's API client ID using JWT
        issuer = f"https://login.microsoftonline.com/{tenant_id_final}/v2.0"
        jwks_uri = (
            f"https://login.microsoftonline.com/{tenant_id_final}/discovery/v2.0/keys"
        )

        token_verifier = JWTVerifier(
            jwks_uri=jwks_uri,
            issuer=issuer,
            audience=settings.client_id,
            algorithm="RS256",
            required_scopes=prefixed_required_scopes,
        )

        # Extract secret string from SecretStr
        client_secret_str = (
            settings.client_secret.get_secret_value() if settings.client_secret else ""
        )

        # Build Azure OAuth endpoints with tenant
        authorization_endpoint = (
            f"https://login.microsoftonline.com/{tenant_id_final}/oauth2/v2.0/authorize"
        )
        token_endpoint = (
            f"https://login.microsoftonline.com/{tenant_id_final}/oauth2/v2.0/token"
        )

        # Initialize OAuth proxy with Azure endpoints
        super().__init__(
            upstream_authorization_endpoint=authorization_endpoint,
            upstream_token_endpoint=token_endpoint,
            upstream_client_id=settings.client_id,
            upstream_client_secret=client_secret_str,
            token_verifier=token_verifier,
            base_url=settings.base_url,
            redirect_path=settings.redirect_path,
            issuer_url=settings.issuer_url
            or settings.base_url,  # Default to base_url if not specified
            allowed_client_redirect_uris=settings.allowed_client_redirect_uris,
            client_storage=client_storage,
            jwt_signing_key=settings.jwt_signing_key,
            require_authorization_consent=require_authorization_consent,
        )

        logger.info(
            "Initialized Azure OAuth provider for client %s with tenant %s%s",
            settings.client_id,
            tenant_id_final,
            f" and identifier_uri {self.identifier_uri}" if self.identifier_uri else "",
        )

    async def authorize(
        self,
        client: OAuthClientInformationFull,
        params: AuthorizationParams,
    ) -> str:
        """Start OAuth transaction and redirect to Azure AD.

        Override parent's authorize method to filter out the 'resource' parameter
        which is not supported by Azure AD v2.0 endpoints. The v2.0 endpoints use
        scopes to determine the resource/audience instead of a separate parameter.

        Args:
            client: OAuth client information
            params: Authorization parameters from the client

        Returns:
            Authorization URL to redirect the user to Azure AD
        """
        # Clear the resource parameter that Azure AD v2.0 doesn't support
        # This parameter comes from RFC 8707 (OAuth 2.0 Resource Indicators)
        # but Azure AD v2.0 uses scopes instead to determine the audience
        params_to_use = params
        if hasattr(params, "resource"):
            original_resource = getattr(params, "resource", None)
            if original_resource is not None:
                params_to_use = params.model_copy(update={"resource": None})
                if original_resource:
                    logger.debug(
                        "Filtering out 'resource' parameter '%s' for Azure AD v2.0 (use scopes instead)",
                        original_resource,
                    )
        # Scopes are already prefixed:
        # - self.required_scopes was prefixed during __init__
        # - Client scopes come from PRM which advertises prefixed scopes
        scopes = params_to_use.scopes or self.required_scopes

        final_scopes = list(scopes)
        # Add Microsoft Graph scopes separately - these use shorthand format (e.g., "User.Read")
        # and should not be prefixed with identifier_uri. Azure returns them as-is in tokens.
        if self.additional_authorize_scopes:
            final_scopes.extend(self.additional_authorize_scopes)

        modified_params = params_to_use.model_copy(update={"scopes": final_scopes})

        auth_url = await super().authorize(client, modified_params)
        separator = "&" if "?" in auth_url else "?"
        return f"{auth_url}{separator}prompt=select_account"
