"""Fabric GitHub prompt provider implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from llmling_agent.prompts.base import BasePromptProvider


if TYPE_CHECKING:
    from llmling_agent_config.prompt_hubs import FabricConfig


class FabricPromptHub(BasePromptProvider):
    """Provider for prompts from Fabric GitHub repository."""

    _BASE_URL = "https://raw.githubusercontent.com/danielmiessler/fabric/main"
    _API_URL = "https://api.github.com/repos/danielmiessler/fabric/contents/data/patterns"

    def __init__(self, config: FabricConfig):
        self.config = config

    async def get_prompt(
        self,
        name: str,
        version: str | None = None,  # Ignored for Fabric
        variables: dict[str, Any] | None = None,
    ) -> str:
        """Get prompt from Fabric GitHub repository."""
        system_url = f"{self._BASE_URL}/data/patterns/{name}/system.md"
        user_url = f"{self._BASE_URL}/data/patterns/{name}/user.md"

        async with httpx.AsyncClient() as client:
            # Try system prompt first
            response = await client.get(system_url)
            if response.status_code == 200:  # noqa: PLR2004
                return response.text

            # Try user prompt if system not found
            response = await client.get(user_url)
            if response.status_code == 200:  # noqa: PLR2004
                return response.text

            msg = f"Template '{name}' not found in Fabric repository"
            raise ValueError(msg)

    async def list_prompts(self) -> list[str]:
        """List available prompts from Fabric repository."""
        headers = {"Accept": "application/vnd.github.v3+json"}

        async with httpx.AsyncClient() as client:
            response = await client.get(self._API_URL, headers=headers)

            if response.status_code != 200:  # noqa: PLR2004
                msg = f"Failed to list prompts: {response.status_code}"
                raise RuntimeError(msg)

            content = response.json()
            return [item["name"] for item in content if item["type"] == "dir"]


if __name__ == "__main__":
    import asyncio

    from llmling_agent_config.prompt_hubs import FabricConfig

    async def main():
        hub = FabricPromptHub(FabricConfig())
        # List available prompts
        print("Available prompts:")
        prompts = await hub.list_prompts()
        print("\n".join(f"- {p}" for p in prompts[:5]))  # Show first 5

        # Get a specific prompt
        print("\nFetching 'summarize' prompt:")
        prompt = await hub.get_prompt("summarize")
        print(f"\n{prompt[:200]}...")  # Show first 200 chars

    asyncio.run(main())
