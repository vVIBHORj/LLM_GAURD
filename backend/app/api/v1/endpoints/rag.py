from fastapi import APIRouter, HTTPException
from backend.app.schemas.common import APIResponse
from backend.app.schemas.rag import RAGEvaluateRequest, RAGEvaluationReport
from backend.app.services.rag_service import rag_service

router = APIRouter()

@router.post("/evaluate", response_model=APIResponse[RAGEvaluationReport])
async def evaluate_rag_pipeline(payload: RAGEvaluateRequest):
    """
    Executes end-to-end RAG Triad evaluation:
    1. Chunks document.
    2. Embeds chunks & queries via Ollama embedding model.
    3. Retrieves top matches via cosine similarity.
    4. Generates answers with target LLM.
    5. Scores Context Relevance, Grounded Faithfulness, and Answer Relevance.
    """
    try:
        report = await rag_service.evaluate_rag_pipeline(
            generative_model_id=payload.generative_model_id,
            embedding_model_id=payload.embedding_model_id,
            document_content=payload.document_content,
            document_title=payload.document_title,
            queries=payload.queries
        )
        return APIResponse(
            success=True,
            message=f"RAG evaluation complete. Triad score: {report.rag_triad_score}",
            data=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG evaluation failed: {e}")
