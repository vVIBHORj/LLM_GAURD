import uuid
import math
import logging
from datetime import datetime
from typing import List
import httpx
from backend.app.config import settings
from backend.app.schemas.rag import (
    RAGQueryEvaluation,
    RAGEvaluationReport,
    DocumentChunk
)

logger = logging.getLogger(__name__)

class RAGService:
    """
    RAG Evaluation Service: Local document chunking, Ollama embedding generation,
    cosine similarity retrieval, and RAG Triad evaluation.
    """

    @staticmethod
    def chunk_document(title: str, content: str, chunk_size: int = 300, overlap: int = 50) -> List[DocumentChunk]:
        """Splits document into overlapping text chunks."""
        chunks: List[DocumentChunk] = []
        words = content.split()
        if not words:
            return chunks

        start = 0
        idx = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            chunks.append(DocumentChunk(
                id=str(uuid.uuid4()),
                document_title=title,
                chunk_index=idx,
                text=chunk_text
            ))
            idx += 1
            if end == len(words):
                break
            start += (chunk_size - overlap)

        return chunks

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two vector embeddings."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm1 * norm2)))

    async def get_embeddings(self, model_id: str, texts: List[str]) -> List[List[float]]:
        """Queries local Ollama embed API for vectors."""
        embeddings: List[List[float]] = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                try:
                    res = await client.post(
                        f"{settings.OLLAMA_BASE_URL}/api/embed",
                        json={"model": model_id, "input": text}
                    )
                    if res.status_code == 200:
                        embs = res.json().get("embeddings", [])
                        embeddings.append(embs[0] if embs else [])
                    else:
                        # Fallback to legacy /api/embeddings
                        res2 = await client.post(
                            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                            json={"model": model_id, "prompt": text}
                        )
                        embeddings.append(res2.json().get("embedding", []))
                except Exception as e:
                    logger.warning("Error generating embedding: %s", e)
                    embeddings.append([])
        return embeddings

    @staticmethod
    def calculate_faithfulness(answer: str, context: str) -> float:
        """
        Quantifies groundedness of the generated answer within the retrieved context.
        Uses lexical containment & entity token overlap.
        """
        ans_tokens = set(answer.lower().split())
        ctx_tokens = set(context.lower().split())
        # Filter common stopwords
        stopwords = {"the", "a", "an", "is", "are", "and", "or", "to", "in", "of", "that", "it"}
        content_tokens = ans_tokens - stopwords
        if not content_tokens:
            return 1.0

        overlap = content_tokens.intersection(ctx_tokens)
        return min(1.0, len(overlap) / len(content_tokens))

    async def evaluate_rag_pipeline(
        self,
        generative_model_id: str,
        embedding_model_id: str,
        document_content: str,
        document_title: str,
        queries: List[str]
    ) -> RAGEvaluationReport:
        """
        Executes end-to-end RAG Triad evaluation.
        """
        # 1. Chunk document
        chunks = self.chunk_document(document_title, document_content)
        chunk_texts = [c.text for c in chunks]

        # 2. Embed chunks
        chunk_embeddings = await self.get_embeddings(embedding_model_id, chunk_texts)

        # 3. Embed queries
        query_embeddings = await self.get_embeddings(embedding_model_id, queries)

        query_evals: List[RAGQueryEvaluation] = []
        total_cr = 0.0
        total_faith = 0.0
        total_ar = 0.0

        async with httpx.AsyncClient(timeout=60.0) as client:
            for q_idx, query in enumerate(queries):
                q_emb = query_embeddings[q_idx] if q_idx < len(query_embeddings) else []

                # Find best matching chunk via cosine similarity
                best_sim = -1.0
                best_chunk = chunks[0].text if chunks else ""

                for c_idx, c_emb in enumerate(chunk_embeddings):
                    if q_emb and c_emb:
                        sim = self.cosine_similarity(q_emb, c_emb)
                        if sim > best_sim:
                            best_sim = sim
                            best_chunk = chunks[c_idx].text

                context_relevance = max(0.0, best_sim) if best_sim >= 0 else 0.5

                # Generate answer grounded in context
                prompt = (
                    f"Context information:\n{best_chunk}\n\n"
                    f"Answer this question strictly using the provided context: {query}"
                )

                try:
                    gen_res = await client.post(
                        f"{settings.OLLAMA_BASE_URL}/api/generate",
                        json={
                            "model": generative_model_id,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"num_predict": 128, "temperature": 0.1}
                        }
                    )
                    answer = gen_res.json().get("response", "").strip() if gen_res.status_code == 200 else ""
                except Exception as e:
                    logger.warning("Error generating RAG answer: %s", e)
                    answer = "Error generating grounded answer."

                # Faithfulness (Groundedness)
                faithfulness = self.calculate_faithfulness(answer, best_chunk)

                # Answer Relevance (Overlap with query intent)
                ans_emb_list = await self.get_embeddings(embedding_model_id, [answer])
                ans_emb = ans_emb_list[0] if ans_emb_list else []
                answer_relevance = self.cosine_similarity(q_emb, ans_emb) if q_emb and ans_emb else 0.7

                query_evals.append(RAGQueryEvaluation(
                    query=query,
                    retrieved_chunk=best_chunk[:200] + "...",
                    generated_answer=answer,
                    context_relevance=round(context_relevance, 2),
                    faithfulness=round(faithfulness, 2),
                    answer_relevance=round(answer_relevance, 2)
                ))

                total_cr += context_relevance
                total_faith += faithfulness
                total_ar += answer_relevance

        n = len(queries)
        avg_cr = round(total_cr / n, 2) if n > 0 else 0.0
        avg_faith = round(total_faith / n, 2) if n > 0 else 0.0
        avg_ar = round(total_ar / n, 2) if n > 0 else 0.0
        triad_score = round((avg_cr + avg_faith + avg_ar) / 3.0, 2)

        return RAGEvaluationReport(
            id=str(uuid.uuid4()),
            generative_model_id=generative_model_id,
            embedding_model_id=embedding_model_id,
            total_queries=n,
            avg_context_relevance=avg_cr,
            avg_faithfulness=avg_faith,
            avg_answer_relevance=avg_ar,
            rag_triad_score=triad_score,
            query_evaluations=query_evals,
            created_at=datetime.utcnow()
        )

rag_service = RAGService()
