"""Resource container for external resources like database connections."""

import logging

from dependency_injector import containers, providers
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from axmp_ai_agent_core.agent.util.agent_cache import TTLQueueConfig
from axmp_ai_agent_core.setting import mongodb_settings

logger = logging.getLogger(__name__)


class ResourcesContainer(containers.DeclarativeContainer):
    """Container for external resources like database connections."""

    # MongoDB client as singleton - following main.py lifespan configuration
    mongo_client: providers.Singleton[AsyncIOMotorClient] = providers.Singleton(
        AsyncIOMotorClient,
        mongodb_settings.uri,
        serverSelectionTimeoutMS=mongodb_settings.connection_timeout_ms,
        heartbeatFrequencyMS=3600000,
        tz_aware=True,
    )

    # MongoDB database
    mongo_database: providers.Factory[AsyncIOMotorDatabase] = providers.Factory(
        lambda client: client[mongodb_settings.database],
        client=mongo_client,
    )

    # Agent TTL queue configuration
    agent_ttl_queue_config: providers.Singleton[TTLQueueConfig] = providers.Singleton(
        TTLQueueConfig,
    )
