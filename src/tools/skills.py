from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..core.agent_config_loader import get_agent_config_loader
from ..logger import setup_logger

logger = setup_logger()


class LookupSkillInput(BaseModel):
    """Input for LookupSkill tool."""

    skill_name: str = Field(
        description="Name of the skill to lookup (from Available Skills list)"
    )


class LookupSkill(BaseTool):
    """Tool to lookup detailed instructions for a skill."""

    name: str = "lookup_skill"
    description: str = (
        "Retrieve detailed instructions and content for a specific skill. "
        "Use this when you need procedural knowledge or workflows defined in a skill."
    )
    args_schema: type[BaseModel] = LookupSkillInput

    def _run(self, skill_name: str) -> str:
        loader = get_agent_config_loader()
        content = loader.get_skill_content(skill_name)

        if content:
            logger.info(f"Agent looked up skill: {skill_name}")
            return content
        else:
            msg = f"Error: Skill '{skill_name}' not found. Please check the 'Available Skills' list."
            logger.warning(f"Skill lookup failed: {skill_name}")
            return msg

    async def _arun(self, skill_name: str) -> str:
        # Re-use sync implementation for simplicity
        return self._run(skill_name)
