#!/usr/bin/env python3
"""
Standalone script to fetch call details from Bolna API and store them in the audio calls database.

Usage:
    python fetch_bolna_calls_standalone.py

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
from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import boto3
from botocore.exceptions import ClientError
import logging
import tempfile
import mimetypes
from dotenv import load_dotenv
import json
import numpy as np

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

# Create a standalone Base class for models
Base = declarative_base()

class AudioCall(Base):
    """Standalone model for storing audio call information."""
    
    __tablename__ = "audio_calls"
    
    call_id = Column(String(255), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    transcript = Column(JSON, nullable=False)
    audio_file_url = Column(Text, nullable=False)
    processed_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f"<AudioCall(call_id='{self.call_id}', timestamp='{self.timestamp}')>"


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
                    if executions_response.status_code == 200:
                        executions_data = executions_response.json()
                        if isinstance(executions_data, list):
                            all_executions.extend(executions_data)
                        logger.info(f"Found {len(executions_data) if isinstance(executions_data, list) else 0} executions for agent {agent_id}")
                    else:
                        logger.warning(f"Failed to get executions for agent {agent_id}: {executions_response.status_code}")
                except Exception as e:
                    logger.warning(f"Error getting executions for agent {agent_id}: {e}")
                    continue
            
            # Sort executions by creation date and limit results
            if all_executions:
                # Sort by created_at if available
                all_executions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                all_executions = all_executions[:limit]
                
                logger.info(f"Successfully fetched {len(all_executions)} total executions")
                
                # Debug: Log the structure of the first execution
                if all_executions:
                    logger.info(f"First execution structure: {all_executions[0]}")
                
                return all_executions
            else:
                logger.info("No executions found for any agents")
                return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch calls from Bolna API: {e}")
            raise
    
    def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """Fetch detailed information for a specific call."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['call_details'].format(call_id=call_id)}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch call details for {call_id}: {e}")
            raise
    
    def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """Fetch transcript for a specific call."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['transcript'].format(call_id=call_id)}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch transcript for {call_id}: {e}")
            raise
    
    def get_call_audio_url(self, call_id: str) -> Optional[str]:
        """Get the audio file URL for a specific call."""
        try:
            url = f"{BOLNA_API_BASE_URL}{BOLNA_API_ENDPOINTS['audio'].format(call_id=call_id)}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # The response might contain the audio file URL or direct audio data
            # This depends on how Bolna API provides audio files
            audio_data = response.json()
            
            # Extract audio URL from response (adjust based on actual API response structure)
            if isinstance(audio_data, dict):
                # Try different possible keys for audio URL
                for key in ['audio_url', 'url', 'file_url', 'download_url', 'media_url']:
                    if key in audio_data and audio_data[key]:
                        return audio_data[key]
                
                # If no URL found, check if the response contains direct audio data
                if 'audio_data' in audio_data or 'file_data' in audio_data:
                    logger.info(f"Audio data found directly in response for call {call_id}")
                    return f"direct://{call_id}"  # Special marker for direct data
                
                logger.warning(f"Could not extract audio URL from response for call {call_id}")
                return None
            else:
                logger.warning(f"Unexpected audio response format for call {call_id}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch audio for {call_id}: {e}")
            return None


class S3Manager:
    """Manager for S3 operations."""
    
    def __init__(self, access_key: str, secret_key: str, region: str, bucket_name: str):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        self.bucket_name = bucket_name
    
    def download_and_upload_audio(self, audio_url: str, call_id: str) -> Optional[str]:
        """Download audio from URL and upload to S3, return S3 URL."""
        try:
            # Handle direct audio data from Bolna API
            if audio_url.startswith('direct://'):
                logger.info(f"Processing direct audio data for call {call_id}")
                # For now, we'll need to handle this differently - might need to call the audio endpoint again
                # and get the actual binary data
                return self._handle_direct_audio_data(call_id)
            
            logger.info(f"Downloading audio from {audio_url} for call {call_id}")
            
            # Download the audio file
            response = requests.get(audio_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Log response headers for debugging
            logger.info(f"Response headers for {audio_url}: {dict(response.headers)}")
            
            # Create a temporary file to store the downloaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
                # Write the downloaded content to the temporary file
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_file_path = temp_file.name
                logger.info(f"Downloaded audio to temporary file: {temp_file_path}")
            
            # Now detect the actual format from file headers (more reliable)
            detected_extension = self._detect_audio_format_from_headers(temp_file_path)
            logger.info(f"Detected audio format: {detected_extension}")
            
            # Create the final filename with correct extension
            final_filename = f"audio.{detected_extension}"
            final_temp_path = temp_file_path.replace('.tmp', f'.{detected_extension}')
            
            # Rename the temp file to have the correct extension
            os.rename(temp_file_path, final_temp_path)
            logger.info(f"Renamed temp file to: {final_temp_path}")
            
            # Create recordings directory if it doesn't exist
            recordings_dir = os.path.join(os.getcwd(), 'recordings')
            os.makedirs(recordings_dir, exist_ok=True)
            
            # Copy the file to recordings directory for local testing
            local_copy_path = os.path.join(recordings_dir, f"{call_id}.{detected_extension}")
            import shutil
            shutil.copy2(final_temp_path, local_copy_path)
            logger.info(f"Saved local copy to: {local_copy_path}")
            
            try:
                # Generate S3 key with proper extension
                s3_key = f"calls/{call_id}/audio.{detected_extension}"
                content_type = self._get_content_type(detected_extension)
                
                logger.info(f"Uploading to S3 with key: {s3_key}, content type: {content_type}")
                
                # Upload to S3
                with open(final_temp_path, 'rb') as file_obj:
                    self.s3_client.upload_fileobj(
                        file_obj,
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={
                            'ContentType': content_type,
                            'Metadata': {
                                'call_id': call_id,
                                'source_url': audio_url,
                                'uploaded_at': str(datetime.now()),
                                'detected_format': detected_extension,
                                'local_copy_path': local_copy_path
                            }
                        }
                    )
                
                # Generate S3 URL
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
                logger.info(f"Successfully uploaded audio for call {call_id} to S3: {s3_url}")
                logger.info(f"Local copy available at: {local_copy_path}")
                
                return s3_url
                
            finally:
                # Clean up temporary file
                if os.path.exists(final_temp_path):
                    os.unlink(final_temp_path)
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download audio from {audio_url}: {e}")
            return None
        except ClientError as e:
            logger.error(f"Failed to upload audio to S3 for call {call_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing audio for call {call_id}: {e}")
            return None
    
    def _handle_direct_audio_data(self, call_id: str) -> Optional[str]:
        """Handle direct audio data from Bolna API (placeholder for now)."""
        # This would need to be implemented based on how Bolna provides direct audio data
        # For now, create a placeholder file
        try:
            # Create recordings directory if it doesn't exist
            recordings_dir = os.path.join(os.getcwd(), 'recordings')
            os.makedirs(recordings_dir, exist_ok=True)
            
            # Create a placeholder file locally
            local_copy_path = os.path.join(recordings_dir, f"{call_id}_placeholder.txt")
            with open(local_copy_path, 'w') as f:
                f.write("Direct audio data not yet implemented - needs Bolna API integration")
            
            logger.info(f"Created placeholder file at: {local_copy_path}")
            
            # For now, we can't upload this to S3 since it's not actual audio
            # Return None to indicate failure
            return None
            
        except Exception as e:
            logger.error(f"Failed to create placeholder for direct audio: {e}")
            return None
    
    def _get_file_extension(self, content_type: str, url: str) -> str:
        """Determine file extension from content type or URL."""
        logger.info(f"Determining file extension for content_type: '{content_type}', url: '{url}'")
        
        # Try to get extension from content type
        if content_type:
            # Handle common audio content types
            content_type_lower = content_type.lower()
            if 'audio/mpeg' in content_type_lower or 'audio/mp3' in content_type_lower:
                return 'mp3'
            elif 'audio/wav' in content_type_lower:
                return 'wav'
            elif 'audio/mp4' in content_type_lower or 'audio/m4a' in content_type_lower:
                return 'm4a'
            elif 'audio/aac' in content_type_lower:
                return 'aac'
            elif 'audio/ogg' in content_type_lower:
                return 'ogg'
            elif 'audio/flac' in content_type_lower:
                return 'flac'
            else:
                # Try mimetypes module as fallback
                ext = mimetypes.guess_extension(content_type)
                if ext:
                    logger.info(f"Found extension '{ext}' from mimetypes for content type '{content_type}'")
                    return ext.lstrip('.')
        
        # Try to get extension from URL
        if '.' in url:
            url_ext = url.split('.')[-1].split('?')[0].split('#')[0]  # Remove query parameters and fragments
            if url_ext.lower() in ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac']:
                logger.info(f"Found extension '{url_ext}' from URL")
                return url_ext.lower()
        
        # Default to mp3 if we can't determine the format
        logger.warning(f"Could not determine file extension, defaulting to 'mp3' for content_type: '{content_type}', url: '{url}'")
        return 'mp3'
    
    def _get_content_type(self, file_extension: str) -> str:
        """Get the appropriate content type for a file extension."""
        content_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4',
            'aac': 'audio/aac',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac'
        }
        content_type = content_types.get(file_extension.lower(), 'audio/mpeg')
        logger.info(f"Setting content type '{content_type}' for file extension '{file_extension}'")
        return content_type

    def _validate_transcript_structure(self, transcript_data):
        """Validate that transcript data has the required structure."""
        if not isinstance(transcript_data, dict):
            return False, f"Transcript must be a dictionary, got {type(transcript_data).__name__}"
        
        # Check for required fields
        if 'turns' not in transcript_data:
            return False, "Transcript missing required 'turns' field"
        
        if not isinstance(transcript_data['turns'], list):
            return False, "Transcript 'turns' field must be a list"
        
        # Validate each turn structure
        for i, turn in enumerate(transcript_data['turns']):
            if not isinstance(turn, dict):
                return False, f"Turn {i} must be a dictionary, got {type(turn).__name__}"
            
            # Check required turn fields
            if 'timestamp' not in turn:
                return False, f"Turn {i} missing required 'timestamp' field"
            if 'role' not in turn:
                return False, f"Turn {i} missing required 'role' field"
            if 'content' not in turn:
                return False, f"Turn {i} missing required 'content' field"
            
            # Validate field types
            if not isinstance(turn['timestamp'], str):
                return False, f"Turn {i} 'timestamp' must be a string, got {type(turn['timestamp']).__name__}"
            if not isinstance(turn['role'], str):
                return False, f"Turn {i} 'role' must be a string, got {type(turn['role']).__name__}"
            if not isinstance(turn['content'], str):
                return False, f"Turn {i} 'content' must be a string, got {type(turn['content']).__name__}"
            
            # Validate role values
            if turn['role'] not in ['AGENT', 'USER']:
                logger.warning(f"Turn {i} has unusual role: {turn['role']}")
        
        # Check for optional but recommended fields
        if 'format' not in transcript_data:
            logger.warning("Transcript missing 'format' field")
        
        if 'metadata' not in transcript_data:
            logger.warning("Transcript missing 'metadata' field")
        
        return True, f"Transcript structure is valid with {len(transcript_data['turns'])} turns"

    def _normalize_transcript(self, transcript_data, call_timestamp=None):
        """Normalize transcript data to ensure it's a dictionary format with turns structure."""
        if isinstance(transcript_data, dict):
            # Already a dictionary, check if it has the right structure
            if 'turns' in transcript_data:
                # Already in the right format, return as is
                return transcript_data
            else:
                # Convert existing dict to turns format
                return self._convert_to_turns_format(transcript_data, call_timestamp)
        elif isinstance(transcript_data, str):
            # Convert string transcript to turns format
            # Try to parse as JSON first
            try:
                import json
                parsed = json.loads(transcript_data)
                if isinstance(parsed, dict):
                    if 'turns' in parsed:
                        return parsed
                    else:
                        return self._convert_to_turns_format(parsed, call_timestamp)
            except (json.JSONDecodeError, ValueError):
                pass
            
            # If not JSON or parsing failed, parse the string format
            return self._parse_bolna_string_format(transcript_data, call_timestamp)
        else:
            # Handle other types (None, list, etc.)
            return self._convert_to_turns_format(
                {"text": str(transcript_data) if transcript_data else ""}, 
                call_timestamp
            )

    def _parse_bolna_string_format(self, transcript_string, call_timestamp=None):
        """Parse Bolna API string format into turns structure."""
        if not transcript_string:
            return self._create_empty_turns_format(call_timestamp)
        
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

    def _convert_to_turns_format(self, data_dict, call_timestamp=None):
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

    def _create_empty_turns_format(self, call_timestamp=None):
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

    def _detect_audio_format_from_headers(self, file_path: str) -> str:
        """Detect audio format by examining file headers."""
        try:
            with open(file_path, 'rb') as f:
                # Read first 16 bytes to examine file headers
                header = f.read(16)
                
                # Check for common audio file signatures
                if header.startswith(b'ID3') or header.startswith(b'\xff\xfb') or header.startswith(b'\xff\xf3'):
                    return 'mp3'
                elif header.startswith(b'RIFF') and header[8:12] == b'WAVE':
                    return 'wav'
                elif header.startswith(b'ftyp'):
                    # Check for MP4/AAC variants
                    ftype = header[4:8]
                    if ftype in [b'M4A ', b'M4B ', b'M4P ', b'M4V ']:
                        return 'm4a'
                    elif ftype == b'MP4 ':
                        return 'mp4'
                elif header.startswith(b'\xff\xf1') or header.startswith(b'\xff\xf9'):
                    return 'aac'
                elif header.startswith(b'OggS'):
                    return 'ogg'
                elif header.startswith(b'fLaC'):
                    return 'flac'
                
                logger.warning(f"Could not detect audio format from headers for {file_path}")
                return 'mp3'  # Default fallback
                
        except Exception as e:
            logger.error(f"Error detecting audio format from headers: {e}")
            return 'mp3'  # Default fallback

    def _ensure_recordings_directory(self) -> str:
        """Ensure the recordings directory exists and return its path."""
        recordings_dir = os.path.join(os.getcwd(), 'recordings')
        os.makedirs(recordings_dir, exist_ok=True)
        return recordings_dir

    def _cleanup_old_recordings(self, max_age_hours: int = 24) -> None:
        """Clean up old recording files to save disk space."""
        try:
            recordings_dir = self._ensure_recordings_directory()
            current_time = datetime.now()
            
            for filename in os.listdir(recordings_dir):
                file_path = os.path.join(recordings_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_age.total_seconds() > (max_age_hours * 3600):
                        os.remove(file_path)
                        logger.info(f"Cleaned up old recording file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old recordings: {e}")

    def _list_recordings(self) -> List[str]:
        """List all available recording files."""
        try:
            recordings_dir = self._ensure_recordings_directory()
            recordings = []
            
            for filename in os.listdir(recordings_dir):
                file_path = os.path.join(recordings_dir, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                    recordings.append({
                        'filename': filename,
                        'size_bytes': file_size,
                        'age_hours': file_age.total_seconds() / 3600
                    })
            
            return recordings
            
        except Exception as e:
            logger.error(f"Error listing recordings: {e}")
            return []

    def analyze_audio_and_enhance_transcript(self, audio_file_path: str, transcript_data: Dict[str, Any], call_timestamp: datetime) -> Dict[str, Any]:
        """Analyze audio file and enhance transcript with accurate timestamps."""
        try:
            logger.info(f"Analyzing audio file: {audio_file_path}")
            
            # Import process module for audio analysis
            from process import analyze_audio
            
            # Analyze the audio file
            analysis_results = analyze_audio(audio_file_path)
            logger.info(f"Audio analysis completed for {audio_file_path}")
            
            # Convert numpy types to native Python types for JSON serialization
            def convert_numpy_types(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {key: convert_numpy_types(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            # Convert analysis results to JSON-serializable format
            json_safe_results = convert_numpy_types(analysis_results)
            
            # Enhance transcript with accurate timestamps using speech segments and pauses
            enhanced_transcript = self._enhance_transcript_with_timestamps(
                transcript_data, 
                json_safe_results, 
                call_timestamp
            )
            
            # Store enhanced transcript in the results
            json_safe_results['enhanced_transcript'] = enhanced_transcript
            
            return json_safe_results
            
        except Exception as e:
            logger.error(f"Error analyzing audio file {audio_file_path}: {e}")
            # Return basic transcript enhancement without audio analysis
            return self._enhance_transcript_with_timestamps(
                transcript_data, 
                {}, 
                call_timestamp
            )

    def _enhance_transcript_with_timestamps(self, transcript_data: Dict[str, Any], analysis_results: Dict[str, Any], call_timestamp: datetime) -> Dict[str, Any]:
        """Enhance transcript with accurate timestamps using audio analysis data."""
        try:
            if not isinstance(transcript_data, dict) or 'turns' not in transcript_data:
                logger.warning("Invalid transcript data for enhancement")
                return transcript_data
            
            turns = transcript_data['turns']
            if not turns:
                return transcript_data
            
            # Get speech segments and pauses from analysis
            speech_segments = analysis_results.get('speech_segments', [])
            pauses = analysis_results.get('pauses', [])
            
            # Create a timeline of all events (speech + pauses)
            # This will be populated from the full_timeline we create below
            timeline_events = []
            
            # Create transcript turns directly from speech segments and transcript text
            enhanced_turns = []
            
            # Create a comprehensive timeline with all events
            full_timeline = []
            
            # Add speech segments to timeline
            for segment in speech_segments:
                full_timeline.append({
                    'type': 'speech',
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'duration': segment.get('duration', 0),
                    'segment_index': len(full_timeline)
                })
            
            # Add pauses to timeline
            for pause in pauses:
                full_timeline.append({
                    'type': 'pause',
                    'start': pause.get('start_time', 0),
                    'end': pause.get('end_time', 0),
                    'duration': pause.get('duration', 0),
                    'pause_type': pause.get('type', 'unknown'),
                    'segment_index': len(full_timeline)
                })
            
            # Sort timeline by start time
            full_timeline.sort(key=lambda x: x['start'])
            
            # Create turns from speech segments and transcript text
            speech_segments_in_timeline = [event for event in full_timeline if event['type'] == 'speech']
            
            if len(speech_segments_in_timeline) > 0:
                logger.info(f"Creating {len(speech_segments_in_timeline)} turns from {len(turns)} transcript entries and {len(speech_segments_in_timeline)} speech segments")
                
                # Create turns for each speech segment
                for i, speech_segment in enumerate(speech_segments_in_timeline):
                    # Find corresponding transcript content
                    if i < len(turns):
                        # Use existing transcript content
                        turn_content = turns[i]['content']
                        turn_role = turns[i]['role']
                        original_timestamp = turns[i].get('timestamp', '')
                    else:
                        # Create placeholder content for additional speech segments
                        turn_content = f"Speech segment {i+1} (no transcript content)"
                        turn_role = 'UNKNOWN'
                        original_timestamp = ''
                    
                    # Create enhanced turn with accurate timing from speech segment
                    enhanced_turn = {
                        'role': turn_role,
                        'content': turn_content,
                        'start_time': speech_segment['start'],
                        'end_time': speech_segment['end'],
                        'duration': speech_segment['duration'],
                        'timeline_position': speech_segment['segment_index'],
                        'original_timestamp': original_timestamp,
                        'speech_segment_index': i
                    }
                    
                    enhanced_turns.append(enhanced_turn)
                
                # If we have more transcript turns than speech segments, add them with estimated timing
                if len(turns) > len(speech_segments_in_timeline):
                    logger.info(f"Adding {len(turns) - len(speech_segments_in_timeline)} additional turns with estimated timing")
                    
                    for i in range(len(speech_segments_in_timeline), len(turns)):
                        turn = turns[i]
                        
                        # Estimate timing after the last speech segment
                        if speech_segments_in_timeline:
                            last_segment = speech_segments_in_timeline[-1]
                            estimated_start = last_segment['end'] + (i - len(speech_segments_in_timeline) + 1) * 0.5
                        else:
                            estimated_start = i * 1.0
                        
                        enhanced_turn = {
                            'role': turn['role'],
                            'content': turn['content'],
                            'start_time': estimated_start,
                            'end_time': estimated_start + 0.5,
                            'duration': 0.5,
                            'timeline_position': -1,  # Indicates estimated timing
                            'original_timestamp': turn.get('timestamp', ''),
                            'speech_segment_index': -1,  # Indicates no speech segment
                            'timing_method': 'estimated'
                        }
                        
                        enhanced_turns.append(enhanced_turn)
            else:
                logger.warning("No speech segments found, creating turns with estimated timing")
                
                # Fallback: create turns with estimated timing
                for i, turn in enumerate(turns):
                    estimated_start = i * 2.0  # Assume 2 seconds per turn
                    
                    enhanced_turn = {
                        'role': turn['role'],
                        'content': turn['content'],
                        'start_time': estimated_start,
                        'end_time': estimated_start + 1.0,
                        'duration': 1.0,
                        'timeline_position': -1,
                        'original_timestamp': turn.get('timestamp', ''),
                        'speech_segment_index': -1,
                        'timing_method': 'estimated_fallback'
                    }
                    
                    enhanced_turns.append(enhanced_turn)
            
            # Create enhanced transcript
            enhanced_transcript = {
                'turns': enhanced_turns,
                'timeline_events': full_timeline,
                'audio_analysis': {
                    'speech_segments': speech_segments,
                    'pauses': pauses,
                    'total_duration': analysis_results.get('audio_info', {}).get('duration', 0),
                    'speech_percentage': analysis_results.get('audio_info', {}).get('speech_percentage', 0)
                },
                'metadata': {
                    'enhancement_method': 'audio_analysis',
                    'original_turns_count': len(turns),
                    'enhanced_turns_count': len(enhanced_turns),
                    'timeline_events_count': len(full_timeline)
                }
            }
            
            logger.info(f"Enhanced transcript created with {len(enhanced_turns)} turns and {len(timeline_events)} timeline events")
            return enhanced_transcript
            
        except Exception as e:
            logger.error(f"Error enhancing transcript: {e}")
            return transcript_data


class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session."""
        return self.SessionLocal()
    
    def call_exists(self, call_id: str) -> bool:
        """Check if a call already exists in the database."""
        session = self.get_session()
        try:
            existing_call = session.query(AudioCall).filter(AudioCall.call_id == call_id).first()
            return existing_call is not None
        finally:
            session.close()
    
    def create_call(self, call_data: Dict[str, Any]) -> bool:
        """Create a new call record in the database."""
        session = self.get_session()
        try:
            # Convert timestamp if it's a string
            timestamp = call_data.get('timestamp')
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            elif timestamp is None:
                timestamp = datetime.utcnow()
            
            now = datetime.utcnow()
            
            db_call = AudioCall(
                call_id=call_data['call_id'],
                transcript=call_data['transcript'],
                audio_file_url=call_data['audio_file_url'],
                processed_data=call_data.get('processed_data'),
                timestamp=timestamp,
                created_at=now,
                updated_at=now
            )
            
            session.add(db_call)
            session.commit()
            session.refresh(db_call)
            
            logger.info(f"Successfully created call record for {call_data['call_id']}")
            return True
            
        except IntegrityError:
            session.rollback()
            logger.warning(f"Call {call_data['call_id']} already exists, skipping...")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create call record for {call_data['call_id']}: {e}")
            return False
        finally:
            session.close()


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
        # Initialize managers
        bolna_client = BolnaAPIClient(bolna_api_key)
        s3_manager = S3Manager(aws_access_key, aws_secret_key, aws_region, s3_bucket)
        db_manager = DatabaseManager(database_url)
        
        # Clean up old recordings before starting
        logger.info("Cleaning up old recording files...")
        s3_manager._cleanup_old_recordings(max_age_hours=24)
        
        # List existing recordings
        existing_recordings = s3_manager._list_recordings()
        if existing_recordings:
            logger.info(f"Found {len(existing_recordings)} existing recording files:")
            for recording in existing_recordings:
                logger.info(f"  - {recording['filename']} ({recording['size_bytes']} bytes, {recording['age_hours']:.1f} hours old)")
        
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
            
            # Check if call already exists in database
            if db_manager.call_exists(call_id):
                logger.info(f"Call {call_id} already exists in database, skipping.")
                continue
            
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
            transcript = call.get('transcript')
            if not transcript:
                logger.warning(f"Could not get transcript for call {call_id}, skipping.")
                continue
            
            # Normalize transcript data to ensure it's a dictionary with turns structure
            normalized_transcript = s3_manager._normalize_transcript(transcript, call_timestamp)
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
            
            # Validate the normalized transcript structure
            is_valid, validation_message = s3_manager._validate_transcript_structure(normalized_transcript)
            if not is_valid:
                logger.error(f"Transcript validation failed for call {call_id}: {validation_message}")
                continue
            
            logger.info(f"Transcript validation passed for call {call_id}")
            
            # Get audio URL
            if not call.get('telephony_data'):
                logger.warning(f"No telephony data for call {call_id}, skipping.")
                continue
                
            audio_url = call.get('telephony_data', {}).get('recording_url')
            if not audio_url:
                logger.warning(f"Could not get audio URL for call {call_id}, skipping.")
                continue
            
            # Download and upload audio to S3
            logger.info(f"Processing audio for call {call_id}...")
            s3_url = s3_manager.download_and_upload_audio(audio_url, call_id)
            
            if s3_url:
                logger.info(f"Successfully processed audio for call {call_id}")
                
                # Get the local audio file path for analysis
                temp_path = os.path.join(os.getcwd(), 'recordings', f"{call_id}.wav")
                detected_format = s3_manager._detect_audio_format_from_headers(temp_path)
                local_audio_path = os.path.join(os.getcwd(), 'recordings', f"{call_id}.{detected_format}")
                
                # Analyze audio and enhance transcript
                logger.info(f"Analyzing audio and enhancing transcript for call {call_id}...")
                analysis_results = s3_manager.analyze_audio_and_enhance_transcript(
                    local_audio_path, 
                    normalized_transcript, 
                    call_timestamp
                )
                
                # Store analysis results in processed_data
                processed_data = analysis_results
                
                # Create call record in database
                call_data = {
                    'call_id': call_id,
                    'transcript': analysis_results.get('enhanced_transcript', normalized_transcript),
                    'audio_file_url': s3_url,
                    'processed_data': processed_data,
                    'timestamp': call_timestamp
                }
                
                if db_manager.create_call(call_data):
                    logger.info(f"Successfully created call record for {call_id} with audio analysis")
                else:
                    logger.error(f"Failed to create call record for {call_id}")
            else:
                logger.error(f"Failed to process audio for call {call_id}")
        
        # List final recordings
        final_recordings = s3_manager._list_recordings()
        if final_recordings:
            logger.info(f"Final recording files available:")
            for recording in final_recordings:
                logger.info(f"  - {recording['filename']} ({recording['size_bytes']} bytes, {recording['age_hours']:.1f} hours old)")
        
        logger.info("Processing complete!")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise


def test_transcript_normalization():
    """Test function to verify transcript normalization works correctly."""
    logger.info("Testing transcript normalization...")
    
    # Create a test S3 manager instance
    s3_manager = S3Manager("test", "test", "test", "test")
    
    # Test cases
    test_cases = [
        # String transcript (like from Bolna API) - the main case
        ("assistant: Hello from Bolna\nuser:  hello\nassistant:  Hello! Am I speaking with you? Is this a good time to talk? I am calling to schedule an appointment for you with Dipesh Mittal. May I know a suitable date and time?\nuser:  uh tomorrow twelve pm\nassistant:  Thank you for your preference. Our usual appointment slots are between 11am and 6pm on weekdays. Would you like to extend the timing up to 8pm if 12pm is not available, or is 12pm suitable for you? Also, just to confirm, tomorrow is Wednesday, August 20, 2025. Does that work for you?\n", "bolna_string_format"),
        
        # Dictionary transcript with turns (already correct format)
        ({"turns": [{"timestamp": "2025-08-26T15:04:11.842416", "role": "AGENT", "content": "Hello"}]}, "dict_with_turns"),
        
        # Dictionary transcript without turns (needs conversion)
        ({"text": "Hello world", "segments": []}, "dict_without_turns"),
        
        # JSON string with turns
        ('{"turns": [{"timestamp": "2025-08-26T15:04:11.842416", "role": "AGENT", "content": "Hello"}]}', "json_with_turns"),
        
        # JSON string without turns
        ('{"text": "Hello world", "segments": []}', "json_without_turns"),
        
        # None/empty
        (None, "none"),
        ("", "empty_string"),
        
        # List (unexpected but possible)
        (["segment1", "segment2"], "list")
    ]
    
    # Use a fixed timestamp for consistent testing
    test_timestamp = datetime(2025, 8, 26, 15, 4, 11)
    
    for test_data, test_type in test_cases:
        try:
            logger.info(f"\n--- Testing {test_type} ---")
            logger.info(f"Input type: {type(test_data)}")
            if isinstance(test_data, str):
                logger.info(f"Input preview: {test_data[:100]}...")
            
            normalized = s3_manager._normalize_transcript(test_data, test_timestamp)
            logger.info(f"✓ Normalized: {type(normalized)}")
            
            if isinstance(normalized, dict):
                logger.info(f"  Keys: {list(normalized.keys())}")
                if 'turns' in normalized:
                    turns_count = len(normalized['turns'])
                    logger.info(f"  Turns: {turns_count}")
                    
                    # Show first few turns
                    for i, turn in enumerate(normalized['turns'][:2]):
                        role = turn.get('role', 'UNKNOWN')
                        content_preview = turn.get('content', '')[:30] + "..." if len(turn.get('content', '')) > 30 else turn.get('content', '')
                        logger.info(f"    Turn {i+1}: {role} - {content_preview}")
                    
                    if turns_count > 2:
                        logger.info(f"    ... and {turns_count - 2} more turns")
                
                # Validate the structure
                is_valid, validation_message = s3_manager._validate_transcript_structure(normalized)
                if is_valid:
                    logger.info(f"  ✓ Validation: {validation_message}")
                else:
                    logger.error(f"  ✗ Validation: {validation_message}")
            
        except Exception as e:
            logger.error(f"✗ {test_type}: ERROR: {e}")
    
    logger.info("\nTranscript normalization test complete!")


def test_audio_format_detection():
    """Test function to verify audio format detection works correctly."""
    logger.info("Testing audio format detection...")
    
    # Create a test S3 manager instance
    s3_manager = S3Manager("test", "test", "test", "test")
    
    # Test with a sample MP3 file (if available)
    test_files = [
        ("test.mp3", "mp3"),
        ("test.wav", "wav"),
        ("test.m4a", "m4a"),
        ("test.aac", "aac"),
        ("test.ogg", "ogg"),
        ("test.flac", "flac")
    ]
    
    for filename, expected_format in test_files:
        if os.path.exists(filename):
            detected_format = s3_manager._detect_audio_format_from_headers(filename)
            status = "✓" if detected_format == expected_format else "✗"
            logger.info(f"{status} {filename}: expected {expected_format}, detected {detected_format}")
        else:
            logger.info(f"- {filename}: file not found, skipping")
    
    logger.info("Audio format detection test complete!")


if __name__ == "__main__":
    # Run format detection test if requested
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            test_audio_format_detection()
        elif sys.argv[1] == "--test-transcript":
            test_transcript_normalization()
        else:
            logger.error(f"Unknown test option: {sys.argv[1]}")
            logger.info("Available test options: --test, --test-transcript")
    else:
        main()
