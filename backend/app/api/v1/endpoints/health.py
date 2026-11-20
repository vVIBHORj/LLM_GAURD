import shutil
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas.common import APIResponse
from backend.app.schemas.health import SystemHealthResponse, OllamaHealth, PromptfooHealth
from backend.app.services.ollama_service import ollama_service
from backend.app.services.hardware_monitor import hardware_monitor

router = APIRouter()

@router.get("", response_model=APIResponse[SystemHealthResponse])
async def get_system_health():
    """
    Returns the comprehensive health status of LocalLLM Guard,
    including local Ollama connectivity, Promptfoo availability, and hardware telemetry.
    """
    # 1. Ollama status
    ollama_healthy = False
    ollama_ver = None
    active_models_cnt = 0
    try:
        ver_info = await ollama_service.get_version()
        ollama_healthy = True
        ollama_ver = ver_info.get("version")
        active = await ollama_service.get_active_models()
        active_models_cnt = len(active)
    except Exception:
        pass

    # 2. Promptfoo status
    promptfoo_bin = shutil.which(settings.PROMPTFOO_BINARY)
    promptfoo_status = "READY" if promptfoo_bin else "UNAVAILABLE"

    # 3. Hardware telemetry
    telemetry = hardware_monitor.sample_telemetry()

    overall_status = "HEALTHY" if ollama_healthy and promptfoo_bin else "DEGRADED"

    health_data = SystemHealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        app_version="0.1.0",
        ollama=OllamaHealth(
            status="ONLINE" if ollama_healthy else "OFFLINE",
            version=ollama_ver,
            host=settings.OLLAMA_BASE_URL,
            active_models_count=active_models_cnt
        ),
        promptfoo=PromptfooHealth(
            status=promptfoo_status,
            version="0.126.0" if promptfoo_bin else None
        ),
        hardware=telemetry
    )

    return APIResponse(
        success=True,
        message="System health checked successfully",
        data=health_data
    )
