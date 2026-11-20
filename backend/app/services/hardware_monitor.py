import psutil
import torch
from typing import Dict, Any, Optional

class HardwareMonitor:
    """
    Real-time system telemetry collector.
    Inspects CPU, RAM, and GPU VRAM footprint.
    """

    def __init__(self):
        self._gpu_available = torch.cuda.is_available()
        self._gpu_name = torch.cuda.get_device_name(0) if self._gpu_available else None

    def sample_telemetry(self) -> Dict[str, Any]:
        """Samples instantaneous hardware metrics."""
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)

        gpu_data = {
            "available": self._gpu_available,
            "name": self._gpu_name,
            "total_mb": 0.0,
            "allocated_mb": 0.0,
            "free_mb": 0.0,
            "vram_usage_percent": 0.0
        }

        if self._gpu_available:
            try:
                # In PyTorch, mem_get_info returns (free_bytes, total_bytes)
                free_b, total_b = torch.cuda.mem_get_info(0)
                total_mb = total_b / (1024 ** 2)
                free_mb = free_b / (1024 ** 2)
                allocated_mb = total_mb - free_mb
                vram_pct = (allocated_mb / total_mb) * 100 if total_mb > 0 else 0.0

                gpu_data.update({
                    "total_mb": round(total_mb, 1),
                    "allocated_mb": round(allocated_mb, 1),
                    "free_mb": round(free_mb, 1),
                    "vram_usage_percent": round(vram_pct, 1)
                })
            except Exception:
                pass

        return {
            "cpu": {
                "usage_percent": cpu_pct,
                "cores_logical": psutil.cpu_count(logical=True),
                "cores_physical": psutil.cpu_count(logical=False)
            },
            "ram": {
                "total_mb": round(vm.total / (1024 ** 2), 1),
                "available_mb": round(vm.available / (1024 ** 2), 1),
                "free_mb": round(vm.free / (1024 ** 2), 1),
                "used_percent": round(vm.percent, 1)
            },
            "gpu": gpu_data
        }

hardware_monitor = HardwareMonitor()
