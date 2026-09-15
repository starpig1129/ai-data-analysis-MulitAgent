from typing import TYPE_CHECKING, Any

from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from ..config import WORKING_DIRECTORY
from ..tools.basetool import list_directory
from ..tools.FileEdit import collect_data
from ..tools.internet import google_search, scrape_webpages
from .base import BaseAgent

if TYPE_CHECKING:
    from ..core.language_models import LanguageModelManager
    from ..core.state import State


class HypothesisAgent(BaseAgent):
    """Agent responsible for generating research hypotheses."""

    def __init__(
        self,
        language_model_manager: "LanguageModelManager",
        team_members: list[str],
        working_directory: str = WORKING_DIRECTORY,
    ):
        """
        Initialize the HypothesisAgent.

        Args:
            language_model_manager: Manager for language model configuration.
            team_members: List of team member roles for collaboration.
            working_directory: The directory where the agent's data will be stored.
        """
        super().__init__(
            agent_name="hypothesis_agent",
            language_model_manager=language_model_manager,
            team_members=team_members,
            working_directory=working_directory,
        )

    def _get_tools(self) -> list:
        """Get the list of tools for hypothesis generation."""
        api_wrapper = WikipediaAPIWrapper(wiki_client=None)
        wikipedia = WikipediaQueryRun(api_wrapper=api_wrapper)
        base_tools = [
            collect_data,
            wikipedia,
            google_search,
            scrape_webpages,
            list_directory,
        ] + load_tools(["arxiv"])

        return base_tools

    def get_state_updates(self, state: "State", output: Any) -> dict[str, Any]:
        """Return state updates for hypothesis generation output.

        Args:
            state: The current workflow state.
            output: The agent's output (hypothesis content).

        Returns:
            Dict with 'hypothesis' field update.
        """
        # Extract hypothesis text, ensuring string serialization
        if isinstance(output, str):
            hypothesis_text = output
        elif hasattr(output, "hypothesis"):
            hypothesis_text = str(output.hypothesis)
        elif hasattr(output, "content"):
            hypothesis_text = str(output.content)
        else:
            hypothesis_text = str(output)

        return {"hypothesis": hypothesis_text}
