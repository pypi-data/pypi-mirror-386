import logging
import uuid
from datetime import datetime, timezone

from bson import ObjectId

from oidcauthlib.auth.cache.oauth_cache import OAuthCache
from oidcauthlib.auth.models.cache_item import CacheItem
from oidcauthlib.auth.repository.base_repository import (
    AsyncBaseRepository,
)
from oidcauthlib.auth.repository.repository_factory import (
    RepositoryFactory,
)
from oidcauthlib.utilities.environment.abstract_environment_variables import (
    AbstractEnvironmentVariables,
)
from oidcauthlib.utilities.logger.log_levels import SRC_LOG_LEVELS

logger = logging.getLogger(__name__)
logger.setLevel(SRC_LOG_LEVELS["AUTH"])


class OAuthMongoCache(OAuthCache):
    """
    OAuthMongoCache is a cache implementation for OAuth tokens using MongoDB.
    It inherits from OAuthCache and provides methods to set, get, and delete cache entries
    in a MongoDB collection. The cache is initialized with a unique ID and connects to
    a MongoDB database specified by environment variables.

    """

    def __init__(self, *, environment_variables: AbstractEnvironmentVariables) -> None:
        """
        Initialize the OAuthMongoCache with a unique ID and MongoDB connection.
        It reads the connection string, database name, and collection name from environment variables.
        The environment variables required are:
        - MONGO_URL: The connection string for the MongoDB database.
        - MONGO_DB_NAME: The name of the MongoDB database.
        - MONGO_DB_AUTH_CACHE_COLLECTION_NAME: The name of the MongoDB collection for the
            authentication cache.

        """
        self.id_ = uuid.uuid4()
        self.repository: AsyncBaseRepository[CacheItem] = (
            RepositoryFactory.get_repository(
                repository_type=environment_variables.oauth_cache,
                environment_variables=environment_variables,
            )
        )
        collection_name: str | None = (
            environment_variables.mongo_db_auth_cache_collection_name
        )
        if collection_name is None:
            raise ValueError(
                "MONGO_DB_AUTH_CACHE_COLLECTION_NAME environment variable must be set"
            )
        self.collection_name: str = collection_name

        self.environment_variables: AbstractEnvironmentVariables = environment_variables
        if self.environment_variables is None:
            raise ValueError(
                "OAuthMongoCache requires an EnvironmentVariables instance."
            )
        if not isinstance(self.environment_variables, AbstractEnvironmentVariables):
            raise TypeError(
                "environment_variables must be an instance of EnvironmentVariables"
            )

    @property
    def id(self) -> uuid.UUID:
        """
        Get the unique identifier for this cache instance.
        """
        return self.id_

    async def delete(self, key: str) -> None:
        """
        Delete a cache entry.

        :param key: Unique identifier for the cache entry.
        """
        # check if the key exists in the repository
        logger.debug(f" ====== Delete: {key} =====")
        cache_item: CacheItem | None = await self.repository.find_by_fields(
            collection_name=self.collection_name,
            model_class=CacheItem,
            fields={
                "key": key,
            },
        )
        disable_delete: bool | None = (
            self.environment_variables.mongo_db_cache_disable_delete
        )
        if cache_item is not None and cache_item.id:
            # delete the cache item if it exists
            logger.debug(f" ====== Deleting {cache_item.id} =====")
            if disable_delete:
                cache_item.deleted = datetime.now(timezone.utc)
                await self.repository.insert_or_update(
                    collection_name=self.collection_name,
                    model_class=CacheItem,
                    item=cache_item,
                    keys={
                        "key": key,
                    },
                )
            else:
                await self.repository.delete_by_id(
                    collection_name=self.collection_name,
                    document_id=cache_item.id,
                )

    async def get(self, key: str, default: str | None = None) -> str | None:
        """
        Retrieve a value from the cache.

        :param key: Unique identifier for the cache entry.
        :param default: Default value to return if the key is not found.
        :return: Retrieved value or None if not found or expired.
        """

        cache_item: CacheItem | None = await self.repository.find_by_fields(
            collection_name=self.collection_name,
            model_class=CacheItem,
            fields={
                "key": key,
            },
        )
        logger.debug(
            f" ====== For key {key} found {cache_item} default {default} ====="
        )
        return cache_item.value if cache_item is not None else default

    async def set(self, key: str, value: str, expires: int | None = None) -> None:
        """
        Set a value in the cache with optional expiration.

        :param key: Unique identifier for the cache entry.
        :param value: Value to be stored.
        :param expires: Expiration time in seconds. Defaults to None (no expiration).
        """
        logger.debug(f" ====== Set: {key} {value} =====")
        # first see if the key already exists
        existing_cache_item: CacheItem | None = await self.repository.find_by_fields(
            collection_name=self.collection_name,
            model_class=CacheItem,
            fields={
                "key": key,
            },
        )
        if existing_cache_item is not None:
            logger.debug(f" ====== Existing for key {key}: {existing_cache_item} =====")
            # if it exists, update the value
            existing_cache_item.value = value
            existing_cache_item_id: ObjectId = existing_cache_item.id
            updated_cache_item: CacheItem | None = await self.repository.update_by_id(
                collection_name=self.collection_name,
                document_id=existing_cache_item_id,
                update_data=existing_cache_item,
                model_class=CacheItem,
            )
            if updated_cache_item is None:
                raise ValueError(
                    f"Failed to update cache item with ID: {existing_cache_item_id} for key: {key}"
                )
            logger.debug(
                f"Cache item updated with ID: {updated_cache_item.id} for key: {key} with value: {value}.\n"
            )
        else:
            logger.debug(f" ====== Creating new cache item {key}: {value} =====")
            cache_item = CacheItem(
                key=key, value=value, created=datetime.now(timezone.utc)
            )
            new_object_id = await self.repository.insert(
                collection_name=self.collection_name,
                model=cache_item,
            )
            logger.debug(
                f"New cache item created with ID: {new_object_id}: {cache_item}"
            )
