"""Manages message flow between agents/groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from llmling import BaseRegistry, LLMLingError
from psygnal import Signal

from llmling_agent.log import get_logger
from llmling_agent.talk.talk import Talk


if TYPE_CHECKING:
    from llmling_agent import MessageNode
    from llmling_agent.messaging.messages import ChatMessage
    from llmling_agent.talk.stats import TalkStats
    from llmling_agent_config.conditions import ConnectionCondition


logger = get_logger(__name__)


class ConnectionRegistryError(LLMLingError):
    """Errors related to connection registration."""


@dataclass(frozen=True)
class EventContext[TMessageContent]:
    """Base context for all condition/event operations."""

    message: ChatMessage[TMessageContent]
    """The message being processed."""

    target: MessageNode
    """The target node this message is being sent to."""

    stats: TalkStats
    """Statistics for the current connection."""

    registry: ConnectionRegistry | None
    """Registry of all named connections."""

    talk: Talk
    """The Talk instance handling this message flow."""


@dataclass(frozen=True)
class TriggerContext[TMessageContent](EventContext[TMessageContent]):
    """Context for trigger events, extending base context with event information."""

    event_type: Literal["condition_met", "message_processed", "disconnected"]
    """Type of event that triggered this call."""

    condition: ConnectionCondition
    """The condition that was triggered (if event_type is condition_met)."""


class ConnectionRegistry(BaseRegistry[str, Talk]):
    """Registry for managing named connections.

    Allows looking up Talk instances by their name. Only named
    connections get registered.
    """

    message_flow = Signal(Talk.ConnectionProcessed)

    def __init__(self, *args, **kwargs):
        """Initialize registry and connect event handlers."""
        super().__init__(*args, **kwargs)
        # Connect handlers to EventedDict events
        self._items.events.added.connect(self._on_talk_added)
        self._items.events.removed.connect(self._on_talk_removed)
        self._items.events.changed.connect(self._on_talk_changed)

    def _on_talk_added(self, name: str, talk: Talk):
        """Handle new talk being added to registry."""
        talk.connection_processed.connect(self._handle_message_flow)
        logger.debug("Connected signal for talk: %s", name)

    def _on_talk_removed(self, name: str, talk: Talk):
        """Handle talk being removed from registry."""
        talk.connection_processed.disconnect(self._handle_message_flow)
        logger.debug("Disconnected signal for talk: %s", name)

    def _on_talk_changed(self, name: str, old_talk: Talk, new_talk: Talk):
        """Handle talk being replaced in registry."""
        old_talk.connection_processed.disconnect(self._handle_message_flow)
        new_talk.connection_processed.connect(self._handle_message_flow)
        logger.debug("Reconnected signal for talk: %s", name)

    def _handle_message_flow(self, event: Talk.ConnectionProcessed):
        """Forward message flow to global stream."""
        self.message_flow.emit(event)

    @property
    def _error_class(self) -> type[ConnectionRegistryError]:
        return ConnectionRegistryError

    def _validate_item(self, item: Any) -> Talk:
        """Ensure only Talk instances can be registered."""
        if not isinstance(item, Talk):
            msg = f"Expected Talk instance, got {type(item)}"
            raise self._error_class(msg)

        return item

    def register_auto(self, talk: Talk[Any], base_name: str | None = None) -> str:
        """Register talk with auto-generated unique name.

        Args:
            talk: Talk instance to register
            base_name: Optional base name to use (defaults to talk.name)

        Returns:
            The actual name used for registration
        """
        base = base_name or talk.name
        counter = 1
        name = base

        while name in self:
            name = f"{base}_{counter}"
            counter += 1
        talk.name = name
        self.register(name, talk)
        return name
