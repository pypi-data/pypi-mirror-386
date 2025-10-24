"""Manages message flow between agents/groups."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from psygnal import Signal
from psygnal.containers import EventedList

from llmling_agent.log import get_logger
from llmling_agent.talk import AggregatedTalkStats, Talk, TeamTalk


if TYPE_CHECKING:
    from datetime import timedelta

    from llmling_agent.common_types import (
        AgentName,
        AnyTransformFn,
        AsyncFilterFn,
        QueueStrategy,
    )
    from llmling_agent.messaging.messageemitter import MessageEmitter
    from llmling_agent.messaging.messagenode import MessageNode
    from llmling_agent.messaging.messages import ChatMessage
    from llmling_agent_config.forward_targets import ConnectionType

logger = get_logger(__name__)


class ConnectionManager:
    """Manages connections for both Agents and Teams."""

    connection_processed = Signal(Talk.ConnectionProcessed)

    node_connected = Signal(object)  # Node
    connection_added = Signal(Talk)  # Agent

    def __init__(self, owner: MessageEmitter):
        self.owner = owner
        # helper class for the user
        self._connections = EventedList[Talk]()
        self._wait_states: dict[AgentName, bool] = {}

    def __repr__(self):
        return f"ConnectionManager({self.owner})"

    def _on_talk_added(self, index: int, talk: Talk):
        """Connect to new talk's signal."""
        talk.connection_processed.connect(self._handle_message_flow)

    def _on_talk_removed(self, index: int, talk: Talk):
        """Disconnect from removed talk's signal."""
        talk.connection_processed.disconnect(self._handle_message_flow)

    def _on_talk_changed(self, index: int, old: Talk, new: Talk):
        """Update signal connections on talk change."""
        old.connection_processed.disconnect(self._handle_message_flow)
        new.connection_processed.connect(self._handle_message_flow)

    def _handle_message_flow(self, event: Talk.ConnectionProcessed):
        """Forward message flow to our aggregated signal."""
        self.connection_processed.emit(event)

    def set_wait_state(self, target: MessageEmitter | AgentName, wait: bool = True):
        """Set waiting behavior for target."""
        target_name = target if isinstance(target, str) else target.name
        self._wait_states[target_name] = wait

    async def wait_for_connections(self, _seen: set[AgentName] | None = None):
        """Wait for this agent and all connected agents to complete their tasks."""
        seen: set[AgentName] = _seen or {self.owner.name}  # type: ignore

        # Wait for our own tasks
        await self.owner.task_manager.complete_tasks()

        # Wait for connected agents
        for agent in self.get_targets():
            if agent.name not in seen:
                seen.add(agent.name)
                await agent.connections.wait_for_connections(seen)

    def get_targets(
        self, recursive: bool = False, _seen: set[AgentName] | None = None
    ) -> set[MessageNode]:
        """Get all currently connected target agents.

        Args:
            recursive: Whether to include targets of targets
        """
        # Get direct targets
        targets = {t for conn in self._connections for t in conn.targets if conn.active}

        if not recursive:
            return targets

        # Track seen agents to prevent cycles
        seen = _seen or {self.owner.name}  # type: ignore
        all_targets = set()

        for target in targets:
            if target.name not in seen:
                targets_ = target.connections.get_targets(recursive=True, _seen=seen)
                seen.add(target.name)
                all_targets.add(target)
                all_targets.update(targets_)

        return all_targets

    def has_connection_to(self, target: MessageNode) -> bool:
        """Check if target is connected."""
        return any(target in conn.targets for conn in self._connections if conn.active)

    def create_connection(
        self,
        source: MessageEmitter,
        target: MessageNode | Sequence[MessageNode],
        *,
        connection_type: ConnectionType = "run",
        priority: int = 0,
        delay: timedelta | None = None,
        queued: bool = False,
        queue_strategy: QueueStrategy = "latest",
        transform: AnyTransformFn | None = None,
        filter_condition: AsyncFilterFn | None = None,
        stop_condition: AsyncFilterFn | None = None,
        exit_condition: AsyncFilterFn | None = None,
        name: str | None = None,
    ) -> Talk[Any] | TeamTalk:
        """Create connection(s) to target(s).

        Args:
            source: Source agent or team
            target: Single target or sequence of targets
            connection_type: How to handle messages
            priority: Task priority (lower = higher priority)
            delay: Optional delay before processing
            queued: Whether to queue messages for manual processing
            queue_strategy: How to process queued messages
            transform: Optional message transformation
            filter_condition: When to filter messages
            stop_condition: When to disconnect
            exit_condition: When to exit application
            name: Optional name for cross-referencing connections
        """
        if isinstance(target, Sequence):
            # Create individual talks recursively
            talks = [
                self.create_connection(
                    source,
                    t,
                    connection_type=connection_type,
                    priority=priority,
                    delay=delay,
                    queued=queued,
                    queue_strategy=queue_strategy,
                    transform=transform,
                    filter_condition=filter_condition,
                    stop_condition=stop_condition,
                    exit_condition=exit_condition,
                    # Don't pass name - it should only apply to single connections
                )
                for t in target
            ]
            return TeamTalk(talks)

        # Single target case
        talk = Talk(
            source=source,
            targets=[target],
            connection_type=connection_type,
            name=name,
            priority=priority,
            delay=delay,
            queued=queued,
            queue_strategy=queue_strategy,
            transform=transform,
            filter_condition=filter_condition,
            stop_condition=stop_condition,
            exit_condition=exit_condition,
        )
        # TODO: better perhaps directly connect EventedList signal to node_connected?
        # or emit in _on_talk_added?
        self.node_connected.emit(target)
        self._connections.append(talk)
        self.connection_added.emit(talk)
        if source.context and (pool := source.context.pool):
            # Always use Talk's name for registration
            if name:
                pool.connection_registry.register(name, talk)
            else:
                pool.connection_registry.register_auto(talk)
        else:
            logger.debug("Could not register connection %r, no pool available", name)
        return talk

    async def trigger_all(self) -> dict[AgentName, list[ChatMessage[Any]]]:
        """Trigger all queued connections."""
        return {
            i.source.name: await i.trigger()
            for i in self._connections
            if isinstance(i, Talk) and i.queued
        }

    async def trigger_for(
        self, target: AgentName | MessageNode[Any, Any]
    ) -> list[ChatMessage[Any]]:
        """Trigger queued connections to specific target."""
        target_name = target if isinstance(target, str) else target.name
        results = []
        for talk in self._connections:
            if talk.queued and (t.name == target_name for t in talk.targets):
                results.extend(await talk.trigger())
        return results

    def disconnect_all(self):
        """Disconnect all managed connections."""
        for conn in self._connections:
            conn.disconnect()
        self._connections.clear()

    def disconnect(self, node: MessageNode):
        """Disconnect a specific node."""
        for talk in self._connections:
            if node in talk.targets or node == talk.source:
                talk.active = False
                self._connections.remove(talk)

    async def route_message(self, message: ChatMessage[Any], wait: bool | None = None):
        """Route message to all connections."""
        if wait is not None:
            should_wait = wait
        else:
            should_wait = any(
                self._wait_states.get(t.name, False) for t in self.get_targets()
            )
        msg = "ConnectionManager routing message from %s to %d connections"
        logger.debug(msg, message.name, len(self._connections))
        for talk in self._connections:
            await talk._handle_message(message, None)

        if should_wait:
            await self.wait_for_connections()

    @asynccontextmanager
    async def paused_routing(self):
        """Temporarily pause message routing to connections."""
        active_talks = [talk for talk in self._connections if talk.active]
        for talk in active_talks:
            talk.active = False
        try:
            yield self
        finally:
            for talk in active_talks:
                talk.active = True

    @property
    def stats(self) -> AggregatedTalkStats:
        """Get aggregated statistics for all connections."""
        return AggregatedTalkStats(stats=[conn.stats for conn in self._connections])

    def get_connections(self, recursive: bool = False) -> list[Talk[Any]]:
        """Get all Talk connections, flattening TeamTalks."""
        result = []
        seen = set()

        # Get our direct connections
        for conn in self._connections:
            result.append(conn)  # noqa: PERF402
        # Get target connections if recursive
        if recursive:
            for conn in result:
                for target in conn.targets:
                    if target.name not in seen:
                        seen.add(target.name)
                        result.extend(target.connections.get_connections(True))

        return result

    def get_mermaid_diagram(
        self,
        include_details: bool = True,
        recursive: bool = True,
    ) -> str:
        """Generate mermaid flowchart of all connections."""
        lines = ["flowchart LR"]
        connections = self.get_connections(recursive=recursive)

        for talk in connections:
            source = talk.source.name
            for target in talk.targets:
                if not include_details:
                    lines.append(f"    {source}-->{target.name}")
                    continue
                details: list[str] = []
                details.append(talk.connection_type)
                if talk.queued:
                    details.append(f"queued({talk.queue_strategy})")
                if talk.filter_condition:
                    details.append(f"filter:{talk.filter_condition.__name__}")
                if talk.stop_condition:
                    details.append(f"stop:{talk.stop_condition.__name__}")
                if talk.exit_condition:
                    details.append(f"exit:{talk.exit_condition.__name__}")
                elif any([
                    talk.filter_condition,
                    talk.stop_condition,
                    talk.exit_condition,
                ]):
                    details.append("conditions")

                label = f"|{' '.join(details)}|" if details else ""
                lines.append(f"    {source}--{label}-->{target.name}")

        return "\n".join(lines)


if __name__ == "__main__":
    from llmling_agent.agent import Agent

    agent = Agent("test_agent")
    agent_2 = Agent("test_agent_2")
    agent_3 = Agent("test_agent_3")
    agent_4 = Agent("test_agent_4")
    _conn_1 = agent >> agent_2
    _conn_2 = agent >> agent_3
    _conn_3 = agent_2 >> agent_4
    print(agent.connections.get_connections(recursive=True))
    print(agent.connections.get_mermaid_diagram())
