"""Pydantic schemas for API validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class AudioCallCreate(BaseModel):
    """Schema for creating a new audio call."""

    call_id: str = Field(..., description="Unique identifier for the call")
    transcript: Dict[str, Any] = Field(..., description="Call transcript as JSON")
    audio_file_url: str = Field(..., description="S3 URL for the audio file")
    processed_data: Optional[Dict[str, Any]] = Field(
        None, description="Processed analysis data as JSON (optional)"
    )
    agent_type: Optional[str] = Field(
        None, description="Type of agent for performance analysis (optional)"
    )
    call_context: Optional[str] = Field(
        None, description="Additional context about the call (optional)"
    )
    timestamp: Optional[datetime] = Field(
        None, description="Call timestamp (optional, defaults to now)"
    )


class AudioCallCreateWithProcessing(BaseModel):
    """Schema for creating a new audio call with immediate processing option."""

    call_id: str = Field(..., description="Unique identifier for the call")
    transcript: Dict[str, Any] = Field(..., description="Call transcript as JSON")
    audio_file_url: str = Field(
        ..., description="URL for the audio file (will be processed and uploaded to S3)"
    )
    processed_data: Optional[Dict[str, Any]] = Field(
        None, description="Processed analysis data as JSON (optional)"
    )
    agent_type: Optional[str] = Field(
        None, description="Type of agent for performance analysis (optional)"
    )
    call_context: Optional[str] = Field(
        None, description="Additional context about the call (optional)"
    )
    timestamp: Optional[datetime] = Field(
        None, description="Call timestamp (optional, defaults to now)"
    )
    process_immediately: bool = Field(
        False, description="Whether to process the call immediately after creation"
    )


class AudioCallResponse(BaseModel):
    """Schema for audio call response."""

    call_id: str
    timestamp: int  # Epoch timestamp in seconds
    transcript: Dict[str, Any]
    audio_file_url: str
    processed_data: Optional[Dict[str, Any]] = None
    created_at: int  # Epoch timestamp in seconds
    updated_at: int  # Epoch timestamp in seconds

    @field_validator("timestamp", "created_at", "updated_at", mode="before")
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

    status: str = Field(
        ...,
        description="Processing status: created, processing, success, already_processed, or error",
    )
    message: str = Field(
        ..., description="Human-readable message about the processing result"
    )
    call_id: str = Field(..., description="The call ID that was processed")
    processed_data: Optional[Dict[str, Any]] = Field(
        None, description="Processed analysis data if successful"
    )
    s3_url: Optional[str] = Field(
        None, description="S3 URL of the processed audio file if successful"
    )


class CallStatusResponse(BaseModel):
    """Schema for call processing status response."""

    call_id: str = Field(..., description="The call ID")
    status: str = Field(
        ..., description="Processing status: pending, partially_processed, or completed"
    )
    message: str = Field(
        ..., description="Human-readable message about the current status"
    )
    has_processed_data: bool = Field(
        ..., description="Whether the call has processed analysis data"
    )
    audio_in_s3: bool = Field(..., description="Whether the audio file is stored in S3")
    created_at: Optional[str] = Field(
        ..., description="ISO timestamp when the call was created"
    )
    updated_at: Optional[str] = Field(
        ..., description="ISO timestamp when the call was last updated"
    )


class AgentAnalysisRequest(BaseModel):
    """Schema for requesting agent performance analysis."""

    call_id: str = Field(..., description="The call ID to analyze")
    agent_type: Optional[str] = Field(
        None,
        description="Type of agent for analysis (optional, will use default if not specified)",
    )
    call_context: Optional[str] = Field(
        None, description="Additional context about the call (optional)"
    )


class AgentAnalysisResponse(BaseModel):
    """Schema for agent performance analysis response."""

    call_id: str = Field(..., description="The call ID that was analyzed")
    analysis_result: Dict[str, Any] = Field(
        ..., description="Complete analysis results"
    )
    agent_type: str = Field(..., description="Type of agent that was analyzed")
    agent_name: str = Field(..., description="Name of the agent type")
    analysis_timestamp: str = Field(..., description="When the analysis was performed")
    model_used: str = Field(..., description="OpenAI model used for analysis")
    success: bool = Field(..., description="Whether the analysis was successful")
    error_message: Optional[str] = Field(
        None, description="Error message if analysis failed"
    )


# New schemas for extracted data
class ExtractedDataResponse(BaseModel):
    """Schema for extracted data response."""

    call_id: str = Field(..., description="The call ID")
    extraction_data: Optional[Dict[str, Any]] = Field(
        None, description="Extracted structured data"
    )
    classification_data: Optional[Dict[str, Any]] = Field(
        None, description="Classification results"
    )
    labeling_data: Optional[Dict[str, Any]] = Field(
        None, description="Labeling results"
    )
    processing_status: str = Field(
        ..., description="Processing status: pending, processing, completed, failed"
    )
    processing_errors: Optional[Dict[str, str]] = Field(
        None, description="Any errors during processing"
    )
    created_at: int = Field(
        ..., description="Epoch timestamp when the data was created"
    )
    updated_at: int = Field(
        ..., description="Epoch timestamp when the data was last updated"
    )

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def convert_datetime_to_epoch(cls, v):
        if isinstance(v, datetime):
            return int(v.timestamp())
        return v

    class Config:
        from_attributes = True


class CallDataPipelineRequest(BaseModel):
    """Schema for requesting call data pipeline processing."""

    call_id: str = Field(..., description="The call ID to process")
    force_reprocess: bool = Field(
        False, description="Whether to force reprocessing even if data exists"
    )


class CallDataPipelineResponse(BaseModel):
    """Schema for call data pipeline response."""

    call_id: str = Field(..., description="The call ID that was processed")
    status: str = Field(
        ..., description="Processing status: success, error, or already_processed"
    )
    message: str = Field(
        ..., description="Human-readable message about the processing result"
    )
    extracted_data: Optional[ExtractedDataResponse] = Field(
        None, description="Extracted data if successful"
    )
    errors: Optional[Dict[str, str]] = Field(
        None, description="Any errors during processing"
    )


# Agent Comparison Schemas


class VariableDefinition(BaseModel):
    """Schema for a variable that needs to be filled."""

    name: str
    description: Optional[str] = None


class ManualAgentCreate(BaseModel):
    """Schema for manually creating an agent."""

    agent_name: str
    welcome_message: str
    system_prompt: str
    hangup_prompt: str
    llm_model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 1000


class AgentWithVariables(BaseModel):
    """Schema for agent config with detected variables."""

    agent_id: str
    agent_name: str
    config: Dict[str, Any]
    required_variables: List[str]


class AgentComparisonCreate(BaseModel):
    """Schema for creating a new agent comparison (legacy - for Bolna IDs only)."""

    name: str = Field(..., description="Name for this comparison")
    agent_overview: str = Field(..., description="Overview of what the agent does")
    user_persona: str = Field(..., description="Description of the user persona")
    situation: str = Field(
        ..., description="The situation/scenario for the conversation"
    )
    primary_language: str = Field(
        ..., description="Primary language for the conversation"
    )
    expected_outcome: str = Field(
        ..., description="Expected outcome of the conversation"
    )
    agent_ids: List[str] = Field(..., description="List of Bolna agent IDs to compare")
    num_simulations: int = Field(
        10, description="Number of simulations to run per agent"
    )


class AgentComparisonCreateEnhanced(BaseModel):
    """Schema for creating agent comparison with variable support."""

    name: str = Field(..., description="Name for this comparison")
    agent_overview: str = Field(..., description="Overview of what the agent does")
    user_persona: str = Field(..., description="Description of the user persona")
    situation: str = Field(
        ..., description="The situation/scenario for the conversation"
    )
    primary_language: str = Field(
        ..., description="Primary language for the conversation"
    )
    expected_outcome: str = Field(
        ..., description="Expected outcome of the conversation"
    )

    # Agents can be Bolna IDs OR manual configs
    bolna_agent_ids: Optional[List[str]] = None
    manual_agents: Optional[List[ManualAgentCreate]] = None

    # Variable values to replace
    variable_values: Dict[str, str] = Field(
        default_factory=dict, description="Variable name to value mapping"
    )

    num_simulations: int = Field(
        10, description="Number of simulations to run per agent"
    )

    # Advanced settings (optional overrides)
    max_concurrent_simulations: Optional[int] = Field(
        None,
        description="Override max concurrent simulations (default: 3)",
        ge=1,
        le=10,
    )
    conversation_timeout_seconds: Optional[int] = Field(
        None,
        description="Override conversation timeout in seconds (default: 300)",
        ge=60,
        le=600,
    )
    max_conversation_turns: Optional[int] = Field(
        None,
        description="Override max conversation turns (default: 10)",
        ge=5,
        le=20,
    )


class AgentComparisonResponse(BaseModel):
    """Schema for agent comparison response."""

    comparison_id: str
    name: str
    scenario_config: Dict[str, Any]
    agent_ids: List[str]
    num_simulations: int
    status: str
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    created_at: int
    updated_at: int
    completed_at: Optional[int] = None

    @field_validator("created_at", "updated_at", "completed_at", mode="before")
    @classmethod
    def convert_datetime_to_epoch(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return int(v.timestamp())
        return v

    class Config:
        from_attributes = True


class AgentComparisonRunResponse(BaseModel):
    """Schema for agent comparison run response."""

    run_id: str
    comparison_id: str
    agent_id: str
    agent_name: Optional[str] = None
    call_id: Optional[str] = None
    simulation_number: Optional[int] = None
    status: str
    agent_config: Optional[Dict[str, Any]] = None
    simulated_transcript: Optional[List[Dict[str, Any]]] = None
    total_turns: Optional[int] = None
    turn_latencies: Optional[List[Dict[str, Any]]] = None
    turn_accuracy: Optional[List[Dict[str, Any]]] = None
    latency_median: Optional[float] = None
    latency_p75: Optional[float] = None
    latency_p99: Optional[float] = None
    overall_accuracy: Optional[float] = None
    humanlike_rating: Optional[float] = None
    outcome_orientation: Optional[float] = None
    least_accurate_turns: Optional[List[Dict[str, Any]]] = None
    created_at: int
    completed_at: Optional[int] = None

    @field_validator("created_at", "completed_at", mode="before")
    @classmethod
    def convert_datetime_to_epoch(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return int(v.timestamp())
        return v

    class Config:
        from_attributes = True


class AgentLookupResponse(BaseModel):
    """Schema for agent lookup response."""

    agent_id: str
    agent_name: str
    status: str


class AgentConfigResponse(BaseModel):
    """Schema for full agent configuration response."""

    agent_id: str
    agent_name: str
    supported: bool = Field(
        ..., description="Whether this agent is supported (OpenAI models only)"
    )
    llm_family: str = Field(..., description="LLM family (e.g., 'openai', 'anthropic')")
    llm_model: str = Field(..., description="Specific LLM model name")
    system_prompt: Optional[str] = None
    hangup_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
