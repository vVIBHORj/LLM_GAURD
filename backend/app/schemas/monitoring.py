from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class CPUMetrics(BaseModel):
    usage_percent: Optional[float] = None
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
    reserved_mb: Optional[float] = None
    vram_usage_percent: float
    gpu_utilization_percent: Optional[float] = None
    temperature_c: Optional[float] = None
    power_w: Optional[float] = None
    source: Optional[str] = None

class OllamaModelTelemetry(BaseModel):
    name: str
    size_mb: float
    size_vram_mb: float
    digest: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None

class OllamaTelemetry(BaseModel):
    available: bool
    active_models: List[OllamaModelTelemetry] = Field(default_factory=list)
    total_vram_mb: float = 0.0
    total_size_mb: float = 0.0
    error: Optional[str] = None

class TelemetryResponse(BaseModel):
    cpu: CPUMetrics
    ram: RAMMetrics
    gpu: GPUMetrics
    ollama: Optional[OllamaTelemetry] = None
    hardware_safety_status: str  # SAFE, WARNING, CRITICAL
    can_run_evaluation: bool
    reason: str
