#!/usr/bin/env python3
"""
Simplified Bolna API Fetcher for downloading call data and audio files.

This script focuses only on:
1. Fetching call data from Bolna API
2. Downloading audio files locally
3. Calling the audio processor for analysis and storage

The audio processing, transcript enhancement, and database storage are handled
by the separate audio_processor.py module.

Usage:
    python fetch_bolna_calls_simple.py

Environment Variables Required:
    - BOLNA_API_KEY: Your Bolna API key
    - DATABASE_URL: PostgreSQL connection string
    - AWS_ACCESS_KEY_ID: AWS access key for S3
    - AWS_SECRET_ACCESS_KEY: AWS secret key for S3
    - AWS_REGION: AWS region (default: us-east-1)
    - S3_BUCKET_NAME: S3 bucket name for storing audio files
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import tempfile
import mimetypes
from dotenv import load_dotenv
import json

# Add the parent directory to Python path to import from app.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from app.utils.audio_processor import process_audio_and_store
except ImportError:
    # Try relative import if running from app directory
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.audio_processor import process_audio_and_store

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bolna API configuration
BOLNA_API_BASE_URL = "https://api.bolna.ai"
BOLNA_API_ENDPOINTS = {
    "agents": "/agent/all",  # Get agents first
    "agent_executions": "/agent/{agent_id}/executions",  # Get executions for a specific agent
    "call_details": "/executions/{call_id}",
    "transcript": "/executions/{call_id}/transcript",
    "audio": "/executions/{call_id}/audio"
}


class BolnaAPIClient:
    """Client for interacting with Bolna API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_latest_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch the latest calls from Bolna API by getting agents first, then their executions."""
        try:
            # First, get all agents
            agents_url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['agents']}"
            logger.info(f"Fetching agents from Bolna API...")
            logger.info(f"Request URL: {agents_url}")
            
            agents_response = requests.get(agents_url, headers=self.headers)
            agents_response.raise_for_status()
            agents_data = agents_response.json()
            
            logger.info(f"Successfully fetched {len(agents_data)} agents")
            
            # Get executions for each agent
            all_executions = []
            for agent in agents_data:
                agent_id = agent.get('id')
                if not agent_id:
                    continue
                
                executions_url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['agent_executions'].format(agent_id=agent_id)}"
                logger.info(f"Fetching executions for agent {agent_id}...")
                
                try:
                    executions_response = requests.get(executions_url, headers=self.headers)
                    executions_response.raise_for_status()
                    executions_data = executions_response.json()
                    
                    if isinstance(executions_data, list):
                        all_executions.extend(executions_data)
                        logger.info(f"Fetched {len(executions_data)} executions from agent {agent_id}")
                    else:
                        logger.warning(f"Unexpected executions data format for agent {agent_id}: {type(executions_data)}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to fetch executions for agent {agent_id}: {e}")
                    continue
            
            # Sort executions by timestamp (newest first) and limit results
            if all_executions:
                # Sort by timestamp if available, otherwise by creation time
                def get_timestamp(execution):
                    return execution.get('timestamp') or execution.get('created_at') or execution.get('start_time') or '1970-01-01T00:00:00Z'
                
                all_executions.sort(key=get_timestamp, reverse=True)
                limited_executions = all_executions[:limit]
                
                logger.info(f"Returning {len(limited_executions)} most recent executions out of {len(all_executions)} total")
                return limited_executions
            else:
                logger.warning("No executions found from any agent")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching agents: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_latest_calls: {e}")
            return []
    
    def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific call."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['call_details'].format(call_id=call_id)}"
            logger.info(f"Fetching call details for {call_id}...")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            call_data = response.json()
            logger.info(f"Successfully fetched call details for {call_id}")
            return call_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching call details for {call_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching call details for {call_id}: {e}")
            return None
    
    def get_transcript(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript for a specific call."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['transcript'].format(call_id=call_id)}"
            logger.info(f"Fetching transcript for {call_id}...")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            transcript_data = response.json()
            logger.info(f"Successfully fetched transcript for {call_id}")
            return transcript_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching transcript for {call_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching transcript for {call_id}: {e}")
            return None
    
    def download_audio(self, audio_url: str, call_id: str) -> Optional[str]:
        """Download audio file from URL and save locally."""
        try:
            if not audio_url:
                logger.error(f"No audio URL provided for call {call_id}")
                return None
            
            # Ensure recordings directory exists
            recordings_dir = os.path.join(os.getcwd(), 'recordings')
            os.makedirs(recordings_dir, exist_ok=True)
            
            # Download audio file
            logger.info(f"Downloading audio for call {call_id} from {audio_url}")
            response = requests.get(audio_url, stream=True)
            response.raise_for_status()
            
            # Detect file extension from content type or URL
            content_type = response.headers.get('content-type', '')
            if 'audio/' in content_type:
                file_extension = content_type.split('/')[-1].split(';')[0]
            else:
                # Try to get extension from URL
                file_extension = audio_url.split('.')[-1].split('?')[0]
                if file_extension not in ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac']:
                    file_extension = 'mp3'  # Default fallback
            
            # Save file locally
            local_file_path = os.path.join(recordings_dir, f"{call_id}.{file_extension}")
            
            with open(local_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(local_file_path)
            logger.info(f"Successfully downloaded audio for call {call_id}: {local_file_path} ({file_size} bytes)")
            
            return local_file_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading audio for call {call_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading audio for call {call_id}: {e}")
            return None


class TranscriptNormalizer:
    """Helper class for normalizing transcript data."""
    
    @staticmethod
    def normalize_transcript(transcript_data, call_timestamp=None):
        """Normalize transcript data to ensure it's a dictionary format with turns structure."""
        if isinstance(transcript_data, dict):
            # Already a dictionary, check if it has the right structure
            if 'turns' in transcript_data:
                # Already in the right format, return as is
                return transcript_data
            else:
                # Convert existing dict to turns format
                return TranscriptNormalizer._convert_to_turns_format(transcript_data, call_timestamp)
        elif isinstance(transcript_data, str):
            # Convert string transcript to turns format
            # Try to parse as JSON first
            try:
                parsed = json.loads(transcript_data)
                if isinstance(parsed, dict):
                    if 'turns' in parsed:
                        return parsed
                    else:
                        return TranscriptNormalizer._convert_to_turns_format(parsed, call_timestamp)
            except (json.JSONDecodeError, ValueError):
                pass
            
            # If not JSON or parsing failed, parse the string format
            return TranscriptNormalizer._parse_bolna_string_format(transcript_data, call_timestamp)
        else:
            # Handle other types (None, list, etc.)
            return TranscriptNormalizer._convert_to_turns_format(
                {"text": str(transcript_data) if transcript_data else ""}, 
                call_timestamp
            )
    
    @staticmethod
    def _parse_bolna_string_format(transcript_string, call_timestamp=None):
        """Parse Bolna API string format into turns structure."""
        if not transcript_string:
            return TranscriptNormalizer._create_empty_turns_format(call_timestamp)
        
        # Parse the string format: "assistant: text\nuser: text\nassistant: text"
        lines = transcript_string.strip().split('\n')
        turns = []
        
        # Use call timestamp as base, or current time if not available
        base_timestamp = call_timestamp or datetime.now()
        current_time = base_timestamp
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse role and content
            if line.startswith('assistant:'):
                role = "AGENT"
                content = line[10:].strip()  # Remove "assistant: " prefix
            elif line.startswith('user:'):
                role = "USER"
                content = line[5:].strip()   # Remove "user: " prefix
            else:
                # Unknown format, treat as agent
                role = "AGENT"
                content = line.strip()
            
            if content:  # Only add non-empty content
                turn = {
                    "timestamp": current_time.isoformat(),
                    "role": role,
                    "content": content
                }
                turns.append(turn)
                
                # Add one second for next turn
                current_time = current_time + timedelta(seconds=1)
        
        return {
            "turns": turns,
            "format": "bolna_conversation",
            "metadata": {
                "source": "bolna_api",
                "processing_note": "Converted from Bolna string format to turns structure",
                "original_format": "assistant/user string",
                "total_turns": len(turns)
            }
        }
    
    @staticmethod
    def _convert_to_turns_format(data_dict, call_timestamp=None):
        """Convert existing dictionary format to turns structure."""
        base_timestamp = call_timestamp or datetime.now()
        current_time = base_timestamp
        
        # Extract text content
        text_content = data_dict.get('text', str(data_dict))
        
        # Create a single turn with the content
        turn = {
            "timestamp": current_time.isoformat(),
            "role": "AGENT",
            "content": text_content
        }
        
        return {
            "turns": [turn],
            "format": "converted",
            "metadata": {
                "source": "bolna_api",
                "processing_note": f"Converted from {type(data_dict).__name__} format to turns structure",
                "original_keys": list(data_dict.keys()) if isinstance(data_dict, dict) else [],
                "total_turns": 1
            }
        }
    
    @staticmethod
    def _create_empty_turns_format(call_timestamp=None):
        """Create empty turns structure."""
        base_timestamp = call_timestamp or datetime.now()
        
        return {
            "turns": [],
            "format": "empty",
            "metadata": {
                "source": "bolna_api",
                "processing_note": "Created empty turns structure",
                "total_turns": 0
            }
        }


