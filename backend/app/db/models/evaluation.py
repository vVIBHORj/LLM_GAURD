from datetime import datetime
import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("experiments.id"), nullable=True, index=True)
    model_id: Mapped[str] = mapped_column(String(64), ForeignKey("models.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="QUEUED", index=True)  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED

    total_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tokens_per_second_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    peak_vram_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    peak_ram_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    result_artifact_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    model: Mapped["Model"] = relationship("Model", back_populates="evaluation_runs")
    experiment: Mapped[Optional["Experiment"]] = relationship("Experiment", back_populates="evaluation_runs")
    results: Mapped[List["EvaluationResult"]] = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")
    metrics: Mapped[List["Metric"]] = relationship("Metric", back_populates="run", cascade="all, delete-orphan")
    security_tests: Mapped[List["SecurityTest"]] = relationship("SecurityTest", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_run_status_created", "status", "created_at"),
    )

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    test_case_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    jsonl_line_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    run: Mapped["EvaluationRun"] = relationship("EvaluationRun", back_populates="results")
