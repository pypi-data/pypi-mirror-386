"""System prompt management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Literal


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from toprompt import AnyPromptType

    from llmling_agent.agent import AnyAgent
    from llmling_agent.agent.context import AgentContext


ToolInjectionMode = Literal["off", "all"]
ToolUsageStyle = Literal["suggestive", "strict"]


DEFAULT_TEMPLATE = """\
{%- if inject_agent_info and agent.name %}You are {{ agent.name }}{% if agent.description %}. {{ agent.description }}{% endif %}.

{% endif -%}
{%- if inject_tools != "off" -%}
{%- set tools = agent.tools.get_tools("enabled") -%}
{%- if tools %}

{%- if tool_usage_style == "strict" %}
You MUST use these tools to complete your tasks:
{%- else %}
You have access to these tools:
{%- endif %}
{% for tool in tools %}
- {{ tool.name }}{% if tool.description %}: {{ tool.description }}{% endif %}{% if tool.requires_capability %} (requires {{ tool.requires_capability }}){% endif %}
{%- endfor %}

{%- if tool_usage_style == "strict" %}
Do not attempt to perform tasks without using appropriate tools.
{%- else %}
Use them when appropriate to complete your tasks.
{%- endif %}

{% endif -%}
{% endif -%}
{%- for prompt in prompts %}
{{ prompt|to_prompt if dynamic else prompt }}
{%- if not loop.last %}

{% endif %}
{%- endfor %}"""  # noqa: E501


class SystemPrompts:
    """Manages system prompts for an agent."""

    def __init__(
        self,
        prompts: AnyPromptType | list[AnyPromptType] | None = None,
        template: str | None = None,
        dynamic: bool = True,
        context: AgentContext | None = None,
        inject_agent_info: bool = True,
        inject_tools: ToolInjectionMode = "off",
        tool_usage_style: ToolUsageStyle = "suggestive",
    ):
        """Initialize prompt manager."""
        from jinjarope import Environment
        from toprompt import to_prompt

        match prompts:
            case list():
                self.prompts = prompts
            case None:
                self.prompts = []
            case _:
                self.prompts = [prompts]
        self.context = context
        self.template = template
        self.dynamic = dynamic
        self.inject_agent_info = inject_agent_info
        self.inject_tools = inject_tools
        self.tool_usage_style = tool_usage_style
        self._cached = False
        self._env = Environment(enable_async=True)
        self._env.filters["to_prompt"] = to_prompt

    def __repr__(self) -> str:
        return (
            f"SystemPrompts(prompts={len(self.prompts)}, "
            f"dynamic={self.dynamic}, inject_agent_info={self.inject_agent_info}, "
            f"inject_tools={self.inject_tools!r})"
        )

    def __len__(self) -> int:
        return len(self.prompts)

    def __getitem__(self, idx: int | slice) -> AnyPromptType | list[AnyPromptType]:
        return self.prompts[idx]

    async def add_by_reference(self, reference: str):
        """Add a system prompt using reference syntax.

        Args:
            reference: [provider:]identifier[@version][?var1=val1,...]

        Examples:
            await sys_prompts.add_by_reference("code_review?language=python")
            await sys_prompts.add_by_reference("langfuse:expert@v2")
        """
        if not self.context:
            msg = "No context available to resolve prompts"
            raise RuntimeError(msg)

        try:
            content = await self.context.prompt_manager.get(reference)
            self.prompts.append(content)
        except Exception as e:
            msg = f"Failed to add prompt {reference!r}"
            raise RuntimeError(msg) from e

    async def add(
        self,
        identifier: str,
        *,
        provider: str | None = None,
        version: str | None = None,
        variables: dict[str, Any] | None = None,
    ):
        """Add a system prompt using explicit parameters.

        Args:
            identifier: Prompt identifier/name
            provider: Provider name (None = builtin)
            version: Optional version string
            variables: Optional template variables

        Examples:
            await sys_prompts.add("code_review", variables={"language": "python"})
            await sys_prompts.add("expert", provider="langfuse", version="v2")
        """
        if not self.context:
            msg = "No context available to resolve prompts"
            raise RuntimeError(msg)

        try:
            content = await self.context.prompt_manager.get_from(
                identifier,
                provider=provider,
                version=version,
                variables=variables,
            )
            self.prompts.append(content)
        except Exception as e:
            ref = f"{provider + ':' if provider else ''}{identifier}"
            msg = f"Failed to add prompt {ref!r}"
            raise RuntimeError(msg) from e

    def clear(self):
        """Clear all system prompts."""
        self.prompts = []

    async def refresh_cache(self):
        """Force re-evaluation of prompts."""
        from toprompt import to_prompt

        evaluated = []
        for prompt in self.prompts:
            result = await to_prompt(prompt)
            evaluated.append(result)
        self.prompts = evaluated
        self._cached = True

    @asynccontextmanager
    async def temporary_prompt(
        self, prompt: AnyPromptType, exclusive: bool = False
    ) -> AsyncIterator[None]:
        """Temporarily override system prompts.

        Args:
            prompt: Single prompt or sequence of prompts to use temporarily
            exclusive: Whether to only use given prompt. If False, prompt will be
                       appended to the agents prompts temporarily.
        """
        from toprompt import to_prompt

        original_prompts = self.prompts.copy()
        new_prompt = await to_prompt(prompt)
        self.prompts = [new_prompt] if not exclusive else [*self.prompts, new_prompt]
        try:
            yield
        finally:
            self.prompts = original_prompts

    async def format_system_prompt(self, agent: AnyAgent[Any, Any]) -> str:
        """Format complete system prompt."""
        if not self.dynamic and not self._cached:
            await self.refresh_cache()

        template = self._env.from_string(self.template or DEFAULT_TEMPLATE)
        result = await template.render_async(
            agent=agent,
            prompts=self.prompts,
            dynamic=self.dynamic,
            inject_agent_info=self.inject_agent_info,
            inject_tools=self.inject_tools,
            tool_usage_style=self.tool_usage_style,
        )
        return result.strip()
