from typing import Optional, Dict, Any
from pydantic import BaseModel

class OllamaHealth(BaseModel):
    status: str  # ONLINE, OFFLINE
    version: Optional[str] = None
    host: str
    active_models_count: int = 0

class PromptfooHealth(BaseModel):
    status: str  # READY, UNAVAILABLE
    version: Optional[str] = None

class SystemHealthResponse(BaseModel):
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    app_name: str
    app_version: str
    ollama: OllamaHealth
    promptfoo: PromptfooHealth
    hardware: Dict[str, Any]
