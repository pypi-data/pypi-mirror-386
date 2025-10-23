"""Storage provider base class."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Self
from uuid import uuid4

from llmling_agent.utils.tasks import TaskManager


if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from types import TracebackType

    from llmling_agent.common_types import JsonValue
    from llmling_agent.messaging.messages import ChatMessage, TokenCost
    from llmling_agent.tools import ToolCallInfo
    from llmling_agent_config.session import SessionQuery
    from llmling_agent_config.storage import BaseStorageProviderConfig
    from llmling_agent_storage.models import ConversationData, QueryFilters, StatsFilters


class StoredMessage:
    """Base class for stored message data."""

    id: str
    conversation_id: str
    timestamp: datetime
    role: str
    content: str
    name: str | None = None
    model: str | None = None
    token_usage: dict[str, int] | None = None
    cost: float | None = None
    response_time: float | None = None
    forwarded_from: list[str] | None = None


class StoredConversation:
    """Base class for stored conversation data."""

    id: str
    agent_name: str
    start_time: datetime
    total_tokens: int = 0
    total_cost: float = 0.0


class StorageProvider[T]:
    """Base class for storage providers."""

    can_load_history: bool = False
    """Whether this provider supports loading history."""

    def __init__(self, config: BaseStorageProviderConfig):
        super().__init__()
        self.config = config
        self.task_manager = TaskManager()
        self.log_messages = config.log_messages
        self.log_conversations = config.log_conversations
        self.log_tool_calls = config.log_tool_calls
        self.log_commands = config.log_commands
        self.log_context = config.log_context

    async def __aenter__(self) -> Self:
        """Initialize provider resources."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        """Clean up provider resources."""
        self.cleanup()

    def cleanup(self):
        """Clean up resources."""

    def should_log_agent(self, agent_name: str) -> bool:
        """Check if this provider should log the given agent."""
        return self.config.agents is None or agent_name in self.config.agents

    async def filter_messages(self, query: SessionQuery) -> list[ChatMessage[str]]:
        """Get messages matching query (if supported)."""
        msg = f"{self.__class__.__name__} does not support loading history"
        raise NotImplementedError(msg)

    async def log_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        content: str,
        role: str,
        name: str | None = None,
        cost_info: TokenCost | None = None,
        model: str | None = None,
        response_time: float | None = None,
        forwarded_from: list[str] | None = None,
    ):
        """Log a message (if supported)."""

    async def log_conversation(
        self,
        *,
        conversation_id: str,
        node_name: str,
        start_time: datetime | None = None,
    ):
        """Log a conversation (if supported)."""

    async def log_tool_call(
        self,
        *,
        conversation_id: str,
        message_id: str,
        tool_call: ToolCallInfo,
    ):
        """Log a tool call (if supported)."""

    async def log_command(
        self,
        *,
        agent_name: str,
        session_id: str,
        command: str,
        context_type: type | None = None,
        metadata: dict[str, JsonValue] | None = None,
    ):
        """Log a command (if supported)."""

    async def get_commands(
        self,
        agent_name: str,
        session_id: str,
        *,
        limit: int | None = None,
        current_session_only: bool = False,
    ) -> list[str]:
        """Get command history (if supported)."""
        msg = f"{self.__class__.__name__} does not support retrieving commands"
        raise NotImplementedError(msg)

    async def log_context_message(
        self,
        *,
        conversation_id: str,
        content: str,
        role: str,
        name: str | None = None,
        model: str | None = None,
        message_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Log a context message if context logging is enabled."""
        if not self.log_context:
            return

        await self.log_message(
            conversation_id=conversation_id,
            message_id=message_id or str(uuid4()),
            content=content,
            role=role,
            name=name,
            model=model,
        )

    async def get_conversations(
        self,
        filters: QueryFilters,
    ) -> list[tuple[ConversationData, Sequence[ChatMessage[str]]]]:
        """Get filtered conversations with their messages.

        Args:
            filters: Query filters to apply
        """
        msg = f"{self.__class__.__name__} does not support conversation queries"
        raise NotImplementedError(msg)

    async def get_filtered_conversations(
        self,
        agent_name: str | None = None,
        period: str | None = None,
        since: datetime | None = None,
        query: str | None = None,
        model: str | None = None,
        limit: int | None = None,
        *,
        compact: bool = False,
        include_tokens: bool = False,
    ) -> list[ConversationData]:
        """Get filtered conversations with formatted output.

        Args:
            agent_name: Filter by agent name
            period: Time period to include (e.g. "1h", "2d")
            since: Only show conversations after this time
            query: Search in message content
            model: Filter by model used
            limit: Maximum number of conversations
            compact: Only show first/last message of each conversation
            include_tokens: Include token usage statistics
        """
        msg = f"{self.__class__.__name__} does not support filtered conversations"
        raise NotImplementedError(msg)

    async def get_conversation_stats(
        self,
        filters: StatsFilters,
    ) -> dict[str, dict[str, Any]]:
        """Get conversation statistics grouped by specified criterion.

        Args:
            filters: Filters for statistics query
        """
        msg = f"{self.__class__.__name__} does not support statistics"
        raise NotImplementedError(msg)

    def aggregate_stats(
        self,
        rows: Sequence[tuple[str | None, str | None, datetime, TokenCost | None]],
        group_by: Literal["agent", "model", "hour", "day"],
    ) -> dict[str, dict[str, Any]]:
        """Aggregate statistics data by specified grouping.

        Args:
            rows: Raw stats data (model, agent, timestamp, token_usage)
            group_by: How to group the statistics
        """
        stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"total_tokens": 0, "messages": 0, "models": set()}
        )

        for model, agent, timestamp, token_usage in rows:
            match group_by:
                case "agent":
                    key = agent or "unknown"
                case "model":
                    key = model or "unknown"
                case "hour":
                    key = timestamp.strftime("%Y-%m-%d %H:00")
                case "day":
                    key = timestamp.strftime("%Y-%m-%d")

            entry = stats[key]
            entry["messages"] += 1
            if token_usage:
                entry["total_tokens"] += token_usage.token_usage.get("total", 0)
            if model:
                entry["models"].add(model)

        return stats

    async def reset(
        self,
        *,
        agent_name: str | None = None,
        hard: bool = False,
    ) -> tuple[int, int]:
        """Reset storage, optionally for specific agent only.

        Args:
            agent_name: Only reset data for this agent
            hard: Whether to completely reset storage (e.g., recreate tables)

        Returns:
            Tuple of (conversations deleted, messages deleted)
        """
        raise NotImplementedError

    async def get_conversation_counts(
        self,
        *,
        agent_name: str | None = None,
    ) -> tuple[int, int]:
        """Get counts of conversations and messages.

        Args:
            agent_name: Only count data for this agent

        Returns:
            Tuple of (conversation count, message count)
        """
        raise NotImplementedError

    async def add_checkpoint(
        self,
        message_id: str,
        checkpoint_name: str,
        description: str | None = None,
    ):
        """Add checkpoint to message."""
        raise NotImplementedError

    async def get_messages_until_checkpoint(
        self,
        checkpoint_name: str,
        conversation_id: str,
    ) -> list[T]:
        """Get all messages up to and including checkpoint."""
        raise NotImplementedError

    # Sync wrapper
    def log_context_message_sync(self, **kwargs):
        """Sync wrapper for log_context_message."""
        self.task_manager.fire_and_forget(self.log_context_message(**kwargs))

    # Sync wrappers for all async methods
    def log_message_sync(self, **kwargs):
        """Sync wrapper for log_message."""
        self.task_manager.fire_and_forget(self.log_message(**kwargs))

    def log_conversation_sync(self, **kwargs):
        """Sync wrapper for log_conversation."""
        self.task_manager.fire_and_forget(self.log_conversation(**kwargs))

    def log_tool_call_sync(self, **kwargs):
        """Sync wrapper for log_tool_call."""
        self.task_manager.fire_and_forget(self.log_tool_call(**kwargs))

    def log_command_sync(self, **kwargs):
        """Sync wrapper for log_command."""
        self.task_manager.fire_and_forget(self.log_command(**kwargs))

    def get_commands_sync(self, **kwargs) -> list[str]:
        """Sync wrapper for get_commands."""
        return self.task_manager.run_task_sync(self.get_commands(**kwargs))

    def filter_messages_sync(self, **kwargs) -> list[ChatMessage[str]]:
        """Sync wrapper for filter_messages."""
        return self.task_manager.run_task_sync(self.filter_messages(**kwargs))

    def get_conversations_sync(
        self, **kwargs
    ) -> list[tuple[ConversationData, Sequence[ChatMessage[str]]]]:
        return self.task_manager.run_task_sync(self.get_conversations(**kwargs))

    def get_filtered_conversations_sync(self, **kwargs) -> list[ConversationData]:
        return self.task_manager.run_task_sync(self.get_filtered_conversations(**kwargs))

    def get_conversation_stats_sync(self, **kwargs) -> dict[str, dict[str, Any]]:
        return self.task_manager.run_task_sync(self.get_conversation_stats(**kwargs))
