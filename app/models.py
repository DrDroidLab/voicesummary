"""Database models for the Voice Summary application."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class AudioCall(Base):
    """Model for storing audio call information."""
    
    __tablename__ = "audio_calls"
    
    call_id = Column(String(255), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    transcript = Column(JSON, nullable=False)
    audio_file_url = Column(Text, nullable=False)
    processed_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to extracted data
    extracted_data = relationship("CallExtractedData", back_populates="call", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AudioCall(call_id='{self.call_id}', timestamp='{self.timestamp}')>"


class CallExtractedData(Base):
    """Model for storing extracted, classified, and labeled data from call transcripts."""
    
    __tablename__ = "call_extracted_data"
    
    id = Column(String(255), primary_key=True, index=True)
    call_id = Column(String(255), ForeignKey("audio_calls.call_id"), nullable=False, index=True)
    
    # Data extraction results
    extraction_data = Column(JSON, nullable=True)  # Stores all extraction results
    
    # Classification results
    classification_data = Column(JSON, nullable=True)  # Stores all classification results
    
    # Labeling results
    labeling_data = Column(JSON, nullable=True)  # Stores all labeling results
    
    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_errors = Column(JSON, nullable=True)  # Stores any errors during processing
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to call
    call = relationship("AudioCall", back_populates="extracted_data")
    
    def __repr__(self):
        return f"<CallExtractedData(call_id='{self.call_id}', status='{self.processing_status}')>"
