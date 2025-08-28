"""Pydantic schemas for API validation."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class AudioCallCreate(BaseModel):
    """Schema for creating a new audio call."""
    
    call_id: str = Field(..., description="Unique identifier for the call")
    transcript: Dict[str, Any] = Field(..., description="Call transcript as JSON")
    audio_file_url: str = Field(..., description="S3 URL for the audio file")
    processed_data: Optional[Dict[str, Any]] = Field(None, description="Processed analysis data as JSON (optional)")
    timestamp: Optional[datetime] = Field(None, description="Call timestamp (optional, defaults to now)")


class AudioCallResponse(BaseModel):
    """Schema for audio call response."""
    
    call_id: str
    timestamp: int  # Epoch timestamp in seconds
    transcript: Dict[str, Any]
    audio_file_url: str
    processed_data: Optional[Dict[str, Any]] = None
    created_at: int  # Epoch timestamp in seconds
    updated_at: int  # Epoch timestamp in seconds
    
    @field_validator('timestamp', 'created_at', 'updated_at', mode='before')
    @classmethod
    def convert_datetime_to_epoch(cls, v):
        if isinstance(v, datetime):
            return int(v.timestamp())
        return v
    
    class Config:
        from_attributes = True


class AudioCallUpdate(BaseModel):
    """Schema for updating an audio call."""
    
    transcript: Optional[Dict[str, Any]] = None
    audio_file_url: Optional[str] = None
    processed_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
