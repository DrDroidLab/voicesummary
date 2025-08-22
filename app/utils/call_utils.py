"""Utility functions for accessing call information."""

from typing import Optional, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
from app.models import AudioCall
from app.utils.s3 import s3_manager


def get_call_by_id(call_id: str, db: Session) -> Optional[AudioCall]:
    """
    Get call information by ID.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        AudioCall object if found, None otherwise
    """
    return db.query(AudioCall).filter(AudioCall.call_id == call_id).first()


def get_call_transcript(call_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get transcript JSON for a specific call.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Transcript JSON data if found, None otherwise
    """
    call = get_call_by_id(call_id, db)
    if call:
        return call.transcript
    return None


def get_call_audio_file(call_id: str, db: Session) -> Optional[BinaryIO]:
    """
    Download audio file for a specific call.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        File-like object containing the audio data, or None if not found
    """
    call = get_call_by_id(call_id, db)
    if not call:
        return None
    
    # Extract S3 key from the stored URL
    s3_key = s3_manager.extract_s3_key_from_url(call.audio_file_url)
    if not s3_key:
        return None
    
    # Download audio file from S3
    return s3_manager.download_audio_file(s3_key)


def get_call_audio_url(call_id: str, db: Session, expires_in: int = 3600) -> Optional[str]:
    """
    Get presigned URL for downloading audio file.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        expires_in: URL expiration time in seconds (default: 1 hour)
        
    Returns:
        Presigned URL string, or None if not found
    """
    call = get_call_by_id(call_id, db)
    if not call:
        return None
    
    # Extract S3 key from the stored URL
    s3_key = s3_manager.extract_s3_key_from_url(call.audio_file_url)
    if not s3_key:
        return None
    
    # Generate presigned URL
    return s3_manager.get_audio_file_url(s3_key, expires_in)


def get_call_summary(call_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive call information including metadata.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Dictionary with call information, or None if not found
    """
    call = get_call_by_id(call_id, db)
    if not call:
        return None
    
    return {
        "call_id": call.call_id,
        "timestamp": call.timestamp,
        "transcript": call.transcript,
        "audio_file_url": call.audio_file_url,
        "created_at": call.created_at,
        "updated_at": call.updated_at,
        "audio_download_url": get_call_audio_url(call_id, db)
    }


def validate_audio_file_exists(audio_url: str) -> bool:
    """
    Validate that an audio file exists in S3.
    
    Args:
        audio_url: S3 URL for the audio file
        
    Returns:
        True if file exists, False otherwise
    """
    s3_key = s3_manager.extract_s3_key_from_url(audio_url)
    if not s3_key:
        return False
    
    return s3_manager.file_exists(s3_key)
