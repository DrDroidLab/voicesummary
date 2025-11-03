"""Turn-by-turn accuracy validation using GPT-5"""

import json
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AudioCall

logger = logging.getLogger(__name__)

try:
    import openai

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI not available - accuracy validation disabled")


class TurnAccuracyValidator:
    """Validate agent accuracy at each turn using GPT-5"""

    def __init__(self):
        if not HAS_OPENAI:
            raise RuntimeError(
                "OpenAI package is required for turn accuracy validation"
            )

        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.validation_model  # Use GPT-5 for accuracy validation

    def validate_call_turns(
        self, call_id: str, script_turns: List[Dict[str, str]], db: Session
    ) -> Dict[str, Any]:
        """
        Validate each turn in a call for accuracy

        Returns: {
            "turn_accuracy": [{"turn": 1, "accuracy": 8, ...}],
            "humanlike_rating": 8.5,
            "overall_accuracy": 9.0,
            "least_accurate_turns": [{"turn": 3, "accuracy": 5, ...}]
        }
        """
        call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
        if not call or not call.transcript:
            logger.error(f"Call not found or no transcript: {call_id}")
            return {"error": "Call not found or no transcript"}

        turns = call.transcript.get("turns", [])

        # Validate each AGENT/ASSISTANT turn
        turn_validations = []
        context_history = []

        for i, turn in enumerate(turns):
            role = turn.get("role", "").upper()
            content = turn.get("content", "")

            # Build conversation context
            context_history.append(f"{role}: {content}")

            # Only validate AGENT/ASSISTANT turns
            if role in ["AGENT", "AGENT_SPEECH", "ASSISTANT"]:
                # Find matching script turn to get expected criteria
                expected_criteria = self._get_expected_criteria(i, script_turns)

                # Validate this turn
                validation = self._validate_single_turn(
                    turn_number=i + 1,
                    agent_response=content,
                    context="\n".join(
                        context_history[:-1]
                    ),  # All context before this turn
                    expected_criteria=expected_criteria,
                )

                turn_validations.append(validation)

        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics(turn_validations)

        logger.info(
            f"Validated {len(turn_validations)} turns for call {call_id}: "
            f"accuracy={overall_metrics['overall_accuracy']}, humanlike={overall_metrics['humanlike_rating']}"
        )

        return {
            "turn_accuracy": turn_validations,
            "humanlike_rating": overall_metrics["humanlike_rating"],
            "overall_accuracy": overall_metrics["overall_accuracy"],
            "least_accurate_turns": overall_metrics["least_accurate_turns"],
        }

    async def validate_simulated_transcript(
        self, transcript: Dict[str, Any], scenario: Dict[str, str], db: Session
    ) -> Dict[str, Any]:
        """
        Validate a simulated conversation with a SINGLE comprehensive GPT-5 call.

        Args:
            transcript: {"turns": [{"role": "USER|AGENT", "content": "..."}]}
            scenario: Scenario config with expected_outcome, agent_overview, user_persona, etc.

        Returns:
            {
                "turn_accuracy": [],  # Kept for compatibility
                "humanlike_rating": 8.5,
                "overall_accuracy": 0.87,
                "least_accurate_turns": []  # Kept for compatibility
            }
        """
        turns = transcript.get("turns", [])

        if not turns:
            logger.warning("No turns found in simulated transcript")
            return {
                "turn_accuracy": [],
                "humanlike_rating": None,
                "overall_accuracy": None,
                "outcome_orientation": None,
                "least_accurate_turns": [],
            }

        # Use single comprehensive validation
        result = await self._validate_conversation_comprehensive(turns, scenario)

        return {
            "turn_accuracy": [],  # No longer doing turn-by-turn
            "humanlike_rating": result.get("humanlike"),
            "overall_accuracy": (
                result.get("accuracy", 0) / 10.0 if result.get("accuracy") else None
            ),  # Convert 0-10 to 0-1
            "outcome_orientation": result.get(
                "outcome"
            ),  # Include outcome from comprehensive validation
            "least_accurate_turns": [],
        }

    async def _validate_conversation_comprehensive(
        self, turns: List[Dict[str, Any]], scenario: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Single GPT-5 call to comprehensively evaluate the entire conversation.

        Returns:
            {
                "accuracy": 0-10,
                "humanlike": 0-10,
                "outcome": 0-10,
                "accuracy_reasoning": "...",
                "humanlike_reasoning": "...",
                "outcome_reasoning": "..."
            }
        """
        logger.info(f"Starting comprehensive validation for {len(turns)} turns")

        # Format conversation
        conversation_text = "\n".join(
            [
                f"{turn.get('role', 'UNKNOWN')}: {turn.get('content', turn.get('text', ''))}"
                for turn in turns
            ]
        )

        prompt = f"""You are evaluating a voice AI conversation across three critical dimensions. Analyze the ENTIRE conversation carefully.

**SCENARIO CONTEXT**:
- Agent Overview: {scenario.get('agent_overview', '')}
- User Persona: {scenario.get('user_persona', '')}
- Situation: {scenario.get('situation', '')}
- Language: {scenario.get('primary_language', '')}
- Expected Outcome: {scenario.get('expected_outcome', '')}

**CONVERSATION TRANSCRIPT**:
{conversation_text}

**EVALUATION INSTRUCTIONS**:

1. **ACCURACY (0-10)**: Evaluate how well the agent handled the scenario across ALL turns
   - Did the agent understand the context correctly?
   - Were responses appropriate for each turn?
   - Did the agent stay on topic and address user concerns?
   - Were there any major mistakes, misunderstandings, or inappropriate responses?

2. **HUMANLIKE (0-10)**: Evaluate how natural and human-like the conversation felt
   - Natural conversational flow and pacing
   - Appropriate empathy and emotional tone
   - No robotic patterns, awkward phrasing, or repetitive language
   - Culturally and linguistically appropriate (especially for {scenario.get('primary_language', 'the target language')})

3. **OUTCOME (0-10)**: Evaluate how well the expected outcome was achieved
   - 0-2: Outcome not achieved, conversation went off track
   - 3-4: Minor progress but largely unsuccessful
   - 5-6: Partial achievement, some key aspects addressed
   - 7-8: Most of the outcome achieved with minor gaps
   - 9-10: Expected outcome fully achieved

**IMPORTANT**: Be realistic and critical. Most real conversations will have issues. Don't inflate scores.

Return ONLY a JSON object with this exact structure:
{{
    "accuracy": <0-10 float>,
    "humanlike": <0-10 float>,
    "outcome": <0-10 float>,
    "accuracy_reasoning": "<2-3 sentences explaining the accuracy score>",
    "humanlike_reasoning": "<2-3 sentences explaining the humanlike score>",
    "outcome_reasoning": "<2-3 sentences explaining the outcome score>"
}}"""

        try:
            import asyncio

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of conversational AI. You provide accurate, critical assessments.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=2000,  # Increased to allow for reasoning tokens + response
            )

            logger.info(f"GPT-5 response object: {response}")
            logger.info(f"Response choices: {len(response.choices)}")
            if response.choices:
                logger.info(
                    f"First choice finish_reason: {response.choices[0].finish_reason}"
                )
                logger.info(f"First choice message: {response.choices[0].message}")

            content = response.choices[0].message.content
            if content is None:
                logger.error("GPT-5 returned None content - likely refusal")
                return self._default_comprehensive_result()

            content = content.strip()
            logger.info(f"GPT-5 comprehensive response length: {len(content)} chars")
            logger.info(f"GPT-5 comprehensive response preview: {content[:500]}")

            result = self._extract_json(content)
            logger.info(f"Extracted result keys: {list(result.keys())}")

            # Validate required fields
            if not all(k in result for k in ["accuracy", "humanlike", "outcome"]):
                logger.error(
                    f"Missing required fields in validation result. Expected: accuracy, humanlike, outcome. Got: {list(result.keys())}"
                )
                logger.error(f"Full extracted result: {result}")
                return self._default_comprehensive_result()

            # Log the evaluation
            logger.info(
                f"Comprehensive validation: accuracy={result['accuracy']}/10, "
                f"humanlike={result['humanlike']}/10, outcome={result['outcome']}/10"
            )

            return result

        except Exception as e:
            logger.error(f"Comprehensive validation failed: {e}", exc_info=True)
            return self._default_comprehensive_result()

    def _default_comprehensive_result(self) -> Dict[str, Any]:
        """Return default scores when validation fails"""
        return {
            "accuracy": 5.0,
            "humanlike": 5.0,
            "outcome": 5.0,
            "accuracy_reasoning": "Validation failed - default score",
            "humanlike_reasoning": "Validation failed - default score",
            "outcome_reasoning": "Validation failed - default score",
        }

    async def _validate_simulated_turn(
        self,
        turn_number: int,
        agent_response: str,
        context: str,
        scenario: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Validate a single agent turn in a simulated conversation.

        Returns: {"turn": int, "is_accurate": bool, "feedback": str}
        """
        prompt = f"""You are evaluating an AI agent's response in a conversation.

**Scenario Context**:
- Agent Overview: {scenario.get('agent_overview', '')}
- User Persona: {scenario.get('user_persona', '')}
- Situation: {scenario.get('situation', '')}
- Expected Outcome: {scenario.get('expected_outcome', '')}

**Previous Context**:
{context if context else "(Start of conversation)"}

**Agent's Response** (Turn {turn_number}):
{agent_response}

**Instructions**:
Evaluate whether this response is accurate and appropriate given the scenario and context.
Consider:
1. Does it align with the agent's role and overview?
2. Is it contextually relevant to the previous turns?
3. Does it move toward the expected outcome?
4. Is the tone and approach appropriate?

Return ONLY a JSON object:
{{
    "is_accurate": true/false,
    "feedback": "Brief explanation (1-2 sentences) of why this response is/isn't accurate"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of conversational AI responses.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=300,
            )

            content = response.choices[0].message.content.strip()
            result = self._extract_json(content)

            return {
                "turn": turn_number,
                "is_accurate": result.get("is_accurate", False),
                "feedback": result.get("feedback", "No feedback provided"),
            }

        except Exception as e:
            logger.error(f"Turn validation failed for turn {turn_number}: {e}")
            return {
                "turn": turn_number,
                "is_accurate": True,  # Default to true on error
                "feedback": f"Validation error: {str(e)}",
            }

    async def _evaluate_humanlike_rating(
        self, turns: List[Dict[str, Any]], scenario: Dict[str, str]
    ) -> float:
        """
        Evaluate how human-like and natural the agent's conversation style is.

        Returns: Score from 0-10
        """
        conversation_text = "\n".join(
            [
                f"{turn.get('role', 'UNKNOWN')}: {turn.get('content', turn.get('text', ''))}"
                for turn in turns
            ]
        )

        prompt = f"""Rate how human-like and natural this agent's conversation style is on a scale of 0-10.

**Scenario**:
- Agent Overview: {scenario.get('agent_overview', '')}
- Language: {scenario.get('primary_language', '')}

**Full Conversation**:
{conversation_text}

**Instructions**:
Consider:
- Natural flow and pacing
- Appropriate empathy and tone
- Language naturalness (no robotic patterns, glitches, or repetitions)
- Cultural and linguistic appropriateness

Return ONLY a JSON object:
{{
    "score": 0-10 (float),
    "reasoning": "Brief explanation"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of conversational naturalness.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=300,
            )

            content = response.choices[0].message.content.strip()
            result = self._extract_json(content)

            score = float(result.get("score", 5.0))
            logger.debug(
                f"Humanlike rating: {score}/10 - {result.get('reasoning', '')[:100]}"
            )

            return round(score, 1)

        except Exception as e:
            logger.error(f"Humanlike rating evaluation failed: {e}")
            return 5.0

    def _get_expected_criteria(self, turn_index: int, script_turns: List[Dict]) -> str:
        """Get expected response criteria for a turn"""
        # Look for corresponding ASSISTANT turn in script
        for turn in script_turns:
            if turn.get("role") == "ASSISTANT":
                return turn.get("content", "")
        return ""

    def _validate_single_turn(
        self,
        turn_number: int,
        agent_response: str,
        context: str,
        expected_criteria: str,
    ) -> Dict[str, Any]:
        """
        Validate a single agent turn using GPT-5

        Returns: {
            "turn": int,
            "accuracy": float (0-10),
            "context_understanding": float (0-10),
            "response_quality": float (0-10),
            "reasoning": str,
            "issues": [str]
        }
        """
        prompt = f"""You are evaluating a voice agent's response for human-likeness and accuracy.

CONVERSATION CONTEXT (everything said before this turn):
{context}

AGENT'S RESPONSE:
{agent_response}

EXPECTED RESPONSE CRITERIA:
{expected_criteria if expected_criteria else "N/A - Evaluate based on context appropriateness"}

Evaluate the agent's response on these criteria:

1. ACCURACY (0-10): Did the agent answer correctly based on the context and question?
   - Consider factual correctness
   - Consider whether the response addresses what was asked
   - Consider if the response is complete

2. CONTEXT UNDERSTANDING (0-10): Did the agent demonstrate understanding of the conversation so far?
   - Consider if the agent remembered previous turns
   - Consider if the response makes sense given the conversation flow

3. RESPONSE QUALITY (0-10): How human-like and natural was the response?
   - No glitches, repetitions, or robotic patterns
   - Natural language flow
   - Appropriate tone and formality

Return ONLY a JSON object:
{{
    "accuracy": 0-10,
    "context_understanding": 0-10,
    "response_quality": 0-10,
    "reasoning": "Brief explanation of scores",
    "issues": ["list any specific problems: glitches, inaccuracies, unnatural responses"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of conversational AI quality. You assess accuracy, context understanding, and human-likeness.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=1500,
            )

            content = response.choices[0].message.content.strip()
            result = self._extract_json(content)

            if "accuracy" not in result:
                logger.error(f"Invalid validation result for turn {turn_number}")
                return self._default_validation(turn_number)

            # Add turn number
            result["turn"] = turn_number

            return result

        except Exception as e:
            logger.error(f"Turn validation failed for turn {turn_number}: {e}")
            return self._default_validation(turn_number)

    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from GPT response"""
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
        except Exception as e:
            logger.error(f"JSON extraction failed: {e}")

        return {}

    def _default_validation(self, turn_number: int) -> Dict[str, Any]:
        """Default validation when GPT-5 fails"""
        return {
            "turn": turn_number,
            "accuracy": 5.0,
            "context_understanding": 5.0,
            "response_quality": 5.0,
            "reasoning": "Validation failed - default scores assigned",
            "issues": ["Validation system error"],
        }

    def _calculate_overall_metrics(
        self, turn_validations: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate overall metrics from turn validations"""
        if not turn_validations:
            return {
                "humanlike_rating": 0.0,
                "overall_accuracy": 0.0,
                "least_accurate_turns": [],
            }

        # Average humanlike rating (response quality)
        humanlike_scores = [t.get("response_quality", 0) for t in turn_validations]
        humanlike_rating = sum(humanlike_scores) / len(humanlike_scores)

        # Overall accuracy (average of accuracy and context understanding)
        accuracy_scores = [t.get("accuracy", 0) for t in turn_validations]
        context_scores = [t.get("context_understanding", 0) for t in turn_validations]
        overall_accuracy = (sum(accuracy_scores) + sum(context_scores)) / (
            2 * len(turn_validations)
        )

        # Find turns with accuracy < 7
        least_accurate = [
            {
                "turn": t["turn"],
                "accuracy": t.get("accuracy", 0),
                "issue": t.get("reasoning", ""),
                "problems": t.get("issues", []),
            }
            for t in turn_validations
            if t.get("accuracy", 10) < 7
        ]

        # Sort by accuracy and take worst 3
        least_accurate.sort(key=lambda x: x["accuracy"])
        least_accurate = least_accurate[:3]

        return {
            "humanlike_rating": round(humanlike_rating, 2),
            "overall_accuracy": round(overall_accuracy, 2),
            "least_accurate_turns": least_accurate,
        }

    def evaluate_outcome_orientation(
        self, transcript: List[Dict[str, Any]], expected_outcome: str
    ) -> float:
        """
        Evaluate if the conversation achieved the expected outcome.

        Uses GPT-5 to assess how well the conversation met the expected outcome
        defined in the scenario.

        Args:
            transcript: Full conversation transcript with role and content
            expected_outcome: The expected outcome from the scenario

        Returns:
            Score from 0-10 indicating how well the outcome was achieved
        """
        try:
            # Format transcript
            conversation_text = "\n".join(
                [
                    f"{turn.get('role', 'UNKNOWN')}: {turn.get('content', '')}"
                    for turn in transcript
                ]
            )

            prompt = f"""Evaluate if this conversation achieved the expected outcome.

**Expected Outcome**: {expected_outcome}

**Conversation Transcript**:
{conversation_text}

**Instructions**:
Rate 0-10 how well the expected outcome was achieved:
- 0-2: Outcome not achieved at all, conversation went off track
- 3-4: Minor progress towards outcome but largely unsuccessful
- 5-6: Partial achievement, some key aspects addressed
- 7-8: Most of the outcome achieved with minor gaps
- 9-10: Expected outcome fully achieved

Return ONLY a JSON object:
{{
    "score": 0-10 (float),
    "reasoning": "Brief explanation of why this score was given, highlighting what was/wasn't achieved"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of conversational outcomes. You assess whether conversations achieve their stated goals.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=500,
            )

            content = response.choices[0].message.content.strip()
            result = self._extract_json(content)

            score = float(result.get("score", 5.0))
            reasoning = result.get("reasoning", "No reasoning provided")

            logger.info(
                f"Outcome orientation evaluated: {score}/10 - {reasoning[:100]}"
            )

            return round(score, 2)

        except Exception as e:
            logger.error(f"Outcome orientation evaluation failed: {e}")
            return 5.0  # Default to middle score on error
