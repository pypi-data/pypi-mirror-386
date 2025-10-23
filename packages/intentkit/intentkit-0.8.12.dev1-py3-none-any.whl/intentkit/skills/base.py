import logging
from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Literal,
    NotRequired,
    Optional,
    TypedDict,
    Union,
)

from coinbase_agentkit import (
    Action,
    AgentKit,
    AgentKitConfig,
    CdpEvmWalletProvider,
)
from langchain_core.tools import BaseTool, StructuredTool
from langchain_core.tools.base import ToolException
from langgraph.runtime import get_runtime
from pydantic import (
    ValidationError,
)
from pydantic.v1 import ValidationError as ValidationErrorV1
from redis.exceptions import RedisError
from web3 import Web3

from intentkit.abstracts.graph import AgentContext
from intentkit.abstracts.skill import SkillStoreABC
from intentkit.clients import get_wallet_provider
from intentkit.clients.web3 import get_web3_client
from intentkit.models.redis import get_redis
from intentkit.models.skill import (
    AgentSkillData,
    AgentSkillDataCreate,
    ChatSkillData,
    ChatSkillDataCreate,
)
from intentkit.utils.error import IntentKitAPIError, RateLimitExceeded

if TYPE_CHECKING:
    from intentkit.models.agent import Agent

SkillState = Literal["disabled", "public", "private"]
SkillOwnerState = Literal["disabled", "private"]
APIKeyProviderValue = Literal["platform", "agent_owner"]


class SkillConfig(TypedDict):
    """Abstract base class for skill configuration."""

    enabled: bool
    states: Dict[str, SkillState | SkillOwnerState]
    api_key_provider: NotRequired[APIKeyProviderValue]
    __extra__: NotRequired[Dict[str, Any]]


