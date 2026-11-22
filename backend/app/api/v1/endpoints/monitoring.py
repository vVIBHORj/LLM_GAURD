from fastapi import APIRouter
from backend.app.schemas.common import APIResponse
from backend.app.schemas.monitoring import TelemetryResponse, CPUMetrics, RAMMetrics, GPUMetrics, OllamaTelemetry
from backend.app.services.hardware_monitor import hardware_monitor
from backend.app.core.hardware_gate import HardwareGate

router = APIRouter()
gate = HardwareGate(monitor=hardware_monitor)

@router.get("/telemetry", response_model=APIResponse[TelemetryResponse])
def get_hardware_telemetry():
    """
    Returns instantaneous hardware resource telemetry (CPU, RAM, GPU/VRAM)
    and evaluates the pre-flight safety envelope.
    """
    raw = hardware_monitor.sample_telemetry()
    allowed, reason, _ = gate.check_preflight()

    # Determine safety status
    free_ram = raw["ram"]["free_mb"]
    if free_ram < 1000:
        safety_status = "CRITICAL"
    elif free_ram < 1500:
        safety_status = "WARNING"
    else:
        safety_status = "SAFE"

    ollama_data = OllamaTelemetry(**raw["ollama"]) if raw.get("ollama") else None

    payload = TelemetryResponse(
        cpu=CPUMetrics(**raw["cpu"]),
        ram=RAMMetrics(**raw["ram"]),
        gpu=GPUMetrics(**raw["gpu"]),
        ollama=ollama_data,
        hardware_safety_status=safety_status,
        can_run_evaluation=allowed,
        reason=reason
    )

    return APIResponse(
        success=True,
        message="Hardware telemetry gathered",
        data=payload
    )
