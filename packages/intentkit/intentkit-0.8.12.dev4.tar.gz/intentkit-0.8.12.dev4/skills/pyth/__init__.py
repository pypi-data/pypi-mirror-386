"""Pyth AgentKit skills."""

from typing import TYPE_CHECKING, Optional, TypedDict

from coinbase_agentkit import pyth_action_provider

from intentkit.skills.base import (
    SkillConfig,
    SkillState,
    action_to_structured_tool,
    get_agentkit_actions,
)
from intentkit.skills.pyth.base import PythBaseTool

if TYPE_CHECKING:
    from intentkit.models.agent import Agent


class SkillStates(TypedDict):
    PythActionProvider_fetch_price: SkillState
    PythActionProvider_fetch_price_feed: SkillState


class Config(SkillConfig):
    """Configuration for Pyth skills."""

    states: SkillStates


async def get_skills(
    config: "Config",
    is_private: bool,
    agent_id: str,
    agent: Optional["Agent"] = None,
    **_,
) -> list[PythBaseTool]:
    """Get all Pyth skills."""

    available_skills: list[str] = []
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        if state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    actions = await get_agentkit_actions(agent_id, [pyth_action_provider], agent=agent)
    tools: list[PythBaseTool] = []
    for skill in available_skills:
        for action in actions:
            if action.name.endswith(skill):
                tools.append(action_to_structured_tool(action))
    return tools
