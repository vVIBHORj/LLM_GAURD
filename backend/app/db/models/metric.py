import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.evaluation import EvaluationRun

class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. faithfulness, injection_defense, latency
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    run: Mapped["EvaluationRun"] = relationship("EvaluationRun", back_populates="metrics")
