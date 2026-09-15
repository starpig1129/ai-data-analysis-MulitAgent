from typing import TYPE_CHECKING, Any

from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from ..config import WORKING_DIRECTORY
from ..core.node import get_state_attr, update_artifact_dict
from ..core.schemas import ArtifactSchema
from ..tools.basetool import list_directory
from ..tools.FileEdit import collect_data, create_document, read_document
from ..tools.internet import google_search, scrape_webpages
from .base import BaseAgent

if TYPE_CHECKING:
    from ..core.language_models import LanguageModelManager
    from ..core.state import State


class SearchAgent(BaseAgent):
    """Agent responsible for gathering and summarizing research information."""

    def __init__(
        self,
        language_model_manager: "LanguageModelManager",
        team_members: list[str],
        working_directory: str = WORKING_DIRECTORY,
    ):
        """
        Initialize the SearchAgent.
        """
        super().__init__(
            agent_name="search_agent",
            language_model_manager=language_model_manager,
            team_members=team_members,
            working_directory=working_directory,
            response_format=ArtifactSchema,
        )

    def _get_tools(self) -> list:
        """Get the list of tools for information retrieval and summarization."""
        api_wrapper = WikipediaAPIWrapper(wiki_client=None)
        wikipedia = WikipediaQueryRun(api_wrapper=api_wrapper)
        base_tools = [
            create_document,
            read_document,
            collect_data,
            wikipedia,
            google_search,
            scrape_webpages,
            list_directory,
        ] + load_tools(["arxiv"])

        return base_tools

    def get_state_updates(self, state: "State", output: Any) -> dict[str, Any]:
        """Return state updates for search artifacts."""

        def safe_get(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        current = get_state_attr(state, "search_artifacts", {})
        new_data = safe_get(output, "artifacts", output)
        return {"search_artifacts": update_artifact_dict(current, new_data)}
