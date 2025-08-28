#!/usr/bin/env python3
"""
Audio Processor Module for analyzing audio files and enhancing transcripts.

This module provides functions to:
1. Analyze audio files using the ImprovedVoiceAnalyzer
2. Enhance transcripts with accurate timestamps
3. Store processed data in the database
4. Handle S3 uploads and database operations

Usage:
    from audio_processor import process_audio_and_store
    
    # Process audio file and store results
    success = process_audio_and_store(
        audio_file_path="/path/to/audio.wav",
        transcript_data={"turns": [...]},
        call_id="call_123",
        call_timestamp=datetime.now(),
        database_url="postgresql://...",
        s3_config={"access_key": "...", "secret_key": "...", "region": "...", "bucket": "..."}
    )
"""

import os
import sys
import logging
import tempfile
import mimetypes
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import boto3
from botocore.exceptions import ClientError
import json
from .improved_voice_analyzer import ImprovedVoiceAnalyzer
import numpy as np



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


class AudioProcessor:
    """Main class for processing audio files and enhancing transcripts."""
    
    def __init__(self, database_url: str, s3_config: Dict[str, str]):
        """
        Initialize the AudioProcessor.
        
        Args:
            database_url: PostgreSQL connection string
            s3_config: Dictionary with S3 configuration
                - access_key: AWS access key
                - secret_key: AWS secret key  
                - region: AWS region
                - bucket: S3 bucket name
        """
        self.database_url = database_url
        self.s3_config = s3_config
        
        # Initialize database
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=s3_config['access_key'],
            aws_secret_access_key=s3_config['secret_key'],
            region_name=s3_config['region']
        )
        self.s3_bucket = s3_config['bucket']
    
    def process_audio_and_store(
        self,
        audio_file_path: str,
        transcript_data: Dict[str, Any],
        call_id: str,
        call_timestamp: datetime
    ) -> Tuple[bool, str]:
        """
        Main function to process audio file and store results.
        
        Args:
            audio_file_path: Path to the local audio file
            transcript_data: Transcript data to enhance
            call_id: Unique identifier for the call
            call_timestamp: Timestamp of the call
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info(f"Starting audio processing for call {call_id}")
            
            # Step 1: Analyze audio using the analyze_audio function
            logger.info(f"Analyzing audio file: {audio_file_path}")
            
            analyzer = ImprovedVoiceAnalyzer(
                audio_path=audio_file_path,
                pause_sensitivity="normal"
            )
            
            # Single function call - does everything
            analysis_results = analyzer.analyze_conversation()
            
            # Step 2: Convert numpy types to JSON-serializable formats
            analysis_results = self._convert_numpy_types(analysis_results)
            
            # Step 3: Enhance transcript with accurate timestamps
            logger.info("Enhancing transcript with audio analysis results")
            enhanced_transcript = self._enhance_transcript_with_timestamps(
                transcript_data, 
                analysis_results, 
                call_timestamp
            )
            
            # Step 4: Always upload local audio file to S3 (don't use existing URLs)
            logger.info("Uploading audio file to S3 with detected format")
            s3_url = self._upload_audio_to_s3(audio_file_path, call_id)
            if not s3_url:
                return False, "Failed to upload audio to S3"
            
            logger.info(f"Successfully uploaded audio to S3: {s3_url}")
            
            # Step 5: Store in database
            logger.info("Storing call data in database")
            success = self._store_call_in_database(
                call_id=call_id,
                transcript=enhanced_transcript,
                audio_file_url=s3_url,
                processed_data=analysis_results,
                timestamp=call_timestamp
            )
            
            if success:
                logger.info(f"Successfully processed and stored call {call_id}")
                return True, f"Call {call_id} processed and stored successfully"
            else:
                return False, f"Failed to store call {call_id} in database"
                
        except Exception as e:
            error_msg = f"Error processing audio for call {call_id}: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _convert_numpy_types(self, data: Any) -> Any:
        """Convert numpy types to JSON-serializable Python types."""
        if isinstance(data, dict):
            return {key: self._convert_numpy_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_numpy_types(item) for item in data]
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return data
    
    def _enhance_transcript_with_timestamps(
        self, 
        transcript_data: Dict[str, Any], 
        analysis_results: Dict[str, Any],
        call_timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Enhance transcript with accurate timestamps from audio analysis.
        
        Args:
            transcript_data: Original transcript data
            analysis_results: Results from audio analysis
            call_timestamp: Base timestamp for the call
            
        Returns:
            Enhanced transcript with accurate timestamps
        """
        try:
            # Extract turns from transcript
            turns = transcript_data.get('turns', [])
            if not turns:
                logger.warning("No turns found in transcript data")
                return transcript_data
            
            # Get speech segments and pauses from analysis
            speech_segments = analysis_results.get('speech_segments', [])
            pauses = analysis_results.get('pauses', [])
            
            # Create a timeline of all events (speech + pauses)
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
            
            enhanced_turns = []
            
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
                        'speech_segment_index': i,
                        'timing_method': 'audio_analysis'
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
            
            logger.info(f"Enhanced transcript created with {len(enhanced_turns)} turns and {len(full_timeline)} timeline events")
            return enhanced_transcript
            
        except Exception as e:
            logger.error(f"Error enhancing transcript: {e}")
            return transcript_data
    
    def _upload_audio_to_s3(self, audio_file_path: str, call_id: str) -> Optional[str]:
        """Upload audio file to S3 and return the URL."""
        try:
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
            
            # Detect file extension
            file_extension = self._detect_audio_format(audio_file_path)
            s3_key = f"audio_calls/{call_id}.{file_extension}"
            
            # Upload file to S3
            logger.info(f"Uploading {audio_file_path} to S3 as {s3_key}")
            self.s3_client.upload_file(
                audio_file_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={'ContentType': f'audio/{file_extension}'}
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.s3_bucket}.s3.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded audio to S3: {s3_url}")
            
            return s3_url
            
        except Exception as e:
            logger.error(f"Error uploading audio to S3: {e}")
            return None
    
    def _detect_audio_format(self, file_path: str) -> str:
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
    
    def _store_call_in_database(
        self,
        call_id: str,
        transcript: Dict[str, Any],
        audio_file_url: str,
        processed_data: Dict[str, Any],
        timestamp: datetime
    ) -> bool:
        """Store call data in the database."""
        session = self.get_session()
        try:
            # Convert timestamp if it's a string
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            elif timestamp is None:
                timestamp = datetime.utcnow()
            
            now = datetime.utcnow()
            
            db_call = AudioCall(
                call_id=call_id,
                transcript=transcript,
                audio_file_url=audio_file_url,
                processed_data=processed_data,
                timestamp=timestamp,
                created_at=now,
                updated_at=now
            )
            
            session.add(db_call)
            session.commit()
            session.refresh(db_call)
            
            logger.info(f"Successfully created call record for {call_id}")
            return True
            
        except IntegrityError:
            session.rollback()
            logger.warning(f"Call {call_id} already exists, skipping...")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create call record for {call_id}: {e}")
            return False
        finally:
            session.close()
    
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


