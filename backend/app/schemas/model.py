from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ModelBase(BaseModel):
    id: str
    name: str
    family: Optional[str] = None
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None
    context_window_default: int = 2048
    disk_size_bytes: Optional[int] = None
    is_available: bool = True

class ModelRead(ModelBase):
    last_seen_at: datetime

    class Config:
        from_attributes = True

class ModelSyncResponse(BaseModel):
    discovered_count: int
    models: List[ModelRead]
