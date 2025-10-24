from abc import abstractmethod
from typing import Any, Optional, List, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import msal
from msgraph import GraphServiceClient
from msal import PublicClientApplication, SerializableTokenCache
# Microsoft Graph SDK imports
from azure.identity import (
    ClientSecretCredential,
    UsernamePasswordCredential,
    OnBehalfOfCredential
)
from azure.core.credentials import (
    AccessToken,
    TokenCredential
)
from navconfig.logging import logging
from ..conf import (
    SHAREPOINT_TENANT_NAME,
    O365_CLIENT_ID,
    O365_CLIENT_SECRET,
    O365_TENANT_ID,
)
from .credentials import CredentialsInterface
from ..exceptions import InvalidArgument


logging.getLogger('msal').setLevel(logging.INFO)


# Tokens are typically 90 days for non-SPA apps. :contentReference[oaicite:0]{index=0}
TOKEN_CACHE_TTL_SECONDS = 75 * 24 * 3600  # 75 days


class MSALTokenCredential(TokenCredential):
    """
    Custom TokenCredential that uses MSAL tokens for azure-identity compatibility.
    This allows us to use MSAL-acquired tokens with the Graph SDK.
    """

    def __init__(self, msal_app, scopes: List[str], username: str = None, password: str = None):
        self.msal_app = msal_app
        self.scopes = scopes
        self.username = username
        self.password = password
        self._token_cache = None
        self._logger = logging.getLogger(__name__)

    def get_token(self, *scopes, **kwargs) -> AccessToken:
        """Get token using MSAL."""
        try:
            # Use provided scopes or default
            token_scopes = list(scopes) if scopes else self.scopes

            if self.username and self.password:
                # Username/password flow
                result = self.msal_app.acquire_token_by_username_password(
                    username=self.username,
                    password=self.password,
                    scopes=token_scopes
                )
            else:
                # Client credentials flow
                result = self.msal_app.acquire_token_for_client(scopes=token_scopes)

            if "access_token" not in result:
                error_msg = result.get('error_description', 'Unknown error')
                raise RuntimeError(f"MSAL token acquisition failed: {error_msg}")

            # Convert to AccessToken
            return AccessToken(
                token=result['access_token'],
                expires_on=result.get('expires_in', 3600) + asyncio.get_event_loop().time()
            )

        except Exception as e:
            self._logger.error(f"MSALTokenCredential failed: {e}")
            raise

class MSALCacheTokenCredential(TokenCredential):
    """TokenCredential that uses an MSAL PublicClientApplication with a serialized cache (e.g., Redis)."""
    def __init__(self, pca: PublicClientApplication, scopes: List[str], account=None, logger=None):
        self.pca = pca
        self.scopes = scopes
        self.account = account
        self._logger = logger or logging.getLogger(__name__)

    def get_token(self, *scopes, **kwargs) -> AccessToken:
        wanted_scopes = list(scopes) if scopes else self.scopes
        result = self.pca.acquire_token_silent(wanted_scopes, account=self.account)
        if not result or "access_token" not in result:
            raise InvalidArgument(
                "No cached token available. Run interactive_login() first."
            )
        # MSAL returns expires_in (seconds). Convert to absolute epoch as azure-core expects.
        return AccessToken(
            result["access_token"], int(time.time()) + int(result.get("expires_in", 3600))
        )


