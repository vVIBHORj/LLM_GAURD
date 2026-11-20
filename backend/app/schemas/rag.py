from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DocumentIngestRequest(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentChunk(BaseModel):
    id: str
    document_title: str
    chunk_index: int
    text: str

class RAGEvaluateRequest(BaseModel):
    generative_model_id: str = "llama3.2:latest"
    embedding_model_id: str = "qwen3-embedding:0.6b"
    document_content: str
    document_title: str = "Reference Document"
    queries: List[str] = Field(..., min_length=1)

class RAGQueryEvaluation(BaseModel):
    query: str
    retrieved_chunk: str
    generated_answer: str
    context_relevance: float # 0.0 to 1.0
    faithfulness: float     # 0.0 to 1.0 (groundedness)
    answer_relevance: float  # 0.0 to 1.0

class RAGEvaluationReport(BaseModel):
    id: str
    generative_model_id: str
    embedding_model_id: str
    total_queries: int
    avg_context_relevance: float
    avg_faithfulness: float
    avg_answer_relevance: float
    rag_triad_score: float # Harmonic mean or weighted average
    query_evaluations: List[RAGQueryEvaluation]
    created_at: datetime
