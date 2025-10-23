from typing import Any, Dict, Optional

import httpx

from .config import Config


class APIError(Exception):
    """Base API exception"""

    pass


class UnauthorizedError(APIError):
    """Raised when API returns 401 unauthorized"""

    pass


class PaymentRequiredError(APIError):
    """Raised when API returns 402 payment required"""

    pass


class APITimeoutError(APIError):
    """Raised when API request times out"""

    pass


# Deprecated: Use APITimeoutError instead
TimeoutError = APITimeoutError


class APIClient:
    """
      Note: APIClient is kept for API compatibility but not used.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        require_auth: bool = True,
    ):
        # API key is not used.
        pass

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make a request to the API"""
        pass

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request to the API"""
        return self.request("GET", endpoint, params=params)

    def post(
        self, endpoint: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request to the API"""
        return self.request("POST", endpoint, json=json)

    def patch(
        self, endpoint: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a PATCH request to the API"""
        return self.request("PATCH", endpoint, json=json)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request to the API"""
        return self.request("DELETE", endpoint)

    def __str__(self) -> str:
        """For debugging"""
        return f"APIClient(base_url={self.base_url})"


class AsyncAPIClient:
    """
      Async version of APIClient using httpx.AsyncClient
      Note: AsyncAPIClient is kept for API compatibility but not used.
    """


    def __init__(
        self,
        api_key: Optional[str] = None,
        require_auth: bool = True,
    ):
        pass

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make an async request to the API"""
        pass

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an async GET request to the API"""
        return await self.request("GET", endpoint, params=params)

    async def post(
        self, endpoint: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an async POST request to the API"""
        return await self.request("POST", endpoint, json=json)

    async def patch(
        self, endpoint: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an async PATCH request to the API"""
        return await self.request("PATCH", endpoint, json=json)

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make an async DELETE request to the API"""
        return await self.request("DELETE", endpoint)

    async def aclose(self) -> None:
        """Close the async client"""
        pass

    async def __aenter__(self) -> "AsyncAPIClient":
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.aclose()

    def __str__(self) -> str:
        """For debugging"""
        return f"AsyncAPIClient(base_url={self.base_url})"
