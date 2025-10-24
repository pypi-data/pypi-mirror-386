"""Data models for agent chat sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from llmling_agent.log import get_logger
from llmling_agent.utils.now import get_now


if TYPE_CHECKING:
    from datetime import datetime

    from llmling_agent import ChatMessage


logger = get_logger(__name__)


@dataclass
class SessionState:
    """Current state of the interactive session."""

    current_model: str | None = None
    message_count: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    start_time: datetime = field(default_factory=get_now)
    last_command: str | None = None
    last_response_time: float | None = None

    def update_tokens(self, message: ChatMessage[Any]):
        """Update token counts and costs from message."""
        if cost_info := message.cost_info:
            # Update token counts from cost_info
            token_usage = cost_info.token_usage
            self.total_tokens = token_usage["total"]
            self.input_tokens = token_usage["prompt"]
            self.output_tokens = token_usage["completion"]
            # Update cost
            self.total_cost = float(cost_info.total_cost)
            logger.debug("Updated session cost to: $%.6f", self.total_cost)

        # Update response time if available
        if message.response_time is not None:
            self.response_time = message.response_time

    @property
    def duration(self) -> str:
        """Get formatted duration since session start."""
        duration = get_now() - self.start_time
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
