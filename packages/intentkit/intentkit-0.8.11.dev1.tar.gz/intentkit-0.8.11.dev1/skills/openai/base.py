"""Base class for OpenAI skills."""

from typing import Type

from langchain_core.tools.base import ToolException
from pydantic import BaseModel, Field

from intentkit.abstracts.skill import SkillStoreABC
from intentkit.skills.base import IntentKitSkill


class OpenAIBaseTool(IntentKitSkill):
    """Base class for all OpenAI skills.

    This class provides common functionality for all OpenAI skills.
    """

    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(
        description="The skill store for persisting data"
    )

    def get_api_key(self) -> str:
        context = self.get_context()
        skill_config = context.agent.skill_config(self.category)
        api_key_provider = skill_config.get("api_key_provider")
        if api_key_provider == "platform":
            return self.skill_store.get_system_config("openai_api_key")
        # for backward compatibility, may only have api_key in skill_config
        elif skill_config.get("api_key"):
            return skill_config.get("api_key")
        else:
            raise ToolException(
                f"Invalid API key provider: {api_key_provider}, or no api_key in config"
            )

    @property
    def category(self) -> str:
        return "openai"
