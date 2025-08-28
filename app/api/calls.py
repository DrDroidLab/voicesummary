"""API endpoints for managing audio calls."""

import logging
import os
from datetime import datetime
from typing import List
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AudioCall
from app.schemas import AudioCallCreate, AudioCallResponse, AudioCallUpdate
from app.utils.s3 import s3_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.post("/", response_model=AudioCallResponse, status_code=status.HTTP_201_CREATED)
async def create_call(
    call_data: AudioCallCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new audio call record.
    
    Args:
        call_data: Call information including transcript and audio URL
        db: Database session
        
    Returns:
        Created call record
    """
    # Check if call_id already exists
    existing_call = db.query(AudioCall).filter(AudioCall.call_id == call_data.call_id).first()
    if existing_call:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Call with ID {call_data.call_id} already exists"
        )
    
    # Validate that the audio file exists in S3
    # s3_key = s3_manager.extract_s3_key_from_url(call_data.audio_file_url)
    # if not s3_key or not s3_manager.file_exists(s3_key):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Audio file not found in S3"
    #     )
    
    # Create new call record
    db_call = AudioCall(
        call_id=call_data.call_id,
        transcript=call_data.transcript,
        audio_file_url=call_data.audio_file_url,
        timestamp=call_data.timestamp or datetime.utcnow()
    )
    
    try:
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        return db_call
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create call: {str(e)}"
        )


@router.get("/count")
async def get_calls_count(db: Session = Depends(get_db)):
    """
    Get total count of calls.
    
    Args:
        db: Database session
        
    Returns:
        Total count of calls
    """
    count = db.query(AudioCall).count()
    return {"total": count}


@router.get("/{call_id}", response_model=AudioCallResponse)
async def get_call(call_id: str, db: Session = Depends(get_db)):
    """
    Get call information by ID.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Call information
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    return call


@router.get("/{call_id}/audio")
async def download_audio(call_id: str, db: Session = Depends(get_db)):
    """
    Download audio file for a specific call.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Audio file as streaming response from S3
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Check if audio_file_url exists
    if not call.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audio file URL available for this call"
        )
    
    # Check if the URL is already an S3 URL
    if call.audio_file_url.startswith(f"https://{s3_manager.bucket_name}.s3.amazonaws.com/"):
        # Already an S3 URL, serve directly from S3
        s3_key = s3_manager.extract_s3_key_from_url(call.audio_file_url)
        if s3_key and s3_manager.file_exists(s3_key):
            audio_file = s3_manager.download_audio_file(s3_key)
            if audio_file:
                # Check if the S3 key has a file extension
                if '.' in s3_key:
                    # S3 key has extension - use it
                    file_extension = s3_key.split('.')[-1]
                    content_type = s3_manager._get_content_type(file_extension)
                else:
                    # S3 key has no extension - detect format from file content
                    logger.info(f"S3 key has no extension, detecting format from content: {s3_key}")
                    
                    # Read the file content to detect format
                    audio_content = audio_file.read()
                    
                    # Check if the content is actually an error message instead of audio
                    if len(audio_content) < 1000:  # Audio files are usually much larger
                        content_text = audio_content.decode('utf-8', errors='ignore')
                        if any(keyword in content_text.lower() for keyword in ['error', 'failed', 'detail', 'exception']):
                            logger.error(f"S3 object contains error message instead of audio: {content_text}")
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="Audio file not available - processing failed"
                            )
                    
                    # Create a temporary file to analyze the format
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_file.write(audio_content)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Detect format from file headers
                        detected_extension = s3_manager._detect_audio_format_from_headers(temp_file_path)
                        logger.info(f"Detected audio format: {detected_extension}")
                        
                        file_extension = detected_extension
                        content_type = s3_manager._get_content_type(detected_extension)
                        
                        logger.info(f"Using detected format for serving: extension={file_extension}, content_type={content_type}")
                        
                    finally:
                        # Clean up temporary file
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                    
                    # Use the audio content we already read
                    audio_data = audio_content
                
                logger.info(f"Serving audio from S3 for call {call_id}: extension={file_extension}, content_type={content_type}")
                
                # Use the audio data we have (either from fresh read or from format detection)
                if 'audio_data' not in locals():
                    audio_data = audio_file.read()
                
                return Response(
                    content=audio_data,
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={call_id}.{file_extension}",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
    
    # If not an S3 URL or S3 file doesn't exist, download from external URL and upload to S3
    try:
        logger.info(f"Processing audio for call {call_id}: URL={call.audio_file_url}")
        
        # Download from external URL and upload to S3 (extension will be auto-detected)
        s3_url = s3_manager.download_and_upload_audio(call.audio_file_url, call_id)
        
        if s3_url:
            # Update the database with the new S3 URL
            call.audio_file_url = s3_url
            db.commit()
            
            # Extract the detected file extension from the S3 URL
            s3_key = s3_manager.extract_s3_key_from_url(s3_url)
            if s3_key and "." in s3_key:
                detected_extension = s3_key.split(".")[-1]
            else:
                detected_extension = "mp3"  # fallback
            
            # Serve the audio from S3
            audio_file = s3_manager.download_audio_file(s3_key)
            
            if audio_file:
                # Determine content type from detected file extension
                content_type = s3_manager._get_content_type(detected_extension)
                
                logger.info(f"Serving audio after S3 upload for call {call_id}: extension={detected_extension}, content_type={content_type}")
                
                return Response(
                    content=audio_file.read(),
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f"attachment; filename={call_id}.{detected_extension}",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to serve audio file from S3"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download and upload audio file to S3"
            )
            
    except Exception as e:
        logger.error(f"Error processing audio for call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio file: {str(e)}"
        )


@router.get("/{call_id}/transcript")
async def get_transcript(call_id: str, db: Session = Depends(get_db)):
    """
    Get transcript JSON for a specific call.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Transcript JSON data
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    return {"call_id": call_id, "transcript": call.transcript}


@router.post("/{call_id}/process-audio")
async def process_audio(call_id: str, db: Session = Depends(get_db)):
    """
    Process audio file for a specific call by downloading from external URL and uploading to S3.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
        
    Returns:
        Processing status and S3 URL if successful
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Check if audio_file_url exists
    if not call.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audio file URL available for this call"
        )
    
    # Check if already processed (S3 URL)
    if call.audio_file_url.startswith(f"https://{s3_manager.bucket_name}.s3.amazonaws.com/"):
        return {
            "status": "already_processed",
            "message": "Audio file already processed and stored in S3",
            "s3_url": call.audio_file_url
        }
    
    try:
        # Determine file extension from URL
        file_extension = "mp3"  # Default
        if "." in call.audio_file_url:
            file_extension = call.audio_file_url.split(".")[-1].split("?")[0]
        
        logger.info(f"Processing audio for call {call_id}: URL={call.audio_file_url}, detected_extension={file_extension}")
        
        # Download from external URL and upload to S3
        s3_url = s3_manager.download_and_upload_audio(call.audio_file_url, call_id, file_extension)
        
        if s3_url:
            # Update the database with the new S3 URL
            call.audio_file_url = s3_url
            db.commit()
            
            return {
                "status": "success",
                "message": "Audio file successfully processed and uploaded to S3",
                "s3_url": s3_url
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download and upload audio file to S3"
            )
            
    except Exception as e:
        logger.error(f"Error processing audio for call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio file: {str(e)}"
        )


@router.get("/", response_model=List[AudioCallResponse])
async def list_calls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all calls with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of call records
    """
    # Order by created_at descending (newest first) and apply pagination
    calls = db.query(AudioCall).order_by(AudioCall.created_at.desc()).offset(skip).limit(limit).all()
    return calls


@router.put("/{call_id}", response_model=AudioCallResponse)
async def update_call(
    call_id: str,
    call_update: AudioCallUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing call record.
    
    Args:
        call_id: Unique identifier for the call
        call_update: Updated call information
        db: Database session
        
    Returns:
        Updated call record
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Update fields if provided
    update_data = call_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(call, field, value)
    
    try:
        db.commit()
        db.refresh(call)
        return call
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update call: {str(e)}"
        )


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(call_id: str, db: Session = Depends(get_db)):
    """
    Delete a call record.
    
    Args:
        call_id: Unique identifier for the call
        db: Database session
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    try:
        db.delete(call)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete call: {str(e)}"
        )
