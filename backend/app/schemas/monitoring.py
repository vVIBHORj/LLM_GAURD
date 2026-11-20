from typing import Dict, Any, Optional
from pydantic import BaseModel

class CPUMetrics(BaseModel):
    usage_percent: float
    cores_logical: int
    cores_physical: int

class RAMMetrics(BaseModel):
    total_mb: float
    available_mb: float
    free_mb: float
    used_percent: float

class GPUMetrics(BaseModel):
    available: bool
    name: Optional[str] = None
    total_mb: float
    allocated_mb: float
    free_mb: float
    vram_usage_percent: float

class TelemetryResponse(BaseModel):
    cpu: CPUMetrics
    ram: RAMMetrics
    gpu: GPUMetrics
    hardware_safety_status: str  # SAFE, WARNING, CRITICAL
    can_run_evaluation: bool
    reason: str
