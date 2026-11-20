import logging
from typing import Tuple, Dict, Any
from backend.app.config import settings
from backend.app.services.hardware_monitor import HardwareMonitor

logger = logging.getLogger(__name__)

class HardwareGate:
    """
    Enforces hardware safety limits before initiating expensive model evaluations.
    Specifically calibrated for 16GB RAM and 4GB VRAM.
    """

    def __init__(self, monitor: HardwareMonitor | None = None):
        self.monitor = monitor or HardwareMonitor()

    def check_preflight(self, model_size_gb: float = 0.0) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates whether sufficient system RAM and GPU VRAM exist to execute an evaluation run.
        Returns: (is_allowed, reason, telemetry_snapshot)
        """
        telemetry = self.monitor.sample_telemetry()
        free_ram_mb = telemetry["ram"]["free_mb"]
        ram_percent = telemetry["ram"]["used_percent"]

        # 1. RAM Safety Check
        if free_ram_mb < settings.MIN_FREE_RAM_MB:
            msg = (
                f"Insufficient system RAM: {free_ram_mb:.1f} MB free, "
                f"minimum required is {settings.MIN_FREE_RAM_MB} MB. "
                f"Total RAM usage is {ram_percent:.1f}%."
            )
            logger.warning(msg)
            return False, msg, telemetry

        # 2. VRAM Safety Check (if GPU present)
        gpu_info = telemetry.get("gpu")
        if gpu_info and gpu_info.get("available"):
            vram_usage_pct = gpu_info.get("vram_usage_percent", 0.0)
            if vram_usage_pct > settings.MAX_VRAM_USAGE_PERCENT:
                msg = (
                    f"GPU VRAM usage is high: {vram_usage_pct:.1f}% "
                    f"(Threshold: {settings.MAX_VRAM_USAGE_PERCENT}%). "
                    f"Allocated: {gpu_info.get('allocated_mb', 0):.1f} MB."
                )
                logger.warning(msg)
                return False, msg, telemetry

        return True, "Hardware resources within safe operational envelope.", telemetry
