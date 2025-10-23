"""Agent-related CLI commands."""

from __future__ import annotations

import shutil

from llmling.cli.constants import output_format_opt, verbose_opt
from llmling.cli.utils import OutputFormat, format_output
import typer as t

from llmling_agent.utils.inspection import validate_import
from llmling_agent_cli import agent_store, resolve_agent_config


agent_cli = t.Typer(help="Agent management commands", no_args_is_help=True)

NAME_HELP = "Name for the configuration (defaults to filename)"

INTERACTIVE_CMD = "--interactive/--no-interactive"
INTERACTIVE_HELP = "Use interactive configuration wizard"


@agent_cli.command("init")
def init_agent_config(
    output: str = t.Argument(help="Path to write agent configuration file"),
    name: str | None = t.Option(None, "--name", "-n", help=NAME_HELP),
    interactive: bool = t.Option(False, INTERACTIVE_CMD, help=INTERACTIVE_HELP),
):
    """Initialize a new agent configuration file.

    Creates and activates a new agent configuration. The configuration will be
    automatically registered and set as active.
    """
    from upath import UPath

    if interactive:
        validate_import("promptantic", "chat")
        from promptantic import ModelGenerator

        from llmling_agent import AgentsManifest

        generator = ModelGenerator()
        manifest = generator.populate(AgentsManifest)
        manifest.save(output)
    else:
        from llmling_agent import config_resources

        shutil.copy2(config_resources.AGENTS_TEMPLATE, output)

    config_name = name or UPath(output).stem
    agent_store.add_config(config_name, output)
    agent_store.set_active(config_name)

    print(f"\nCreated and activated agent configuration '{config_name}': {output}")
    print("\nTry these commands:")
    print("  llmling-agent list")
    print("  llmling-agent chat simple_agent")


@agent_cli.command("add")
def add_agent_file(
    name: str = t.Argument(help="Name for the agent configuration file"),
    path: str = t.Argument(help="Path to agent configuration file"),
    verbose: bool = verbose_opt,
):
    """Add a new agent configuration file."""
    try:
        agent_store.add_config(name, path)
        t.echo(f"Added agent configuration '{name}' -> {path}")
    except Exception as e:
        t.echo(f"Error adding configuration: {e}", err=True)
        raise t.Exit(1) from e


@agent_cli.command("set")
def set_active_file(
    name: str = t.Argument(help="Name of agent configuration to set as active"),
    verbose: bool = verbose_opt,
):
    """Set the active agent configuration file."""
    try:
        agent_store.set_active(name)
        t.echo(f"Set '{name}' as active agent configuration")
    except Exception as e:
        t.echo(f"Error setting active configuration: {e}", err=True)
        raise t.Exit(1) from e


@agent_cli.command("list")
def list_agents(
    config_name: str = t.Option(
        None,
        "-c",
        "--config",
        help="Name of agent configuration to list (defaults to active)",
    ),
    output_format: OutputFormat = output_format_opt,
    verbose: bool = verbose_opt,
):
    """List agents from the active (or specified) configuration."""
    from llmling_agent import AgentsManifest

    try:
        try:
            config_path = resolve_agent_config(config_name)
        except ValueError as e:
            msg = str(e)
            raise t.BadParameter(msg) from e

        agent_def = AgentsManifest.from_file(config_path)
        # Set the name field from the dict key for each agent
        agents = [ag.model_copy(update={"name": n}) for n, ag in agent_def.agents.items()]
        format_output(agents, output_format)

    except t.Exit:
        raise
    except Exception as e:
        t.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback

            t.echo(traceback.format_exc(), err=True)
        raise t.Exit(1) from e
