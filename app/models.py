"""Database models for the Voice Summary application."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.database import Base


class AudioCall(Base):
    """Model for storing audio call information."""
    
    __tablename__ = "audio_calls"
    
    call_id = Column(String(255), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    transcript = Column(JSON, nullable=False)
    audio_file_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<AudioCall(call_id='{self.call_id}', timestamp='{self.timestamp}')>"
