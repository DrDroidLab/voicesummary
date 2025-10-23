"""Validate scenario configuration for agent comparison"""

from typing import Dict, Tuple

SUPPORTED_LANGUAGES = [
    "English",
    "Hindi",
    "Spanish",
    "French",
    "German",
    "Portuguese",
    "Italian",
    "Mandarin",
    "Japanese",
    "Korean",
    "Arabic",
    "Russian",
]


class ScenarioValidator:
    """Validates scenario configuration for agent comparison"""

    @staticmethod
    def validate_scenario(scenario_config: Dict[str, str]) -> Tuple[bool, str]:
        """
        Validate scenario has all required fields with sufficient content.

        Args:
            scenario_config: Dictionary with agent_overview, user_persona,
                           situation, primary_language, and expected_outcome

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        required_fields = [
            "agent_overview",
            "user_persona",
            "situation",
            "primary_language",
            "expected_outcome",
        ]

        # Check all required fields exist
        for field in required_fields:
            if field not in scenario_config:
                return False, f"Missing required field: {field}"

            value = scenario_config[field]

            # Check field has content
            if not value or not isinstance(value, str):
                return False, f"Field '{field}' must be a non-empty string"

            # Check minimum length (except for language)
            if field != "primary_language" and len(value.strip()) < 10:
                return False, f"Field '{field}' must be at least 10 characters"

        # Validate language
        language = scenario_config["primary_language"].strip()
        if language not in SUPPORTED_LANGUAGES:
            supported_langs = ", ".join(SUPPORTED_LANGUAGES)
            return (
                False,
                f"Unsupported language '{language}'. " f"Supported: {supported_langs}",
            )

        return True, ""
