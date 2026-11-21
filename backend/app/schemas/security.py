from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SecurityScanCreate(BaseModel):
    model_id: str
    engine: str = "promptfoo" # "promptfoo" (rigorous) or "direct" (Ollama direct API)
    categories: Optional[List[str]] = None # injection, jailbreak, leakage, hierarchy, command
    custom_attack_prompts: Optional[List[str]] = None
    num_predict: int = Field(default=512, ge=64, le=2048)

class AttackResult(BaseModel):
    category: str
    attack_vector: str
    prompt: str
    model_response: str
    defended: bool
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    verdict: Optional[str] = "INCONCLUSIVE" # DEFENDED, VULNERABLE, INCONCLUSIVE (default INCONCLUSIVE prevents accidental defense attribution)
    thinking_preview: Optional[str] = None

class SecurityReportRead(BaseModel):
    id: str
    model_id: str
    engine_used: str = "promptfoo"
    total_attacks: int
    defended_attacks: int
    defense_rate: float
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    category_breakdown: Dict[str, float]
    attack_details: List[AttackResult]
    generated_at: datetime
