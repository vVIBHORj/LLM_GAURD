from backend.app.db.models.model import Model
from backend.app.db.models.dataset import Dataset, DatasetTestCase
from backend.app.services.benchmark_service import benchmark_service

def test_pareto_frontier_calculation():
    points = [
        {"model_id": "fast_low_acc", "tokens_per_sec": 100.0, "accuracy_rate": 0.70},
        {"model_id": "slow_high_acc", "tokens_per_sec": 20.0, "accuracy_rate": 0.95},
        {"model_id": "dominated_model", "tokens_per_sec": 15.0, "accuracy_rate": 0.65},
    ]
    pareto_pts = benchmark_service.calculate_pareto_frontier(points)
    pts_by_id = {p.model_id: p for p in pareto_pts}

    assert pts_by_id["fast_low_acc"].is_pareto_optimal is True
    assert pts_by_id["slow_high_acc"].is_pareto_optimal is True
    assert pts_by_id["dominated_model"].is_pareto_optimal is False

def test_benchmarks_api(client, db_session):
    m1 = Model(id="llama3.2:latest", name="llama3.2:latest")
    m2 = Model(id="qwen2.5:3b", name="qwen2.5:3b")
    dataset = Dataset(name="Benchmark Dataset")
    db_session.add_all([m1, m2, dataset])
    db_session.commit()

    payload = {
        "title": "LocalLLM Guard 3B Shootout",
        "dataset_id": dataset.id,
        "model_ids": ["llama3.2:latest", "qwen2.5:3b"]
    }

    create_res = client.post("/api/v1/benchmarks", json=payload)
    assert create_res.status_code == 202
    data = create_res.json()["data"]
    assert data["title"] == "LocalLLM Guard 3B Shootout"
    assert len(data["results"]) == 2
    assert len(data["pareto_frontier"]) == 2

    # List
    list_res = client.get("/api/v1/benchmarks")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1