def process_audio_and_store(
    audio_file_path: str,
    transcript_data: Dict[str, Any],
    call_id: str,
    call_timestamp: datetime,
    database_url: str,
    s3_config: Dict[str, str]
) -> Tuple[bool, str]:
    """
    Convenience function to process audio and store results.
    
    This is the main function that should be called from external scripts.
    
    Args:
        audio_file_path: Path to the local audio file
        transcript_data: Transcript data to enhance
        call_id: Unique identifier for the call
        call_timestamp: Timestamp of the call
        database_url: PostgreSQL connection string
        s3_config: Dictionary with S3 configuration
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    processor = AudioProcessor(database_url, s3_config)
    return processor.process_audio_and_store(
        audio_file_path=audio_file_path,
        transcript_data=transcript_data,
        call_id=call_id,
        call_timestamp=call_timestamp
    )


if __name__ == "__main__":
    # Example usage
    print("Audio Processor Module")
    print("This module provides the process_audio_and_store function for external use.")
    print("\nUsage:")
    print("from audio_processor import process_audio_and_store")
    print("\n# Process audio file and store results")
    print("success, message = process_audio_and_store(")
    print("    audio_file_path='/path/to/audio.wav',")
    print("    transcript_data={'turns': [...]},")
    print("    call_id='call_123',")
    print("    call_timestamp=datetime.now(),")
    print("    database_url='postgresql://...',")
    print("    s3_config={'access_key': '...', 'secret_key': '...', 'region': '...', 'bucket': '...'}")
    print(")")
