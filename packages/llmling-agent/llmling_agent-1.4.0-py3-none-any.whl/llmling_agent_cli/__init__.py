"""CLI commands for llmling-agent."""

from __future__ import annotations

from llmling import ConfigStore


agent_store = ConfigStore("agents.json")


def resolve_agent_config(config: str | None) -> str:
    """Resolve agent configuration path from name or direct path.

    Args:
        config: Configuration name or path. If None, uses active config.

    Returns:
        Resolved configuration path

    Raises:
        ValueError: If no configuration is found or no active config is set
    """
    if not config:
        if active := agent_store.get_active():
            return active.path
        msg = "No active agent configuration set. Use 'agents set' to set one."
        raise ValueError(msg)

    try:
        # First try as stored config name
        return agent_store.get_config(config)
    except KeyError:
        # If not found, treat as direct path
        return config
