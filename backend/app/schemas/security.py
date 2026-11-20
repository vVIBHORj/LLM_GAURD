from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SecurityScanCreate(BaseModel):
    model_id: str
    categories: Optional[List[str]] = None # injection, jailbreak, leakage, hierarchy
    custom_attack_prompts: Optional[List[str]] = None

class AttackResult(BaseModel):
    category: str
    attack_vector: str
    prompt: str
    model_response: str
    defended: bool
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    reason: str

class SecurityReportRead(BaseModel):
    id: str
    model_id: str
    total_attacks: int
    defended_attacks: int
    defense_rate: float
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    category_breakdown: Dict[str, float] # e.g. {"injection": 0.85, "jailbreak": 0.90}
    attack_details: List[AttackResult]
    generated_at: datetime
