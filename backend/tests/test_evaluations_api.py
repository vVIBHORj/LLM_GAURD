from backend.app.db.models.model import Model
from backend.app.db.models.dataset import Dataset, DatasetTestCase
from backend.app.db.models.evaluation import EvaluationRun, EvaluationResult
from backend.app.services.jsonl_storage import jsonl_storage
from backend.app.config import settings

def test_evaluation_enqueue_and_retrieval(client, db_session):
    # Setup test model and dataset
    model = Model(id="llama3.2:latest", name="llama3.2:latest")
    db_session.add(model)
    db_session.commit()

    dataset = Dataset(name="Eval Test Suite")
    db_session.add(dataset)
    db_session.commit()

    tc = DatasetTestCase(dataset_id=dataset.id, prompt="Test prompt", expected_output="Expected")
    db_session.add(tc)
    db_session.commit()

    # 1. Enqueue evaluation
    payload = {
        "model_id": "llama3.2:latest",
        "dataset_id": dataset.id,
        "temperature": 0.1,
        "num_predict": 100,
        "concurrency": 1
    }
    res = client.post("/api/v1/evaluations", json=payload)
    assert res.status_code == 202
    run_data = res.json()["data"]
    run_id = run_data["id"]
    assert run_data["status"] == "QUEUED"
    assert run_data["model_id"] == "llama3.2:latest"

    # 2. Query status
    status_res = client.get(f"/api/v1/evaluations/{run_id}")
    assert status_res.status_code == 200
    fetched_run = status_res.json()["data"]
    assert fetched_run["id"] == run_id

    # 3. Simulate completion and verify results API with JSONL enrichment
    jsonl_path = settings.PROMPTFOO_RUNS_DIR / f"{run_id}.jsonl"
    line_idx = jsonl_storage.append_record(jsonl_path, {
        "run_id": run_id,
        "vars": {"prompt": "Test prompt"},
        "raw_output": "Generated response here",
        "passed": True
    })

    eval_result = EvaluationResult(
        run_id=run_id,
        test_case_id=tc.id,
        passed=True,
        score=1.0,
        latency_ms=120.0,
        jsonl_line_index=line_idx
    )
    db_session.add(eval_result)

    run_in_db = db_session.query(EvaluationRun).filter_by(id=run_id).first()
    run_in_db.status = "COMPLETED"
    run_in_db.result_artifact_path = str(jsonl_path)
    db_session.commit()

    results_res = client.get(f"/api/v1/evaluations/{run_id}/results")
    assert results_res.status_code == 200
    results_list = results_res.json()["data"]
    assert len(results_list) == 1
    first_res = results_list[0]
    assert first_res["passed"] is True
    assert first_res["raw_output"] == "Generated response here"
    assert first_res["prompt_text"] == "Test prompt"

    # Cleanup
    jsonl_path.unlink(missing_ok=True)
