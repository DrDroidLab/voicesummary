"""Generates realistic user responses based on scenario and conversation."""

import asyncio
import logging
from typing import Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


class ScenarioBasedUserSimulator:
    """
    Generates user responses turn-by-turn based on scenario context.

    Uses GPT-4o-mini to dynamically generate user messages that respond to
    the agent's actual responses, creating a natural conversation flow.
    """

    def __init__(self, scenario: Dict[str, str], openai_api_key: str):
        """
        Initialize the user simulator.

        Args:
            scenario: Dictionary containing:
                - agent_overview: What the agent does
                - user_persona: Description of the user
                - situation: The scenario context
                - primary_language: Language for conversation
                - expected_outcome: Desired outcome
            openai_api_key: OpenAI API key for GPT-4o-mini
        """
        if not openai_api_key:
            raise ValueError("OpenAI API key is required")

        self.scenario = scenario
        self.client = OpenAI(api_key=openai_api_key)
        self.model = "gpt-4o-mini"

    async def generate_next_user_turn(
        self, conversation_history: List[Dict[str, str]]
    ) -> Optional[str]:
        """
        Generate the next user message based on conversation history.

        Args:
            conversation_history: List of conversation turns, each containing:
                - role: "USER" or "AGENT"
                - content: Message content
                - timestamp_ms: Timestamp (optional)

        Returns:
            User's next message as a string, or None if should end

        The simulator responds naturally to the agent's last message
        while staying in character with the user persona and working
        towards the expected outcome.
        """
        try:
            # Build prompt for user simulator
            prompt = self._build_prompt(conversation_history)

            logger.debug(
                f"Generating user turn with GPT-4o-mini, "
                f"history length: {len(conversation_history)}"
            )

            # Call GPT-4o-mini asynchronously
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
            )

            user_message = response.choices[0].message.content.strip()

            # Check if simulator indicates conversation should end
            if "CONVERSATION_COMPLETE" in user_message:
                logger.info("User simulator indicated conversation should end")
                return None

            logger.info(f"Generated user turn: {user_message[:50]}...")
            return user_message

        except Exception as e:
            logger.error(f"Failed to generate user turn: {e}")
            raise

    def _build_prompt(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Build the prompt for GPT-4o-mini to generate next user turn.

        Args:
            conversation_history: List of conversation turns

        Returns:
            Formatted prompt string
        """
        # Format conversation history
        history_text = self._format_history(conversation_history)

        prompt = f"""You are simulating a realistic user in a voice conversation scenario.

**User Persona**: {self.scenario['user_persona']}

**Situation**: {self.scenario['situation']}

**Expected Outcome**: {self.scenario['expected_outcome']}

**Agent Overview**: {self.scenario['agent_overview']}

**Language**: {self.scenario['primary_language']}

**Conversation So Far**:
{history_text}

**Instructions**:
1. Generate the NEXT realistic user response in \
{self.scenario['primary_language']}
2. Stay in character as the user persona described above
3. Respond naturally to the agent's last message
4. Work towards achieving the expected outcome
5. Keep responses concise and conversational (1-3 sentences)
6. If the agent has clearly ended the conversation or achieved the \
outcome, return exactly: "CONVERSATION_COMPLETE"

**Return ONLY the user's next message as plain text \
(no formatting, no prefixes).**
"""
        return prompt

    def _format_history(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Format conversation history for the prompt.

        Args:
            conversation_history: List of conversation turns

        Returns:
            Formatted history string
        """
        if not conversation_history:
            return "(No conversation yet - this will be the first user message)"

        lines = []
        for turn in conversation_history:
            role = turn.get("role", "UNKNOWN")
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")

        return "\n".join(lines)
