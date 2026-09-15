from typing import TYPE_CHECKING, Any

from ..config import WORKING_DIRECTORY
from ..core.node import get_state_attr, update_artifact_dict
from ..core.schemas import ArtifactSchema
from ..tools.basetool import list_directory
from ..tools.FileEdit import create_document, edit_document, read_document
from .base import BaseAgent

if TYPE_CHECKING:
    from ..core.language_models import LanguageModelManager
    from ..core.state import State


class ReportAgent(BaseAgent):
    """Agent responsible for drafting comprehensive research reports."""

    def __init__(
        self,
        language_model_manager: "LanguageModelManager",
        team_members: list[str],
        working_directory: str = WORKING_DIRECTORY,
    ):
        """
        Initialize the ReportAgent.

        Args:
            language_model_manager: Manager for language model configuration.
            team_members: List of team member roles for collaboration.
            working_directory: The directory where the agent's data will be stored.
        """
        super().__init__(
            agent_name="report_agent",
            language_model_manager=language_model_manager,
            team_members=team_members,
            working_directory=working_directory,
        )
        self.response_format = ArtifactSchema

    def _get_tools(self) -> list:
        """Get the list of tools for report writing."""
        return [create_document, read_document, edit_document, list_directory]

    def get_state_updates(self, state: "State", output: Any) -> dict[str, Any]:
        """Return state updates for report artifacts.

        Args:
            state: The current workflow state.
            output: The agent's ArtifactSchema output.

        Returns:
            Dict with 'report_artifacts' field update.
        """
        current = get_state_attr(state, "report_artifacts", {})
        new_data = getattr(output, "artifacts", output)
        return {"report_artifacts": update_artifact_dict(current, new_data)}
