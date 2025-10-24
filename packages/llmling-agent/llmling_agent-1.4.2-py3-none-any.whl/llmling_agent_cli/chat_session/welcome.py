"""Welcome message information / helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from llmling_agent import AnyAgent


@dataclass
class WelcomeInfo:
    """Container for welcome message information."""

    header: list[str]
    agent_info: list[str]
    config_info: list[str]
    tools_info: list[str]
    prompts_info: list[str]
    usage_info: list[str]
    footer: list[str]

    def all_sections(self) -> list[tuple[str, list[str]]]:
        """Get all sections with their titles."""
        return [
            ("", self.header),
            ("", self.agent_info),
            ("", self.config_info),
            ("", self.tools_info),
            ("", self.prompts_info),
            ("", self.usage_info),
            ("", self.footer),
        ]


async def create_welcome_messages(
    agent: AnyAgent[Any, Any],
    *,
    streaming: bool = False,
    rich_format: bool = True,
) -> WelcomeInfo:
    """Create welcome messages for any interface.

    Args:
        agent: The agent to create welcome messages for
        streaming: Whether streaming mode is enabled
        rich_format: Whether to include rich text formatting

    Returns:
        Structured welcome information
    """

    # Helper for conditional rich formatting
    def fmt(text: str, style: str) -> str:
        """Apply rich formatting if enabled."""
        return f"[{style}]{text}[/]" if rich_format else text

    # Build all sections
    header = [fmt("LLMling Agent Chat", "bold blue"), "=" * 50]

    agent_info = [f"{fmt('Agent:', 'bold')} {agent.name}"]
    if agent.context.config.description:
        agent_info.append(fmt(agent.context.config.description, "dim"))

    model = agent.model_name or "default"
    mode = "streaming" if streaming else "non-streaming"
    config_info = [f"{fmt('Model:', 'bold')} {model}", f"{fmt('Mode:', 'bold')} {mode}"]

    tools = [t.name for t in await agent.tools.get_tools(state="enabled")]

    tools_info = [fmt("Tools:", "bold")]
    if tools:
        tools_info.extend(f"  • {tool}" for tool in tools)

    prompts_info = []
    if agent.context.config.system_prompts:
        prompts_info.append(fmt("System Prompts:", "bold"))
        from llmling_agent_config.system_prompts import (
            FilePromptConfig,
            FunctionPromptConfig,
            LibraryPromptConfig,
            StaticPromptConfig,
        )

        for prompt in agent.context.config.system_prompts:
            match prompt:
                case str():
                    prompts_info.append(fmt(f"  {prompt.split()[0]}...", "dim"))
                case StaticPromptConfig():
                    prompts_info.append(fmt("  static prompt", "dim"))
                case FilePromptConfig():
                    prompts_info.append(fmt("  file prompt", "dim"))
                case LibraryPromptConfig():
                    prompts_info.append(fmt("  library prompt", "dim"))
                case FunctionPromptConfig():
                    prompts_info.append(fmt("  function prompt", "dim"))
                case _:
                    msg = f"Unexpected prompt type: {type(prompt)}"
                    raise ValueError(msg)

    usage_info = [
        fmt("Usage:", "bold"),
        f"• Type {fmt('/help', 'green')} for available commands",
        f"• Type {fmt('/exit', 'green')} to quit",
    ]

    footer = ["=" * 50, ""]

    return WelcomeInfo(
        header=header,
        agent_info=agent_info,
        config_info=config_info,
        tools_info=tools_info,
        prompts_info=prompts_info,
        usage_info=usage_info,
        footer=footer,
    )
