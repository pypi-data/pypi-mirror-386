"""Base class for OpenAI skills."""

from typing import Type

from langchain_core.tools.base import ToolException
from pydantic import BaseModel, Field

from intentkit.config.config import config
from intentkit.skills.base import IntentKitSkill


class OpenAIBaseTool(IntentKitSkill):
    """Base class for all OpenAI skills.

    This class provides common functionality for all OpenAI skills.
    """

    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]

    def get_api_key(self) -> str:
        context = self.get_context()
        skill_config = context.agent.skill_config(self.category)
        api_key_provider = skill_config.get("api_key_provider")
        if api_key_provider == "platform":
            if not config.openai_api_key:
                raise ToolException("OpenAI API key is not configured")
            return config.openai_api_key
        # for backward compatibility, may only have api_key in skill_config
        if skill_config.get("api_key"):
            return skill_config.get("api_key")
        raise ToolException(
            f"Invalid API key provider: {api_key_provider}, or no api_key in config"
        )

    @property
    def category(self) -> str:
        return "openai"
