"""Agent connection management commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.tree import Tree
from slashed import CommandContext, CommandError, SlashedCommand  # noqa: TC002
from slashed.completers import CallbackCompleter

from llmling_agent.log import get_logger
from llmling_agent.messaging.context import NodeContext  # noqa: TC001
from llmling_agent.messaging.messagenode import MessageNode
from llmling_agent_commands.completers import get_available_nodes


if TYPE_CHECKING:
    from llmling_agent.messaging.messageemitter import MessageEmitter


logger = get_logger(__name__)


CONNECT_HELP = """\
Connect the current node to another node.
Messages will be forwarded to the target node.

Examples:
  /connect node2          # Forward to node, wait for responses
  /connect node2 --no-wait  # Forward without waiting
"""

DISCONNECT_HELP = """\
Disconnect the current node from a target node.
Stops forwarding messages to the specified node.

Example: /disconnect node2
"""

LIST_CONNECTIONS_HELP = """\
Show current node connections and their status.
Displays:
- Connected nodes
- Wait settings
- Message flow direction
"""


def format_node_name(node: MessageEmitter[Any, Any], current: bool = False) -> str:
    """Format node name for display."""
    name = node.name
    if current:
        return f"[bold blue]{name}[/]"
    if node.connections.get_targets():
        return f"[green]{name}[/]"
    return f"[dim]{name}[/]"


class ConnectCommand(SlashedCommand):
    """Connect the current node to another node.

    Messages will be forwarded to the target node.

    Examples:
      /connect node2          # Forward to node, wait for responses
      /connect node2 --no-wait  # Forward without waiting
    """

    name = "connect"
    category = "nodes"

    async def execute_command(
        self,
        ctx: CommandContext[NodeContext],
        node_name: str,
        *,
        wait: bool = True,
    ):
        """Connect to another node.

        Args:
            ctx: Command context
            node_name: Name of the node to connect to
            wait: Whether to wait for responses (default: True)
        """
        source = ctx.context.node_name

        try:
            assert ctx.context.pool
            target_node = ctx.context.pool[node_name]
            assert isinstance(target_node, MessageNode)
            ctx.context.node.connect_to(target_node)
            ctx.context.node.connections.set_wait_state(node_name, wait)

            wait_text = "*(waiting for responses)*" if wait else "*(async)*"
            msg = f"🔗 **Connected:** `{source}` → `{node_name}` {wait_text}"
            await ctx.output.print(msg)
        except Exception as e:
            msg = f"Failed to connect {source!r} to {node_name!r}: {e}"
            raise CommandError(msg) from e

    def get_completer(self):
        """Get completer for node names."""
        return CallbackCompleter(get_available_nodes)


class DisconnectCommand(SlashedCommand):
    """Disconnect the current node from a target node.

    Stops forwarding messages to the specified node.

    Example: /disconnect node2
    """

    name = "disconnect"
    category = "nodes"

    async def execute_command(
        self,
        ctx: CommandContext[NodeContext],
        node_name: str,
    ):
        """Disconnect from another node.

        Args:
            ctx: Command context
            node_name: Name of the node to disconnect from
        """
        source = ctx.context.node_name
        try:
            assert ctx.context.pool
            target_node = ctx.context.pool[node_name]
            assert isinstance(target_node, MessageNode)
            ctx.context.node.connections.disconnect(target_node)
            await ctx.output.print(f"🔌 **Disconnected:** `{source}` ⛔ `{node_name}`")
        except Exception as e:
            msg = f"{source!r} failed to disconnect from {node_name!r}: {e}"
            raise CommandError(msg) from e

    def get_completer(self):
        """Get completer for node names."""
        return CallbackCompleter(get_available_nodes)


class DisconnectAllCommand(SlashedCommand):
    """Disconnect from all nodes.

    Remove all node connections.
    """

    name = "disconnect-all"
    category = "nodes"

    async def execute_command(self, ctx: CommandContext[NodeContext]):
        """Disconnect from all nodes.

        Args:
            ctx: Command context
        """
        if not ctx.context.node.connections.get_targets():
            await ctx.output.print("ℹ️ **No active connections**")  #  noqa: RUF001
            return
        source = ctx.context.node_name
        await ctx.context.node.disconnect_all()
        await ctx.output.print(f"🔌 **Disconnected** `{source}` from all nodes")


class ListConnectionsCommand(SlashedCommand):
    """Show current node connections and their status.

    Displays:
    - Connected nodes
    - Wait settings
    - Message flow direction
    """

    name = "connections"
    category = "nodes"

    async def execute_command(self, ctx: CommandContext[NodeContext]):
        """List current connections.

        Args:
            ctx: Command context
        """
        if not ctx.context.node.connections.get_targets():
            await ctx.output.print("ℹ️ **No active connections**")  #  noqa: RUF001
            return

        # Create tree visualization
        tree = Tree(format_node_name(ctx.context.node, current=True))

        # Use session's get_connections() for info
        for node in ctx.context.node.connections.get_targets():
            assert ctx.context.pool
            name = format_node_name(ctx.context.pool[node.name])
            _branch = tree.add(name)

        # Create string representation
        from rich.console import Console

        console = Console()
        with console.capture() as capture:
            console.print(tree)
        tree_str = capture.get()
        await ctx.output.print(f"\n## 🌳 Connection Tree\n\n```\n{tree_str}\n```")
