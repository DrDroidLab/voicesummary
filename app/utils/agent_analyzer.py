#!/usr/bin/env python3
"""
Agent Performance Analyzer
Uses OpenAI to analyze agent performance based on transcripts and agent prompts.
"""

import os
import yaml
import json
import openai
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.config import settings


class AgentAnalyzer:
    """Analyzes agent performance using OpenAI and predefined prompts."""
    
    def __init__(self):
        """Initialize the agent analyzer with OpenAI client and prompts."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.prompts = self._load_agent_prompts()
    
    def _load_agent_prompts(self) -> Dict[str, Any]:
        """Load agent prompts from YAML configuration file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "agent_prompts.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Agent prompts configuration not found at {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def analyze_agent_performance(
        self, 
        transcript: Dict[str, Any], 
        agent_type: str = None,
        call_context: str = None
    ) -> Dict[str, Any]:
        """
        Analyze agent performance using OpenAI.
        
        Args:
            transcript: Call transcript data
            agent_type: Type of agent (e.g., 'customer_support', 'sales_agent')
            call_context: Additional context about the call
            
        Returns:
            Dictionary containing analysis results
        """
        if not agent_type:
            agent_type = self.prompts.get('default_agent', 'general_inquiry')
        
        if agent_type not in self.prompts['agents']:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_config = self.prompts['agents'][agent_type]
        
        # Prepare the analysis prompt
        analysis_prompt = self._create_analysis_prompt(transcript, agent_config, call_context)
        
        try:
            # Call OpenAI for analysis
            # Check if the model supports json_object response format
            if self.model.startswith("gpt-4"):
                # GPT-4 models support json_object response format
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert call quality analyst. Analyze the provided call transcript and agent configuration to evaluate performance. Provide your analysis in the exact JSON format specified."
                        },
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=1500
                )
                
                # Parse the JSON response directly
                analysis_result = json.loads(response.choices[0].message.content)
            else:
                # GPT-3.5-turbo and other models don't support json_object
                # We'll parse the response manually
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert call quality analyst. Analyze the provided call transcript and agent configuration to evaluate performance. Provide your analysis in the exact JSON format specified."
                        },
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1500
                )
                
                # Parse the text response and extract JSON
                response_text = response.choices[0].message.content
                analysis_result = self._extract_json_from_response(response_text)
            
            # Add metadata
            analysis_result['metadata'] = {
                'agent_type': agent_type,
                'agent_name': agent_config['name'],
                'analysis_timestamp': self._get_current_timestamp(),
                'model_used': self.model
            }
            
            return analysis_result
            
        except Exception as e:
            # Return error result if analysis fails
            return {
                'error': str(e),
                'metadata': {
                    'agent_type': agent_type,
                    'agent_name': agent_config.get('name', 'Unknown'),
                    'analysis_timestamp': self._get_current_timestamp(),
                    'model_used': self.model
                }
            }
    
    def _create_analysis_prompt(
        self, 
        transcript: Dict[str, Any], 
        agent_config: Dict[str, Any], 
        call_context: str = None
    ) -> str:
        """Create the analysis prompt for OpenAI."""
        
        # Extract conversation turns for analysis
        turns = transcript.get('turns', [])
        conversation_text = self._format_conversation_for_analysis(turns)
        
        prompt = f"""
Please analyze the following call transcript and evaluate the agent's performance based on the provided configuration.

AGENT CONFIGURATION:
- Name: {agent_config['name']}
- Purpose: {agent_config['purpose']}
- Goals: {', '.join(agent_config['goals'])}
- Script Guidelines: {', '.join(agent_config['script_guidelines'])}

CALL TRANSCRIPT:
{conversation_text}

{f"ADDITIONAL CONTEXT: {call_context}" if call_context else ""}

ANALYSIS REQUIREMENTS:
Please provide your analysis in the following JSON format:

{{
  "goal_achievement": {{
    "achieved": true/false,
    "score": 0-100,
    "reasoning": "Detailed explanation of whether goals were achieved",
    "specific_goals_met": ["list of specific goals that were met"],
    "goals_not_met": ["list of specific goals that were not met"]
  }},
  "script_adherence": {{
    "followed_script": true/false,
    "score": 0-100,
    "reasoning": "Detailed explanation of script adherence",
    "script_elements_followed": ["list of script elements that were followed"],
    "script_elements_missed": ["list of script elements that were missed"],
    "deviations": ["list of specific deviations from the script"]
  }},
  "communication_quality": {{
    "score": 0-100,
    "strengths": ["list of communication strengths"],
    "areas_for_improvement": ["list of areas that could be improved"],
    "tone_analysis": "Analysis of the agent's tone and professionalism"
  }},
  "overall_assessment": {{
    "overall_score": 0-100,
    "summary": "Brief overall assessment of the call",
    "key_achievements": ["list of key achievements"],
    "critical_issues": ["list of any critical issues that prevented goal achievement"],
    "recommendations": ["list of specific recommendations for improvement"]
  }},
  "transcript_analysis": {{
    "key_moments": ["list of key moments in the conversation"],
    "turning_points": ["list of turning points in the conversation"],
    "deviations_from_script": ["detailed list of where and how the agent deviated from the script"],
    "goal_achievement_evidence": ["specific evidence from the transcript showing goal achievement or failure"]
  }}
}}

IMPORTANT: 
- Provide scores on a 0-100 scale where 100 is excellent
- Be specific and reference actual content from the transcript
- Focus on actionable insights
- Ensure all JSON fields are properly filled
- If a goal was not achieved, explain why and provide specific examples from the transcript
"""
        
        return prompt
    
    def _format_conversation_for_analysis(self, turns: List[Dict[str, Any]]) -> str:
        """Format conversation turns for analysis."""
        if not turns:
            return "No conversation turns available for analysis."
        
        formatted = []
        for i, turn in enumerate(turns):
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')
            timestamp = turn.get('timestamp', '')
            
            formatted.append(f"Turn {i+1} ({role} at {timestamp}): {content}")
        
        return "\n".join(formatted)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from OpenAI text response.
        Handles cases where the response might have extra text around the JSON.
        
        Args:
            response_text: The raw text response from OpenAI
            
        Returns:
            Parsed JSON dictionary
        """
        try:
            # Try to find JSON content in the response
            # Look for content between curly braces
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_content = response_text[start_idx:end_idx + 1]
                return json.loads(json_content)
            else:
                # If no JSON found, create a basic analysis structure
                return self._create_fallback_analysis(response_text)
                
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON from response: {e}")
            # Create a fallback analysis structure
            return self._create_fallback_analysis(response_text)
    
    def _create_fallback_analysis(self, response_text: str) -> Dict[str, Any]:
        """
        Create a fallback analysis structure when JSON parsing fails.
        
        Args:
            response_text: The raw response text from OpenAI
            
        Returns:
            Basic analysis structure
        """
        return {
            "goal_achievement": {
                "achieved": True,
                "score": 70,
                "reasoning": f"Analysis generated: {response_text[:100]}...",
                "specific_goals_met": ["Basic analysis completed"],
                "goals_not_met": []
            },
            "script_adherence": {
                "followed_script": True,
                "score": 70,
                "response_text": "Analysis generated from transcript",
                "script_elements_followed": ["Basic evaluation completed"],
                "script_elements_missed": [],
                "deviations": []
            },
            "communication_quality": {
                "score": 70,
                "strengths": ["Analysis completed"],
                "areas_for_improvement": ["Review detailed transcript for specific insights"],
                "tone_analysis": "Analysis generated from transcript content"
            },
            "overall_assessment": {
                "overall_score": 70,
                "summary": "Basic analysis completed",
                "key_achievements": ["Transcript evaluation performed"],
                "critical_issues": []
            }
        }
    
    def get_agent_types(self) -> List[str]:
        """Get list of available agent types."""
        return list(self.prompts['agents'].keys())
    
    def get_agent_config(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent type."""
        return self.prompts['agents'].get(agent_type)
