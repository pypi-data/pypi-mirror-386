"""Service container for business logic layer dependencies."""

from dependency_injector import containers, providers

from axmp_ai_agent_core.agent.util.agent_cache import AsyncTTLQueue
from axmp_ai_agent_core.di.repository_container import RepositoriesContainer
from axmp_ai_agent_core.di.resource_container import ResourcesContainer
from axmp_ai_agent_core.service.agent_profile_service import AgentProfileService
from axmp_ai_agent_core.service.user_service import UserService
from axmp_ai_agent_core.service.workspace_service import WorkspaceService


class ServicesContainer(containers.DeclarativeContainer):
    """Container for service layer dependencies."""

    wiring_config = containers.WiringConfiguration(
        # modules=[
        #     "axmp_ai_agent_core.router.user_credential_router",
        # ],
        packages=[
            "axmp_ai_agent_core.router",
        ],
    )

    # Resource dependencies
    resources: providers.Container = providers.Container(
        ResourcesContainer,
    )

    # Repository dependencies
    repositories: providers.Container = providers.Container(
        RepositoriesContainer,
    )

    # Service providers
    # --------------------------------------------------------------------------
    agent_ttl_queue: providers.Factory[AsyncTTLQueue] = providers.Singleton(
        AsyncTTLQueue,
        config=resources.agent_ttl_queue_config,
    )

    user_service: providers.Factory[UserService] = providers.Factory(
        UserService,
        client=resources.mongo_client,
        user_repository=repositories.user_repository,
        group_repository=repositories.group_repository,
        user_credential_repository=repositories.user_credential_repository,
    )

    agent_profile_service: providers.Factory[AgentProfileService] = providers.Factory(
        AgentProfileService,
        client=resources.mongo_client,
        agent_profile_repository=repositories.agent_profile_repository,
        chat_file_repository=repositories.chat_file_repository,
        llm_provider_repository=repositories.llm_provider_repository,
        user_credential_repository=repositories.user_credential_repository,
        chat_memory_repository=repositories.chat_memory_repository,
        agent_profile_history_repository=repositories.agent_profile_history_repository,
    )

    workspace_service: providers.Factory[WorkspaceService] = providers.Factory(
        WorkspaceService,
        client=resources.mongo_client,
        conversation_repository=repositories.conversation_repository,
        llm_provider_repository=repositories.llm_provider_repository,
    )
