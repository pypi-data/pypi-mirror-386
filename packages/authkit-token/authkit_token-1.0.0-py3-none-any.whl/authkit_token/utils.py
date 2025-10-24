"""Utility functions for authkit-token package."""


def get_headers(secret: str) -> dict[str, str]:
    """
    Generate request headers with the API secret.

    Args:
        secret: The API secret key

    Returns:
        Dictionary of HTTP headers
    """
    return {
        "X-Pica-Secret": secret,
        "Content-Type": "application/json",
    }
