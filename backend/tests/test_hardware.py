import asyncio
import subprocess
from datetime import datetime
from unittest.mock import patch, MagicMock
import httpx
import pytest

from backend.app.services.hardware_monitor import HardwareMonitor, hardware_monitor
from backend.app.core.hardware_gate import HardwareGate
from backend.app.services.telemetry_sampler import TelemetrySampler, TelemetrySnapshot

def test_hardware_monitor_sampling():
    monitor = HardwareMonitor()
    telemetry = monitor.sample_telemetry()
    assert "cpu" in telemetry
    assert "ram" in telemetry
    assert "gpu" in telemetry
    assert telemetry["ram"]["total_mb"] > 0
    assert telemetry["ram"]["available_mb"] > 0

def test_hardware_gate_thresholds():
    monitor = HardwareMonitor()
    gate = HardwareGate(monitor=monitor)
    allowed, reason, telemetry = gate.check_preflight()
    assert isinstance(allowed, bool)
    assert isinstance(reason, str)
    assert isinstance(telemetry, dict)

def test_telemetry_endpoint(client):
    response = client.get("/api/v1/monitoring/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cpu" in data["data"]
    assert "ram" in data["data"]
    assert "gpu" in data["data"]
    assert "hardware_safety_status" in data["data"]


# ============================================================================
# Phase 2, Task 2.2: Comprehensive Hardware Telemetry Tests
# ============================================================================

def test_nvidia_smi_parsing():
    """Test 1: NVIDIA SMI parsing of all 7 fields (name, VRAM, utilization, temp, power)."""
    monitor = HardwareMonitor()
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "NVIDIA GeForce RTX 3050 Laptop GPU, 4096, 1024, 3072, 45, 52, 28.5\n"

    with patch("subprocess.run", return_value=mock_proc):
        gpu = monitor._sample_gpu_nvidia_smi()
        assert gpu is not None
        assert gpu["available"] is True
        assert gpu["name"] == "NVIDIA GeForce RTX 3050 Laptop GPU"
        assert gpu["total_mb"] == 4096.0
        assert gpu["allocated_mb"] == 1024.0
        assert gpu["free_mb"] == 3072.0
        assert gpu["vram_usage_percent"] == 25.0
        assert gpu["gpu_utilization_percent"] == 45.0
        assert gpu["temperature_c"] == 52.0
        assert gpu["power_w"] == 28.5
        assert gpu["source"] == "nvidia-smi"


def test_ollama_api_ps_parsing():
    """Test 2: Ollama /api/ps response parsing and model VRAM aggregation."""
    monitor = HardwareMonitor()
    raw_ps = {
        "models": [
            {
                "name": "qwen3:1.7b",
                "model": "qwen3:1.7b",
                "size": 1424103680,
                "size_vram": 1424103680,
                "digest": "8f68893c685c",
                "details": {
                    "format": "gguf",
                    "parameter_size": "1.7B",
                    "quantization_level": "Q4_K_M"
                },
                "expires_at": "2026-11-22T14:00:00Z"
            }
        ]
    }
    parsed = monitor._parse_ollama_ps_response(raw_ps)
    assert parsed["available"] is True
    assert len(parsed["active_models"]) == 1
    assert parsed["active_models"][0]["name"] == "qwen3:1.7b"
    assert parsed["active_models"][0]["size_vram_mb"] == round(1424103680 / (1024 ** 2), 1)
    assert parsed["total_vram_mb"] == round(1424103680 / (1024 ** 2), 1)
    assert parsed["error"] is None


def test_missing_nvidia_smi_executable():
    """Test 3: Graceful fallback when nvidia-smi is not found in PATH or filesystem."""
    monitor = HardwareMonitor()
    monitor._nvidia_smi_path = None
    with patch.object(monitor, "_find_nvidia_smi", return_value=None), \
         patch.object(monitor, "_sample_gpu_torch", return_value=None):
        gpu = monitor.sample_gpu()
        assert gpu["available"] is False
        assert gpu["name"] is None
        assert gpu["allocated_mb"] == 0.0
        assert gpu["source"] == "none"


def test_ollama_unavailable():
    """Test 4: Ollama /api/ps connection failure handled gracefully without crashing."""
    monitor = HardwareMonitor()
    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")):
        res = monitor.sample_ollama_sync()
        assert res["available"] is False
        assert res["active_models"] == []
        assert res["total_vram_mb"] == 0.0
        assert "Connection refused" in res["error"]


def test_partial_telemetry_availability():
    """Test 5: [N/A] or [Not Supported] fields parsed as None, not invented as 0.0."""
    monitor = HardwareMonitor()
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "NVIDIA GeForce RTX 3050 Laptop GPU, 4096, 512, 3584, [Not Supported], [N/A], [N/A]\n"

    with patch("subprocess.run", return_value=mock_proc):
        gpu = monitor._sample_gpu_nvidia_smi()
        assert gpu is not None
        assert gpu["total_mb"] == 4096.0
        assert gpu["allocated_mb"] == 512.0
        # Unsupported metrics must be None, NOT 0.0
        assert gpu["gpu_utilization_percent"] is None
        assert gpu["temperature_c"] is None
        assert gpu["power_w"] is None
        assert gpu["vram_usage_percent"] == 12.5


def test_sampling_during_evaluation():
    """Test 6: Periodic sampling actively captures snapshots during simulated execution."""
    async def _run():
        monitor = HardwareMonitor()
        mock_snapshot = {
            "cpu": {"usage_percent": 35.0, "cores_logical": 16, "cores_physical": 8},
            "ram": {"total_mb": 16000.0, "available_mb": 10000.0, "free_mb": 8000.0, "used_percent": 37.5},
            "gpu": {"available": True, "name": "RTX 3050", "total_mb": 4096.0, "allocated_mb": 1200.0, "free_mb": 2896.0, "vram_usage_percent": 29.3, "gpu_utilization_percent": 50.0, "temperature_c": 55.0, "power_w": 25.0},
            "ollama": {"available": True, "active_models": [{"name": "qwen3:1.7b"}], "total_vram_mb": 1100.0, "total_size_mb": 1400.0, "error": None}
        }

        with patch.object(monitor, "sample_telemetry_async", return_value=mock_snapshot):
            sampler = TelemetrySampler(run_id="test-eval-sampling", interval_seconds=0.04, monitor=monitor)
            await sampler.start()
            assert sampler.is_active is True
            # Simulate evaluation workload
            await asyncio.sleep(0.15)
            summary = await sampler.stop()

            assert summary.sample_count >= 3
            assert summary.duration_seconds >= 0.1
            assert summary.peak_vram_mb == 1200.0
            assert summary.peak_ollama_vram_mb == 1100.0

    asyncio.run(_run())


def test_peak_and_average_calculation():
    """Test 7: Mathematical correctness of peak and average metric calculations."""
    sampler = TelemetrySampler(run_id="test-math-eval")
    t0 = datetime.utcnow()

    # Create 3 synthetic snapshots with known values
    sampler.samples = [
        TelemetrySnapshot(
            timestamp=t0,
            cpu_percent=20.0,
            ram_used_mb=4000.0,
            ram_used_percent=25.0,
            gpu_allocated_mb=1000.0,
            gpu_utilization_percent=30.0,
            gpu_temperature_c=50.0,
            gpu_power_w=20.0,
            ollama_vram_mb=800.0,
            ollama_active_models=["model_a"]
        ),
        TelemetrySnapshot(
            timestamp=t0,
            cpu_percent=80.0,
            ram_used_mb=6000.0,
            ram_used_percent=37.5,
            gpu_allocated_mb=3000.0,
            gpu_utilization_percent=90.0,
            gpu_temperature_c=65.0,
            gpu_power_w=40.0,
            ollama_vram_mb=2500.0,
            ollama_active_models=["model_a"]
        ),
        TelemetrySnapshot(
            timestamp=t0,
            cpu_percent=50.0,
            ram_used_mb=5000.0,
            ram_used_percent=31.2,
            gpu_allocated_mb=2000.0,
            gpu_utilization_percent=60.0,
            gpu_temperature_c=60.0,
            gpu_power_w=30.0,
            ollama_vram_mb=1500.0,
            ollama_active_models=["model_a"]
        )
    ]

    summary = sampler._calculate_summary(datetime.utcnow(), 10.0)

    # Verification of peaks
    assert summary.peak_ram_mb == 6000.0
    assert summary.peak_vram_mb == 3000.0
    assert summary.peak_cpu_percent == 80.0
    assert summary.peak_gpu_utilization == 90.0
    assert summary.peak_ollama_vram_mb == 2500.0
    assert summary.peak_temperature_c == 65.0
    assert summary.peak_power_w == 40.0

    # Verification of averages
    assert summary.avg_ram_mb == 5000.0
    assert summary.avg_vram_mb == 2000.0
    assert summary.avg_cpu_percent == 50.0
    assert summary.avg_gpu_utilization == 60.0
    assert summary.avg_ollama_vram_mb == 1600.0
    assert summary.avg_power_w == 30.0


def test_sampling_cleanup_after_success():
    """Test 8: Background sampling task cleanly stopped and finalized on success."""
    async def _run():
        sampler = TelemetrySampler(run_id="test-clean-success", interval_seconds=0.03)
        await sampler.start()
        assert sampler.is_active is True
        assert sampler._task is not None
        assert not sampler._task.done()

        summary = await sampler.stop()
        assert sampler.is_active is False
        assert sampler._task.done()
        assert summary.run_id == "test-clean-success"

    asyncio.run(_run())


def test_sampling_cleanup_after_timeout_or_cancellation():
    """Test 9: Sampling background task terminates cleanly even when evaluation times out."""
    async def _run():
        sampler = TelemetrySampler(run_id="test-timeout-cleanup", interval_seconds=0.03)
        await sampler.start()
        assert sampler.is_active is True

        summary = None
        try:
            try:
                # Simulate subprocess timeout
                raise asyncio.TimeoutError("Promptfoo evaluation timed out after 300 seconds")
            finally:
                summary = await sampler.stop()
        except asyncio.TimeoutError:
            pass

        assert sampler.is_active is False
        assert sampler._task.done()
        assert summary is not None
        assert summary.sample_count >= 1

    asyncio.run(_run())


def test_correct_association_with_evaluation_ids():
    """Test 10: Samples and summaries are correctly associated with specific evaluation IDs."""
    async def _run():
        sampler_1 = TelemetrySampler(run_id="eval-run-001", interval_seconds=0.05)
        sampler_2 = TelemetrySampler(run_id="eval-run-002", interval_seconds=0.05)

        await sampler_1.start()
        await sampler_2.start()

        s1 = await sampler_1.stop()
        s2 = await sampler_2.stop()

        assert s1.run_id == "eval-run-001"
        assert s2.run_id == "eval-run-002"

    asyncio.run(_run())


def test_nvidia_smi_reserved_memory_parsing():
    """
    Task 2.2.1: Validates that driver-reserved VRAM (134 MiB) reconciles:
    Total VRAM = Free VRAM + Used VRAM + Reserved VRAM.
    """
    monitor = HardwareMonitor()
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "NVIDIA GeForce RTX 3050 Laptop GPU, 4096, 0, 3962, 134, 0, 45, 14.53\n"

    with patch("subprocess.run", return_value=mock_proc):
        gpu = monitor._sample_gpu_nvidia_smi()
        assert gpu is not None
        assert gpu["total_mb"] == 4096.0
        assert gpu["allocated_mb"] == 0.0
        assert gpu["free_mb"] == 3962.0
        assert gpu["reserved_mb"] == 134.0
        # Exact mathematical reconciliation
        assert gpu["free_mb"] + gpu["allocated_mb"] + gpu["reserved_mb"] == gpu["total_mb"]


def test_cpu_sampling_initialization_prevents_artificial_zero():
    """
    Task 2.2.1: Verifies that an instantaneous CPU reading (< 100ms elapsed)
    is marked unavailable (None) rather than an artificial zero, preventing
    distortion of workload averages.
    """
    monitor = HardwareMonitor()
    # 1. Immediately after priming, elapsed time is ~0s (< 0.1s)
    monitor.prime_cpu()
    instantaneous_sample = monitor.sample_cpu(min_interval_seconds=0.1)
    assert instantaneous_sample["usage_percent"] is None  # Handled as unavailable, NOT 0.0

    # 2. In TelemetrySampler, baseline sample does not distort average CPU calculation
    sampler = TelemetrySampler(run_id="test-cpu-init", monitor=monitor)
    t0 = datetime.utcnow()
    # Snapshot 0: baseline with usage_percent None
    # Snapshot 1 & 2: actual evaluation samples with 40% and 60%
    sampler.samples = [
        TelemetrySnapshot(
            timestamp=t0,
            cpu_percent=None,
            ram_used_mb=4000.0,
            ram_used_percent=25.0,
            gpu_allocated_mb=1000.0,
            gpu_utilization_percent=30.0,
            gpu_temperature_c=50.0,
            gpu_power_w=20.0,
            ollama_vram_mb=800.0
        ),
        TelemetrySnapshot(
            timestamp=t0,
            cpu_percent=40.0,
            ram_used_mb=4500.0,
            ram_used_percent=28.0,
            gpu_allocated_mb=1000.0,
            gpu_utilization_percent=50.0,
            gpu_temperature_c=55.0,
            gpu_power_w=25.0,
            ollama_vram_mb=800.0
        ),
        TelemetrySnapshot(
            timestamp=t0,
            cpu_percent=60.0,
            ram_used_mb=5000.0,
            ram_used_percent=31.0,
            gpu_allocated_mb=1000.0,
            gpu_utilization_percent=70.0,
            gpu_temperature_c=60.0,
            gpu_power_w=30.0,
            ollama_vram_mb=800.0
        ),
    ]
    summary = sampler._calculate_summary(datetime.utcnow(), 2.0)
    # Average CPU should be (40 + 60) / 2 = 50.0%, NOT dragged down to 33.3% by an artificial zero
    assert summary.avg_cpu_percent == 50.0
    assert summary.peak_cpu_percent == 60.0

