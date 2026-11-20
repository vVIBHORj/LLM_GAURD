import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.db.session import init_db
from backend.app.workers.execution_worker import execution_worker
from backend.app.api.v1.api import api_router

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("localllm_guard")

STATIC_DIR = Path(__file__).resolve().parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: initialize database schema and start sequential execution worker.
    """
    logger.info("Initializing LocalLLM Guard backend...")
    settings.ensure_directories()
    init_db()
    logger.info("SQLite database initialized at: %s", settings.DATABASE_URL)

    await execution_worker.start()
    yield
    await execution_worker.stop()
    logger.info("LocalLLM Guard backend shutdown complete.")

def create_app() -> FastAPI:
    """Factory function for FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Local-First LLM Evaluation, Reliability, Benchmarking, and Security Testing Platform",
        lifespan=lifespan
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Attach API v1 Router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/dashboard", response_class=HTMLResponse)
    def serve_dashboard():
        """Serves the standalone dark-theme infrastructure dashboard."""
        dashboard_file = STATIC_DIR / "dashboard.html"
        if dashboard_file.exists():
            return FileResponse(dashboard_file)
        return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)

    @app.get("/")
    def root(request: Request):
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            dashboard_file = STATIC_DIR / "dashboard.html"
            if dashboard_file.exists():
                return FileResponse(dashboard_file)

        return {
            "app": settings.APP_NAME,
            "version": "0.1.0",
            "dashboard": "/dashboard",
            "docs": "/docs",
            "status": "online"
        }

    return app

app = create_app()
