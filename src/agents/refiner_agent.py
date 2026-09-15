from typing import TYPE_CHECKING

from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from ..config import WORKING_DIRECTORY
from ..core.schemas import ArtifactSchema
from ..tools.basetool import list_directory
from ..tools.FileEdit import create_document, edit_document, read_document
from ..tools.internet import google_search, scrape_webpages
from .base import BaseAgent

if TYPE_CHECKING:
    from ..core.language_models import LanguageModelManager


class RefinerAgent(BaseAgent):
    """Agent responsible for optimizing and enhancing research reports."""

    def __init__(
        self,
        language_model_manager: "LanguageModelManager",
        team_members: list[str],
        working_directory: str = WORKING_DIRECTORY,
    ):
        """
        Initialize the RefinerAgent.

        Args:
            language_model_manager: Manager for language model configuration.
            team_members: List of team member roles for collaboration.
            working_directory: The directory where the agent's data will be stored.
        """
        super().__init__(
            agent_name="refiner_agent",
            language_model_manager=language_model_manager,
            team_members=team_members,
            working_directory=working_directory,
        )
        self.response_format = ArtifactSchema

    def _get_tools(self) -> list:
        """Get the list of tools for report refinement."""
        api_wrapper = WikipediaAPIWrapper(wiki_client=None)
        wikipedia = WikipediaQueryRun(api_wrapper=api_wrapper)
        base_tools = [
            create_document,
            read_document,
            edit_document,
            wikipedia,
            google_search,
            scrape_webpages,
            list_directory,
        ] + load_tools(["arxiv"])

        return base_tools
