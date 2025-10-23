"""Support for manually created agents (no Bolna)"""

from typing import Any, Dict
from uuid import uuid4


class ManualAgentManager:
    """Handle agents created without Bolna integration"""

    @staticmethod
    def create_agent_config(
        agent_name: str,
        welcome_message: str,
        system_prompt: str,
        hangup_prompt: str,
        llm_model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Create agent config matching Bolna structure
        """
        agent_id = f"manual-{str(uuid4())}"

        return {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "welcome_message": welcome_message,
            "system_prompt": system_prompt,
            "hangup_prompt": hangup_prompt,
            "llm_family": "openai",
            "llm_model": llm_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1.0,
            "supported": True,
        }
