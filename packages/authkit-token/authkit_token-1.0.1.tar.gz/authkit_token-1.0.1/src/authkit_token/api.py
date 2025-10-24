"""API functions for interacting with Pica AuthKit."""

import asyncio
from typing import Optional, cast

import httpx

from .types import AuthkitResponse, ConnectorPaginationOptions, CreateEventLinkPayload


async def _paginate_authkit_connections_async(
    url: str,
    headers: dict[str, str],
    payload: Optional[CreateEventLinkPayload] = None,
    options: Optional[ConnectorPaginationOptions] = None,
) -> AuthkitResponse:
    """
    Pagination helper function for authkit API that fetches all pages asynchronously.

    Args:
        url: Base URL for the API
        headers: Request headers
        payload: Request payload
        options: Pagination options

    Returns:
        Combined results from all pages
    """
    if options is None:
        options = {}

    limit = options.get("limit", 100)
    max_concurrent_requests = options.get("max_concurrent_requests", 3)
    max_retries = options.get("max_retries", 3)

    async def fetch_authkit_page(
        client: httpx.AsyncClient, page: int, page_limit: int
    ) -> AuthkitResponse:
        """Fetch a specific page."""
        response = await client.post(
            f"{url}/v1/authkit",
            params={"limit": page_limit, "page": page},
            json=payload or {},
            headers=headers,
        )
        response.raise_for_status()
        return cast(AuthkitResponse, response.json())

    async def fetch_page_with_retry(client: httpx.AsyncClient, page: int) -> AuthkitResponse:
        """Fetch a page with retry logic."""
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                return await fetch_authkit_page(client, page, limit)
            except Exception as error:
                last_error = error
                if attempt < max_retries:
                    # Exponential backoff: wait 1s, 2s, 4s...
                    await asyncio.sleep(1.0 * (2 ** (attempt - 1)))

        if last_error:
            raise last_error
        raise RuntimeError("Failed to fetch page")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First request to get total pages count
        first_response = await fetch_authkit_page(client, 1, limit)
        pages = first_response["pages"]
        total = first_response["total"]

        # If we got all data in first request, return it
        if pages <= 1:
            return first_response

        # Create array of remaining page numbers to fetch
        remaining_pages = list(range(2, pages + 1))

        # Execute requests in batches to avoid overwhelming the API
        responses: list[AuthkitResponse] = [first_response]

        for i in range(0, len(remaining_pages), max_concurrent_requests):
            batch = remaining_pages[i : i + max_concurrent_requests]
            batch_promises = [fetch_page_with_retry(client, page) for page in batch]

            try:
                batch_results = await asyncio.gather(*batch_promises)
                responses.extend(batch_results)
            except Exception as error:
                print(f"Failed to fetch authkit batch starting at page {batch[0]}: {error}")
                raise

        # Combine all results
        all_rows = []
        for response in responses:
            all_rows.extend(response["rows"])

        # Get the latest request_id from the most recent response
        latest_response = responses[-1]

        return {
            "rows": all_rows,
            "page": 1,  # Since we're returning all data, we're effectively on "page 1"
            "pages": 1,
            "total": total,
            "request_id": latest_response["request_id"],
        }


def _paginate_authkit_connections_sync(
    url: str,
    headers: dict[str, str],
    payload: Optional[CreateEventLinkPayload] = None,
    options: Optional[ConnectorPaginationOptions] = None,
) -> AuthkitResponse:
    """
    Pagination helper function for authkit API that fetches all pages synchronously.

    Args:
        url: Base URL for the API
        headers: Request headers
        payload: Request payload
        options: Pagination options

    Returns:
        Combined results from all pages
    """
    if options is None:
        options = {}

    limit = options.get("limit", 100)
    max_retries = options.get("max_retries", 3)

    def fetch_authkit_page(client: httpx.Client, page: int, page_limit: int) -> AuthkitResponse:
        """Fetch a specific page."""
        response = client.post(
            f"{url}/v1/authkit",
            params={"limit": page_limit, "page": page},
            json=payload or {},
            headers=headers,
        )
        response.raise_for_status()
        return cast(AuthkitResponse, response.json())

    def fetch_page_with_retry(client: httpx.Client, page: int) -> AuthkitResponse:
        """Fetch a page with retry logic."""
        import time

        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                return fetch_authkit_page(client, page, limit)
            except Exception as error:
                last_error = error
                if attempt < max_retries:
                    # Exponential backoff: wait 1s, 2s, 4s...
                    time.sleep(1.0 * (2 ** (attempt - 1)))

        if last_error:
            raise last_error
        raise RuntimeError("Failed to fetch page")

    with httpx.Client(timeout=30.0) as client:
        # First request to get total pages count
        first_response = fetch_authkit_page(client, 1, limit)
        pages = first_response["pages"]
        total = first_response["total"]

        # If we got all data in first request, return it
        if pages <= 1:
            return first_response

        # Create array of remaining page numbers to fetch
        remaining_pages = list(range(2, pages + 1))

        # Fetch remaining pages sequentially (no concurrent requests in sync mode)
        responses: list[AuthkitResponse] = [first_response]

        for page in remaining_pages:
            try:
                response = fetch_page_with_retry(client, page)
                responses.append(response)
            except Exception as error:
                print(f"Failed to fetch authkit page {page}: {error}")
                raise

        # Combine all results
        all_rows = []
        for response in responses:
            all_rows.extend(response["rows"])

        # Get the latest request_id from the most recent response
        latest_response = responses[-1]

        return {
            "rows": all_rows,
            "page": 1,  # Since we're returning all data, we're effectively on "page 1"
            "pages": 1,
            "total": total,
            "request_id": latest_response["request_id"],
        }


async def create_event_link_token_async(
    headers: dict[str, str],
    url: str,
    payload: Optional[CreateEventLinkPayload] = None,
) -> Optional[AuthkitResponse]:
    """
    Create an event link token asynchronously.

    Args:
        headers: Request headers
        url: Base URL for the API
        payload: Optional payload with identity and other parameters

    Returns:
        Authkit response with connections data, or None on error
    """
    try:
        # Fetch all authkit connections with pagination support
        authkit_response = await _paginate_authkit_connections_async(
            url, headers, payload, {"limit": 100, "max_concurrent_requests": 3, "max_retries": 3}
        )
        return authkit_response
    except httpx.HTTPStatusError as error:
        # Return error response data if available
        return cast(AuthkitResponse, error.response.json()) if error.response else None
    except Exception:
        return None


def create_event_link_token_sync(
    headers: dict[str, str],
    url: str,
    payload: Optional[CreateEventLinkPayload] = None,
) -> Optional[AuthkitResponse]:
    """
    Create an event link token synchronously.

    Args:
        headers: Request headers
        url: Base URL for the API
        payload: Optional payload with identity and other parameters

    Returns:
        Authkit response with connections data, or None on error
    """
    try:
        # Fetch all authkit connections with pagination support
        authkit_response = _paginate_authkit_connections_sync(
            url, headers, payload, {"limit": 100, "max_concurrent_requests": 3, "max_retries": 3}
        )
        return authkit_response
    except httpx.HTTPStatusError as error:
        # Return error response data if available
        return cast(AuthkitResponse, error.response.json()) if error.response else None
    except Exception:
        return None
