"""Chat files model."""

from axmp_ai_agent_core.entity.base_model import WorkspaceBaseModel


class ChatFile(WorkspaceBaseModel):
    """Chat files model."""

    upload_url: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    project_id: str | None = None
