"""Debug commands for ACP notification replay and testing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import anyenv
from slashed import CommandContext, SlashedCommand  # noqa: TC002

from acp.schema import (
    AgentMessageChunk,
    AgentThoughtChunk,
    ContentToolCallContent,
    SessionNotification,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    UserMessageChunk,
)
from llmling_agent.log import get_logger


if TYPE_CHECKING:
    from acp.acp_types import SessionUpdate, ToolCallKind, ToolCallStatus
    from llmling_agent_acp.commands.acp_commands import ACPCommandContext


logger = get_logger(__name__)


class DebugSendTextCommand(SlashedCommand):
    """Send a text chunk notification for debugging.

    Useful for testing client rendering of different message types.
    """

    name = "debug-send-text"
    category = "debug"

    async def execute_command(
        self,
        ctx: CommandContext[ACPCommandContext],
        text: str,
        *,
        chunk_type: str = "agent",
    ):
        """Send a text chunk notification.

        Args:
            ctx: Command context
            text: Text content to send
            chunk_type: Type of chunk ('agent', 'user', 'thought')
        """
        session = ctx.context.session
        try:
            content = TextContentBlock(type="text", text=text)

            if chunk_type == "agent":
                update: SessionUpdate = AgentMessageChunk(content=content)
            elif chunk_type == "user":
                update = UserMessageChunk(content=content)
            elif chunk_type == "thought":
                update = AgentThoughtChunk(content=content)
            else:
                await ctx.output.print(f"❌ **Invalid chunk type:** `{chunk_type}`")
                return

            notification = SessionNotification(
                session_id=session.session_id, update=update
            )
            await session.client.session_update(notification)
            await ctx.output.print(f"✅ **Sent {chunk_type} text chunk:** {text[:50]}...")

        except Exception as e:
            logger.exception("Failed to send debug text chunk")
            await ctx.output.print(f"❌ **Failed to send text chunk:** {e}")


class DebugSendToolCallCommand(SlashedCommand):
    """Send a tool call notification for debugging.

    Tests the client's tool call visualization and status handling.
    """

    name = "debug-send-tool-call"
    category = "debug"

    async def execute_command(
        self,
        ctx: CommandContext[ACPCommandContext],
        title: str,
        *,
        kind: ToolCallKind = "other",
    ):
        """Send a tool call notification.

        Args:
            ctx: Command context
            title: Tool call title/description
            kind: Tool kind ('read', 'edit', 'delete', 'move', 'search',
                  'execute', 'think', 'fetch', 'other')
        """
        session = ctx.context.session
        try:
            id_ = f"debug-{hash(title)}"
            await session.notifications.tool_call_start(id_, title=title, kind=kind)
            await ctx.output.print(f"✅ **Sent tool call:** {title}")
        except Exception as e:
            logger.exception("Failed to send debug tool call")
            await ctx.output.print(f"❌ **Failed to send tool call:** {e}")


class DebugUpdateToolCallCommand(SlashedCommand):
    """Send a tool call update notification for debugging.

    Tests tool call progress updates and result display.
    """

    name = "debug-update-tool"
    category = "debug"

    async def execute_command(
        self,
        ctx: CommandContext[ACPCommandContext],
        tool_call_id: str,
        *,
        status: ToolCallStatus = "completed",
        content: str = "",
    ):
        """Send a tool call update notification.

        Args:
            ctx: Command context
            tool_call_id: ID of tool call to update
            status: New status
            content: Content to include in update
        """
        session = ctx.context.session
        try:
            tool_content = None
            if content:
                tool_content = [
                    ContentToolCallContent(
                        type="content",
                        content=TextContentBlock(type="text", text=content),
                    )
                ]
            await session.notifications.tool_call_progress(
                tool_call_id,
                status,
                content=tool_content,
            )
            await ctx.output.print(f"✅ **Updated tool call {tool_call_id}:** {status}")

        except Exception as e:
            logger.exception("Failed to update debug tool call")
            await ctx.output.print(f"❌ **Failed to update tool call:** {e}")


class DebugReplaySequenceCommand(SlashedCommand):
    """Replay a sequence of ACP notifications from a JSON file.

    Allows testing complex interaction flows by replaying recorded sequences.
    """

    name = "debug-replay"
    category = "debug"

    async def execute_command(
        self,
        ctx: CommandContext[ACPCommandContext],
        file_path: str,
    ):
        """Replay a sequence of ACP notifications from a JSON file.

        Args:
            ctx: Command context
            file_path: Path to JSON file containing notification sequence
        """
        session = ctx.context.session
        try:
            path = Path(file_path)
            if not path.exists():
                await ctx.output.print(f"❌ **File not found:** `{file_path}`")
                return

            with path.open() as f:
                sequence_data = json.load(f)

            if (
                not isinstance(sequence_data, dict)
                or "notifications" not in sequence_data
            ):
                await ctx.output.print(
                    "❌ **Invalid replay file.** Expected: `{'notifications': [...]}`"
                )
                return

            notifications = sequence_data["notifications"]
            count = 0

            for notification_data in notifications:
                try:
                    # Parse the notification based on its type
                    update_data = notification_data.get("update", {})
                    update_type = update_data.get("session_update")

                    if update_type == "agent_message_chunk":
                        content = TextContentBlock(**update_data["content"])
                        update: SessionUpdate = AgentMessageChunk(content=content)
                    elif update_type == "user_message_chunk":
                        content = TextContentBlock(**update_data["content"])
                        update = UserMessageChunk(content=content)
                    elif update_type == "agent_thought_chunk":
                        content = TextContentBlock(**update_data["content"])
                        update = AgentThoughtChunk(content=content)
                    elif update_type == "tool_call":
                        update = ToolCallStart(**update_data)
                    elif update_type == "tool_call_update":
                        update = ToolCallProgress(**update_data)
                    else:
                        logger.warning("Unknown update type: %s", update_type)
                        continue

                    notification = SessionNotification(
                        session_id=session.session_id, update=update
                    )

                    await session.client.session_update(notification)
                    count += 1

                    # Optional delay between notifications
                    if delay := sequence_data.get("delay_ms", 0):
                        import asyncio

                        await asyncio.sleep(delay / 1000)

                except Exception as e:  # noqa: BLE001
                    logger.warning("Failed to replay notification: %s", e)
                    continue

            await ctx.output.print(
                f"✅ **Replayed {count} notifications from** `{file_path}`"
            )

        except Exception as e:
            logger.exception("Failed to replay debug sequence")
            await ctx.output.print(f"❌ **Failed to replay sequence:** {e}")


class DebugSessionInfoCommand(SlashedCommand):
    """Show current ACP session debugging information.

    Displays session state, client capabilities, and configuration details.
    """

    name = "debug-session-info"
    category = "debug"

    async def execute_command(self, ctx: CommandContext[ACPCommandContext]):
        """Show current ACP session debugging information."""
        session = ctx.context.session
        try:
            info = {
                "session_id": session.session_id,
                "current_agent": session.current_agent_name,
                "available_agents": list(session.agent_pool.agents.keys()),
                "cwd": session.cwd,
                "client_capabilities": (
                    session.client_capabilities.model_dump()
                    if session.client_capabilities
                    else None
                ),
                "mcp_servers": len(session.mcp_manager.servers)
                if session.mcp_manager
                else 0,
            }

            text = anyenv.dump_json(info, indent=True)
            await ctx.output.print(f"## 🔍 Session Debug Info\n\n```json\n{text}\n```")

        except Exception as e:
            logger.exception("Failed to get session info")
            await ctx.output.print(f"❌ **Failed to get session info:** {e}")


class DebugCreateTemplateCommand(SlashedCommand):
    """Create a template JSON file for debugging notification sequences.

    Generates a sample replay file with common notification types.
    """

    name = "debug-create-template"
    category = "debug"

    async def execute_command(
        self,
        ctx: CommandContext[ACPCommandContext],
        *,
        file_path: str = "debug_replay_template.json",
    ):
        """Create a template JSON file for debugging notification sequences.

        Args:
            ctx: Command context
            file_path: Path where to create the template file
        """
        try:
            from acp.schema import ContentToolCallContent

            # Create proper BaseModel instances
            message_chunk = AgentMessageChunk(
                content=TextContentBlock(
                    type="text", text="Hello, this is a debug message!"
                )
            )

            tool_start = ToolCallStart(
                tool_call_id="debug-tool-1",
                title="Debug Tool Call",
                status="in_progress",
                kind="other",
                content=None,
                locations=None,
            )

            tool_update = ToolCallProgress(
                tool_call_id="debug-tool-1",
                status="completed",
                content=[
                    ContentToolCallContent(
                        type="content",
                        content=TextContentBlock(
                            type="text", text="Tool completed successfully!"
                        ),
                    )
                ],
                session_update="tool_call_update",
            )

            # Create notifications using proper SessionNotification models
            notifications = [
                SessionNotification(session_id="template", update=message_chunk),
                SessionNotification(session_id="template", update=tool_start),
                SessionNotification(session_id="template", update=tool_update),
            ]

            # Convert to JSON-serializable format
            template = {
                "description": "ACP notification replay sequence for debugging",
                "delay_ms": 100,
                "notifications": [
                    notif.model_dump()["update"] for notif in notifications
                ],
            }

            with Path(file_path).open("w") as f:
                json.dump(template, f, indent=2)

            await ctx.output.print(f"✅ **Created replay template:** `{file_path}`")

        except Exception as e:
            logger.exception("Failed to create replay template")
            await ctx.output.print(f"❌ **Failed to create template:** {e}")


class DebugSendRawCommand(SlashedCommand):
    """Send a raw ACP notification from JSON string.

    For advanced debugging - send arbitrary notification structures.
    """

    name = "debug-send-raw"
    category = "debug"

    async def execute_command(
        self,
        ctx: CommandContext[ACPCommandContext],
        notification_json: str,
    ):
        """Send a raw ACP notification from JSON string.

        Args:
            ctx: Command context
            notification_json: JSON string of the notification to send
        """
        session = ctx.context.session
        try:
            data = anyenv.load_json(notification_json, return_type=dict)

            # Validate it has the expected structure
            if "update" not in data:
                msg = "❌ **Notification JSON must contain 'update' field**"
                await ctx.output.print(msg)
                return

            notification = SessionNotification(session_id=session.session_id, **data)
            await session.client.session_update(notification)
            await ctx.output.print("✅ **Sent raw notification**")
        except json.JSONDecodeError as e:
            await ctx.output.print(f"❌ **Invalid JSON:** {e}")
        except Exception as e:
            logger.exception("Failed to send raw notification")
            await ctx.output.print(f"❌ **Failed to send raw notification:** {e}")


def get_debug_commands() -> list[type[SlashedCommand]]:
    """Get all ACP debug commands."""
    return [
        DebugSendTextCommand,
        DebugSendToolCallCommand,
        DebugUpdateToolCallCommand,
        DebugReplaySequenceCommand,
        DebugSessionInfoCommand,
        DebugCreateTemplateCommand,
        DebugSendRawCommand,
    ]
