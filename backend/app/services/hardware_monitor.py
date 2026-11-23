import os
import shutil
import subprocess
import logging
import time
import psutil
import httpx
from typing import Dict, Any, Optional
from backend.app.config import settings

logger = logging.getLogger(__name__)

def _parse_numeric_field(val: str) -> Optional[float]:
    """Parses numeric output from nvidia-smi, treating [N/A] or [Not Supported] as None."""
    s = (val or "").strip()
    if not s or "not supported" in s.lower() or "n/a" in s.lower():
        return None
    try:
        return float(s)
    except ValueError:
        return None

class HardwareMonitor:
    """
    Real-time system telemetry collector for Windows 11 / Linux.
    Inspects CPU, RAM, NVIDIA GPU (via nvidia-smi with torch fallback),
    and Ollama model VRAM allocations via /api/ps.
    """

    def __init__(self, ollama_base_url: Optional[str] = None):
        self.ollama_base_url = (ollama_base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._nvidia_smi_path = self._find_nvidia_smi()
        self._last_cpu_time: float = 0.0
        self.prime_cpu()

    def prime_cpu(self) -> None:
        """Primes psutil CPU counter and records the reference timestamp."""
        try:
            psutil.cpu_percent(interval=None)
            self._last_cpu_time = time.monotonic()
        except Exception:
            self._last_cpu_time = 0.0

    def _find_nvidia_smi(self) -> Optional[str]:
        """Locates the nvidia-smi executable on Windows or Linux."""
        found = shutil.which("nvidia-smi")
        if found:
            return found

        # Common Windows paths when not in PATH
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        candidates = [
            os.path.join(system_root, "System32", "nvidia-smi.exe"),
            os.path.join(program_files, "NVIDIA Corporation", "NVSMI", "nvidia-smi.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    def _sample_gpu_nvidia_smi(self) -> Optional[Dict[str, Any]]:
        """
        Queries nvidia-smi for system-wide GPU VRAM, driver reservation, utilization,
        temperature, and power draw.
        """
        smi_path = self._nvidia_smi_path or self._find_nvidia_smi()
        if not smi_path:
            return None

        # Query with memory.reserved (supported on driver 535+ / modern Windows WDDM)
        cmd_with_reserved = [
            smi_path,
            "--query-gpu=name,memory.total,memory.used,memory.free,memory.reserved,utilization.gpu,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits"
        ]
        cmd_standard = [
            smi_path,
            "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits"
        ]

        try:
            res = subprocess.run(cmd_with_reserved, capture_output=True, text=True, timeout=2.0, check=False)
            if res.returncode != 0:
                # Fallback to standard query without memory.reserved
                res = subprocess.run(cmd_standard, capture_output=True, text=True, timeout=2.0, check=False)
                if res.returncode != 0:
                    logger.debug("nvidia-smi returned non-zero code %d: %s", res.returncode, res.stderr)
                    return None

            output_line = res.stdout.strip().splitlines()
            if not output_line:
                return None

            parts = [p.strip() for p in output_line[0].split(",")]
            if len(parts) < 4:
                return None

            name = parts[0]
            total_mb = _parse_numeric_field(parts[1]) or 0.0
            used_mb = _parse_numeric_field(parts[2]) or 0.0
            free_mb = _parse_numeric_field(parts[3]) or 0.0

            if len(parts) >= 8:
                # Query returned memory.reserved
                reserved_mb = _parse_numeric_field(parts[4])
                util_pct = _parse_numeric_field(parts[5])
                temp_c = _parse_numeric_field(parts[6])
                power_w = _parse_numeric_field(parts[7])
            else:
                # Query without memory.reserved
                reserved_mb = None
                util_pct = _parse_numeric_field(parts[4]) if len(parts) > 4 else None
                temp_c = _parse_numeric_field(parts[5]) if len(parts) > 5 else None
                power_w = _parse_numeric_field(parts[6]) if len(parts) > 6 else None

            vram_usage_percent = round((used_mb / total_mb) * 100, 1) if total_mb > 0 else 0.0

            return {
                "available": True,
                "name": name,
                "total_mb": round(total_mb, 1),
                "allocated_mb": round(used_mb, 1),
                "free_mb": round(free_mb, 1),
                "reserved_mb": round(reserved_mb, 1) if reserved_mb is not None else None,
                "vram_usage_percent": vram_usage_percent,
                "gpu_utilization_percent": util_pct,
                "temperature_c": temp_c,
                "power_w": power_w,
                "source": "nvidia-smi"
            }
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            logger.debug("nvidia-smi query failed: %s", e)
            return None
        except Exception as e:
            logger.warning("Unexpected error querying nvidia-smi: %s", e)
            return None

    def _sample_gpu_torch(self) -> Optional[Dict[str, Any]]:
        """Fallback to torch.cuda.mem_get_info() if available."""
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                free_b, total_b = torch.cuda.mem_get_info(0)
                total_mb = total_b / (1024 ** 2)
                free_mb = free_b / (1024 ** 2)
                allocated_mb = total_mb - free_mb
                vram_pct = (allocated_mb / total_mb) * 100 if total_mb > 0 else 0.0

                return {
                    "available": True,
                    "name": name,
                    "total_mb": round(total_mb, 1),
                    "allocated_mb": round(allocated_mb, 1),
                    "free_mb": round(free_mb, 1),
                    "reserved_mb": None,
                    "vram_usage_percent": round(vram_pct, 1),
                    "gpu_utilization_percent": None,
                    "temperature_c": None,
                    "power_w": None,
                    "source": "torch.cuda"
                }
        except Exception:
            pass
        return None

    def sample_gpu(self) -> Dict[str, Any]:
        """Gathers GPU telemetry, preferring nvidia-smi over PyTorch."""
        smi_res = self._sample_gpu_nvidia_smi()
        if smi_res:
            return smi_res

        torch_res = self._sample_gpu_torch()
        if torch_res:
            return torch_res

        return {
            "available": False,
            "name": None,
            "total_mb": 0.0,
            "allocated_mb": 0.0,
            "free_mb": 0.0,
            "reserved_mb": None,
            "vram_usage_percent": 0.0,
            "gpu_utilization_percent": None,
            "temperature_c": None,
            "power_w": None,
            "source": "none"
        }

    def sample_cpu(self, min_interval_seconds: float = 0.1) -> Dict[str, Any]:
        """
        Samples CPU utilization and core topology.
        If the elapsed time since last priming/sampling is effectively instantaneous
        (< 100ms), usage_percent is recorded as None (unavailable) rather than an artificial zero.
        """
        now = time.monotonic()
        elapsed = now - self._last_cpu_time
        self._last_cpu_time = now

        usage_pct: Optional[float] = None
        if elapsed >= min_interval_seconds:
            try:
                usage_pct = psutil.cpu_percent(interval=None)
            except Exception:
                usage_pct = None

        return {
            "usage_percent": usage_pct,
            "cores_logical": psutil.cpu_count(logical=True) or 1,
            "cores_physical": psutil.cpu_count(logical=False) or 1
        }

    def sample_ram(self) -> Dict[str, Any]:
        """Samples system RAM capacity and utilization."""
        vm = psutil.virtual_memory()
        return {
            "total_mb": round(vm.total / (1024 ** 2), 1),
            "available_mb": round(vm.available / (1024 ** 2), 1),
            "free_mb": round(vm.free / (1024 ** 2), 1),
            "used_percent": round(vm.percent, 1)
        }

    def _parse_ollama_ps_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parses the raw JSON dictionary from Ollama /api/ps into structured telemetry."""
        models = data.get("models", [])
        total_vram_b = sum(m.get("size_vram", 0) for m in models)
        total_size_b = sum(m.get("size", 0) for m in models)
        active_info = [
            {
                "name": m.get("name", ""),
                "size_mb": round(m.get("size", 0) / (1024 ** 2), 1),
                "size_vram_mb": round(m.get("size_vram", 0) / (1024 ** 2), 1),
                "digest": m.get("digest"),
                "details": m.get("details"),
                "expires_at": m.get("expires_at")
            }
            for m in models
        ]
        return {
            "available": True,
            "active_models": active_info,
            "total_vram_mb": round(total_vram_b / (1024 ** 2), 1),
            "total_size_mb": round(total_size_b / (1024 ** 2), 1),
            "error": None
        }

    def sample_ollama_sync(self) -> Dict[str, Any]:
        """Queries Ollama /api/ps synchronously with a short timeout."""
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"{self.ollama_base_url}/api/ps")
                if res.status_code == 200:
                    return self._parse_ollama_ps_response(res.json())
                return {
                    "available": False,
                    "active_models": [],
                    "total_vram_mb": 0.0,
                    "total_size_mb": 0.0,
                    "error": f"HTTP {res.status_code}"
                }
        except Exception as e:
            return {
                "available": False,
                "active_models": [],
                "total_vram_mb": 0.0,
                "total_size_mb": 0.0,
                "error": str(e)
            }

    async def sample_ollama_async(self) -> Dict[str, Any]:
        """Queries Ollama /api/ps asynchronously without blocking."""
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{self.ollama_base_url}/api/ps")
                if res.status_code == 200:
                    return self._parse_ollama_ps_response(res.json())
                return {
                    "available": False,
                    "active_models": [],
                    "total_vram_mb": 0.0,
                    "total_size_mb": 0.0,
                    "error": f"HTTP {res.status_code}"
                }
        except Exception as e:
            return {
                "available": False,
                "active_models": [],
                "total_vram_mb": 0.0,
                "total_size_mb": 0.0,
                "error": str(e)
            }

    def sample_telemetry(self, include_ollama: bool = True) -> Dict[str, Any]:
        """Gathers an instantaneous synchronous hardware telemetry snapshot."""
        telemetry = {
            "cpu": self.sample_cpu(),
            "ram": self.sample_ram(),
            "gpu": self.sample_gpu()
        }
        if include_ollama:
            telemetry["ollama"] = self.sample_ollama_sync()
        return telemetry

    async def sample_telemetry_async(self, include_ollama: bool = True) -> Dict[str, Any]:
        """Gathers an instantaneous asynchronous hardware telemetry snapshot."""
        import asyncio
        cpu_data = self.sample_cpu()
        ram_data = self.sample_ram()
        # Offload GPU subprocess query to thread pool so it does not block the asyncio event loop
        gpu_data = await asyncio.to_thread(self.sample_gpu)

        telemetry = {
            "cpu": cpu_data,
            "ram": ram_data,
            "gpu": gpu_data
        }
        if include_ollama:
            telemetry["ollama"] = await self.sample_ollama_async()
        return telemetry

hardware_monitor = HardwareMonitor()
