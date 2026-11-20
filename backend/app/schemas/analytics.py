from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ModelRankingItem(BaseModel):
    rank: int
    model_id: str
    composite_score: float
    accuracy_score: float
    security_score: float
    speed_score: float
    memory_score: float
    tokens_per_sec: float
    vram_used_mb: float

class ModelRankingsResponse(BaseModel):
    weights: Dict[str, float]
    rankings: List[ModelRankingItem]

class RecommendationRequest(BaseModel):
    max_vram_mb: Optional[float] = 4096.0
    min_tokens_per_sec: Optional[float] = 20.0
    task_priority: str = "balanced" # speed, accuracy, security, balanced

class ModelRecommendation(BaseModel):
    recommended_model_id: str
    rationale: str
    composite_score: float
    speed_tokens_sec: float
    vram_requirement_mb: float
    fit_assessment: str
