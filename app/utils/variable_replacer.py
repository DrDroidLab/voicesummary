"""Pure variable detection and replacement - no added intelligence"""

import re
from typing import Any, Dict, Set


class VariableReplacer:
    """Detect and replace {placeholder} variables in agent configs"""

    @staticmethod
    def detect_variables(text: str) -> Set[str]:
        """
        Extract all {variable} placeholders from text

        Returns: Set of variable names (without braces)
        """
        pattern = r"\{([^}]+)\}"
        return set(re.findall(pattern, text))

    @staticmethod
    def detect_config_variables(agent_config: Dict[str, Any]) -> Set[str]:
        """
        Scan entire agent config for variables

        Checks: welcome_message, system_prompt, hangup_prompt
        """
        all_vars = set()

        if agent_config.get("welcome_message"):
            all_vars.update(
                VariableReplacer.detect_variables(agent_config["welcome_message"])
            )

        if agent_config.get("system_prompt"):
            all_vars.update(
                VariableReplacer.detect_variables(agent_config["system_prompt"])
            )

        if agent_config.get("hangup_prompt"):
            all_vars.update(
                VariableReplacer.detect_variables(agent_config["hangup_prompt"])
            )

        return all_vars

    @staticmethod
    def replace_variables(text: str, variable_values: Dict[str, str]) -> str:
        """
        Replace {variable} with actual values

        Args:
            text: Text containing {placeholders}
            variable_values: {"variable_name": "actual_value"}
        """
        result = text
        for var_name, value in variable_values.items():
            result = result.replace(f"{{{var_name}}}", value)
        return result

    @staticmethod
    def replace_config_variables(
        agent_config: Dict[str, Any], variable_values: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Return new config with all variables replaced
        """
        config = agent_config.copy()

        if config.get("welcome_message"):
            config["welcome_message"] = VariableReplacer.replace_variables(
                config["welcome_message"], variable_values
            )

        if config.get("system_prompt"):
            config["system_prompt"] = VariableReplacer.replace_variables(
                config["system_prompt"], variable_values
            )

        if config.get("hangup_prompt"):
            config["hangup_prompt"] = VariableReplacer.replace_variables(
                config["hangup_prompt"], variable_values
            )

        return config
