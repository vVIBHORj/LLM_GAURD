import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.app.config import settings
from backend.app.services.hardware_monitor import HardwareMonitor, hardware_monitor

logger = logging.getLogger(__name__)

@dataclass
class TelemetrySnapshot:
    """Individual instantaneous telemetry measurement captured during inference."""
    timestamp: datetime
    cpu_percent: Optional[float]
    ram_used_mb: float
    ram_used_percent: float
    gpu_allocated_mb: float
    gpu_utilization_percent: Optional[float]
    gpu_temperature_c: Optional[float]
    gpu_power_w: Optional[float]
    ollama_vram_mb: Optional[float]
    ollama_active_models: List[str] = field(default_factory=list)

@dataclass
class TelemetrySummary:
    """Aggregated resource telemetry summary computed over an evaluation run."""
    run_id: str
    sample_count: int
    duration_seconds: float
    started_at: datetime
    completed_at: datetime

    # System RAM
    peak_ram_mb: float
    avg_ram_mb: float

    # GPU VRAM
    peak_vram_mb: float
    avg_vram_mb: float

    # GPU Utilization
    peak_gpu_utilization: Optional[float]
    avg_gpu_utilization: Optional[float]

    # CPU Utilization
    peak_cpu_percent: float
    avg_cpu_percent: float

    # Ollama Model VRAM Allocation
    peak_ollama_vram_mb: Optional[float]
    avg_ollama_vram_mb: Optional[float]

    # Thermal & Power Metrics
    peak_temperature_c: Optional[float]
    avg_power_w: Optional[float]
    peak_power_w: Optional[float]

    # Captured Sample Series
    samples: List[TelemetrySnapshot] = field(default_factory=list)

