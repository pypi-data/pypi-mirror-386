"""API key management client."""

from typing import Any, List, Optional

from ._base_client import BaseClient
from .config import ArkForgeConfig
from .models import (
    ApiKeyDetails,
    ApiKeyInfo,
    CreateKeyRequest,
    CreateKeyResponse,
)


class KeyManagementClient(BaseClient):
    """API key management client.

    This client provides methods for managing API keys including creation,
    listing, rotation, and revocation.

    Example:
        >>> from arkforge import KeyManagementClient
        >>> client = KeyManagementClient(api_key="sk-arkforge-admin-key")
        >>>
        >>> # Create new key
        >>> new_key = client.create_key(
        ...     CreateKeyRequest(
        ...         name="Production Key",
        ...         expires_in_days=90
        ...     )
        ... )
        >>> print(new_key.api_key)  # Save this!
        sk-arkforge-abc123...
        >>>
        >>> # List keys
        >>> keys = client.list_keys()
        >>> for key in keys:
        ...     print(f"{key.name}: {key.prefix}")
    """

    def __init__(
        self, api_key: str, base_url: str = "http://localhost:3001", **kwargs: Any
    ) -> None:
        """Initialize key management client.

        Args:
            api_key: Admin API key with key management scope
            base_url: API base URL (default: http://localhost:3001)
            **kwargs: Additional config options

        Example:
            >>> client = KeyManagementClient(
            ...     api_key="sk-arkforge-admin-abc123"
            ... )
        """
        config = ArkForgeConfig(api_key=api_key, base_url=base_url, **kwargs)
        super().__init__(config)

    def create_key(self, request: CreateKeyRequest) -> CreateKeyResponse:
        """Create new API key.

        WARNING: The full API key is only returned once! Store it securely.

        Args:
            request: Key creation request

        Returns:
            Created key response (includes full API key)

        Raises:
            ValidationError: Invalid request parameters
            AuthenticationError: Insufficient permissions
            RateLimitError: Rate limit exceeded
            ServiceError: Server error

        Example:
            >>> from arkforge.models import CreateKeyRequest
            >>> request = CreateKeyRequest(
            ...     name="Production Key",
            ...     expires_in_days=90,
            ...     scopes=["read", "write"]
            ... )
            >>> response = client.create_key(request)
            >>> api_key = response.api_key  # SAVE THIS!
            >>> print(f"Key ID: {response.key_id}")
            >>> print(f"Prefix: {response.prefix}")
        """
        response = self._http.request(
            method="POST",
            path="/api/v1/keys",
            json=request.model_dump(exclude_none=True, by_alias=True),
        )
        return CreateKeyResponse.model_validate(response)

    async def create_key_async(self, request: CreateKeyRequest) -> CreateKeyResponse:
        """Create new API key (async).

        Asynchronous version of create_key().

        Args:
            request: Key creation request

        Returns:
            Created key response

        Example:
            >>> response = await client.create_key_async(request)
        """
        response = await self._http.request_async(
            method="POST",
            path="/api/v1/keys",
            json=request.model_dump(exclude_none=True, by_alias=True),
        )
        return CreateKeyResponse.model_validate(response)

    def list_keys(self) -> List[ApiKeyInfo]:
        """List all API keys.

        Returns basic information about all API keys (without full keys).

        Returns:
            List of API key information

        Raises:
            AuthenticationError: Insufficient permissions
            RateLimitError: Rate limit exceeded
            ServiceError: Server error

        Example:
            >>> keys = client.list_keys()
            >>> for key in keys:
            ...     print(f"[{key.id}] {key.name}")
            ...     print(f"  Prefix: {key.prefix}")
            ...     print(f"  Scopes: {', '.join(key.scopes)}")
            ...     print(f"  Active: {key.is_active}")
        """
        response = self._http.request(method="GET", path="/api/v1/keys")
        return [ApiKeyInfo.model_validate(key) for key in response]

    async def list_keys_async(self) -> List[ApiKeyInfo]:
        """List all API keys (async).

        Asynchronous version of list_keys().

        Returns:
            List of API key information

        Example:
            >>> keys = await client.list_keys_async()
        """
        response = await self._http.request_async(method="GET", path="/api/v1/keys")
        return [ApiKeyInfo.model_validate(key) for key in response]

    def get_key_details(self, key_id: int) -> ApiKeyDetails:
        """Get API key details with usage statistics.

        Args:
            key_id: API key ID

        Returns:
            Detailed key information with usage stats

        Raises:
            ValidationError: Invalid key ID
            AuthenticationError: Insufficient permissions
            RateLimitError: Rate limit exceeded
            ServiceError: Server error

        Example:
            >>> details = client.get_key_details(123)
            >>> print(f"Name: {details.name}")
            >>> print(f"Total Requests: {details.usage.total_requests}")
            >>> print(f"Success Rate: {details.usage.successful_requests / details.usage.total_requests * 100:.1f}%")
        """
        response = self._http.request(method="GET", path=f"/api/v1/keys/{key_id}")
        return ApiKeyDetails.model_validate(response)

    async def get_key_details_async(self, key_id: int) -> ApiKeyDetails:
        """Get API key details with usage statistics (async).

        Args:
            key_id: API key ID

        Returns:
            Detailed key information

        Example:
            >>> details = await client.get_key_details_async(123)
        """
        response = await self._http.request_async(method="GET", path=f"/api/v1/keys/{key_id}")
        return ApiKeyDetails.model_validate(response)

    def revoke_key(self, key_id: int, reason: Optional[str] = None) -> None:
        """Revoke API key.

        This permanently deactivates the API key. It cannot be undone.

        Args:
            key_id: API key ID to revoke
            reason: Optional revocation reason

        Raises:
            ValidationError: Invalid key ID
            AuthenticationError: Insufficient permissions
            RateLimitError: Rate limit exceeded
            ServiceError: Server error

        Example:
            >>> client.revoke_key(123, reason="No longer needed")
        """
        json_data = {"reason": reason} if reason else None
        self._http.request(method="DELETE", path=f"/api/v1/keys/{key_id}", json=json_data)

    async def revoke_key_async(self, key_id: int, reason: Optional[str] = None) -> None:
        """Revoke API key (async).

        Args:
            key_id: API key ID to revoke
            reason: Optional revocation reason

        Example:
            >>> await client.revoke_key_async(123)
        """
        json_data = {"reason": reason} if reason else None
        await self._http.request_async(
            method="DELETE", path=f"/api/v1/keys/{key_id}", json=json_data
        )

    def rotate_key(self, key_id: int, name: Optional[str] = None) -> CreateKeyResponse:
        """Rotate API key (creates new key, revokes old).

        This creates a new API key and automatically revokes the old one.
        Use this for regular key rotation for security.

        Args:
            key_id: API key ID to rotate
            name: Optional name for new key

        Returns:
            New API key (old key is automatically revoked)

        Raises:
            ValidationError: Invalid key ID
            AuthenticationError: Insufficient permissions
            RateLimitError: Rate limit exceeded
            ServiceError: Server error

        Example:
            >>> new_key = client.rotate_key(123, name="Rotated Production Key")
            >>> print(new_key.api_key)  # Save the new key!
            >>> # Old key (ID 123) is now revoked
        """
        json_data = {"name": name} if name else None
        response = self._http.request(
            method="POST", path=f"/api/v1/keys/{key_id}/rotate", json=json_data
        )
        return CreateKeyResponse.model_validate(response)

    async def rotate_key_async(self, key_id: int, name: Optional[str] = None) -> CreateKeyResponse:
        """Rotate API key (async).

        Args:
            key_id: API key ID to rotate
            name: Optional name for new key

        Returns:
            New API key

        Example:
            >>> new_key = await client.rotate_key_async(123)
        """
        json_data = {"name": name} if name else None
        response = await self._http.request_async(
            method="POST", path=f"/api/v1/keys/{key_id}/rotate", json=json_data
        )
        return CreateKeyResponse.model_validate(response)

    def update_scopes(self, key_id: int, scopes: List[str]) -> None:
        """Update API key scopes.

        Args:
            key_id: API key ID
            scopes: New scopes list

        Raises:
            ValidationError: Invalid key ID or scopes
            AuthenticationError: Insufficient permissions
            RateLimitError: Rate limit exceeded
            ServiceError: Server error

        Example:
            >>> client.update_scopes(123, ["read", "write", "admin"])
        """
        self._http.request(
            method="PATCH", path=f"/api/v1/keys/{key_id}/scopes", json={"scopes": scopes}
        )

    async def update_scopes_async(self, key_id: int, scopes: List[str]) -> None:
        """Update API key scopes (async).

        Args:
            key_id: API key ID
            scopes: New scopes list

        Example:
            >>> await client.update_scopes_async(123, ["read"])
        """
        await self._http.request_async(
            method="PATCH", path=f"/api/v1/keys/{key_id}/scopes", json={"scopes": scopes}
        )
