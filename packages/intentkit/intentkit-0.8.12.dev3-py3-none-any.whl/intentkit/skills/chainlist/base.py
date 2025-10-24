from typing import Type

from pydantic import BaseModel, Field

from intentkit.skills.base import IntentKitSkill


class ChainlistBaseTool(IntentKitSkill):
    """Base class for chainlist tools."""

    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]

    @property
    def category(self) -> str:
        return "chainlist"
