"""Tests for the AuthKitToken client."""

import pytest
from pytest_httpx import HTTPXMock

from authkit_token import AuthKitToken


@pytest.fixture
def mock_authkit_response() -> dict:
    """Mock response from authkit API."""
    return {
        "rows": [
            {
                "id": 1,
                "connection_def_id": 100,
                "type": "oauth",
                "title": "Test Connection",
                "image": "https://example.com/image.png",
                "activated_at": "2024-01-01T00:00:00Z",
                "secret_id": "secret_123",
                "client_secret_display": "***",
                "client_id_display": "client_123",
                "scopes": "read,write",
                "environment": "live",
                "guide": "https://example.com/guide",
                "created_at": "2024-01-01T00:00:00Z",
                "tags": ["test"],
                "active": True,
            }
        ],
        "total": 1,
        "pages": 1,
        "page": 1,
        "request_id": 12345,
    }


@pytest.fixture
def mock_authkit_paginated_response() -> list[dict]:
    """Mock paginated response from authkit API."""
    return [
        {
            "rows": [
                {
                    "id": 1,
                    "connection_def_id": 100,
                    "type": "oauth",
                    "title": "Connection 1",
                    "image": "https://example.com/image.png",
                    "activated_at": "2024-01-01T00:00:00Z",
                    "environment": "live",
                    "created_at": "2024-01-01T00:00:00Z",
                    "tags": [],
                    "active": True,
                }
            ],
            "total": 3,
            "pages": 3,
            "page": 1,
            "request_id": 12345,
        },
        {
            "rows": [
                {
                    "id": 2,
                    "connection_def_id": 101,
                    "type": "oauth",
                    "title": "Connection 2",
                    "image": "https://example.com/image.png",
                    "activated_at": "2024-01-01T00:00:00Z",
                    "environment": "live",
                    "created_at": "2024-01-01T00:00:00Z",
                    "tags": [],
                    "active": True,
                }
            ],
            "total": 3,
            "pages": 3,
            "page": 2,
            "request_id": 12346,
        },
        {
            "rows": [
                {
                    "id": 3,
                    "connection_def_id": 102,
                    "type": "oauth",
                    "title": "Connection 3",
                    "image": "https://example.com/image.png",
                    "activated_at": "2024-01-01T00:00:00Z",
                    "environment": "live",
                    "created_at": "2024-01-01T00:00:00Z",
                    "tags": [],
                    "active": True,
                }
            ],
            "total": 3,
            "pages": 3,
            "page": 3,
            "request_id": 12347,
        },
    ]


