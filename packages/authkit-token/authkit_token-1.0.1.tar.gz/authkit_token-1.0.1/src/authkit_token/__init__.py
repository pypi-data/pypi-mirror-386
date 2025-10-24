"""
authkit-token: Secure token generation for Pica AuthKit.

This package provides a simple interface for generating secure tokens
to use with Pica AuthKit in your Python applications.

Example:
    >>> from authkit_token import AuthKitToken
    >>>
    >>> # Create a client
    >>> client = AuthKitToken("sk_live_1234")
    >>>
    >>> # Generate a token synchronously
    >>> token = client.create(identity="user_123", identity_type="user")
    >>>
    >>> # Or asynchronously
    >>> token = await client.create_async(identity="user_123", identity_type="user")
"""

from .client import AuthKitToken
from .types import (
    AuthkitConnection,
    AuthkitResponse,
    ClientConfig,
    CreateEventLinkPayload,
    IdentityType,
)

__version__ = "1.0.1"

__all__ = [
    "AuthKitToken",
    "AuthkitConnection",
    "AuthkitResponse",
    "ClientConfig",
    "CreateEventLinkPayload",
    "IdentityType",
]