def main():
    """Main function to fetch and process Bolna calls."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    bolna_api_key = os.getenv('BOLNA_API_KEY')
    database_url = os.getenv('DATABASE_URL')
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    s3_bucket = os.getenv('S3_BUCKET_NAME')
    
    # Validate required environment variables
    if not all([bolna_api_key, database_url, aws_access_key, aws_secret_key, s3_bucket]):
        logger.error("Missing required environment variables. Please check your .env file.")
        return
    
    try:
        # Initialize Bolna API client
        bolna_client = BolnaAPIClient(bolna_api_key)
        
        # Prepare S3 configuration for audio processor
        s3_config = {
            'access_key': aws_access_key,
            'secret_key': aws_secret_key,
            'region': aws_region,
            'bucket': s3_bucket
        }
        
        # Fetch latest calls from Bolna
        logger.info("Fetching latest calls from Bolna API...")
        calls = bolna_client.get_latest_calls(limit=5)
        
        if not calls:
            logger.info("No new calls found.")
            return
        
        logger.info(f"Found {len(calls)} calls to process.")
        
        # Process each call
        for call in calls:
            call_id = call.get('id')
            if not call_id:
                continue
            
            logger.info(f"Processing call: {call_id}")
            
            # Get call details
            call_details = bolna_client.get_call_details(call_id)
            if not call_details:
                logger.warning(f"Could not get details for call {call_id}, skipping.")
                continue
            
            # Extract timestamp from call details or use current time as fallback
            call_timestamp = call_details.get('timestamp') or call_details.get('created_at') or call_details.get('start_time')
            if call_timestamp:
                # Convert string timestamp to datetime object if needed
                if isinstance(call_timestamp, str):
                    try:
                        # Try to parse ISO format timestamp
                        call_timestamp = datetime.fromisoformat(call_timestamp.replace('Z', '+00:00'))
                        logger.info(f"Parsed timestamp from call details: {call_timestamp}")
                    except ValueError:
                        try:
                            # Try to parse other common formats
                            call_timestamp = datetime.strptime(call_timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                            logger.info(f"Parsed timestamp with microseconds: {call_timestamp}")
                        except ValueError:
                            try:
                                # Try to parse without microseconds
                                call_timestamp = datetime.strptime(call_timestamp, '%Y-%m-%dT%H:%M:%S')
                                logger.info(f"Parsed timestamp without microseconds: {call_timestamp}")
                            except ValueError:
                                logger.warning(f"Could not parse timestamp '{call_timestamp}', using current time")
                                call_timestamp = datetime.now()
                elif isinstance(call_timestamp, datetime):
                    logger.info(f"Using datetime timestamp from call details: {call_timestamp}")
                else:
                    logger.warning(f"Unexpected timestamp type {type(call_timestamp)}, using current time")
                    call_timestamp = datetime.now()
            else:
                call_timestamp = datetime.now()
                logger.info(f"No timestamp in call details, using current time: {call_timestamp}")
            
            # Get transcript
            transcript = call_details.get('transcript')
            if not transcript:
                logger.warning(f"Could not get transcript for call {call_id}, skipping.")
                continue
            
            # Normalize transcript data to ensure it's a dictionary with turns structure
            normalized_transcript = TranscriptNormalizer.normalize_transcript(transcript, call_timestamp)
            logger.info(f"Normalized transcript for call {call_id}: {type(transcript)} -> {type(normalized_transcript)}")
            
            # Log transcript details for debugging
            if isinstance(normalized_transcript, dict):
                if 'turns' in normalized_transcript:
                    turns_count = len(normalized_transcript['turns'])
                    logger.info(f"Transcript for call {call_id}: {turns_count} turns")
                    
                    # Show first few turns as preview
                    for i, turn in enumerate(normalized_transcript['turns'][:3]):
                        role = turn.get('role', 'UNKNOWN')
                        content_preview = turn.get('content', '')[:50] + "..." if len(turn.get('content', '')) > 50 else turn.get('content', '')
                        logger.info(f"  Turn {i+1}: {role} - {content_preview}")
                    
                    if turns_count > 3:
                        logger.info(f"  ... and {turns_count - 3} more turns")
                else:
                    logger.info(f"Transcript keys: {list(normalized_transcript.keys())}")
            
            # Get audio URL
            if not call_details.get('telephony_data'):
                logger.warning(f"No telephony data for call {call_id}, skipping.")
                continue
                
            audio_url = call_details.get('telephony_data', {}).get('recording_url')
            if not audio_url:
                logger.warning(f"Could not get audio URL for call {call_id}, skipping.")
                continue
            
            # Download audio file locally
            logger.info(f"Downloading audio for call {call_id}...")
            local_audio_path = bolna_client.download_audio(audio_url, call_id)
            
            if local_audio_path:
                logger.info(f"Successfully downloaded audio for call {call_id}")
                
                # Call the audio processor to handle analysis and storage
                logger.info(f"Processing audio and storing results for call {call_id}...")
                success, message = process_audio_and_store(
                    audio_file_path=local_audio_path,
                    transcript_data=normalized_transcript,
                    call_id=call_id,
                    call_timestamp=call_timestamp,
                    database_url=database_url,
                    s3_config=s3_config
                )
                
                if success:
                    logger.info(f"Successfully processed call {call_id}: {message}")
                else:
                    logger.error(f"Failed to process call {call_id}: {message}")
            else:
                logger.error(f"Failed to download audio for call {call_id}")
        
        logger.info("Processing complete!")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    main()
