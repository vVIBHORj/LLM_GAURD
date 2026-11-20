from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    models,
    monitoring,
    datasets,
    evaluations,
    benchmarks,
    security,
    rag,
    analytics
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["System & Health"])
api_router.include_router(models.router, prefix="/models", tags=["Model Registry"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Hardware Telemetry"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Dataset Management"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluation Engine"])
api_router.include_router(benchmarks.router, prefix="/benchmarks", tags=["Benchmark Comparisons"])
api_router.include_router(security.router, prefix="/security", tags=["Security & Red-Teaming"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG Evaluation"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Recommendations"])
