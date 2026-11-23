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
    concurrency: int = Field(default=1, ge=1, le=4)

class ModelBenchmarkScore(BaseModel):
    model_id: str
    run_id: Optional[str] = None
    status: str = "BENCHMARKED"  # BENCHMARKED, UNBENCHMARKED, INELIGIBLE
    accuracy_score: Optional[float] = None
    speed_tokens_sec: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    peak_vram_mb: Optional[float] = None
    peak_ollama_vram_mb: Optional[float] = None
    gpu_name: Optional[str] = None
    gpu_source: Optional[str] = None
    memory_efficiency_score: Optional[float] = None
    rank: Optional[int] = None

class ParetoPoint(BaseModel):
    model_id: str
    run_id: Optional[str] = None
    tokens_per_sec: float
    accuracy_rate: float
    peak_vram_mb: float
    is_pareto_optimal: bool

class BenchmarkReportRead(BaseModel):
    id: str
    title: str
    dataset_id: Optional[str] = None
    model_ids: List[str]
    generation_config: Optional[Dict[str, Any]] = None
    generated_at: datetime
    results: List[ModelBenchmarkScore] = Field(default_factory=list)
    pareto_frontier: List[ParetoPoint] = Field(default_factory=list)

    class Config:
        from_attributes = True