class IntentKitSkill(BaseTool):
    """Abstract base class for IntentKit skills.
    Will have predefined abilities.
    """

    skill_store: SkillStoreABC
    # overwrite the value of BaseTool
    handle_tool_error: Optional[Union[bool, str, Callable[[ToolException], str]]] = (
        lambda e: f"tool error: {e}"
    )
    """Handle the content of the ToolException thrown."""

    # overwrite the value of BaseTool
    handle_validation_error: Optional[
        Union[bool, str, Callable[[Union[ValidationError, ValidationErrorV1]], str]]
    ] = lambda e: f"validation error: {e}"
    """Handle the content of the ValidationError thrown."""

    # Logger for the class
    logger: logging.Logger = logging.getLogger(__name__)

    @property
    def category(self) -> str:
        """Get the category of the skill."""
        raise NotImplementedError

    async def user_rate_limit(
        self, user_id: str, limit: int, minutes: int, key: str
    ) -> None:
        """Check if a user has exceeded the rate limit for this skill.

        Args:
            user_id: The ID of the user to check
            limit: Maximum number of requests allowed
            minutes: Time window in minutes
            key: The key to use for rate limiting (e.g., skill name or category)

        Raises:
            RateLimitExceeded: If the user has exceeded the rate limit

        Returns:
            None: Always returns None if no exception is raised
        """
        if not user_id:
            return None  # No rate limiting for users without ID

        try:
            redis = get_redis()
            # Create a unique key for this rate limit and user
            rate_limit_key = f"rate_limit:{key}:{user_id}"

            # Get the current count
            count = await redis.incr(rate_limit_key)

            # Set expiration if this is the first request
            if count == 1:
                await redis.expire(
                    rate_limit_key, minutes * 60
                )  # Convert minutes to seconds

            # Check if user has exceeded the limit
            if count > limit:
                raise RateLimitExceeded(f"Rate limit exceeded for {key}")

            return None

        except RuntimeError:
            # Redis client not initialized, log and allow the request
            self.logger.info(f"Redis not initialized, skipping rate limit for {key}")
            return None
        except RedisError as e:
            # Redis error, log and allow the request
            self.logger.info(
                f"Redis error in rate limiting: {e}, skipping rate limit for {key}"
            )
            return None

    async def user_rate_limit_by_skill(
        self, user_id: str, limit: int, minutes: int
    ) -> None:
        """Check if a user has exceeded the rate limit for this specific skill.

        This uses the skill name as the rate limit key.

        Args:
            user_id: The ID of the user to check
            limit: Maximum number of requests allowed
            minutes: Time window in minutes

        Raises:
            RateLimitExceeded: If the user has exceeded the rate limit
        """
        return await self.user_rate_limit(user_id, limit, minutes, self.name)

    async def user_rate_limit_by_category(
        self, user_id: str, limit: int, minutes: int
    ) -> None:
        """Check if a user has exceeded the rate limit for this skill category.

        This uses the skill category as the rate limit key, which means the limit
        is shared across all skills in the same category.

        Args:
            user_id: The ID of the user to check
            limit: Maximum number of requests allowed
            minutes: Time window in minutes

        Raises:
            RateLimitExceeded: If the user has exceeded the rate limit
        """
        return await self.user_rate_limit(user_id, limit, minutes, self.category)

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            "Use _arun instead, IntentKit only supports synchronous skill calls"
        )

    @staticmethod
    def get_context() -> AgentContext:
        runtime = get_runtime(AgentContext)
        if runtime.context is None or not isinstance(runtime.context, AgentContext):
            raise ValueError("No AgentContext found")
        return runtime.context

    def web3_client(self) -> Web3:
        """Get a Web3 client for the skill."""
        context = self.get_context()
        agent = context.agent
        network_id = agent.network_id

        return get_web3_client(network_id)

    async def get_agent_skill_data(
        self,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve persisted data for this skill scoped to the active agent."""
        return await self.get_agent_skill_data_raw(self.name, key)

    async def get_agent_skill_data_raw(
        self,
        skill_name: str,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve persisted data for a specific skill scoped to the active agent."""
        context = self.get_context()
        return await AgentSkillData.get(context.agent_id, skill_name, key)

    async def save_agent_skill_data(self, key: str, data: Dict[str, Any]) -> None:
        """Persist data for this skill scoped to the active agent."""
        await self.save_agent_skill_data_raw(self.name, key, data)

    async def save_agent_skill_data_raw(
        self,
        skill_name: str,
        key: str,
        data: Dict[str, Any],
    ) -> None:
        """Persist data for a specific skill scoped to the active agent."""
        context = self.get_context()
        skill_data = AgentSkillDataCreate(
            agent_id=context.agent_id,
            skill=skill_name,
            key=key,
            data=data,
        )
        await skill_data.save()

    async def delete_agent_skill_data(self, key: str) -> None:
        """Remove persisted data for this skill scoped to the active agent."""
        context = self.get_context()
        await AgentSkillData.delete(context.agent_id, self.name, key)

    async def get_thread_skill_data(
        self,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve persisted data for this skill scoped to the active chat."""
        context = self.get_context()
        return await ChatSkillData.get(context.chat_id, self.name, key)

    async def save_thread_skill_data(self, key: str, data: Dict[str, Any]) -> None:
        """Persist data for this skill scoped to the active chat."""
        context = self.get_context()
        skill_data = ChatSkillDataCreate(
            chat_id=context.chat_id,
            agent_id=context.agent_id,
            skill=self.name,
            key=key,
            data=data,
        )
        await skill_data.save()


async def get_agentkit_actions(
    agent_id: str,
    _store: SkillStoreABC,
    provider_factories: Sequence[Callable[[], object]],
    *,
    agent: Optional["Agent"] = None,
) -> list[Action]:
    """Build an AgentKit instance and return its actions."""

    if agent is None:
        try:
            context = IntentKitSkill.get_context()
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise IntentKitAPIError(
                500,
                "AgentContextMissing",
                "Agent context is required to initialize AgentKit actions.",
            ) from exc
        agent = context.agent

    if agent.id != agent_id:
        raise IntentKitAPIError(
            400,
            "AgentMismatch",
            "The requested agent does not match the active context agent.",
        )

    wallet_provider: CdpEvmWalletProvider = await get_wallet_provider(agent)

    agent_kit = AgentKit(
        AgentKitConfig(
            wallet_provider=wallet_provider,
            action_providers=[factory() for factory in provider_factories],
        )
    )
    return agent_kit.get_actions()


def action_to_structured_tool(action: Action) -> StructuredTool:
    """Convert an AgentKit action to a LangChain StructuredTool."""

    def _tool_fn(**kwargs: object) -> str:
        return action.invoke(kwargs)

    tool = StructuredTool(
        name=action.name,
        description=action.description,
        func=_tool_fn,
        args_schema=action.args_schema,
    )
    tool.handle_tool_error = lambda e: f"tool error: {e}"
    tool.handle_validation_error = lambda e: f"validation error: {e}"
    return tool
