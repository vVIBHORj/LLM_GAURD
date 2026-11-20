import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class SecurityTest(Base):
    __tablename__ = "security_tests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False) # injection, jailbreak, leakage, hierarchy
    defended: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str] = mapped_column(String(16), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    attack_vector: Mapped[str] = mapped_column(String(100), nullable=False)

    run: Mapped["EvaluationRun"] = relationship("EvaluationRun", back_populates="security_tests")
