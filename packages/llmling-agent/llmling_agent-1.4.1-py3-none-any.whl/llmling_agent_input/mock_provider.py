"""Mock input provider implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from llmling_agent_input.base import InputProvider


if TYPE_CHECKING:
    from mcp import types

    from llmling_agent.agent.context import AgentContext, ConfirmationResult
    from llmling_agent.messaging.messages import ChatMessage
    from llmling_agent.tools.base import Tool

InputMethod = Literal[
    "get_input",
    "get_streaming_input",
    "get_tool_confirmation",
    "get_code_input",
    "get_elicitation",
]


@dataclass
class InputCall:
    """Record of an input provider call."""

    method: InputMethod
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    result: Any


class MockInputProvider(InputProvider):
    """Provider that records calls and returns pre-configured responses."""

    def __init__(
        self,
        *,
        input_response: str = "mock response",
        tool_confirmation: ConfirmationResult = "allow",
        code_response: str = "mock code",
        elicitation_response: dict[str, Any] | None = None,
    ):
        self.input_response = input_response
        self.tool_confirmation = tool_confirmation
        self.code_response = code_response
        self.elicitation_response = elicitation_response or {"response": "mock response"}
        self.calls: list[InputCall] = []

    async def get_input(
        self,
        context: AgentContext,
        prompt: str,
        result_type: type | None = None,
        message_history: list[ChatMessage] | None = None,
    ) -> Any:
        kwargs = {"result_type": result_type, "message_history": message_history}
        args_ = (context, prompt)
        call = InputCall("get_input", args_, kwargs, result=self.input_response)
        self.calls.append(call)
        return self.input_response

    async def get_tool_confirmation(
        self,
        context: AgentContext,
        tool: Tool,
        args: dict[str, Any],
        message_history: list[ChatMessage] | None = None,
    ) -> ConfirmationResult:
        kwargs = {"message_history": message_history}
        args_ = (context, tool, args)
        result = self.tool_confirmation
        call = InputCall("get_tool_confirmation", args_, kwargs, result=result)
        self.calls.append(call)
        return result  # pyright: ignore

    async def get_code_input(
        self,
        context: AgentContext,
        template: str | None = None,
        language: str = "python",
        description: str | None = None,
    ) -> str:
        kwargs = {"template": template, "language": language, "description": description}
        call = InputCall("get_code_input", (context,), kwargs, result=self.code_response)
        self.calls.append(call)
        return self.code_response

    async def get_elicitation(
        self,
        context: AgentContext,
        params: types.ElicitRequestParams,
        message_history: list[ChatMessage] | None = None,
    ) -> types.ElicitResult | types.ErrorData:
        from mcp import types

        kwargs = {"message_history": message_history}
        args_ = (context, params)
        result = types.ElicitResult(action="accept", content=self.elicitation_response)
        call = InputCall("get_elicitation", args_, kwargs, result=result)
        self.calls.append(call)
        return result
