from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.dataset import Dataset
    from backend.app.db.models.evaluation import EvaluationRun

class BenchmarkReport(Base):
    __tablename__ = "benchmark_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    dataset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("datasets.id"), nullable=True, index=True)
    model_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    generation_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    composite_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset")
    benchmark_results: Mapped[List["BenchmarkResult"]] = relationship("BenchmarkResult", back_populates="report", cascade="all, delete-orphan")

class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("benchmark_reports.id"), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("evaluation_runs.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="BENCHMARKED")  # BENCHMARKED, UNBENCHMARKED, INELIGIBLE

    accuracy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    security_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speed_tokens_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    peak_vram_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    peak_ollama_vram_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gpu_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gpu_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    memory_efficiency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    report: Mapped["BenchmarkReport"] = relationship("BenchmarkReport", back_populates="benchmark_results")
    evaluation_run: Mapped[Optional["EvaluationRun"]] = relationship("EvaluationRun")
