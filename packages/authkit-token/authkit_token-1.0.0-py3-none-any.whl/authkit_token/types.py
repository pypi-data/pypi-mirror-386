"""Type definitions for authkit-token package."""

from typing import Any, Dict, List, Literal, Optional, TypedDict


IdentityType = Literal["user", "team", "organization", "project"]


class Author(TypedDict, total=False):
    """Author information."""

    _id: str
    name: Optional[str]
    avatar: Optional[str]


class Ownership(TypedDict, total=False):
    """Ownership information."""

    buildable_id: str
    client_id: Optional[str]
    project_id: Optional[str]
    organization_id: Optional[str]
    author: Optional[Author]
    user_id: Optional[str]


class EventLink(TypedDict, total=False):
    """Event link data structure."""

    _id: Optional[str]
    version: str
    ownership: Ownership
    identity: Optional[str]
    identity_type: Optional[IdentityType]
    group: Optional[str]
    label: Optional[str]
    token: str
    created_at: int
    created_date: str
    updated_at: Optional[int]
    expires_at: int
    environment: Optional[str]
    usage_source: Optional[str]
    _type: str


class CreateEventLinkPayload(TypedDict, total=False):
    """Payload for creating event link token."""

    identity: Optional[str]
    identity_type: Optional[IdentityType]
    group: Optional[str]
    label: Optional[str]


class Platform(TypedDict, total=False):
    """Platform information."""

    type: str
    title: str
    connection_definition_id: str
    active: Optional[bool]
    image: str
    activated_at: Optional[int]
    secrets_service_id: Optional[str]
    secret: Optional[Dict[str, str]]
    environment: Optional[Literal["test", "live"]]


class Feature(TypedDict):
    """Feature flag."""

    key: str
    value: Literal["enabled", "disabled"]
    updated_at: int


class ConnectionRecord(TypedDict, total=False):
    """Connection record information."""

    _id: str
    platform_version: str
    connection_definition_id: str
    name: str
    key: str
    environment: str
    platform: str
    secrets_service_id: str
    settings: Dict[str, Any]
    throughput: Dict[str, Any]
    created_at: int
    updated_at: int
    updated: bool
    version: str
    last_modified_by: str
    deleted: bool
    change_log: Dict[str, Any]
    tags: List[str]
    active: bool
    deprecated: bool


class AuthkitConnection(TypedDict, total=False):
    """Authkit connection information."""

    id: int
    connection_def_id: int
    type: str
    title: str
    image: str
    activated_at: str
    secret_id: Optional[str]
    client_secret_display: Optional[str]
    client_id_display: Optional[str]
    scopes: Optional[str]
    environment: str
    guide: Optional[str]
    created_at: str
    tags: List[str]
    active: bool


class AuthkitResponse(TypedDict):
    """Response from authkit API."""

    rows: List[AuthkitConnection]
    total: int
    pages: int
    page: int
    request_id: int


class ConnectorPaginationOptions(TypedDict, total=False):
    """Options for pagination."""

    limit: int
    max_concurrent_requests: int
    max_retries: int


class ClientConfig(TypedDict, total=False):
    """Configuration for AuthKitToken client."""

    base_url: Optional[str]