class TestAuthKitToken:
    """Test cases for AuthKitToken client."""

    def test_initialization(self) -> None:
        """Test client initialization."""
        client = AuthKitToken("sk_test_123")
        assert client._secret == "sk_test_123"
        assert client._url == "https://api.picaos.com"

    def test_initialization_with_custom_url(self) -> None:
        """Test client initialization with custom base URL."""
        client = AuthKitToken("sk_test_123", {"base_url": "https://custom.api.com"})
        assert client._secret == "sk_test_123"
        assert client._url == "https://custom.api.com"

    def test_create_sync_basic(self, httpx_mock: HTTPXMock, mock_authkit_response: dict) -> None:
        """Test synchronous token creation without parameters."""
        httpx_mock.add_response(
            url="https://api.picaos.com/v1/authkit?limit=100&page=1",
            method="POST",
            json=mock_authkit_response,
        )

        client = AuthKitToken("sk_test_123")
        response = client.create()

        assert response is not None
        assert response["total"] == 1
        assert len(response["rows"]) == 1
        assert response["rows"][0]["title"] == "Test Connection"

    def test_create_sync_with_identity(
        self, httpx_mock: HTTPXMock, mock_authkit_response: dict
    ) -> None:
        """Test synchronous token creation with identity."""
        httpx_mock.add_response(
            url="https://api.picaos.com/v1/authkit?limit=100&page=1",
            method="POST",
            json=mock_authkit_response,
        )

        client = AuthKitToken("sk_test_123")
        response = client.create(identity="user_123", identity_type="user")

        assert response is not None
        assert response["total"] == 1

        # Verify the request was made with correct payload
        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["X-Pica-Secret"] == "sk_test_123"
        assert request.headers["Content-Type"] == "application/json"

    def test_create_sync_pagination(
        self, httpx_mock: HTTPXMock, mock_authkit_paginated_response: list[dict]
    ) -> None:
        """Test synchronous token creation with pagination."""
        # Mock all three pages
        for page_num, page_response in enumerate(mock_authkit_paginated_response, start=1):
            httpx_mock.add_response(
                url=f"https://api.picaos.com/v1/authkit?limit=100&page={page_num}",
                method="POST",
                json=page_response,
            )

        client = AuthKitToken("sk_test_123")
        response = client.create()

        assert response is not None
        assert response["total"] == 3
        assert len(response["rows"]) == 3
        assert response["pages"] == 1  # All data combined into single page
        assert response["rows"][0]["id"] == 1
        assert response["rows"][1]["id"] == 2
        assert response["rows"][2]["id"] == 3

    @pytest.mark.asyncio
    async def test_create_async_basic(
        self, httpx_mock: HTTPXMock, mock_authkit_response: dict
    ) -> None:
        """Test asynchronous token creation without parameters."""
        httpx_mock.add_response(
            url="https://api.picaos.com/v1/authkit?limit=100&page=1",
            method="POST",
            json=mock_authkit_response,
        )

        client = AuthKitToken("sk_test_123")
        response = await client.create_async()

        assert response is not None
        assert response["total"] == 1
        assert len(response["rows"]) == 1
        assert response["rows"][0]["title"] == "Test Connection"

    @pytest.mark.asyncio
    async def test_create_async_with_identity(
        self, httpx_mock: HTTPXMock, mock_authkit_response: dict
    ) -> None:
        """Test asynchronous token creation with identity."""
        httpx_mock.add_response(
            url="https://api.picaos.com/v1/authkit?limit=100&page=1",
            method="POST",
            json=mock_authkit_response,
        )

        client = AuthKitToken("sk_test_123")
        response = await client.create_async(identity="user_123", identity_type="user")

        assert response is not None
        assert response["total"] == 1

    @pytest.mark.asyncio
    async def test_create_async_pagination(
        self, httpx_mock: HTTPXMock, mock_authkit_paginated_response: list[dict]
    ) -> None:
        """Test asynchronous token creation with pagination."""
        # Mock all three pages
        for page_num, page_response in enumerate(mock_authkit_paginated_response, start=1):
            httpx_mock.add_response(
                url=f"https://api.picaos.com/v1/authkit?limit=100&page={page_num}",
                method="POST",
                json=page_response,
            )

        client = AuthKitToken("sk_test_123")
        response = await client.create_async()

        assert response is not None
        assert response["total"] == 3
        assert len(response["rows"]) == 3
        assert response["pages"] == 1  # All data combined into single page

    def test_create_sync_error_handling(self, httpx_mock: HTTPXMock) -> None:
        """Test synchronous error handling."""
        httpx_mock.add_response(
            url="https://api.picaos.com/v1/authkit?limit=100&page=1",
            method="POST",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        client = AuthKitToken("sk_test_invalid")
        response = client.create()

        assert response is not None
        assert "error" in response

    @pytest.mark.asyncio
    async def test_create_async_error_handling(self, httpx_mock: HTTPXMock) -> None:
        """Test asynchronous error handling."""
        httpx_mock.add_response(
            url="https://api.picaos.com/v1/authkit?limit=100&page=1",
            method="POST",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        client = AuthKitToken("sk_test_invalid")
        response = await client.create_async()

        assert response is not None
        assert "error" in response

    def test_deprecated_parameters(
        self, httpx_mock: HTTPXMock, mock_authkit_response: dict
    ) -> None:
        """Test that deprecated parameters still work."""
        httpx_mock.add_response(
            url="https://api.picaos.com/v1/authkit?limit=100&page=1",
            method="POST",
            json=mock_authkit_response,
        )

        client = AuthKitToken("sk_test_123")
        response = client.create(group="test_group", label="test_label")

        assert response is not None
        assert response["total"] == 1
