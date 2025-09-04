"""
TenantAuthenticator - Handle tenant authentication and request routing
This module provides authentication and routing functionality for multi-tenant requests.
"""

import hashlib
import secrets
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from tenant_manager import TenantManager, TenantNotFoundError

logger = logging.getLogger(__name__)


class TenantAuthenticationError(Exception):
    """Raised when tenant authentication fails"""

    pass


class TenantAPIKey:
    """Represents a tenant API key with metadata"""

    def __init__(
        self,
        tenant_id: UUID,
        key_id: str,
        key_hash: str,
        name: str = "Default",
        created_at: datetime = None,
        last_used: datetime = None,
        is_active: bool = True,
    ):
        self.tenant_id = tenant_id
        self.key_id = key_id
        self.key_hash = key_hash
        self.name = name
        self.created_at = created_at or datetime.now()
        self.last_used = last_used
        self.is_active = is_active


class TenantAuthenticator:
    """
    Handle tenant authentication and request routing.

    This authenticator provides:
    1. API key generation and validation
    2. Tenant identification from requests
    3. Database connection routing per tenant
    4. Security and rate limiting hooks
    """

    def __init__(self, tenant_manager: TenantManager):
        """
        Initialize authenticator with tenant manager.

        Args:
            tenant_manager: TenantManager instance for tenant operations
        """
        self.tenant_manager = tenant_manager
        self._api_key_cache: Dict[str, TenantAPIKey] = {}
        self._cache_expiry = timedelta(minutes=15)  # Cache API keys for 15 minutes
        self._last_cache_clear = datetime.now()

    def _clear_expired_cache(self):
        """Clear expired entries from API key cache"""
        now = datetime.now()
        if now - self._last_cache_clear > self._cache_expiry:
            self._api_key_cache.clear()
            self._last_cache_clear = now

    def _hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key for secure storage.

        Args:
            api_key: Raw API key to hash

        Returns:
            Hashed API key for storage
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    def generate_api_key(
        self, tenant_id: UUID, key_name: str = "Default"
    ) -> tuple[str, str]:
        """
        Generate a new API key for a tenant.

        Args:
            tenant_id: UUID of the tenant
            key_name: Human-readable name for the API key

        Returns:
            Tuple of (api_key, key_id) - store key_id and hash for validation

        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        # Generate secure random API key
        api_key = f"mtrag_{secrets.token_urlsafe(32)}"
        key_id = f"key_{secrets.token_urlsafe(8)}"

        logger.info(f"Generated API key '{key_name}' for tenant {tenant_id}")

        return api_key, key_id

    async def store_api_key(
        self, tenant_id: UUID, key_id: str, key_hash: str, key_name: str = "Default"
    ) -> bool:
        """
        Store API key information in the catalog database.

        Args:
            tenant_id: UUID of the tenant
            key_id: Unique identifier for the key
            key_hash: Hashed API key for validation
            key_name: Human-readable name for the key

        Returns:
            True if storage successful

        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        try:
            # Verify tenant exists
            tenant_info = await self.tenant_manager.get_tenant(tenant_id)
            if not tenant_info:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            # Store API key in tenant configs
            api_key_config = {
                "key_id": key_id,
                "key_hash": key_hash,
                "name": key_name,
                "created_at": datetime.now().isoformat(),
                "last_used": None,
                "is_active": True,
            }

            await self.tenant_manager.catalog_db.update_tenant_config(
                tenant_id, {f"api_key_{key_id}": api_key_config}
            )

            logger.info(f"Stored API key '{key_name}' for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store API key for tenant {tenant_id}: {str(e)}")
            raise

    async def authenticate_tenant(self, api_key: str) -> UUID:
        """
        Authenticate tenant by API key.

        Args:
            api_key: API key provided in request

        Returns:
            UUID of authenticated tenant

        Raises:
            TenantAuthenticationError: If authentication fails
        """
        try:
            # Clear expired cache entries
            self._clear_expired_cache()

            # Check cache first
            key_hash = self._hash_api_key(api_key)
            if key_hash in self._api_key_cache:
                cached_key = self._api_key_cache[key_hash]
                if cached_key.is_active:
                    # Update last used time
                    await self._update_key_last_used(
                        cached_key.tenant_id, cached_key.key_id
                    )
                    logger.debug(
                        f"Authenticated tenant {cached_key.tenant_id} from cache"
                    )
                    return cached_key.tenant_id
                else:
                    # Remove inactive key from cache
                    del self._api_key_cache[key_hash]

            # Search all tenants for matching API key
            tenant_id = await self._find_tenant_by_api_key(api_key)

            if not tenant_id:
                logger.warning("Authentication failed: Invalid API key")
                raise TenantAuthenticationError("Invalid API key")

            logger.info(f"Successfully authenticated tenant: {tenant_id}")
            return tenant_id

        except TenantAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication failed with error: {str(e)}")
            raise TenantAuthenticationError(f"Authentication error: {str(e)}")

    async def _find_tenant_by_api_key(self, api_key: str) -> Optional[UUID]:
        """
        Find tenant ID by searching all tenant API keys.

        Args:
            api_key: API key to search for

        Returns:
            Tenant UUID if found, None otherwise
        """
        key_hash = self._hash_api_key(api_key)

        # Get all tenants
        tenants = await self.tenant_manager.list_tenants(
            limit=1000
        )  # TODO: Paginate for large deployments

        for tenant in tenants:
            try:
                # Get tenant configs
                tenant_configs = (
                    await self.tenant_manager.catalog_db.get_tenant_configs(
                        tenant.tenant_id
                    )
                )

                # Check all API keys for this tenant
                for config_key, config_value in tenant_configs.items():
                    if config_key.startswith("api_key_") and isinstance(
                        config_value, dict
                    ):
                        stored_hash = config_value.get("key_hash")
                        is_active = config_value.get("is_active", True)

                        if stored_hash == key_hash and is_active:
                            # Cache the valid key
                            key_id = config_value.get("key_id")
                            api_key_obj = TenantAPIKey(
                                tenant_id=tenant.tenant_id,
                                key_id=key_id,
                                key_hash=key_hash,
                                name=config_value.get("name", "Unknown"),
                                created_at=datetime.fromisoformat(
                                    config_value.get(
                                        "created_at", datetime.now().isoformat()
                                    )
                                ),
                                last_used=datetime.fromisoformat(
                                    config_value.get("last_used")
                                )
                                if config_value.get("last_used")
                                else None,
                                is_active=is_active,
                            )
                            self._api_key_cache[key_hash] = api_key_obj

                            # Update last used time
                            await self._update_key_last_used(tenant.tenant_id, key_id)

                            return tenant.tenant_id

            except Exception as e:
                logger.warning(
                    f"Error checking API keys for tenant {tenant.tenant_id}: {str(e)}"
                )
                continue

        return None

    async def _update_key_last_used(self, tenant_id: UUID, key_id: str):
        """Update the last used timestamp for an API key"""
        try:
            config_key = f"api_key_{key_id}"
            tenant_configs = await self.tenant_manager.catalog_db.get_tenant_configs(
                tenant_id
            )

            if config_key in tenant_configs:
                api_key_config = tenant_configs[config_key].copy()
                api_key_config["last_used"] = datetime.now().isoformat()

                await self.tenant_manager.catalog_db.update_tenant_config(
                    tenant_id, {config_key: api_key_config}
                )

        except Exception as e:
            logger.warning(
                f"Failed to update last used time for key {key_id}: {str(e)}"
            )

    async def get_tenant_database_connection(self, tenant_id: UUID):
        """
        Get database connection for authenticated tenant.

        Args:
            tenant_id: UUID of authenticated tenant

        Returns:
            Database connection URL for the tenant

        Raises:
            TenantNotFoundError: If tenant doesn't exist or is inactive
        """
        try:
            db_url = await self.tenant_manager.get_tenant_database_url(tenant_id)
            return db_url

        except Exception as e:
            logger.error(
                f"Failed to get database connection for tenant {tenant_id}: {str(e)}"
            )
            raise

    async def revoke_api_key(self, tenant_id: UUID, key_id: str) -> bool:
        """
        Revoke an API key by marking it as inactive.

        Args:
            tenant_id: UUID of the tenant
            key_id: ID of the key to revoke

        Returns:
            True if revocation successful

        Raises:
            TenantNotFoundError: If tenant or key doesn't exist
        """
        try:
            config_key = f"api_key_{key_id}"
            tenant_configs = await self.tenant_manager.catalog_db.get_tenant_configs(
                tenant_id
            )

            if config_key not in tenant_configs:
                raise TenantNotFoundError(
                    f"API key {key_id} not found for tenant {tenant_id}"
                )

            # Mark key as inactive
            api_key_config = tenant_configs[config_key].copy()
            api_key_config["is_active"] = False
            api_key_config["revoked_at"] = datetime.now().isoformat()

            await self.tenant_manager.catalog_db.update_tenant_config(
                tenant_id, {config_key: api_key_config}
            )

            # Remove from cache if present
            key_hash = api_key_config.get("key_hash")
            if key_hash in self._api_key_cache:
                del self._api_key_cache[key_hash]

            logger.info(f"Revoked API key {key_id} for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to revoke API key {key_id} for tenant {tenant_id}: {str(e)}"
            )
            raise

    async def list_tenant_api_keys(self, tenant_id: UUID) -> Dict[str, Dict[str, Any]]:
        """
        List all API keys for a tenant.

        Args:
            tenant_id: UUID of the tenant

        Returns:
            Dictionary of API key information (without sensitive data)

        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        try:
            # Verify tenant exists
            tenant_info = await self.tenant_manager.get_tenant(tenant_id)
            if not tenant_info:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            tenant_configs = await self.tenant_manager.catalog_db.get_tenant_configs(
                tenant_id
            )

            api_keys = {}
            for config_key, config_value in tenant_configs.items():
                if config_key.startswith("api_key_") and isinstance(config_value, dict):
                    key_id = config_value.get("key_id")
                    api_keys[key_id] = {
                        "name": config_value.get("name", "Unknown"),
                        "created_at": config_value.get("created_at"),
                        "last_used": config_value.get("last_used"),
                        "is_active": config_value.get("is_active", True),
                        "revoked_at": config_value.get("revoked_at"),
                    }

            return api_keys

        except Exception as e:
            logger.error(f"Failed to list API keys for tenant {tenant_id}: {str(e)}")
            raise

    def extract_api_key_from_header(self, authorization_header: str) -> Optional[str]:
        """
        Extract API key from Authorization header.

        Args:
            authorization_header: Authorization header value

        Returns:
            API key if valid format, None otherwise
        """
        if not authorization_header:
            return None

        if not authorization_header.startswith("Bearer "):
            return None

        api_key = authorization_header[7:]  # Remove "Bearer " prefix

        # Basic validation
        if not api_key or len(api_key) < 10:
            return None

        return api_key

    async def create_tenant_api_key(
        self, tenant_id: UUID, key_name: str = "Default"
    ) -> str:
        """
        Create and store a new API key for a tenant.

        Args:
            tenant_id: UUID of the tenant
            key_name: Human-readable name for the API key

        Returns:
            Generated API key (store this securely, it won't be shown again)

        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        try:
            # Generate API key
            api_key, key_id = self.generate_api_key(tenant_id, key_name)
            key_hash = self._hash_api_key(api_key)

            # Store in database
            await self.store_api_key(tenant_id, key_id, key_hash, key_name)

            logger.info(f"Created API key '{key_name}' for tenant {tenant_id}")
            return api_key

        except Exception as e:
            logger.error(f"Failed to create API key for tenant {tenant_id}: {str(e)}")
            raise
