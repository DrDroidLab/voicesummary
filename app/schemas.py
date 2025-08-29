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
    agent_type: Optional[str] = Field(None, description="Type of agent for performance analysis (optional)")
    call_context: Optional[str] = Field(None, description="Additional context about the call (optional)")
    timestamp: Optional[datetime] = Field(None, description="Call timestamp (optional, defaults to now)")


class AudioCallCreateWithProcessing(BaseModel):
    """Schema for creating a new audio call with immediate processing option."""
    
    call_id: str = Field(..., description="Unique identifier for the call")
    transcript: Dict[str, Any] = Field(..., description="Call transcript as JSON")
    audio_file_url: str = Field(..., description="URL for the audio file (will be processed and uploaded to S3)")
    processed_data: Optional[Dict[str, Any]] = Field(None, description="Processed analysis data as JSON (optional)")
    agent_type: Optional[str] = Field(None, description="Type of agent for performance analysis (optional)")
    call_context: Optional[str] = Field(None, description="Additional context about the call (optional)")
    timestamp: Optional[datetime] = Field(None, description="Call timestamp (optional, defaults to now)")
    process_immediately: bool = Field(False, description="Whether to process the call immediately after creation")


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


class CallProcessingResponse(BaseModel):
    """Schema for call processing response."""
    
    status: str = Field(..., description="Processing status: created, processing, success, already_processed, or error")
    message: str = Field(..., description="Human-readable message about the processing result")
    call_id: str = Field(..., description="The call ID that was processed")
    processed_data: Optional[Dict[str, Any]] = Field(None, description="Processed analysis data if successful")
    s3_url: Optional[str] = Field(None, description="S3 URL of the processed audio file if successful")


class CallStatusResponse(BaseModel):
    """Schema for call processing status response."""
    
    call_id: str = Field(..., description="The call ID")
    status: str = Field(..., description="Processing status: pending, partially_processed, or completed")
    message: str = Field(..., description="Human-readable message about the current status")
    has_processed_data: bool = Field(..., description="Whether the call has processed analysis data")
    audio_in_s3: bool = Field(..., description="Whether the audio file is stored in S3")
    created_at: Optional[str] = Field(..., description="ISO timestamp when the call was created")
    updated_at: Optional[str] = Field(..., description="ISO timestamp when the call was last updated")


class AgentAnalysisRequest(BaseModel):
    """Schema for requesting agent performance analysis."""
    
    call_id: str = Field(..., description="The call ID to analyze")
    agent_type: Optional[str] = Field(None, description="Type of agent for analysis (optional, will use default if not specified)")
    call_context: Optional[str] = Field(None, description="Additional context about the call (optional)")


class AgentAnalysisResponse(BaseModel):
    """Schema for agent performance analysis response."""
    
    call_id: str = Field(..., description="The call ID that was analyzed")
    analysis_result: Dict[str, Any] = Field(..., description="Complete analysis results")
    agent_type: str = Field(..., description="Type of agent that was analyzed")
    agent_name: str = Field(..., description="Name of the agent type")
    analysis_timestamp: str = Field(..., description="When the analysis was performed")
    model_used: str = Field(..., description="OpenAI model used for analysis")
    success: bool = Field(..., description="Whether the analysis was successful")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
