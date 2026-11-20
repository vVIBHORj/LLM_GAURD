from backend.app.services.hardware_monitor import HardwareMonitor
from backend.app.core.hardware_gate import HardwareGate

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
