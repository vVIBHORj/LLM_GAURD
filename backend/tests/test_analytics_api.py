from backend.app.services.analytics_service import analytics_service
from backend.app.schemas.analytics import RecommendationRequest

def test_calculate_rankings():
    models_data = [
        {"model_id": "model_a", "accuracy": 0.95, "security": 0.90, "tokens_per_sec": 100.0, "vram_mb": 2000.0},
        {"model_id": "model_b", "accuracy": 0.70, "security": 0.60, "tokens_per_sec": 30.0, "vram_mb": 3500.0}
    ]
    rankings = analytics_service.calculate_rankings(models_data)
    assert len(rankings.rankings) == 2
    assert rankings.rankings[0].model_id == "model_a"
    assert rankings.rankings[0].rank == 1
    assert rankings.rankings[1].rank == 2

def test_analytics_recommendation_api(client):
    # Test speed preference
    req_speed = {"task_priority": "speed", "max_vram_mb": 4096.0}
    res_speed = client.post("/api/v1/analytics/recommend", json=req_speed)
    assert res_speed.status_code == 200
    data_speed = res_speed.json()["data"]
    assert "recommended_model_id" in data_speed
    assert data_speed["speed_tokens_sec"] > 0

    # Test rankings API
    res_rank = client.get("/api/v1/analytics/rankings")
    assert res_rank.status_code == 200
    rank_data = res_rank.json()["data"]
    assert len(rank_data["rankings"]) > 0
