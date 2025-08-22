"""Pydantic schemas for API validation."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AudioCallCreate(BaseModel):
    """Schema for creating a new audio call."""
    
    call_id: str = Field(..., description="Unique identifier for the call")
    transcript: Dict[str, Any] = Field(..., description="Call transcript as JSON")
    audio_file_url: str = Field(..., description="S3 URL for the audio file")
    timestamp: Optional[datetime] = Field(None, description="Call timestamp (optional, defaults to now)")


class AudioCallResponse(BaseModel):
    """Schema for audio call response."""
    
    call_id: str
    timestamp: datetime
    transcript: Dict[str, Any]
    audio_file_url: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AudioCallUpdate(BaseModel):
    """Schema for updating an audio call."""
    
    transcript: Optional[Dict[str, Any]] = None
    audio_file_url: Optional[str] = None
    timestamp: Optional[datetime] = None
