from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class BenchmarkCreate(BaseModel):
    title: str
    dataset_id: str
    model_ids: List[str] = Field(..., min_length=1)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    num_predict: int = Field(default=256, ge=1, le=4096)
    num_ctx: int = Field(default=2048, ge=512, le=32768)

class ModelBenchmarkScore(BaseModel):
    model_id: str
    accuracy_score: float
    speed_tokens_sec: float
    avg_latency_ms: float
    peak_vram_mb: float
    memory_efficiency_score: float
    rank: int

class ParetoPoint(BaseModel):
    model_id: str
    tokens_per_sec: float
    accuracy_rate: float
    peak_vram_mb: float
    is_pareto_optimal: bool

class BenchmarkReportRead(BaseModel):
    id: str
    title: str
    model_ids: List[str]
    generated_at: datetime
    results: List[ModelBenchmarkScore] = Field(default_factory=list)
    pareto_frontier: List[ParetoPoint] = Field(default_factory=list)

    class Config:
        from_attributes = True
