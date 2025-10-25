"""ACP (Agent Client Protocol) session management for llmling-agent.

This module provides session lifecycle management, state tracking, and coordination
between agents and ACP clients through the JSON-RPC protocol.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic_ai import FinalResultEvent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    RetryPromptPart,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPartDelta,
    ToolReturnPart,
)

from acp.filesystem import ACPFileSystem
from acp.notifications import ACPNotifications
from acp.requests import ACPRequests
from acp.schema import ReadTextFileRequest
from llmling_agent.log import get_logger
from llmling_agent.mcp_server.manager import MCPManager
from llmling_agent.resource_providers.aggregating import AggregatingResourceProvider
from llmling_agent_acp.acp_tools import (
    ACPFileSystemProvider,
    ACPPlanProvider,
    ACPTerminalProvider,
)
from llmling_agent_acp.command_bridge import SLASH_PATTERN
from llmling_agent_acp.converters import (
    convert_acp_mcp_server_to_config,
    from_content_blocks,
)


# Tools that send their own rich ACP notifications (with ToolCallLocation, etc.)
# These tools are excluded from generic session-level notifications to prevent duplication
ACP_SELF_NOTIFYING_TOOLS = {"read_text_file", "write_text_file", "run_command"}


def _is_slash_command(text: str) -> bool:
    """Check if text starts with a slash command."""
    return bool(SLASH_PATTERN.match(text.strip()))


if TYPE_CHECKING:
    from collections.abc import Sequence

    from mcp.types import Prompt
    from pydantic_ai import AgentStreamEvent

    from acp import Client
    from acp.acp_types import ContentBlock, MCPServer, StopReason
    from acp.schema import ClientCapabilities
    from llmling_agent import Agent, AgentPool
    from llmling_agent.models.content import BaseContent
    from llmling_agent_acp.acp_agent import LLMlingACPAgent
    from llmling_agent_acp.command_bridge import ACPCommandBridge
    from llmling_agent_acp.session_manager import ACPSessionManager

    # from llmling_agent_acp.permission_server import PermissionMCPServer
    from llmling_agent_providers.base import UsageLimits


logger = get_logger(__name__)


@dataclass
class ACPSession:
    """Individual ACP session state and management.

    Manages the lifecycle and state of a single ACP session, including:
    - Agent instance and conversation state
    - Working directory and environment
    - MCP server connections
    - File system bridge for client operations
    - Tool execution and streaming updates
    """

    session_id: str
    """Unique session identifier"""

    agent_pool: AgentPool[Any]
    """AgentPool containing available agents"""

    current_agent_name: str
    """Name of currently active agent"""

    cwd: str
    """Working directory for the session"""

    client: Client
    """External library Client interface for operations"""

    acp_agent: LLMlingACPAgent
    """ACP agent instance for capability tools"""

    mcp_servers: Sequence[MCPServer] | None = None
    """Optional MCP server configurations"""

    usage_limits: UsageLimits | None = None
    """Optional usage limits for model requests and tokens"""

    command_bridge: ACPCommandBridge | None = None
    """Optional command bridge for slash commands"""

    client_capabilities: ClientCapabilities | None = None
    """Client capabilities for tool registration"""

    manager: ACPSessionManager | None = None
    """Session manager for managing sessions. Used for session management commands."""

    def __post_init__(self) -> None:
        """Initialize session state and set up providers."""
        self.mcp_servers = self.mcp_servers or []

        self._active = True
        self._task_lock = asyncio.Lock()
        self._cancelled = False
        self.mcp_manager: MCPManager | None = None
        self.fs = ACPFileSystem(self.client, session_id=self.session_id)
        self.capability_provider: AggregatingResourceProvider | None = None
        self.notifications = ACPNotifications(
            client=self.client,
            session_id=self.session_id,
        )
        self.requests = ACPRequests(client=self.client, session_id=self.session_id)

        if self.client_capabilities:
            providers = [
                ACPPlanProvider(self),
                ACPTerminalProvider(self),
                ACPFileSystemProvider(self),
            ]

            self.capability_provider = AggregatingResourceProvider(
                providers=providers, name=f"acp_capabilities_{self.session_id}"
            )
            # Add capability provider to current agent
            current_agent = self.agent_pool.get_agent(self.current_agent_name)
            current_agent.tools.add_provider(self.capability_provider)

        # Add cwd context to all agents in the pool
        for agent in self.agent_pool.agents.values():
            agent.sys_prompts.prompts.append(self.get_cwd_context)  # pyright: ignore[reportArgumentType]

        msg = "Created ACP session %s with agent pool (current: %s)"
        logger.info(msg, self.session_id, self.current_agent_name)

    async def initialize_mcp_servers(self) -> None:
        """Initialize MCP servers if any are configured."""
        # Always initialize permission server first
        # await self._initialize_permission_server()

        if not self.mcp_servers:
            return

        msg = "Initializing %d MCP servers for session %s"
        logger.info(msg, len(self.mcp_servers), self.session_id)
        cfgs = [convert_acp_mcp_server_to_config(s) for s in self.mcp_servers]
        # Initialize MCP manager with converted configs
        name = f"session_{self.session_id}"
        # Define accessible roots for MCP servers
        accessible_roots: list[str] = []
        if self.cwd:
            path = Path(self.cwd).resolve()
            accessible_roots.append(path.as_uri())

        self.mcp_manager = MCPManager(
            name,
            servers=cfgs,
            context=self.agent.context,
            progress_handler=self.handle_acp_progress,
            accessible_roots=accessible_roots,
        )
        try:
            # Start MCP manager and, fetch and add tools
            await self.mcp_manager.__aenter__()
            self.agent.tools.add_provider(self.mcp_manager)
            msg = "Added %d MCP servers to current agent for session %s"
            logger.info(msg, len(cfgs), self.session_id)
            # Register MCP prompts as slash commands
            await self._register_mcp_prompts_as_commands()

        except Exception:
            msg = "Failed to initialize MCP manager for session %s"
            logger.exception(msg, self.session_id)
            # Don't fail session creation, just log the error
            self.mcp_manager = None

    async def initialize_project_context(self) -> None:
        """Load AGENTS.md file and inject project context into all agents.

        TODO: Consider moving this to __aenter__
        """
        try:
            # Use ACP readFile request to fetch AGENTS.md
            path = f"{self.cwd}/AGENTS.md"
            request = ReadTextFileRequest(path=path, session_id=self.session_id)
            agents_md_response = await self.client.read_text_file(request)
            # Check if file is non-empty
            content = agents_md_response.content.strip()
            if not content:
                msg = "AGENTS.md exists but is empty for session %s"
                logger.debug(msg, self.session_id)
                return

            project_prompt = f"""## Project Information

