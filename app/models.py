"""Database models for the Voice Summary application."""

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AudioCall(Base):
    """Model for storing audio call information."""

    __tablename__ = "audio_calls"

    call_id = Column(String(255), primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    transcript = Column(JSON, nullable=False)
    audio_file_url = Column(Text, nullable=False)
    processed_data = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to extracted data
    extracted_data = relationship(
        "CallExtractedData", back_populates="call", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AudioCall(call_id='{self.call_id}', timestamp='{self.timestamp}')>"


class CallExtractedData(Base):
    """Model for storing extracted, classified, and labeled data from call transcripts."""

    __tablename__ = "call_extracted_data"

    id = Column(String(255), primary_key=True, index=True)
    call_id = Column(
        String(255), ForeignKey("audio_calls.call_id"), nullable=False, index=True
    )

    # Data extraction results
    extraction_data = Column(JSON, nullable=True)  # Stores all extraction results

    # Classification results
    classification_data = Column(
        JSON, nullable=True
    )  # Stores all classification results

    # Labeling results
    labeling_data = Column(JSON, nullable=True)  # Stores all labeling results

    # Processing status
    processing_status = Column(
        String(50), default="pending"
    )  # pending, processing, completed, failed
    processing_errors = Column(
        JSON, nullable=True
    )  # Stores any errors during processing

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to call
    call = relationship("AudioCall", back_populates="extracted_data")

    def __repr__(self):
        return f"<CallExtractedData(call_id='{self.call_id}', status='{self.processing_status}')>"


class AgentComparison(Base):
    """Model for agent comparison test execution."""

    __tablename__ = "agent_comparisons"

    comparison_id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_by = Column(String(255), nullable=True)

    # Scenario and agent configuration
    scenario_config = Column(
        JSON, nullable=False
    )  # Scenario fields: agent_overview, user_persona, situation, primary_language, expected_outcome
    agent_ids = Column(JSON, nullable=False)  # ["agent_1", "agent_2", "agent_3"]
    num_simulations = Column(
        Integer, nullable=False, server_default="10"
    )  # Number of simulations per agent

    # Execution status
    status = Column(
        String(50), default="pending"
    )  # pending, running, completed, failed
    current_phase = Column(
        String(50), nullable=True
    )  # fetching_configs, running_simulations, aggregating, analyzing, completed
    error_message = Column(Text, nullable=True)  # Error message if status is failed

    # Results
    results = Column(JSON, nullable=True)  # Aggregated comparison results

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    runs = relationship(
        "AgentComparisonRun", back_populates="comparison", cascade="all, delete-orphan"
    )
    aggregates = relationship(
        "AgentComparisonAggregate",
        back_populates="comparison",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<AgentComparison(comparison_id='{self.comparison_id}', status='{self.status}')>"


class AgentComparisonRun(Base):
    """Model for individual agent execution within a comparison."""

    __tablename__ = "agent_comparison_runs"

    run_id = Column(String(255), primary_key=True, index=True)
    comparison_id = Column(
        String(255), ForeignKey("agent_comparisons.comparison_id"), nullable=False
    )
    agent_id = Column(String(255), nullable=False, index=True)
    agent_name = Column(String(255), nullable=True)
    call_id = Column(String(255), ForeignKey("audio_calls.call_id"), nullable=True)
    simulation_number = Column(Integer, nullable=True)  # 1-indexed simulation number

    status = Column(
        String(50), default="pending"
    )  # pending, running, completed, failed

    # Agent configuration from Bolna
    agent_config = Column(JSON, nullable=True)  # Full agent config fetched from Bolna

    # Simulated conversation
    simulated_transcript = Column(
        JSON, nullable=True
    )  # Full transcript from simulation
    total_turns = Column(Integer, nullable=True)  # Number of turns in conversation

    # Turn-by-turn metrics
    turn_latencies = Column(JSON, nullable=True)  # [{"turn": 1, "latency": 1.2}]
    turn_accuracy = Column(
        JSON, nullable=True
    )  # [{"turn": 1, "accuracy": 8.5, "reasoning": "..."}]

    # Summary metrics
    latency_median = Column(Float, nullable=True)
    latency_p75 = Column(Float, nullable=True)
    latency_p99 = Column(Float, nullable=True)
    overall_accuracy = Column(Float, nullable=True)  # 0-10
    humanlike_rating = Column(Float, nullable=True)  # 0-10
    outcome_orientation = Column(Float, nullable=True)  # 0-10

    # Issues
    least_accurate_turns = Column(JSON, nullable=True)  # Turns with accuracy < 7

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    comparison = relationship("AgentComparison", back_populates="runs")

    def __repr__(self):
        return f"<AgentComparisonRun(run_id='{self.run_id}', agent_id='{self.agent_id}', status='{self.status}')>"


class AgentComparisonAggregate(Base):
    """Model for aggregated metrics across multiple simulations per agent."""

    __tablename__ = "agent_comparison_aggregates"

    aggregate_id = Column(String(255), primary_key=True, index=True)
    comparison_id = Column(
        String(255),
        ForeignKey("agent_comparisons.comparison_id"),
        nullable=False,
        index=True,
    )
    agent_id = Column(String(255), nullable=False, index=True)
    agent_name = Column(String(255), nullable=True)

    # Simulation counts
    total_simulations = Column(Integer, nullable=False)
    successful_simulations = Column(Integer, nullable=False)
    failed_simulations = Column(Integer, nullable=False)

    # Latency stats (mean and std for each percentile)
    latency_median_mean = Column(Float, nullable=True)
    latency_median_std = Column(Float, nullable=True)
    latency_p75_mean = Column(Float, nullable=True)
    latency_p75_std = Column(Float, nullable=True)
    latency_p99_mean = Column(Float, nullable=True)
    latency_p99_std = Column(Float, nullable=True)

    # Accuracy stats
    accuracy_mean = Column(Float, nullable=True)
    accuracy_std = Column(Float, nullable=True)
    accuracy_min = Column(Float, nullable=True)
    accuracy_max = Column(Float, nullable=True)

    # Humanlike stats
    humanlike_mean = Column(Float, nullable=True)
    humanlike_std = Column(Float, nullable=True)
    humanlike_min = Column(Float, nullable=True)
    humanlike_max = Column(Float, nullable=True)

    # Outcome orientation stats
    outcome_mean = Column(Float, nullable=True)
    outcome_std = Column(Float, nullable=True)
    outcome_min = Column(Float, nullable=True)
    outcome_max = Column(Float, nullable=True)

    # Composite score stats
    composite_score_mean = Column(Float, nullable=True)
    composite_score_std = Column(Float, nullable=True)

    # Turn stats
    avg_turns_mean = Column(Float, nullable=True)
    avg_turns_std = Column(Float, nullable=True)

    # Hangup success rate
    hangup_success_rate = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    comparison = relationship("AgentComparison", back_populates="aggregates")

    def __repr__(self):
        return f"<AgentComparisonAggregate(aggregate_id='{self.aggregate_id}', agent_id='{self.agent_id}')>"
