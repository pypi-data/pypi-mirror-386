"""CLI commands for llmling-agent."""

from __future__ import annotations

from llmling_agent.agent.agent import Agent
from llmling_agent.agent.structured import StructuredAgent
from llmling_agent.agent.context import AgentContext
from llmling_agent.agent.process_manager import (
    ProcessManager,
    ProcessOutput,
    RunningProcess,
)


type AnyAgent[TDeps = None, TResult = str] = (
    Agent[TDeps] | StructuredAgent[TDeps, TResult]
)

from llmling_agent.agent.conversation import ConversationManager
from llmling_agent.agent.interactions import Interactions
from llmling_agent.agent.sys_prompts import SystemPrompts


__all__ = [
    "Agent",
    "AgentContext",
    "AnyAgent",
    "ConversationManager",
    "Interactions",
    "ProcessManager",
    "ProcessOutput",
    "RunningProcess",
    "StructuredAgent",
    "SystemPrompts",
]
