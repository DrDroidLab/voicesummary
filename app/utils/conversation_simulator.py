"""Simulates realistic multi-turn conversations with hangup detection."""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List

from openai import OpenAI

from app.config import settings
from app.utils.scenario_based_user_simulator import ScenarioBasedUserSimulator

logger = logging.getLogger(__name__)


class ConversationSimulator:
    """
    Simulates realistic conversations between a user and an agent.

    Uses real-time user turn generation and agent LLM calls with proper
    hangup detection based on Bolna's call_cancellation_prompt.
    """

    def __init__(self, openai_api_key: str):
        """Initialize the conversation simulator."""
        if not openai_api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=openai_api_key)

    async def simulate(
        self,
        agent_config: Dict[str, Any],
        scenario: Dict[str, str],
        max_turns: int = None,
    ) -> Dict[str, Any]:
        """
        Simulate a conversation between user and agent.

        Args:
            agent_config: Agent configuration from Bolna (contains system_prompt,
                         llm_model, temperature, hangup_prompt, etc.)
            scenario: Scenario configuration (agent_overview, user_persona,
                     situation, primary_language, expected_outcome)
            max_turns: Override maximum conversation turns (defaults to
                      settings.max_conversation_turns)

        Returns:
            Dictionary containing:
            {
                "transcript": List of turns with role, content, timestamp_ms, latency_ms
                "latencies": List of agent response latencies in ms
                "total_turns": Number of conversation turns
                "hangup_reason": Why the conversation ended
            }
        """
        try:
            logger.info(
                f"Starting conversation simulation for agent {agent_config['agent_id']}"
            )

            transcript = []
            latencies = []
            conversation_history = []

            # Initialize user simulator
            user_simulator = ScenarioBasedUserSimulator(scenario, self.client.api_key)

            # Add welcome message if present
            if agent_config.get("welcome_message"):
                welcome_turn = {
                    "role": "AGENT",
                    "content": agent_config["welcome_message"],
                    "timestamp_ms": int(time.time() * 1000),
                    "latency_ms": 0,
                }
                transcript.append(welcome_turn)
                conversation_history.append(
                    {"role": "AGENT", "content": agent_config["welcome_message"]}
                )

            # Multi-turn conversation loop
            hangup_reason = "max_turns_reached"
            effective_max_turns = (
                max_turns if max_turns is not None else settings.max_conversation_turns
            )

            for turn_num in range(1, effective_max_turns + 1):
                logger.debug(f"Starting turn {turn_num}")

                # 1. Generate user response
                user_msg = await user_simulator.generate_next_user_turn(
                    conversation_history
                )

                if user_msg is None:
                    hangup_reason = "user_simulator_ended"
                    logger.info(
                        f"Conversation ended by user simulator at turn {turn_num}"
                    )
                    break

                # 2. Add user turn to transcript
                user_turn = {
                    "role": "USER",
                    "content": user_msg,
                    "timestamp_ms": int(time.time() * 1000),
                }
                transcript.append(user_turn)
                conversation_history.append({"role": "USER", "content": user_msg})

                # 3. Get agent response
                start_time = time.time()
                agent_response = await self._call_agent_llm(
                    agent_config, conversation_history
                )
                latency_ms = (time.time() - start_time) * 1000

                # 4. Add agent turn to transcript
                agent_turn = {
                    "role": "AGENT",
                    "content": agent_response,
                    "timestamp_ms": int(time.time() * 1000),
                    "latency_ms": round(latency_ms, 2),
                }
                transcript.append(agent_turn)
                conversation_history.append(
                    {"role": "AGENT", "content": agent_response}
                )
                latencies.append(latency_ms)

                # 5. Check if conversation should end using hangup logic
                should_hangup = await self._check_hangup(
                    agent_config.get("hangup_prompt", ""), conversation_history
                )

                if should_hangup:
                    hangup_reason = "hangup_logic_triggered"
                    logger.info(
                        f"Conversation ended by hangup logic at turn {turn_num}"
                    )
                    break

            result = {
                "transcript": transcript,
                "latencies": latencies,
                "total_turns": len([t for t in transcript if t["role"] == "USER"]),
                "hangup_reason": hangup_reason,
            }

            logger.info(
                f"Simulation completed for agent {agent_config['agent_id']}: {result['total_turns']} turns, reason={hangup_reason}"
            )

            return result

        except Exception as e:
            logger.error(f"Conversation simulation failed: {e}")
            raise

    async def _call_agent_llm(
        self, agent_config: Dict[str, Any], conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Call the agent's LLM to get a response.

        Args:
            agent_config: Agent configuration with llm_model, system_prompt, temperature, etc.
            conversation_history: List of conversation turns

        Returns:
            Agent's response as a string
        """
        try:
            # Build messages for OpenAI API
            messages = [
                {"role": "system", "content": agent_config.get("system_prompt", "")}
            ]

            # Add conversation history
            for turn in conversation_history:
                role_mapping = {"USER": "user", "AGENT": "assistant"}
                openai_role = role_mapping.get(turn["role"], "user")
                messages.append({"role": openai_role, "content": turn["content"]})

            # Call agent's LLM
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=agent_config.get("llm_model", "gpt-4"),
                messages=messages,
                temperature=agent_config.get("temperature", 0.7),
                max_tokens=agent_config.get("max_tokens", 1000),
                top_p=agent_config.get("top_p", 1.0),
            )

            agent_message = response.choices[0].message.content.strip()
            return agent_message

        except Exception as e:
            logger.error(f"Agent LLM call failed: {e}")
            raise

    async def _check_hangup(
        self, hangup_prompt: str, conversation_history: List[Dict[str, str]]
    ) -> bool:
        """
        Check if conversation should end using Bolna's hangup logic.

        Uses GPT-4o-mini with the agent's call_cancellation_prompt to evaluate
        whether the conversation has reached a natural conclusion.

        Args:
            hangup_prompt: The call_cancellation_prompt from agent config
            conversation_history: List of conversation turns

        Returns:
            True if conversation should end, False otherwise
        """
        if not hangup_prompt:
            return False

        try:
            # Format conversation for hangup detection
            conversation_parts = []
            for turn in conversation_history:
                # Map our roles to Bolna's format: user/assistant
                role_name = "assistant" if turn["role"] == "AGENT" else "user"
                conversation_parts.append(f"{role_name}: {turn['content']}")

            conversation_text = "\n".join(conversation_parts)

            # Format: <hangup_prompt from config>
            # Respond only in this JSON format: {{ "hangup": "Yes" or "No" }}
            # Conversation: <conversation>
            prompt = f"""{hangup_prompt}
Respond only in this JSON format: {{"hangup": "Yes" or "No"}}

Conversation:
{conversation_text}"""

            # Call GPT-4o-mini to evaluate hangup
            hangup_check = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
                max_tokens=50,
            )

            result_text = hangup_check.choices[0].message.content.strip()

            # Try parsing as JSON first (Bolna format: {"hangup": "Yes"})
            should_hangup = False
            try:
                result_json = json.loads(result_text)
                if isinstance(result_json, dict):
                    hangup_value = str(result_json.get("hangup", "")).lower()
                    should_hangup = hangup_value in ["yes", "true", "1"]
            except json.JSONDecodeError:
                # Fallback to keyword matching for plain text responses
                result_lower = result_text.lower()
                should_hangup = any(
                    indicator in result_lower
                    for indicator in ["yes", "hang up", "end call", "terminate"]
                )

            if should_hangup:
                logger.debug(f"Hangup check result: {result_text}")

            return should_hangup

        except Exception as e:
            logger.error(f"Hangup check failed: {e}")
            return False
