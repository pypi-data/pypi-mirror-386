"""Pybotchi Context."""

from asyncio import get_event_loop, new_event_loop
from collections.abc import Coroutine
from concurrent.futures import Executor
from copy import deepcopy
from functools import cached_property
from typing import Any, Generic, Self

from langchain_core.language_models.chat_models import BaseChatModel

from pydantic import BaseModel, Field, PrivateAttr

from typing_extensions import TypeVar

from .action import Action, ActionReturn, T, TAction
from .constants import ChatRole, UNSPECIFIED, UsageMetadata
from .llm import LLM
from .mcp import MCPIntegration

TContext = TypeVar("TContext", bound="Context")
TLLM = TypeVar("TLLM", default=BaseChatModel)


class Context(BaseModel, Generic[TLLM]):
    """Context Handler."""

    prompts: list[dict[str, Any]] = Field(default_factory=list)
    allowed_actions: dict[str, bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    integrations: dict[str, MCPIntegration] = Field(default_factory=dict)
    usage: dict[str, UsageMetadata] = Field(default_factory=dict)
    streaming: bool = False
    max_self_loop: int | None = None
    parent: Self | None = None

    _action_call: dict[str, int] = PrivateAttr(default_factory=dict)

    @cached_property
    def llm(self) -> TLLM:
        """Get base LLM."""
        return LLM.base()

    async def start(
        self, action: type[TAction], /, **kwargs: Any
    ) -> tuple[TAction, ActionReturn]:
        """Start Action."""
        if not self.prompts or self.prompts[0]["role"] != ChatRole.SYSTEM:
            raise RuntimeError("Prompts should not be empty and start with system!")

        self._action_call.clear()

        agent = action(**kwargs)
        return agent, await agent.execute(self)

    def check_self_recursion(self, action: "Action") -> bool:
        """Check self recursion."""
        cls = action.__class__
        name = f"{cls.__module__}.{cls.__name__}"
        if name not in self._action_call:
            self._action_call[name] = 1
        else:
            self._action_call[name] += 1
            max = action.__max_iteration__ or self.max_self_loop
            if max and self._action_call[name] > max:
                return True
        return False

    def add_usage(
        self,
        action: "Action",
        model: BaseChatModel | str,
        usage: UsageMetadata,
        name: str | None = None,
    ) -> None:
        """Add usage."""
        model_name = (
            getattr(model, "model_name", getattr(model, "deployment_name", UNSPECIFIED))
            if isinstance(model, BaseChatModel)
            else model
        )
        action._usage.append({"name": name, "model": model_name, "usage": usage})

        if not (model_usage := self.usage.get(model_name)):
            model_usage = self.usage[model_name] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "input_token_details": {
                    "audio": 0,
                    "cache_creation": 0,
                    "cache_read": 0,
                },
                "output_token_details": {
                    "audio": 0,
                    "reasoning": 0,
                },
            }

        model_usage["input_tokens"] += usage["input_tokens"]
        model_usage["output_tokens"] += usage["output_tokens"]
        model_usage["total_tokens"] += usage["total_tokens"]

        _input_token_details = model_usage["input_token_details"]
        if input_token_details := usage.get("input_token_details"):
            _input_token_details["audio"] += input_token_details.get("audio", 0)
            _input_token_details["cache_creation"] += input_token_details.get(
                "cache_creation", 0
            )
            _input_token_details["cache_read"] += input_token_details.get(
                "cache_read", 0
            )

        _output_token_details = model_usage["output_token_details"]
        if output_token_details := usage.get("output_token_details"):
            _output_token_details["audio"] += output_token_details.get("audio", 0)
            _output_token_details["reasoning"] += output_token_details.get(
                "reasoning", 0
            )

    async def add_message(
        self, role: ChatRole, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add message."""
        self.prompts.append({"content": content, "role": role})

    async def add_response(
        self,
        action: "Action",
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add tool."""
        tool_call = action._tool_call
        self.prompts.append(
            {
                "content": "",
                "role": ChatRole.ASSISTANT,
                "tool_calls": [tool_call],
            }
        )
        self.prompts.append(
            {"content": content, "role": ChatRole.TOOL, "tool_call_id": tool_call["id"]}
        )

    async def notify(self, message: dict[str, Any]) -> None:
        """Notify Client."""
        pass

    def run_new_event_loop(self, task: Coroutine[Any, Any, T]) -> T:
        """Run concurrent on different thread."""
        loop = new_event_loop()
        try:
            return loop.run_until_complete(task)
        except Exception:
            raise
        finally:
            loop.close()

    async def run_in_thread(
        self, task: Coroutine[Any, Any, T], executor: Executor | None = None
    ) -> T:
        """Run concurrent on different thread."""
        return await get_event_loop().run_in_executor(
            executor, self.run_new_event_loop, task
        )

    async def detach_context(self: TContext) -> TContext:
        """Spawn detached context."""
        return self.__class__(**self.detached_kwargs(), parent=self)

    def detached_kwargs(self) -> dict[str, Any]:
        """Retrieve detached kwargs."""
        return {
            "prompts": deepcopy(self.prompts),
            "allowed_actions": deepcopy(self.allowed_actions),
            "metadata": deepcopy(self.metadata),
            "integrations": deepcopy(self.integrations),
            "streaming": self.streaming,
            "max_self_loop": self.max_self_loop,
        }

    async def detached_start(
        self: TContext, action: type["Action"], /, **kwargs: Any
    ) -> tuple[TContext, "Action", ActionReturn]:
        """Start Action."""
        context = await self.detach_context()
        _action, _action_return = await context.start(action, **kwargs)
        return context, _action, _action_return
