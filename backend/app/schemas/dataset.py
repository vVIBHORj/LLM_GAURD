from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TestCaseBase(BaseModel):
    prompt: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    assertions: Optional[List[Dict[str, Any]]] = None
    metadata_payload: Optional[Dict[str, Any]] = None

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseRead(TestCaseBase):
    id: str
    dataset_id: str

    class Config:
        from_attributes = True

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: str = "general" # general, security, rag, coding

class DatasetCreate(DatasetBase):
    test_cases: Optional[List[TestCaseCreate]] = Field(default_factory=list)

class DatasetRead(DatasetBase):
    id: str
    version: int
    created_at: datetime
    test_case_count: int = 0

    class Config:
        from_attributes = True

class DatasetDetailRead(DatasetRead):
    test_cases: List[TestCaseRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
