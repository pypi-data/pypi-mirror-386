"""Tests for utility functions."""

from authkit_token.utils import get_headers


def test_get_headers() -> None:
    """Test header generation."""
    secret = "sk_test_123456"
    headers = get_headers(secret)

    assert headers["X-Pica-Secret"] == secret
    assert headers["Content-Type"] == "application/json"
    assert len(headers) == 2
