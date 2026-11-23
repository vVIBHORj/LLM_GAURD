from backend.app.services.analytics_service import analytics_service
from backend.app.db.models.model import Model
from backend.app.db.models.dataset import Dataset, DatasetTestCase
from backend.app.db.models.evaluation import EvaluationRun, EvaluationResult

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

def test_analytics_recommendation_api(client, db_session):
    # Seed evaluated models with real runs
    m1 = Model(id="llama3.2:latest", name="llama3.2:latest")
    m2 = Model(id="qwen2.5:3b", name="qwen2.5:3b")
    dataset = Dataset(name="Analytics Suite")
    db_session.add_all([m1, m2, dataset])
    db_session.commit()

    tc = DatasetTestCase(dataset_id=dataset.id, prompt="Test prompt", expected_output="Expected")
    db_session.add(tc)
    db_session.commit()

    run1 = EvaluationRun(
        model_id="llama3.2:latest",
        dataset_id=dataset.id,
        status="COMPLETED",
        tokens_per_second_avg=109.3,
        peak_vram_mb=2238.0
    )
    run2 = EvaluationRun(
        model_id="qwen2.5:3b",
        dataset_id=dataset.id,
        status="COMPLETED",
        tokens_per_second_avg=55.0,
        peak_vram_mb=2063.0
    )
    db_session.add_all([run1, run2])
    db_session.commit()

    res1 = EvaluationResult(run_id=run1.id, test_case_id=tc.id, passed=True, score=1.0)
    res2 = EvaluationResult(run_id=run2.id, test_case_id=tc.id, passed=True, score=1.0)
    db_session.add_all([res1, res2])
    db_session.commit()

    # Test speed preference
    req_speed = {"task_priority": "speed", "max_vram_mb": 4096.0}
    res_speed = client.post("/api/v1/analytics/recommend", json=req_speed)
    assert res_speed.status_code == 200
    data_speed = res_speed.json()["data"]
    assert "recommended_model_id" in data_speed
    assert data_speed["recommended_model_id"] == "llama3.2:latest"
    assert data_speed["speed_tokens_sec"] > 0

    # Test rankings API
    res_rank = client.get("/api/v1/analytics/rankings")
    assert res_rank.status_code == 200
    rank_data = res_rank.json()["data"]
    assert len(rank_data["rankings"]) == 2
