from unittest.mock import patch
from backend.app.db.models.model import Model

def test_list_models_empty(client):
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []

def test_sync_models_with_mocked_ollama(client, db_session):
    mock_models = [
        {
            "name": "llama3.2:latest",
            "size": 2019393189,
            "details": {
                "family": "llama",
                "parameter_size": "3B",
                "quantization_level": "Q4_K_M"
            }
        },
        {
            "name": "qwen2.5:3b",
            "size": 1900000000,
            "details": {
                "family": "qwen2",
                "parameter_size": "3B",
                "quantization_level": "Q4_K_M"
            }
        }
    ]

    with patch("backend.app.services.ollama_service.ollama_service.list_models", return_value=mock_models):
        response = client.post("/api/v1/models/sync")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        sync_result = data["data"]
        assert sync_result["discovered_count"] == 2
        assert len(sync_result["models"]) == 2

    # Verify database was updated
    models_in_db = db_session.query(Model).all()
    assert len(models_in_db) == 2
    model_ids = [m.id for m in models_in_db]
    assert "llama3.2:latest" in model_ids
    assert "qwen2.5:3b" in model_ids
