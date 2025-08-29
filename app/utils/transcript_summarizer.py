#!/usr/bin/env python3
"""
Transcript Summarizer
Uses OpenAI to create concise summaries of call transcripts.
"""

import openai
from typing import Dict, Any, Optional
from app.config import settings
import json


def get_agent_prompt():
    try:
        import yaml
        import os
        
        # Get the root directory (where config/ is located)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        config_file_path = os.path.join(root_dir, 'config', 'agent_prompts.yaml')
        
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get('default_agent_prompt', '')
    except Exception as e:
        print(f"Warning: Could not load agent prompt from config: {e}")
        return ""


class TranscriptSummarizer:
    """Summarizes call transcripts using OpenAI."""
    
    def __init__(self):
        """Initialize the transcript summarizer with OpenAI client."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = 'gpt-4o'
    
    def summarize_transcript(
        self, 
        transcript: Dict[str, Any],
        call_context: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Summarize a call transcript using OpenAI.
        
        Args:
            transcript: Call transcript data
            call_context: Additional context about the call (optional)
            
        Returns:
            Dictionary containing summary results, or None if failed
        """
        try:
            # Prepare the summarization prompt
            print('###### - 1')
            summary_prompt = self._create_summary_prompt(transcript, call_context)
            print('###### - 2')
            
            # Call OpenAI for summarization
            # Check if the model supports json_object response format
            # GPT-4 models support json_object response format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert call analyst. Create a concise, professional summary of the call transcript. Focus on key points, outcomes, and actionable insights."
                    },
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse the JSON response directly
            print('response', response)
            summary_result = json.loads(response.choices[0].message.content)
            
            # Add metadata
            summary_result['metadata'] = {
                'model_used': self.model,
                'summary_timestamp': self._get_current_timestamp()
            }
            
            return summary_result
            
        except Exception as e:
            # Return None if summarization fails
            print(f"Warning: Transcript summarization failed: {e}")
            return None
    
    def _create_summary_prompt(
        self, 
        transcript: Dict[str, Any], 
        call_context: str = None
    ) -> str:
        """Create the summarization prompt for OpenAI."""
        
        # Extract conversation turns for summarization
        turns = transcript.get('turns', [])
        print('turns')
        print('###### - 3')
        conversation_text = self._format_conversation_for_summary(turns)
        
        # Load agent prompt from config YAML file
        agent_prompt = get_agent_prompt()
        
        prompt = f"""
Please provide a comprehensive summary of the following call transcript in the exact JSON format specified.

{f"ADDITIONAL CONTEXT: {call_context}" if call_context else ""}

CALL TRANSCRIPT:
{conversation_text}

This is what the agent's purpose was as part of the call:
{agent_prompt}

Please provide your summary in the following JSON format:

{{
  "executive_summary": "Brief 2-3 sentence overview of the call",
  "call_outcome": "What was the final result or resolution of the call when compared to the intended behavior or goal?",
  "call_quality": {{
    "resolution_achieved": true/false,
    "customer_satisfaction": "high/medium/low based on transcript tone",
    "overall_rating": "excellent/good/fair/poor"
  }},
  "areas_of_improvement": ["list the areas of improvement that the agent should work on and if it deviated from intended behavior"],
}}

IMPORTANT: 
- Keep the executive summary concise but informative
- Focus on business value and actionable insights
- Be objective and professional in tone
- Ensure all JSON fields are properly filled
- Base insights on actual transcript content
"""
        
        return prompt
    
    def _format_conversation_for_summary(self, turns: list) -> str:
        """Format conversation turns for summarization."""
        if not turns:
            return "No conversation turns available for summarization."
        
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
                # If no JSON found, create a basic summary structure
                return self._create_fallback_summary(response_text)
                
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON from response: {e}")
            # Create a fallback summary structure
            return self._create_fallback_summary(response_text)
    
    def _create_fallback_summary(self, response_text: str) -> Dict[str, Any]:
        """
        Create a fallback summary structure when JSON parsing fails.
        
        Args:
            response_text: The raw response text from OpenAI
            
        Returns:
            Basic summary structure
        """
        return {
            "executive_summary": f"Call summary: {response_text[:200]}...",
            "call_outcome": "Call completed",
            "call_quality": {
                "resolution_achieved": True,
                "customer_satisfaction": "medium",
                "overall_rating": "good"
            },
            "areas_of_improvement": ["Review call details for specific insights"]
        }


def summarize_transcript(
    transcript: Dict[str, Any],
    call_context: str = None
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to summarize a transcript.
    
    Args:
        transcript: Call transcript data
        call_context: Additional context about the call (optional)
        
    Returns:
        Summary results dictionary, or None if failed
    """
    try:
        summarizer = TranscriptSummarizer()
        return summarizer.summarize_transcript(transcript, call_context)
    except Exception as e:
        print(f"Warning: Could not create transcript summarizer: {e}")
        return None
