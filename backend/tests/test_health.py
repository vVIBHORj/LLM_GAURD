def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "LocalLLM Guard"
    assert data["status"] == "online"
    assert "dashboard" in data

def test_dashboard_endpoint(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "LocalLLM Guard" in response.text
    assert "Overview" in response.text
    assert "Model Registry" in response.text

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    health = data["data"]
    assert "status" in health
    assert "ollama" in health
    assert "promptfoo" in health
    assert "hardware" in health
    assert health["ollama"]["host"] == "http://127.0.0.1:11434"
