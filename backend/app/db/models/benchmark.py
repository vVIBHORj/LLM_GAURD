from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class BenchmarkReport(Base):
    __tablename__ = "benchmark_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    model_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    composite_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    benchmark_results: Mapped[List["BenchmarkResult"]] = relationship("BenchmarkResult", back_populates="report", cascade="all, delete-orphan")

class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("benchmark_reports.id"), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, default=0.0)
    speed_tokens_sec: Mapped[float] = mapped_column(Float, default=0.0)
    memory_efficiency_score: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, default=1)

    report: Mapped["BenchmarkReport"] = relationship("BenchmarkReport", back_populates="benchmark_results")
