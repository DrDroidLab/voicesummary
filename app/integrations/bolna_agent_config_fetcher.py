"""Fetches agent configurations from Bolna API."""

import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class BolnaAgentConfigFetcher:
    """Fetches and parses agent configurations from Bolna API."""

    BASE_URL = "https://api.bolna.ai"

    def __init__(self, api_key: str):
        """Initialize the fetcher with Bolna API key."""
        if not api_key:
            raise ValueError("Bolna API key is required")

        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def fetch(self, agent_id: str) -> Dict[str, Any]:
        """
        Fetch full agent configuration from Bolna API.

        Args:
            agent_id: The Bolna agent ID to fetch

        Returns:
            Dictionary containing parsed agent configuration:
            {
                "agent_id": str,
                "agent_name": str,
                "welcome_message": str,
                "system_prompt": str,
                "hangup_prompt": str,
                "llm_family": str,
                "llm_model": str,
                "temperature": float,
                "max_tokens": int,
                "top_p": float,
                "supported": bool  # True only if family == "openai"
            }

        Raises:
            requests.HTTPError: If API request fails
            KeyError: If expected fields are missing from response
        """
        try:
            url = f"{self.BASE_URL}/agent/{agent_id}"
            logger.info(f"Fetching agent config for {agent_id}")

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract LLM configuration from tasks
            if not data.get("tasks") or len(data["tasks"]) == 0:
                raise ValueError(f"Agent {agent_id} has no tasks configured")

            first_task = data["tasks"][0]
            llm_config = first_task["tools_config"]["llm_agent"]["llm_config"]
            task_config = first_task["task_config"]

            # Parse LLM family and model
            llm_family = llm_config.get("family", "unknown")
            llm_model = llm_config.get("model", "").replace("azure/", "")

            # Extract system prompt (from agent_prompts)
            system_prompt = ""
            if "agent_prompts" in data and "task_1" in data["agent_prompts"]:
                system_prompt = data["agent_prompts"]["task_1"].get("system_prompt", "")

            # Extract hangup prompt
            hangup_prompt = task_config.get("call_cancellation_prompt", "")

            config = {
                "agent_id": agent_id,
                "agent_name": data.get("agent_name", agent_id),
                "welcome_message": data.get("agent_welcome_message", ""),
                "system_prompt": system_prompt,
                "hangup_prompt": hangup_prompt,
                "llm_family": llm_family,
                "llm_model": llm_model,
                "temperature": llm_config.get("temperature", 0.7),
                "max_tokens": llm_config.get("max_tokens", 1000),
                "top_p": llm_config.get("top_p", 1.0),
                "supported": llm_family == "openai",
            }

            logger.info(
                f"Successfully fetched config for {agent_id}: "
                f"{config['agent_name']} (supported={config['supported']})"
            )
            return config

        except requests.RequestException as e:
            logger.error(f"Failed to fetch agent config for {agent_id}: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse agent config for {agent_id}: {e}")
            raise ValueError(f"Invalid agent configuration structure: {e}")
