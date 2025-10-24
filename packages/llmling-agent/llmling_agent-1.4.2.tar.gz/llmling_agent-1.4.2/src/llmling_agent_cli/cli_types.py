"""Type definitions for CLI options."""

from __future__ import annotations

from typing import Literal


# Log levels
LogLevel = Literal["debug", "info", "warning", "error"]

# Output detail levels
DetailLevel = Literal["simple", "detailed", "markdown"]

# Statistics grouping options
GroupBy = Literal["agent", "model", "hour", "day"]

# Output formats (from llmling.cli.constants)
OutputFormat = Literal["json", "yaml", "table", "text"]

# Provider types
Provider = Literal["pydantic_ai"]

# Merge methods for pull requests
MergeMethod = Literal["merge", "squash", "rebase"]