class O365Client(CredentialsInterface):
    """
    O365Client - Migrated to Microsoft Graph SDK

    Overview

        The O365Client class is an abstract base class for managing connections to Office 365 services
        using the official Microsoft Graph SDK. It handles authentication, credential processing,
        and provides methods for obtaining the Graph client. It uses Azure Identity for authentication
        and Microsoft Graph SDK for context management.

    Supported Authentication Methods:
        - Username/Password (UsernamePasswordCredential)
        - Client Credentials (ClientSecretCredential)
        - On-Behalf-Of (OnBehalfOfCredential)

    .. table:: Properties
    :widths: auto

        +------------------+----------+--------------------------------------------------------------------------------------------------+
        | Name             | Required | Description                                                                                      |
        +------------------+----------+--------------------------------------------------------------------------------------------------+
        | url              |   No     | The base URL for the Office 365 service.                                                         |
        +------------------+----------+--------------------------------------------------------------------------------------------------+
        | tenant           |   Yes    | The tenant ID for the Office 365 service.                                                        |
        +------------------+----------+--------------------------------------------------------------------------------------------------+
        | site             |   No     | The site URL for the Office 365 service.                                                         |
        +------------------+----------+--------------------------------------------------------------------------------------------------+
        | credential       |   Yes    | The Azure Identity credential object.                                                            |
        +------------------+----------+--------------------------------------------------------------------------------------------------+
        | graph_client     |   Yes    | The Microsoft Graph SDK client object.                                                           |
        +------------------+----------+--------------------------------------------------------------------------------------------------+
        | credentials      |   Yes    | A dictionary containing the credentials for authentication.                                      |
        +------------------+----------+--------------------------------------------------------------------------------------------------+

    Return

        The methods in this class manage the authentication and connection setup for Office 365 services,
        providing an abstract base for subclasses to implement specific service interactions.

    """  # noqa
    _credentials: dict = {
        "username": str,
        "password": str,
        "client_id": str,
        "client_secret": str,
        "tenant": str,
        "site": str,
        "tenant_id": str,
        "assertion": str,  # For OnBehalfOfCredential
    }

    def __init__(self, *args, **kwargs) -> None:
        self.url: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.tenant: Optional[str] = None
        self.site: Optional[str] = None

        # Azure Identity and Graph SDK objects
        self._credential: Optional[TokenCredential] = None
        self._graph_client: Optional[GraphServiceClient] = None
        self._access_token: Optional[str] = None

        # Legacy compatibility properties
        self.auth_context: Any = None  # For backwards compatibility
        self.context: Any = None  # For backwards compatibility

        self._logger = logging.getLogger('Flowtask.O365Client')
        self._executor = ThreadPoolExecutor()

        # Default credentials from config
        self._default_tenant_id = O365_TENANT_ID
        self._default_client_id = O365_CLIENT_ID
        self._default_client_secret = O365_CLIENT_SECRET
        self._default_tenant_name = SHAREPOINT_TENANT_NAME

        # Default scopes for Graph API
        self._default_scopes = ["https://graph.microsoft.com/.default"]

        super(O365Client, self).__init__(*args, **kwargs)

    @abstractmethod
    def get_context(self, url: str, *args):
        """Abstract method for backwards compatibility - subclasses can override."""
        pass

    @abstractmethod
    def _start_(self, **kwargs):
        """Abstract method to initialize subclass-specific configuration."""
        pass

    async def run_in_executor(self, fn, *args, **kwargs):
        """
        Calling any blocking process in an executor.
        """
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, fn, *args, **kwargs
        )

    def processing_credentials(self):
        """Process credentials using the inherited CredentialsInterface."""
        super().processing_credentials()

        # Extract tenant and site from credentials
        try:
            self.tenant = self.credentials.get('tenant', None)
            if not self.tenant:
                self.tenant = self._default_tenant_name
            self.site = self.credentials.get('site', None)
            self.tenant_id = self.credentials.get('tenant_id', self._default_tenant_id)
        except KeyError as e:
            raise RuntimeError(
                f"Office365: Missing Tenant or Site Configuration: {e}."
            ) from e

    def _effective_scopes(self, scopes: Optional[List[str]] = None) -> List[str]:
        if self.credentials.get("username") or self.credentials.get("assertion"):
            return ["User.Read", "Files.ReadWrite.All", "Sites.Read.All", "offline_access", "openid", "profile"]
        if scopes:
            return scopes
        return self._default_scopes

    def _create_credential(self) -> TokenCredential:
        """
        Create appropriate Azure Identity credential based on available credentials.

        Returns:
            TokenCredential: The appropriate credential for authentication
        """
        # Extract credentials
        username = self.credentials.get("username")
        password = self.credentials.get("password")
        client_id = self.credentials.get("client_id", self._default_client_id)
        client_secret = self.credentials.get("client_secret", self._default_client_secret)
        tenant_id = self.credentials.get('tenant_id', self._default_tenant_id)
        assertion = self.credentials.get("assertion")  # For OnBehalfOfCredential

        if not tenant_id:
            raise RuntimeError(
                "Office365: Missing tenant_id in credentials"
            )

        # Priority order for authentication methods:

        # 1. OnBehalfOfCredential (if assertion is provided)
        if assertion and client_id and client_secret:
            self._logger.info("Using OnBehalfOfCredential authentication")
            return OnBehalfOfCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
                user_assertion=assertion
            )

        # 2. Username/Password authentication
        if username and password and client_id and client_secret:
            self._logger.info("Using UsernamePasswordCredential authentication")
            # Create MSAL confidential client app
            msal_app = msal.ConfidentialClientApplication(
                authority=f'https://login.microsoftonline.com/{tenant_id}',
                client_id=client_id,
                client_credential=client_secret
            )

            # Return custom credential that uses MSAL
            return MSALTokenCredential(
                msal_app=msal_app,
                scopes=self._default_scopes,
                username=username,
                password=password
            )
        # 3. Public client Username/Password (only if no client_secret)
        if username and password and client_id and not client_secret:
            self._logger.info("Using UsernamePasswordCredential (public client) authentication")
            return UsernamePasswordCredential(
                client_id=client_id,
                username=username,
                password=password,
                tenant_id=tenant_id
            )

        # 4. Client Credentials (app-only)
        if client_id and client_secret:
            self._logger.info("Using ClientSecretCredential authentication")
            return ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )

        # No valid credential combination found
        raise RuntimeError(
            "Office365: No valid credential combination found. "
            "Provide either (username + password), (client_id + client_secret), "
            "or (assertion + client_id + client_secret)"
        )

    def _create_graph_client(self, scopes: Optional[List[str]] = None) -> GraphServiceClient:
        """
        Create Microsoft Graph client with the appropriate credential.

        Args:
            scopes: List of scopes for the Graph client

        Returns:
            GraphServiceClient: Configured Graph client
        """
        if not self._credential:
            self._credential = self._create_credential()

        scopes = self._effective_scopes(scopes)

        # Create Graph client
        graph_client = GraphServiceClient(
            credentials=self._credential,
            scopes=scopes
        )

        self._logger.info(
            "Microsoft Graph client created successfully"
        )
        return graph_client

    @property
    def graph_client(self) -> GraphServiceClient:
        """
        Get the Graph client, creating it if necessary.

        Returns:
            GraphServiceClient: The configured Graph client
        """
        if not self._graph_client:
            self._graph_client = self._create_graph_client()
        return self._graph_client

    @property
    def access_token(self) -> Optional[str]:
        """
        Get current access token for backwards compatibility.

        Returns:
            str: Current access token or None
        """
        return self._access_token

    # Async Context Methods:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    def connection(self):
        """
        Establish connection to Office 365 services using Microsoft Graph SDK.

        This method replaces the old office365-rest-python-client based authentication
        with modern Azure Identity + Microsoft Graph SDK approach.
        """
        # Call the abstract _start_ method
        self._start_()

        # Process credentials using the inherited interface
        self.processing_credentials()

        try:
            # Create credential based on available authentication methods
            self._credential = self._create_credential()

            # Create Graph client
            self._graph_client = self._create_graph_client()

            # Test the connection by making a simple Graph API call
            # await self._test_connection()

            self._logger.info("Office365: Authentication success using Microsoft Graph SDK")

        except Exception as err:
            self._logger.error(f"Office365: Authentication Error: {err}")
            raise RuntimeError(f"Office365: Authentication Error: {err}") from err

        return self

    async def _test_connection(self):
        """Test the connection by making a simple Graph API call."""
        try:
            # Make a simple call to test authentication
            # This is synchronous for compatibility with the existing interface
            async def test_me():
                try:
                    me = await self.graph_client.me.get()
                    self._logger.info(
                        f"🔗 Connected as: {me.display_name} ({me.user_principal_name})"
                    )
                    return True
                except Exception:
                    # If /me fails (app-only), try a different endpoint
                    try:
                        organization = await self.graph_client.organization.get()
                        if organization and organization.value:
                            org = organization.value[0]
                            self._logger.info(
                                f"🔗 Connected to organization: {org.display_name}"
                            )
                        else:
                            self._logger.info(
                                "🔗 Graph API connection successful (app-only)"
                            )
                        return True
                    except Exception as e:
                        self._logger.warning(
                            f"⚠️ Connection test failed: {e}"
                        )
                        return False

            # Run the async test
            if await test_me():
                self._logger.debug("Graph API connection test passed")
            else:
                self._logger.warning("Graph API connection test inconclusive")

        except Exception as e:
            self._logger.warning(f"Could not test Graph API connection: {e}")

    def user_auth(self, username: str, password: str, scopes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Authenticate using username and password with Microsoft Graph SDK.

        This method is maintained for backwards compatibility but now uses
        Azure Identity UsernamePasswordCredential internally.

        Args:
            username: User's username/email
            password: User's password
            scopes: List of scopes to request

        Returns:
            dict: Token information (for compatibility)
        """
        tenant_id = self.credentials.get('tenant_id', self._default_tenant_id)
        client_id = self.credentials.get("client_id", self._default_client_id)
        client_secret = self.credentials.get("client_secret", self._default_client_secret)

        if not scopes:
            scopes = self._default_scopes

        try:
            # For confidential clients (apps with client_secret), we need to use
            # ConfidentialClientApplication with username/password flow
            if client_secret:
                self._logger.info("Using MSAL ConfidentialClientApplication for username/password")
                app = msal.ConfidentialClientApplication(
                    authority=f'https://login.microsoftonline.com/{tenant_id}',
                    client_id=client_id,
                    client_credential=client_secret
                )
            else:
                # Use MSAL for direct token acquisition (for compatibility)
                app = msal.PublicClientApplication(
                    authority=f'https://login.microsoftonline.com/{tenant_id}',
                    client_id=client_id,
                    client_credential=client_secret
                )

            result = app.acquire_token_by_username_password(
                username,
                password,
                scopes=scopes
            )

            if "access_token" not in result:
                error_message = result.get('error_description', 'Unknown error')
                error_code = result.get('error', 'Unknown error code')
                raise RuntimeError(
                    f"Failed to obtain access token: {error_code} - {error_message}"
                )

            # Store token
            self._access_token = result['access_token']

            if client_secret:
                # Create new MSAL-based credential for ongoing Graph SDK use
                msal_app = msal.ConfidentialClientApplication(
                    authority=f'https://login.microsoftonline.com/{tenant_id}',
                    client_id=client_id,
                    client_credential=client_secret
                )
                self._credential = MSALTokenCredential(
                    msal_app=msal_app,
                    scopes=scopes,
                    username=username,
                    password=password
                )
            else:
                # For public clients, use UsernamePasswordCredential
                self._credential = UsernamePasswordCredential(
                    client_id=client_id,
                    username=username,
                    password=password,
                    tenant_id=tenant_id
                )

            self._logger.info(
                "✅ Username/password authentication successful"
            )
            return result

        except Exception as e:
            self._logger.error(f"❌ Username/password authentication failed: {e}")
            raise

    def acquire_token(self, scopes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Acquire token using client credentials with Microsoft Graph SDK.

        This method is maintained for backwards compatibility but now uses
        Azure Identity ClientSecretCredential internally.

        Args:
            scopes: List of scopes to request

        Returns:
            dict: Token information (for compatibility)
        """
        client_id = self.credentials.get("client_id", self._default_client_id)
        client_secret = self.credentials.get("client_secret", self._default_client_secret)
        tenant_id = self.credentials.get('tenant_id', self._default_tenant_id)

        if not scopes:
            scopes = self._default_scopes

        try:
            # Use MSAL for direct token acquisition (for compatibility)
            authority_url = f'https://login.microsoftonline.com/{tenant_id}'
            app = msal.ConfidentialClientApplication(
                authority=authority_url,
                client_id=client_id,
                client_credential=client_secret
            )

            result = app.acquire_token_for_client(scopes=scopes)

            if "access_token" not in result:
                error_message = result.get('error_description', 'Unknown error')
                error_code = result.get('error', 'Unknown error code')
                raise RuntimeError(
                    f"Failed to obtain access token: {error_code} - {error_message}"
                )

            # Store token for backwards compatibility
            self._access_token = result['access_token']

            # Also create the proper credential for Graph SDK
            self._credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )

            self._logger.info(
                "✅ Client credentials authentication successful"
            )
            return result

        except Exception as e:
            self._logger.error(
                f"❌ Client credentials authentication failed: {e}"
            )
            raise

    def acquire_token_on_behalf_of(
        self,
        user_assertion: str,
        scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Acquire token using On-Behalf-Of flow with Microsoft Graph SDK.

        This is a new method that supports the OnBehalfOfCredential flow.

        Args:
            user_assertion: The user assertion (JWT token)
            scopes: List of scopes to request

        Returns:
            dict: Token information
        """
        client_id = self.credentials.get("client_id", self._default_client_id)
        client_secret = self.credentials.get("client_secret", self._default_client_secret)
        tenant_id = self.credentials.get('tenant_id', self._default_tenant_id)

        if not scopes:
            scopes = self._default_scopes

        try:
            # Use MSAL for On-Behalf-Of flow
            authority_url = f'https://login.microsoftonline.com/{tenant_id}'
            app = msal.ConfidentialClientApplication(
                authority=authority_url,
                client_id=client_id,
                client_credential=client_secret
            )

            result = app.acquire_token_on_behalf_of(
                user_assertion=user_assertion,
                scopes=scopes
            )

            if "access_token" not in result:
                error_message = result.get('error_description', 'Unknown error')
                error_code = result.get('error', 'Unknown error code')
                raise RuntimeError(
                    f"Failed to obtain OBO token: {error_code} - {error_message}"
                )

            # Store token for backwards compatibility
            self._access_token = result['access_token']

            # Also create the proper credential for Graph SDK
            self._credential = OnBehalfOfCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
                user_assertion=user_assertion
            )

            self._logger.info("✅ On-Behalf-Of authentication successful")
            return result

        except Exception as e:
            self._logger.error(f"❌ On-Behalf-Of authentication failed: {e}")
            raise

    # Utility methods for easier Graph API access

    async def get_me(self):
        """Get current user information."""
        return await self.graph_client.me.get()

    async def get_organization(self):
        """Get organization information."""
        return await self.graph_client.organization.get()

    async def get_sites(self):
        """Get SharePoint sites."""
        return await self.graph_client.sites.get()

    async def get_drives(self):
        """Get OneDrive/SharePoint drives."""
        return await self.graph_client.me.drives.get()

    # Backwards compatibility properties

    @property
    def _graph_client_legacy(self) -> GraphServiceClient:
        """Legacy property name for backwards compatibility."""
        return self.graph_client

    def close(self):
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=False)
        self._credential = None
        self._graph_client = None
        self._access_token = None

    def _cache_key(self) -> str:
        tenant = self.credentials.get("tenant_id", self._default_tenant_id) or ""
        client_id = self.credentials.get("client_id", self._default_client_id) or ""
        user_hint = self.credentials.get("username", "")  # optional
        return f"msal:cache:{tenant}:{client_id}:{user_hint}"

    async def _load_token_cache(self, cache: SerializableTokenCache) -> None:
        try:
            if getattr(self, "redis", None):
                blob = await self.redis.get(self._cache_key())
                if blob:
                    cache.deserialize(blob.decode("utf-8"))
                    self._logger.info("Loaded MSAL token cache from Redis")
        except Exception as e:
            self._logger.warning(
                f"Could not load token cache: {e}"
            )

    async def _save_token_cache(self, cache: SerializableTokenCache) -> None:
        try:
            if getattr(self, "redis", None) and cache.has_state_changed:
                blob = cache.serialize()
                await self.redis.set(
                    self._cache_key(),
                    blob.encode("utf-8"),
                    ex=TOKEN_CACHE_TTL_SECONDS
                )
                self._logger.info("Saved MSAL token cache to Redis")
        except Exception as e:
            self._logger.warning(
                f"Could not save token cache: {e}"
            )

    async def interactive_login(
        self,
        scopes: Optional[List[str]] = None,
        redirect_uri: str = "http://localhost",  # must be registered on the app
        open_browser: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform Authorization Code + PKCE interactive login (supports MFA),
        then persist the MSAL cache to Redis. Reuses the cache on subsequent runs.
        """
        # Scopes must include offline_access to receive refresh tokens. :contentReference[oaicite:1]{index=1}
        scopes = scopes or [
            "User.Read", "Files.ReadWrite.All", "Sites.Read.All", "offline_access", "openid", "profile"
        ]

        tenant_id = self.credentials.get('tenant_id', self._default_tenant_id)
        client_id = self.credentials.get("client_id", self._default_client_id)
        authority = f"https://login.microsoftonline.com/{tenant_id}"

        # Prepare cache, load from Redis if present
        cache = SerializableTokenCache()
        await self._load_token_cache(cache)

        # Create a Public Client (no secret) bound to this cache
        pca = PublicClientApplication(
            client_id=client_id,
            authority=authority,
            token_cache=cache
        )

        # Try silent first (if user already logged in and cache is valid)
        accounts = pca.get_accounts()
        result = None
        if accounts:
            result = pca.acquire_token_silent(scopes, account=accounts[0])

        if not result or "access_token" not in result:
            # Interactive (opens system browser by default) :contentReference[oaicite:2]{index=2}
            result = pca.acquire_token_interactive(
                scopes=scopes,
                redirect_uri=redirect_uri,
                prompt="select_account",
                open_browser=open_browser,  # set False if you want to drive the URL with Playwright yourself
            )
            if "access_token" not in result:
                raise RuntimeError(
                    f"Interactive login failed: {result.get('error_description', 'Unknown error')}"
                )

        # Persist cache to Redis so future runs can refresh silently
        await self._save_token_cache(cache)

        # Build a TokenCredential backed by this MSAL PCA & cache for GraphServiceClient
        account = pca.get_accounts()[0] if pca.get_accounts() else None
        self._credential = MSALCacheTokenCredential(pca=pca, scopes=scopes, account=account, logger=self._logger)
        self._graph_client = self._create_graph_client(scopes=scopes)

        self._logger.info("✅ Interactive login complete; tokens will refresh silently from cache")
        return result

    async def ensure_interactive_session(self, scopes: Optional[List[str]] = None):
        """
        Ensure an interactive session (with cached refresh tokens) exists.
        Creates Graph client credential from MSAL cache without prompting, if possible.
        """
        scopes = scopes or [
            "User.Read", "Files.ReadWrite.All", "Sites.Read.All", "offline_access", "openid", "profile"
        ]
        tenant_id = self.credentials.get('tenant_id', self._default_tenant_id)
        client_id = self.credentials.get("client_id", self._default_client_id)
        authority = f"https://login.microsoftonline.com/{tenant_id}"

        cache = SerializableTokenCache()
        await self._load_token_cache(cache)

        pca = PublicClientApplication(
            client_id=client_id,
            authority=authority,
            token_cache=cache
        )
        accounts = pca.get_accounts()
        if not accounts:
            # No cached account -> caller should run interactive_login()
            raise InvalidArgument(
                "No cached session; call interactive_login() first"
            )

        # Try silent; if fails, caller must re-run interactive_login()
        result = pca.acquire_token_silent(scopes, account=accounts[0])
        if not result or "access_token" not in result:
            raise InvalidArgument(
                "Cached session expired; call interactive_login() again"
            )

        # Build credential and graph client from cache
        self._credential = MSALCacheTokenCredential(
            pca=pca,
            scopes=scopes,
            account=accounts[0],
            logger=self._logger
        )
        self._graph_client = self._create_graph_client(scopes=scopes)
        self._logger.debug(
            "🔐 Using cached MSAL session (silent refresh enabled)"
        )
