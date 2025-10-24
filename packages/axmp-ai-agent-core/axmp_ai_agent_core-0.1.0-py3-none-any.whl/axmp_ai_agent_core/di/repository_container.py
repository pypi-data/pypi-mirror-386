"""Repository container for data access layer dependencies."""

from dependency_injector import containers, providers

from axmp_ai_agent_core.db.agent_profile_history_repository import (
    AgentProfileHistoryRepository,
)
from axmp_ai_agent_core.db.agent_profile_repository import AgentProfileRepository
from axmp_ai_agent_core.db.chat_file_repository import ChatFileRepository
from axmp_ai_agent_core.db.chat_memory_repository import ChatMemoryRepository
from axmp_ai_agent_core.db.conversation_repository import ConversationRepository
from axmp_ai_agent_core.db.group_repository import GroupRepository
from axmp_ai_agent_core.db.llm_provider_repository import LlmProviderRepository
from axmp_ai_agent_core.db.user_credential_repository import UserCredentialRepository
from axmp_ai_agent_core.db.user_repository import UserRepository
from axmp_ai_agent_core.di.resource_container import ResourcesContainer
from axmp_ai_agent_core.setting import mongodb_settings


class RepositoriesContainer(containers.DeclarativeContainer):
    """Container for repository layer dependencies."""

    # Resource dependencies
    resources: providers.Container = providers.Container(
        ResourcesContainer,
    )

    # Repository providers
    # --------------------------------------------------------------------------
    user_repository: providers.Factory[UserRepository] = providers.Factory(
        UserRepository,
        collection=providers.Factory(
            lambda database: database[mongodb_settings.collection_user],
            database=resources.mongo_database,
        ),
    )

    group_repository: providers.Factory[GroupRepository] = providers.Factory(
        GroupRepository,
        collection=providers.Factory(
            lambda database: database[mongodb_settings.collection_group],
            database=resources.mongo_database,
        ),
    )

    user_credential_repository: providers.Factory[UserCredentialRepository] = (
        providers.Factory(
            UserCredentialRepository,
            collection=providers.Factory(
                lambda database: database[mongodb_settings.collection_user_credential],
                database=resources.mongo_database,
            ),
        )
    )

    agent_profile_repository: providers.Factory[AgentProfileRepository] = (
        providers.Factory(
            AgentProfileRepository,
            collection=providers.Factory(
                lambda database: database[mongodb_settings.collection_agent_profile],
                database=resources.mongo_database,
            ),
        )
    )

    chat_file_repository: providers.Factory[ChatFileRepository] = providers.Factory(
        ChatFileRepository,
        collection=providers.Factory(
            lambda database: database[mongodb_settings.collection_chat_file],
            database=resources.mongo_database,
        ),
    )

    llm_provider_repository: providers.Factory[LlmProviderRepository] = (
        providers.Factory(
            LlmProviderRepository,
            collection=providers.Factory(
                lambda database: database[mongodb_settings.collection_llm_provider],
                database=resources.mongo_database,
            ),
        )
    )

    chat_memory_repository: providers.Factory[ChatMemoryRepository] = providers.Factory(
        ChatMemoryRepository,
        collection=providers.Factory(
            lambda database: database[mongodb_settings.collection_chat_memory],
            database=resources.mongo_database,
        ),
    )

    conversation_repository: providers.Factory[ConversationRepository] = (
        providers.Factory(
            ConversationRepository,
            collection=providers.Factory(
                lambda database: database[mongodb_settings.collection_conversation],
                database=resources.mongo_database,
            ),
        )
    )

    agent_profile_history_repository: providers.Factory[
        AgentProfileHistoryRepository
    ] = providers.Factory(
        AgentProfileHistoryRepository,
        collection=providers.Factory(
            lambda database: database[
                mongodb_settings.collection_agent_profile_history
            ],
            database=resources.mongo_database,
        ),
    )
