from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class Model(Base):
    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g. "llama3.2:latest"
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    family: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    parameter_size: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # e.g. "3B"
    quantization: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)    # e.g. "Q4_K_M"
    context_window_default: Mapped[int] = mapped_column(Integer, default=2048)
    disk_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    evaluation_runs: Mapped[List["EvaluationRun"]] = relationship("EvaluationRun", back_populates="model")
