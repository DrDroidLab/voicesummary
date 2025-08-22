"""API endpoints for managing audio calls."""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AudioCall
from app.schemas import AudioCallCreate, AudioCallResponse, AudioCallUpdate
from app.utils.s3 import s3_manager

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
        Audio file as streaming response
    """
    call = db.query(AudioCall).filter(AudioCall.call_id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Extract S3 key from the stored URL
    s3_key = s3_manager.extract_s3_key_from_url(call.audio_file_url)
    if not s3_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file URL"
        )
    
    # Download audio file from S3
    audio_file = s3_manager.download_audio_file(s3_key)
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download audio file from S3"
        )
    
    # Return audio file as streaming response
    return Response(
        content=audio_file.read(),
        media_type="audio/mpeg",  # Adjust based on your audio format
        headers={"Content-Disposition": f"attachment; filename={call_id}.mp3"}
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
    calls = db.query(AudioCall).offset(skip).limit(limit).all()
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
