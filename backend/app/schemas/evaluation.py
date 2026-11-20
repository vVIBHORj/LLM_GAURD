from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class EvaluationRunCreate(BaseModel):
    model_id: str
    dataset_id: str
    experiment_name: Optional[str] = None
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    num_predict: int = Field(default=256, ge=1, le=4096)
    num_ctx: int = Field(default=2048, ge=512, le=32768)
    concurrency: int = Field(default=1, ge=1, le=4)
    priority: int = Field(default=10, ge=1, le=100)

class EvaluationResultRead(BaseModel):
    id: str
    run_id: str
    test_case_id: Optional[str] = None
    passed: bool
    score: float
    latency_ms: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    jsonl_line_index: Optional[int] = None
    raw_output: Optional[str] = None
    prompt_text: Optional[str] = None

    class Config:
        from_attributes = True

class RunProgress(BaseModel):
    total_tests: int = 0
    completed_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0

class MetricRead(BaseModel):
    metric_name: str
    metric_value: float
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class EvaluationRunRead(BaseModel):
    id: str
    experiment_id: Optional[str] = None
    model_id: str
    status: str
    total_duration_seconds: Optional[float] = None
    tokens_per_second_avg: Optional[float] = None
    peak_vram_mb: Optional[float] = None
    peak_ram_mb: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    progress: Optional[RunProgress] = None
    metrics: List[MetricRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
