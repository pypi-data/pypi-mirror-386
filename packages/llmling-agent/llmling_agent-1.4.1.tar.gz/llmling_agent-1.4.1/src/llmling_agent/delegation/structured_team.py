"""Two-node team with a validator node."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from llmling_agent.delegation.teamrun import TeamRun


if TYPE_CHECKING:
    from llmling_agent import AnyAgent, MessageNode


class StructuredTeam[TResult](TeamRun[Any, TResult]):
    """A team that produces typed/structured output through a processor node."""

    def __init__(
        self,
        worker: MessageNode[Any, Any],
        processor: AnyAgent[Any, TResult],
        *,
        name: str | None = None,
        description: str | None = None,
    ):
        """Initialize structured team.

        Args:
            worker: The node doing the main work
            processor: Node that processes/validates the output
            name: Optional name for this team
            description: Optional description
        """
        super().__init__(
            agents=[worker, processor],
            name=name or f"{worker.name}>{processor.name}",
            description=description,
        )

    @property
    def worker(self) -> MessageNode[Any, Any]:
        """Get the worker node."""
        return self.agents[0]

    @worker.setter
    def worker(self, value: MessageNode[Any, Any]):
        """Set the worker node."""
        self.agents[0] = value

    @property
    def processor(self) -> AnyAgent[Any, TResult]:
        """Get the processor node."""
        return self.agents[1]  # type: ignore

    @processor.setter
    def processor(self, value: AnyAgent[Any, TResult]):
        """Set the processor node."""
        self.agents[1] = value