class TelemetrySampler:
    """
    Asynchronous periodic hardware telemetry sampler.
    Runs non-blockingly during active model inference to record accurate
    resource consumption, peak footprint, and average workload metrics.
    """

    def __init__(
        self,
        run_id: str,
        interval_seconds: Optional[float] = None,
        monitor: Optional[HardwareMonitor] = None
    ):
        self.run_id = run_id
        self.interval = interval_seconds or settings.TELEMETRY_SAMPLE_INTERVAL_SECONDS
        self.monitor = monitor or hardware_monitor
        self.samples: List[TelemetrySnapshot] = []
        self._active = False
        self._task: Optional[asyncio.Task] = None
        self._start_time: Optional[datetime] = None
        self.summary: Optional[TelemetrySummary] = None

    @property
    def is_active(self) -> bool:
        return self._active

    async def start(self) -> None:
        """Starts periodic sampling before model evaluation begins."""
        if self._active:
            return
        self._active = True
        self._start_time = datetime.utcnow()
        # Prime the CPU reference counter before taking baseline sample
        if hasattr(self.monitor, "prime_cpu"):
            self.monitor.prime_cpu()
        # Baseline pre-evaluation sample
        await self._take_sample()
        # Launch background sampling loop
        self._task = asyncio.create_task(self._sample_loop())
        logger.debug("TelemetrySampler started for run %s with interval %.2fs", self.run_id, self.interval)

    async def _sample_loop(self) -> None:
        """Background sampling loop running concurrently with evaluation."""
        while self._active:
            try:
                await asyncio.sleep(self.interval)
                if not self._active:
                    break
                await self._take_sample()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Error in telemetry sampler loop for run %s: %s", self.run_id, e)

    async def _take_sample(self) -> None:
        """Captures a single snapshot of system, GPU, and Ollama resources."""
        try:
            telemetry = await self.monitor.sample_telemetry_async(include_ollama=True)
            ram = telemetry.get("ram", {})
            cpu = telemetry.get("cpu", {})
            gpu = telemetry.get("gpu", {})
            ollama = telemetry.get("ollama", {})

            # Calculate RAM used MB (total - available)
            total_ram = ram.get("total_mb", 0.0)
            avail_ram = ram.get("available_mb", 0.0)
            ram_used_mb = max(0.0, total_ram - avail_ram)

            # Ollama VRAM and active models
            ollama_vram = ollama.get("total_vram_mb") if ollama.get("available") else None
            active_models = [m.get("name") for m in ollama.get("active_models", []) if m.get("name")]

            cpu_val = cpu.get("usage_percent")
            snapshot = TelemetrySnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=float(cpu_val) if cpu_val is not None else None,
                ram_used_mb=round(ram_used_mb, 1),
                ram_used_percent=float(ram.get("used_percent", 0.0)),
                gpu_allocated_mb=float(gpu.get("allocated_mb", 0.0)),
                gpu_utilization_percent=gpu.get("gpu_utilization_percent"),
                gpu_temperature_c=gpu.get("temperature_c"),
                gpu_power_w=gpu.get("power_w"),
                ollama_vram_mb=ollama_vram,
                ollama_active_models=active_models
            )
            self.samples.append(snapshot)
        except Exception as e:
            logger.warning("Failed to capture telemetry snapshot for run %s: %s", self.run_id, e)

    def _calculate_summary(self, completed_at: datetime, duration: float) -> TelemetrySummary:
        """Computes peak and average metrics across all collected snapshots."""
        started_at = self._start_time or completed_at

        if not self.samples:
            return TelemetrySummary(
                run_id=self.run_id,
                sample_count=0,
                duration_seconds=round(duration, 2),
                started_at=started_at,
                completed_at=completed_at,
                peak_ram_mb=0.0,
                avg_ram_mb=0.0,
                peak_vram_mb=0.0,
                avg_vram_mb=0.0,
                peak_gpu_utilization=None,
                avg_gpu_utilization=None,
                peak_cpu_percent=0.0,
                avg_cpu_percent=0.0,
                peak_ollama_vram_mb=None,
                avg_ollama_vram_mb=None,
                peak_temperature_c=None,
                avg_power_w=None,
                peak_power_w=None,
                samples=[]
            )

        n = len(self.samples)

        # RAM calculations
        peak_ram = max(s.ram_used_mb for s in self.samples)
        avg_ram = sum(s.ram_used_mb for s in self.samples) / n

        # GPU VRAM calculations
        peak_vram = max(s.gpu_allocated_mb for s in self.samples)
        avg_vram = sum(s.gpu_allocated_mb for s in self.samples) / n

        # CPU calculations (filter None to distinguish unmeasured/instantaneous baseline from 0.0)
        cpu_vals = [s.cpu_percent for s in self.samples if s.cpu_percent is not None]
        peak_cpu = max(cpu_vals) if cpu_vals else 0.0
        avg_cpu = (sum(cpu_vals) / len(cpu_vals)) if cpu_vals else 0.0

        # GPU Utilization (filter None to distinguish unsupported from 0.0)
        gpu_utils = [s.gpu_utilization_percent for s in self.samples if s.gpu_utilization_percent is not None]
        peak_gpu_util = max(gpu_utils) if gpu_utils else None
        avg_gpu_util = (sum(gpu_utils) / len(gpu_utils)) if gpu_utils else None

        # Ollama VRAM allocation
        ollama_vrams = [s.ollama_vram_mb for s in self.samples if s.ollama_vram_mb is not None]
        peak_ollama_vram = max(ollama_vrams) if ollama_vrams else None
        avg_ollama_vram = (sum(ollama_vrams) / len(ollama_vrams)) if ollama_vrams else None

        # Thermal metrics
        temps = [s.gpu_temperature_c for s in self.samples if s.gpu_temperature_c is not None]
        peak_temp = max(temps) if temps else None

        # Power metrics
        powers = [s.gpu_power_w for s in self.samples if s.gpu_power_w is not None]
        avg_power = (sum(powers) / len(powers)) if powers else None
        peak_power = max(powers) if powers else None

        return TelemetrySummary(
            run_id=self.run_id,
            sample_count=n,
            duration_seconds=round(duration, 2),
            started_at=started_at,
            completed_at=completed_at,
            peak_ram_mb=round(peak_ram, 1),
            avg_ram_mb=round(avg_ram, 1),
            peak_vram_mb=round(peak_vram, 1),
            avg_vram_mb=round(avg_vram, 1),
            peak_gpu_utilization=round(peak_gpu_util, 1) if peak_gpu_util is not None else None,
            avg_gpu_utilization=round(avg_gpu_util, 1) if avg_gpu_util is not None else None,
            peak_cpu_percent=round(peak_cpu, 1),
            avg_cpu_percent=round(avg_cpu, 1),
            peak_ollama_vram_mb=round(peak_ollama_vram, 1) if peak_ollama_vram is not None else None,
            avg_ollama_vram_mb=round(avg_ollama_vram, 1) if avg_ollama_vram is not None else None,
            peak_temperature_c=round(peak_temp, 1) if peak_temp is not None else None,
            avg_power_w=round(avg_power, 1) if avg_power is not None else None,
            peak_power_w=round(peak_power, 1) if peak_power is not None else None,
            samples=list(self.samples)
        )

    async def stop(self) -> TelemetrySummary:
        """
        Halts periodic sampling, cancels background task, takes a final sample,
        and computes resource statistics.
        """
        self._active = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Capture final boundary snapshot
        try:
            await self._take_sample()
        except Exception:
            pass

        completed_at = datetime.utcnow()
        duration = (completed_at - (self._start_time or completed_at)).total_seconds()
        self.summary = self._calculate_summary(completed_at, duration)
        logger.debug(
            "TelemetrySampler stopped for run %s (%d samples in %.2fs). Peak VRAM: %.1f MB, Peak RAM: %.1f MB",
            self.run_id, len(self.samples), duration, self.summary.peak_vram_mb, self.summary.peak_ram_mb
        )
        return self.summary

    async def __aenter__(self) -> "TelemetrySampler":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()
