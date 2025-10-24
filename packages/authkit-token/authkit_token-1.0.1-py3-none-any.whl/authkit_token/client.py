"""Main client for AuthKit Token generation."""

from typing import Optional

from .api import create_event_link_token_async, create_event_link_token_sync
from .types import AuthkitResponse, ClientConfig, CreateEventLinkPayload, IdentityType
from .utils import get_headers


class AuthKitToken:
    """
    Client for generating secure tokens for Pica AuthKit.

    This client supports both synchronous and asynchronous token generation.
    Use the `create()` method for synchronous operations and `create_async()`
    for asynchronous operations.

    Example:
        >>> # Synchronous usage
        >>> client = AuthKitToken("sk_live_1234")
        >>> token = client.create(identity="user_123", identity_type="user")
        >>>
        >>> # Asynchronous usage
        >>> client = AuthKitToken("sk_live_1234")
        >>> token = await client.create_async(identity="user_123", identity_type="user")

    Args:
        secret: Your Pica API secret key (starts with sk_live_ or sk_test_)
        config: Optional configuration including custom base_url
    """

    def __init__(self, secret: str, config: Optional[ClientConfig] = None) -> None:
        """
        Initialize the AuthKitToken client.

        Args:
            secret: Your Pica API secret key
            config: Optional configuration dictionary
        """
        self._secret = secret
        self._config = config or {}

    @property
    def _url(self) -> str:
        """Get the base URL for API requests."""
        if self._config.get("base_url"):
            return self._config["base_url"]  # type: ignore
        return "https://api.picaos.com"

    def create(
        self,
        identity: Optional[str] = None,
        identity_type: Optional[IdentityType] = None,
        group: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Optional[AuthkitResponse]:
        """
        Create an authkit token synchronously.

        This method fetches all available connections for the given identity
        or returns all connections if no identity is provided.

        Args:
            identity: Unique identifier for the token. It is recommended to avoid
                     using spaces and colons in this field as it may lead to
                     unexpected behavior in some systems.
            identity_type: Type of identity (user, team, organization, or project)
            group: (Deprecated) Use 'identity' instead
            label: (Deprecated) Legacy parameter

        Returns:
            AuthkitResponse containing connection data, or None on error

        Example:
            >>> client = AuthKitToken("sk_live_1234")
            >>> response = client.create(identity="user_123", identity_type="user")
            >>> if response:
            ...     print(f"Found {response['total']} connections")
        """
        headers = get_headers(self._secret)
        url = self._url

        payload: CreateEventLinkPayload = {}
        if identity is not None:
            payload["identity"] = identity
        if identity_type is not None:
            payload["identity_type"] = identity_type
        if group is not None:
            payload["group"] = group
        if label is not None:
            payload["label"] = label

        result = create_event_link_token_sync(headers, url, payload if payload else None)
        return result

    async def create_async(
        self,
        identity: Optional[str] = None,
        identity_type: Optional[IdentityType] = None,
        group: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Optional[AuthkitResponse]:
        """
        Create an authkit token asynchronously.

        This method fetches all available connections for the given identity
        or returns all connections if no identity is provided.

        Args:
            identity: Unique identifier for the token. It is recommended to avoid
                     using spaces and colons in this field as it may lead to
                     unexpected behavior in some systems.
            identity_type: Type of identity (user, team, organization, or project)
            group: (Deprecated) Use 'identity' instead
            label: (Deprecated) Legacy parameter

        Returns:
            AuthkitResponse containing connection data, or None on error

        Example:
            >>> client = AuthKitToken("sk_live_1234")
            >>> response = await client.create_async(identity="user_123", identity_type="user")
            >>> if response:
            ...     print(f"Found {response['total']} connections")
        """
        headers = get_headers(self._secret)
        url = self._url

        payload: CreateEventLinkPayload = {}
        if identity is not None:
            payload["identity"] = identity
        if identity_type is not None:
            payload["identity_type"] = identity_type
        if group is not None:
            payload["group"] = group
        if label is not None:
            payload["label"] = label

        result = await create_event_link_token_async(headers, url, payload if payload else None)
        return result