{content}

This describes the current project, available agents, and their capabilities.
Use this context to understand the project structure and coordinate
with other agents effectively."""

            # Inject into all agents in the pool
            agent_count = 0
            for agent_name, agent in self.agent_pool.agents.items():
                agent.sys_prompts.prompts.append(project_prompt)
                agent_count += 1
                logger.debug("Injected AGENTS.md context into agent: %s", agent_name)

            msg = "Injected AGENTS.md project context into %d agents for session %s"
            logger.info(msg, agent_count, self.session_id)

        except Exception as e:  # noqa: BLE001
            # File doesn't exist or can't be read - that's fine, just log it
            msg = "No AGENTS.md file found or couldn't read it for session %s: %s"
            logger.debug(msg, self.session_id, e)

    @property
    def agent(self) -> Agent[Any]:
        """Get the currently active agent."""
        return self.agent_pool.get_agent(self.current_agent_name)

    def get_cwd_context(self) -> str:
        """Get current working directory context for prompts."""
        return f"Working directory: {self.cwd}" if self.cwd else ""

    async def switch_active_agent(self, agent_name: str) -> None:
        """Switch to a different agent in the pool.

        Args:
            agent_name: Name of the agent to switch to

        Raises:
            ValueError: If agent not found in pool
        """
        if agent_name not in self.agent_pool.agents:
            available = list(self.agent_pool.agents.keys())
            msg = f"Agent '{agent_name}' not found. Available: {available}"
            raise ValueError(msg)

        old_agent_name = self.current_agent_name
        self.current_agent_name = agent_name

        # Move capability provider from old agent to new agent
        if self.capability_provider:
            old_agent = self.agent_pool.get_agent(old_agent_name)
            new_agent = self.agent_pool.get_agent(agent_name)

            old_agent.tools.remove_provider(self.capability_provider)
            new_agent.tools.add_provider(self.capability_provider)

        msg = "Session %s switched from agent %s to %s"
        logger.info(msg, self.session_id, old_agent_name, agent_name)

        if new_model := new_agent.model_name:
            await self.notifications.update_session_model(new_model)

        await self.send_available_commands_update()

    @property
    def active(self) -> bool:
        """Check if session is active."""
        return self._active

    def cancel(self) -> None:
        """Cancel the current prompt turn."""
        self._cancelled = True
        logger.info("Session %s cancelled", self.session_id)

    def is_cancelled(self) -> bool:
        """Check if the session is cancelled."""
        return self._cancelled

    async def process_prompt(self, content_blocks: Sequence[ContentBlock]) -> StopReason:
        """Process a prompt request and stream responses.

        Args:
            content_blocks: List of content blocks from the prompt request

        Returns:
            SessionNotification objects for streaming to client, or StopReason literal
        """
        if not self._active:
            msg = "Attempted to process prompt on inactive session %s"
            logger.warning(msg, self.session_id)
            return "refusal"

        # Reset cancellation flag
        self._cancelled = False
        # Check for cancellation
        if self._cancelled:
            return "cancelled"

        # Convert content blocks to structured content
        contents = from_content_blocks(content_blocks)
        logger.info("Converted content: %r", contents)

        if not contents:
            msg = "Empty prompt received for session %s"
            logger.warning(msg, self.session_id)
            return "refusal"

        # Check for slash commands in text content
        commands: list[str] = []
        non_command_content: list[str | BaseContent] = []
        for item in contents:
            if isinstance(item, str) and _is_slash_command(item):
                # Found a slash command
                command_text = item.strip()
                logger.info("Found slash command: %s", command_text)
                commands.append(command_text)
            else:
                non_command_content.append(item)

        async with self._task_lock:
            try:
                # Process commands if found
                if commands and self.command_bridge:
                    for command in commands:
                        logger.info("Processing slash command: %s", command)
                        await self.command_bridge.execute_slash_command(command, self)

                    # If only commands, end turn
                    if not non_command_content:
                        return "end_turn"

                # Pass structured content to agent for processing
                msg = "Processing prompt for session %s with %d content items"
                logger.debug(msg, self.session_id, len(non_command_content))
                return await self._process_iter_response(non_command_content)

            except Exception as e:
                logger.exception("Error processing prompt in session %s", self.session_id)
                # Send error as agent message
                msg = f"I encountered an error while processing your request: {e}"
                await self.notifications.send_agent_text(msg)
                # Return refusal for errors
                return "refusal"

    async def _process_iter_response(  # noqa: PLR0911, PLR0915
        self, content: list[str | BaseContent]
    ) -> StopReason:
        """Process content using event-based streaming.

        Args:
            content: List of content objects (strings and Content objects)

        Returns:
            StopReason literal
        """
        from llmling_agent.agent.agent import StreamCompleteEvent

        msg = "Starting agent.run_stream for session %s with %d content items"
        logger.info(msg, self.session_id, len(content))
        logger.info("Agent model: %s", self.agent.model_name)

        event_count = 0
        has_yielded_anything = False
        # Track tool call inputs by tool_call_id for process_agent_stream_event
        inputs: dict[str, dict] = {}

        try:
            async for event in self.agent.run_stream(
                *content, usage_limits=self.usage_limits
            ):
                if self._cancelled:
                    return "cancelled"

                event_count += 1
                msg = "Event %d (%s) for session %s"
                logger.debug(msg, event_count, type(event).__name__, self.session_id)

                match event:
                    case (
                        PartStartEvent(part=TextPart(content=delta))
                        | PartDeltaEvent(delta=TextPartDelta(content_delta=delta))
                    ):
                        has_yielded_anything = True
                        await self.notifications.send_agent_text(delta)
                    case (
                        PartStartEvent(part=ThinkingPart(content=delta))
                        | PartDeltaEvent(delta=ThinkingPartDelta(content_delta=delta))
                    ):
                        if delta is not None:
                            has_yielded_anything = True
                            await self.notifications.send_agent_thought(delta)
                    case PartDeltaEvent(delta=ToolCallPartDelta()):
                        # Handle tool call delta updates
                        msg = "Received ToolCallPartDelta for session %s"
                        logger.debug(msg, self.session_id)

                    case FunctionToolCallEvent() | FunctionToolResultEvent():
                        # Handle tool events using process_agent_stream_event function
                        logger.info("Processing tool event: %s", type(event).__name__)
                        await self.process_agent_stream_event(event, inputs=inputs)
                        has_yielded_anything = True
                    case FinalResultEvent():
                        msg = "Final result received for session %s"
                        logger.debug(msg, self.session_id)
                    case StreamCompleteEvent(message=message):
                        # Handle final completion
                        logger.debug("Stream completed for session %s", self.session_id)
                        # If no chunks were streamed, send the complete content
                        if (
                            not has_yielded_anything
                            and message.content
                            and str(message.content).strip()
                        ):
                            await self.notifications.send_agent_text(str(message.content))
                            has_yielded_anything = True

                    case _:
                        # Log other events for debugging
                        logger.debug("Other event: %s", type(event).__name__)

            msg = "Agent streaming finished. Processed %d events, yielded anything: %s"
            logger.info(msg, event_count, has_yielded_anything)

        except UsageLimitExceeded as e:
            logger.info("Usage limit exceeded for session %s: %s", self.session_id, e)
            # Determine which limit was exceeded based on the error message
            error_msg = str(e)

            # Check for request limit (maps to max_turn_requests)
            if "request_limit" in error_msg:
                return "max_turn_requests"
            # Check for any token limits (maps to max_tokens)
            if any(limit in error_msg for limit in ["tokens_limit", "token_limit"]):
                return "max_tokens"
            # Tool call limits don't have a direct ACP stop reason, treat as refusal
            if "tool_calls_limit" in error_msg or "tool call" in error_msg:
                return "refusal"
            # Default to max_tokens for other usage limits
            return "max_tokens"
        except Exception as e:
            logger.exception("Error in agent streaming for session %s", self.session_id)
            logger.info("Sending error updates for session %s", self.session_id)
            await self.notifications.send_agent_text(f"Agent error: {e}")
            return "cancelled"
        else:
            return "end_turn"

    async def close(self) -> None:
        """Close the session and cleanup resources."""
        if not self._active:
            return

        self._active = False

        try:
            # Clean up MCP manager if present
            if self.mcp_manager:
                await self.mcp_manager.cleanup()
                self.mcp_manager = None

            # Clean up capability provider if present
            if self.capability_provider:
                current_agent = self.agent_pool.get_agent(self.current_agent_name)
                current_agent.tools.remove_provider(self.capability_provider)

            # Remove cwd context callable from all agents
            for agent in self.agent_pool.agents.values():
                if self.get_cwd_context in agent.sys_prompts.prompts:
                    agent.sys_prompts.prompts.remove(self.get_cwd_context)  # pyright: ignore[reportArgumentType]
                self.capability_provider = None

            # Note: Individual agents are managed by the pool's lifecycle
            # The pool will handle agent cleanup when it's closed
            logger.info("Closed ACP session %s", self.session_id)
        except Exception:
            logger.exception("Error closing session %s", self.session_id)

    async def send_available_commands_update(self) -> None:
        """Send current available commands to client."""
        if not self.command_bridge:
            return
        try:
            commands = self.command_bridge.to_available_commands(self.agent.context)
            await self.notifications.update_commands(commands)
        except Exception:
            msg = "Failed to send available commands update for session %s"
            logger.exception(msg, self.session_id)

    async def _register_mcp_prompts_as_commands(self) -> None:
        """Register MCP prompts as slash commands."""
        if not self.mcp_manager or not self.command_bridge:
            return

        try:
            # Collect all prompts from all MCP clients concurrently
            clients = list(self.mcp_manager.clients.values())
            if not clients:
                return

            # Use gather to fetch prompts concurrently, with exception handling
            results = await asyncio.gather(
                *[client.list_prompts() for client in clients], return_exceptions=True
            )

            all_prompts: list[Prompt] = []
            for result in results:
                if isinstance(result, BaseException):
                    logger.warning("Failed to list prompts from MCP client: %s", result)
                else:
                    all_prompts.extend(result)

            # Register prompts as commands
            if all_prompts:
                self.command_bridge.add_mcp_prompt_commands(all_prompts)
                msg = "Registered %d MCP prompts as slash commands for session %s"
                logger.info(msg, len(all_prompts), self.session_id)

                # Send updated command list to client
                await self.send_available_commands_update()

        except Exception:
            msg = "Failed to register MCP prompts as commands for session %s"
            logger.exception(msg, self.session_id)

    async def handle_acp_progress(
        self,
        progress: float,
        total: float | None,
        message: str | None,
        tool_name: str | None = None,
        tool_call_id: str | None = None,
        tool_input: dict[str, Any] | None = None,
    ) -> None:
        """Handle MCP progress and convert to ACP in_progress update."""
        # Skip if we don't have the required context
        if not (tool_name and tool_call_id):
            return

        try:
            # Create content from progress message
            output = message if message else f"Progress: {progress}"
            if total:
                output += f"/{total}"

            # Create ACP tool call progress notification
            await self.notifications.tool_call(
                tool_name=tool_name,
                tool_input=tool_input or {},
                tool_output=output,
                status="in_progress",
                tool_call_id=tool_call_id,
            )

        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to convert MCP progress to ACP notification: %s", e)

    async def process_agent_stream_event(
        self,
        event: AgentStreamEvent,
        inputs: dict[str, Any],
    ) -> None:
        """Process agent stream events.

        Args:
            event: The event to process.
            session_id: The ID of the session.
            inputs: The inputs to the session.

        Yields:
            SessionNotification: The notification to send.
        """
        match event:
            case FunctionToolCallEvent(part=part):
                # Tool call started - save input for later use
                tool_call_id = part.tool_call_id
                inputs[tool_call_id] = part.args_as_dict()

                # Skip generic notifications for self-notifying tools
                if part.tool_name not in ACP_SELF_NOTIFYING_TOOLS:
                    await self.notifications.tool_call(
                        tool_name=part.tool_name,
                        tool_input=part.args_as_dict(),
                        tool_output=None,  # Not available yet
                        status="pending",
                        tool_call_id=tool_call_id,
                    )

            case FunctionToolResultEvent(result=result, tool_call_id=tool_call_id) if (
                isinstance(result, ToolReturnPart)
            ):
                # Tool call completed successfully
                tool_input = inputs.get(tool_call_id, {})

                # Check if the tool result is a streaming AsyncGenerator
                if isinstance(result.content, AsyncGenerator):
                    # Stream the tool output chunks
                    full_content = ""
                    async for chunk in result.content:
                        full_content += str(chunk)

                        # Yield intermediate streaming notification
                        # Skip generic notifications for self-notifying tools
                        if result.tool_name not in ACP_SELF_NOTIFYING_TOOLS:
                            await self.notifications.tool_call(
                                tool_name=result.tool_name,
                                tool_input=tool_input,
                                tool_output=chunk,
                                status="in_progress",
                                tool_call_id=tool_call_id,
                            )

                    # Replace the AsyncGenerator with the full content to
                    # prevent errors
                    result.content = full_content
                    final_output = full_content
                else:
                    final_output = result.content

                # Final completion notification
                # Skip generic notifications for self-notifying tools
                if result.tool_name not in ACP_SELF_NOTIFYING_TOOLS:
                    await self.notifications.tool_call(
                        tool_name=result.tool_name,
                        tool_input=tool_input,
                        tool_output=final_output,
                        status="completed",
                        tool_call_id=tool_call_id,
                    )
                # Clean up stored input
                inputs.pop(tool_call_id, None)

            case FunctionToolResultEvent(result=result, tool_call_id=tool_call_id) if (
                isinstance(result, RetryPromptPart)
            ):
                # Tool call failed and needs retry
                tool_name = result.tool_name or "unknown"
                error_message = result.model_response()
                # Skip generic notifications for self-notifying tools
                if tool_name not in ACP_SELF_NOTIFYING_TOOLS:
                    await self.notifications.tool_call(
                        tool_name=tool_name,
                        tool_input=inputs.get(tool_call_id, {}),
                        tool_output=f"Error: {error_message}",
                        status="failed",
                        tool_call_id=tool_call_id,
                    )
                inputs.pop(tool_call_id, None)  # Clean up stored input
