import uuid
from sqlalchemy import create_engine, text, inspect
from backend.app.db.models.model import Model
from backend.app.db.models.dataset import Dataset, DatasetTestCase
from backend.app.db.models.evaluation import EvaluationRun, EvaluationResult
from backend.app.db.models.metric import Metric
from backend.app.services.benchmark_service import benchmark_service
from backend.app.db.session import migrate_schema


def test_pareto_frontier_calculation():
    points = [
        {"model_id": "fast_low_acc", "run_id": "run-1", "tokens_per_sec": 100.0, "accuracy_rate": 0.70, "peak_vram_mb": 2000.0},
        {"model_id": "slow_high_acc", "run_id": "run-2", "tokens_per_sec": 20.0, "accuracy_rate": 0.95, "peak_vram_mb": 3000.0},
        {"model_id": "dominated_model", "run_id": "run-3", "tokens_per_sec": 15.0, "accuracy_rate": 0.65, "peak_vram_mb": 2500.0},
    ]
    pareto_pts = benchmark_service.calculate_pareto_frontier(points)
    pts_by_id = {p.model_id: p for p in pareto_pts}

    assert pts_by_id["fast_low_acc"].is_pareto_optimal is True
    assert pts_by_id["fast_low_acc"].run_id == "run-1"
    assert pts_by_id["slow_high_acc"].is_pareto_optimal is True
    assert pts_by_id["slow_high_acc"].run_id == "run-2"
    assert pts_by_id["dominated_model"].is_pareto_optimal is False


def test_benchmarks_api_with_real_evaluations(client, db_session):
    m1 = Model(id="llama3.2:latest", name="llama3.2:latest")
    m2 = Model(id="qwen2.5:3b", name="qwen2.5:3b")
    dataset = Dataset(name="Benchmark Dataset")
    db_session.add_all([m1, m2, dataset])
    db_session.commit()

    tc1 = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=dataset.id, prompt="Prompt 1", expected_output="Expected 1")
    tc2 = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=dataset.id, prompt="Prompt 2", expected_output="Expected 2")
    db_session.add_all([tc1, tc2])
    db_session.commit()

    # Seed real completed evaluation runs
    run1 = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id="llama3.2:latest",
        dataset_id=dataset.id,
        status="COMPLETED",
        tokens_per_second_avg=109.3,
        peak_vram_mb=2238.0,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    run2 = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id="qwen2.5:3b",
        dataset_id=dataset.id,
        status="COMPLETED",
        tokens_per_second_avg=55.0,
        peak_vram_mb=2063.0,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    db_session.add_all([run1, run2])
    db_session.commit()

    # Add results: run1 passes 2/2 (1.0), run2 passes 1/2 (0.5)
    r1_1 = EvaluationResult(run_id=run1.id, test_case_id=tc1.id, passed=True, score=1.0, latency_ms=100.0)
    r1_2 = EvaluationResult(run_id=run1.id, test_case_id=tc2.id, passed=True, score=1.0, latency_ms=110.0)
    r2_1 = EvaluationResult(run_id=run2.id, test_case_id=tc1.id, passed=True, score=1.0, latency_ms=150.0)
    r2_2 = EvaluationResult(run_id=run2.id, test_case_id=tc2.id, passed=False, score=0.0, latency_ms=160.0)
    db_session.add_all([r1_1, r1_2, r2_1, r2_2])

    # Add metrics
    m_lat1 = Metric(run_id=run1.id, metric_name="avg_latency_ms", metric_value=105.0)
    m_ollama1 = Metric(run_id=run1.id, metric_name="peak_ollama_vram_mb", metric_value=2000.0)
    m_vram1 = Metric(
        run_id=run1.id,
        metric_name="avg_vram_mb",
        metric_value=2200.0,
        details={"gpu_name": "NVIDIA GeForce RTX 3050 Laptop GPU", "source": "nvidia-smi", "sample_count": 5}
    )
    db_session.add_all([m_lat1, m_ollama1, m_vram1])
    db_session.commit()

    payload = {
        "title": "LocalLLM Guard 3B Shootout",
        "dataset_id": dataset.id,
        "model_ids": ["llama3.2:latest", "qwen2.5:3b"],
        "temperature": 0.1,
        "num_predict": 256,
        "num_ctx": 2048,
        "concurrency": 1
    }

    create_res = client.post("/api/v1/benchmarks", json=payload)
    assert create_res.status_code == 202
    data = create_res.json()["data"]
    assert data["title"] == "LocalLLM Guard 3B Shootout"
    assert data["dataset_id"] == dataset.id
    assert data["generation_config"]["temperature"] == 0.1
    assert data["generation_config"]["concurrency"] == 1
    assert len(data["results"]) == 2
    assert len(data["pareto_frontier"]) == 2

    # Check traceability & real metrics
    r_map = {r["model_id"]: r for r in data["results"]}
    assert r_map["llama3.2:latest"]["run_id"] == run1.id
    assert r_map["llama3.2:latest"]["status"] == "BENCHMARKED"
    assert r_map["llama3.2:latest"]["accuracy_score"] == 1.0
    assert r_map["llama3.2:latest"]["speed_tokens_sec"] == 109.3
    assert r_map["llama3.2:latest"]["avg_latency_ms"] == 105.0
    assert r_map["llama3.2:latest"]["peak_ollama_vram_mb"] == 2000.0
    assert r_map["llama3.2:latest"]["gpu_name"] == "NVIDIA GeForce RTX 3050 Laptop GPU"
    assert r_map["llama3.2:latest"]["gpu_source"] == "nvidia-smi"

    assert r_map["qwen2.5:3b"]["run_id"] == run2.id
    assert r_map["qwen2.5:3b"]["status"] == "BENCHMARKED"
    assert r_map["qwen2.5:3b"]["accuracy_score"] == 0.5
    assert r_map["qwen2.5:3b"]["speed_tokens_sec"] == 55.0
    assert r_map["qwen2.5:3b"]["gpu_name"] is None
    assert r_map["qwen2.5:3b"]["gpu_source"] is None

    # Pareto points must be traceable to run_id
    p_map = {p["model_id"]: p for p in data["pareto_frontier"]}
    assert p_map["llama3.2:latest"]["run_id"] == run1.id
    assert p_map["llama3.2:latest"]["is_pareto_optimal"] is True
    assert p_map["qwen2.5:3b"]["is_pareto_optimal"] is False

    # List endpoint check
    list_res = client.get("/api/v1/benchmarks")
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert len(list_data) >= 1
    first_rep = list_data[0]
    assert len(first_rep["pareto_frontier"]) == 2
    assert first_rep["dataset_id"] == dataset.id

    # Filtered list endpoint check
    filtered_res = client.get(f"/api/v1/benchmarks?dataset_id={dataset.id}")
    assert filtered_res.status_code == 200
    assert len(filtered_res.json()["data"]) >= 1

    other_filtered = client.get("/api/v1/benchmarks?dataset_id=non-existent-dataset")
    assert other_filtered.status_code == 200
    assert len(other_filtered.json()["data"]) == 0

    # Detail endpoint check
    detail_res = client.get(f"/api/v1/benchmarks/{data['id']}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert len(detail_data["pareto_frontier"]) == 2
    assert detail_data["results"][0]["avg_latency_ms"] is not None


def test_benchmarks_api_dataset_isolation(client, db_session):
    """
    Test: Results from different datasets must never be mixed.
    If Model A was evaluated on Dataset X, and Model B was evaluated on Dataset Y,
    compiling a benchmark for Dataset X must NOT use Model B's run on Dataset Y.
    """
    m1 = Model(id="model-dataset-a", name="model-dataset-a")
    m2 = Model(id="model-dataset-b", name="model-dataset-b")
    ds_a = Dataset(name="Dataset A")
    ds_b = Dataset(name="Dataset B")
    db_session.add_all([m1, m2, ds_a, ds_b])
    db_session.commit()

    tc_a = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds_a.id, prompt="Prompt A")
    tc_b = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds_b.id, prompt="Prompt B")
    db_session.add_all([tc_a, tc_b])
    db_session.commit()

    # Run for Model 1 on Dataset A
    run_a = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id=m1.id,
        dataset_id=ds_a.id,
        status="COMPLETED",
        tokens_per_second_avg=80.0,
        peak_vram_mb=2100.0,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    # Run for Model 2 on Dataset B
    run_b = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id=m2.id,
        dataset_id=ds_b.id,
        status="COMPLETED",
        tokens_per_second_avg=95.0,
        peak_vram_mb=2300.0,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    db_session.add_all([run_a, run_b])
    db_session.commit()

    r_a = EvaluationResult(run_id=run_a.id, test_case_id=tc_a.id, passed=True, score=1.0)
    r_b = EvaluationResult(run_id=run_b.id, test_case_id=tc_b.id, passed=True, score=1.0)
    db_session.add_all([r_a, r_b])
    db_session.commit()

    payload = {
        "title": "Dataset A Isolation Test",
        "dataset_id": ds_a.id,
        "model_ids": [m1.id, m2.id],
        "temperature": 0.1,
        "num_predict": 256,
        "num_ctx": 2048,
        "concurrency": 1
    }
    res = client.post("/api/v1/benchmarks", json=payload)
    assert res.status_code == 202
    data = res.json()["data"]

    results_map = {r["model_id"]: r for r in data["results"]}
    # Model 1 was evaluated on Dataset A -> BENCHMARKED
    assert results_map[m1.id]["status"] == "BENCHMARKED"
    assert results_map[m1.id]["run_id"] == run_a.id
    assert results_map[m1.id]["speed_tokens_sec"] == 80.0

    # Model 2 was ONLY evaluated on Dataset B -> UNBENCHMARKED on Dataset A!
    assert results_map[m2.id]["status"] == "UNBENCHMARKED"
    assert results_map[m2.id]["run_id"] is None
    assert results_map[m2.id]["accuracy_score"] is None
    assert results_map[m2.id]["speed_tokens_sec"] is None

    # Only Model 1 should be in the Pareto frontier
    assert len(data["pareto_frontier"]) == 1
    assert data["pareto_frontier"][0]["model_id"] == m1.id


def test_benchmarks_api_unbenchmarked_models(client, db_session):
    """
    Test: If a model has no completed runs, never substitute synthetic values.
    Mark as UNBENCHMARKED, scores as None, and omit from Pareto frontier.
    """
    m1 = Model(id="unbenchmarked-1", name="unbenchmarked-1")
    m2 = Model(id="unbenchmarked-2", name="unbenchmarked-2")
    ds = Dataset(name="Empty Suite")
    db_session.add_all([m1, m2, ds])
    db_session.commit()

    payload = {
        "title": "Zero Run Shootout",
        "dataset_id": ds.id,
        "model_ids": [m1.id, m2.id]
    }
    res = client.post("/api/v1/benchmarks", json=payload)
    assert res.status_code == 202
    data = res.json()["data"]

    assert len(data["results"]) == 2
    for r in data["results"]:
        assert r["status"] == "UNBENCHMARKED"
        assert r["run_id"] is None
        assert r["accuracy_score"] is None
        assert r["speed_tokens_sec"] is None
        assert r["avg_latency_ms"] is None
        assert r["peak_vram_mb"] is None
        assert r["rank"] is None

    assert len(data["pareto_frontier"]) == 0


def test_benchmarks_api_missing_telemetry_metrics_handled_cleanly(client, db_session):
    """
    Test: Missing latency, throughput, or telemetry values are represented
    as None/null without crashing or fabricating mock numbers.
    """
    m = Model(id="partial-telemetry-model", name="partial-telemetry-model")
    ds = Dataset(name="Partial Suite")
    db_session.add_all([m, ds])
    db_session.commit()

    tc = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds.id, prompt="Prompt")
    db_session.add(tc)
    db_session.commit()

    # Run with tokens_per_second_avg, but NO peak_vram_mb and NO Metric records
    run = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id=m.id,
        dataset_id=ds.id,
        status="COMPLETED",
        tokens_per_second_avg=60.0,
        peak_vram_mb=None,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    db_session.add(run)
    db_session.commit()

    r = EvaluationResult(run_id=run.id, test_case_id=tc.id, passed=True, score=1.0, latency_ms=None)
    db_session.add(r)
    db_session.commit()

    payload = {
        "title": "Partial Telemetry Report",
        "dataset_id": ds.id,
        "model_ids": [m.id],
        "temperature": 0.1,
        "num_predict": 256,
        "num_ctx": 2048,
        "concurrency": 1
    }
    res = client.post("/api/v1/benchmarks", json=payload)
    assert res.status_code == 202
    data = res.json()["data"]

    score = data["results"][0]
    assert score["status"] == "BENCHMARKED"
    assert score["speed_tokens_sec"] == 60.0
    assert score["accuracy_score"] == 1.0
    assert score["peak_vram_mb"] is None
    assert score["peak_ollama_vram_mb"] is None
    assert score["avg_latency_ms"] is None
    assert len(data["pareto_frontier"]) == 0


def test_benchmarks_api_configuration_mismatch_is_ineligible(client, db_session):
    """
    Test: Runs with different generation settings (num_predict, temperature, num_ctx, concurrency)
    are marked INELIGIBLE and not silently combined into a controlled benchmark.
    """
    m = Model(id="mismatched-config-model", name="mismatched-config-model")
    ds = Dataset(name="Config Match Suite")
    db_session.add_all([m, ds])
    db_session.commit()

    tc = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds.id, prompt="Prompt")
    db_session.add(tc)
    db_session.commit()

    # Run was executed with num_predict=128
    run = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id=m.id,
        dataset_id=ds.id,
        status="COMPLETED",
        tokens_per_second_avg=85.0,
        peak_vram_mb=2100.0,
        temperature=0.1,
        num_predict=128,  # Does not match target 256
        num_ctx=2048,
        concurrency=1
    )
    db_session.add(run)
    db_session.commit()

    r = EvaluationResult(run_id=run.id, test_case_id=tc.id, passed=True, score=1.0)
    db_session.add(r)
    db_session.commit()

    payload = {
        "title": "Controlled Benchmark (256 Tokens)",
        "dataset_id": ds.id,
        "model_ids": [m.id],
        "temperature": 0.1,
        "num_predict": 256,  # Target requires 256
        "num_ctx": 2048,
        "concurrency": 1
    }
    res = client.post("/api/v1/benchmarks", json=payload)
    assert res.status_code == 202
    data = res.json()["data"]

    score = data["results"][0]
    assert score["status"] == "INELIGIBLE"
    assert score["run_id"] is None
    assert score["accuracy_score"] is None
    assert score["speed_tokens_sec"] is None
    assert len(data["pareto_frontier"]) == 0


def test_benchmarks_api_historical_runs_with_missing_provenance(client, db_session):
    """
    Test: Historical runs where generation configuration is None (missing provenance)
    cannot be verified as controlled comparisons and must be marked INELIGIBLE.
    """
    m = Model(id="legacy-model", name="legacy-model")
    ds = Dataset(name="Target Suite")
    db_session.add_all([m, ds])
    db_session.commit()

    tc = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds.id, prompt="Prompt")
    db_session.add(tc)
    db_session.commit()

    # Legacy run has results on target suite, but missing generation provenance (temperature=None)
    legacy_run = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id=m.id,
        dataset_id=ds.id,
        status="COMPLETED",
        tokens_per_second_avg=50.0,
        peak_vram_mb=2000.0,
        temperature=None,
        num_predict=None
    )
    db_session.add(legacy_run)
    db_session.commit()

    r = EvaluationResult(run_id=legacy_run.id, test_case_id=tc.id, passed=True, score=1.0)
    db_session.add(r)
    db_session.commit()

    payload = {
        "title": "Legacy Run Test",
        "dataset_id": ds.id,
        "model_ids": [m.id]
    }
    res = client.post("/api/v1/benchmarks", json=payload)
    assert res.status_code == 202
    data = res.json()["data"]

    score = data["results"][0]
    assert score["status"] == "INELIGIBLE"
    assert score["run_id"] is None
    assert score["accuracy_score"] is None


def test_benchmarks_api_mixed_dataset_run_is_ineligible(client, db_session):
    """
    Test: If an evaluation run contains test cases from multiple datasets,
    its run-level throughput and peak telemetry cannot be cleanly attributed
    to a single dataset. It must be marked INELIGIBLE.
    """
    m = Model(id="mixed-run-model", name="mixed-run-model")
    ds1 = Dataset(name="Dataset 1")
    ds2 = Dataset(name="Dataset 2")
    db_session.add_all([m, ds1, ds2])
    db_session.commit()

    tc1 = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds1.id, prompt="Prompt 1")
    tc2 = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds2.id, prompt="Prompt 2")
    db_session.add_all([tc1, tc2])
    db_session.commit()

    # Single run that evaluated test cases from BOTH ds1 and ds2
    mixed_run = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id=m.id,
        status="COMPLETED",
        tokens_per_second_avg=75.0,
        peak_vram_mb=2100.0,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    db_session.add(mixed_run)
    db_session.commit()

    r1 = EvaluationResult(run_id=mixed_run.id, test_case_id=tc1.id, passed=True, score=1.0)
    r2 = EvaluationResult(run_id=mixed_run.id, test_case_id=tc2.id, passed=True, score=1.0)
    db_session.add_all([r1, r2])
    db_session.commit()

    payload = {
        "title": "Mixed Dataset Benchmark",
        "dataset_id": ds1.id,
        "model_ids": [m.id]
    }
    res = client.post("/api/v1/benchmarks", json=payload)
    assert res.status_code == 202
    data = res.json()["data"]

    score = data["results"][0]
    assert score["status"] == "INELIGIBLE"
    assert score["accuracy_score"] is None
    assert score["speed_tokens_sec"] is None
    assert len(data["pareto_frontier"]) == 0


def test_generation_config_persistence_through_evaluations_api(client, db_session):
    """
    Test: Generation configuration provenance (temperature, num_predict, num_ctx, concurrency)
    is persisted directly on EvaluationRun at submission time.
    """
    m = Model(id="gen-config-model", name="gen-config-model")
    ds = Dataset(name="Gen Config Dataset")
    db_session.add_all([m, ds])
    db_session.commit()

    tc = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds.id, prompt="Prompt")
    db_session.add(tc)
    db_session.commit()

    payload = {
        "model_id": m.id,
        "dataset_id": ds.id,
        "temperature": 0.7,
        "num_predict": 128,
        "num_ctx": 4096,
        "concurrency": 2,
        "priority": 15
    }
    res = client.post("/api/v1/evaluations", json=payload)
    assert res.status_code == 202
    run_data = res.json()["data"]
    run_id = run_data["id"]

    assert run_data["dataset_id"] == ds.id
    assert run_data["temperature"] == 0.7
    assert run_data["num_predict"] == 128
    assert run_data["num_ctx"] == 4096
    assert run_data["concurrency"] == 2

    # Query DB directly to confirm persistence
    run_in_db = db_session.query(EvaluationRun).filter_by(id=run_id).first()
    assert run_in_db.dataset_id == ds.id
    assert run_in_db.temperature == 0.7
    assert run_in_db.num_predict == 128
    assert run_in_db.num_ctx == 4096
    assert run_in_db.concurrency == 2


def test_database_migration_preserves_existing_data_and_creates_indexes():
    """
    Test: Database migration uses ALTER TABLE non-destructively to add new provenance
    and telemetry columns, creates declared indexes, and preserves all existing rows.
    """
    test_db_url = "sqlite:///:memory:"
    mem_engine = create_engine(test_db_url)

    with mem_engine.connect() as conn:
        # Create datasets table first
        conn.execute(text("""
            CREATE TABLE datasets (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
        """))
        # Create legacy table without new columns
        conn.execute(text("""
            CREATE TABLE evaluation_runs (
                id VARCHAR(36) PRIMARY KEY,
                model_id VARCHAR(64) NOT NULL,
                status VARCHAR(20) DEFAULT 'QUEUED'
            )
        """))
        conn.execute(text("""
            INSERT INTO evaluation_runs (id, model_id, status)
            VALUES ('legacy-run-1', 'llama3.2:latest', 'COMPLETED')
        """))
        conn.execute(text("""
            CREATE TABLE benchmark_reports (
                id VARCHAR(36) PRIMARY KEY,
                title VARCHAR(120) NOT NULL,
                model_ids JSON NOT NULL
            )
        """))
        conn.execute(text("""
            INSERT INTO benchmark_reports (id, title, model_ids)
            VALUES ('legacy-rep-1', 'Legacy Report', '["llama3.2:latest"]')
        """))
        conn.execute(text("""
            CREATE TABLE benchmark_results (
                id VARCHAR(36) PRIMARY KEY,
                report_id VARCHAR(36) NOT NULL,
                model_id VARCHAR(64) NOT NULL
            )
        """))
        conn.commit()

    # Run migration (multiple times to test idempotency)
    migrate_schema(mem_engine)
    migrate_schema(mem_engine)

    with mem_engine.connect() as conn:
        # Verify existing data is preserved
        row = conn.execute(text("SELECT id, model_id, status, dataset_id, temperature FROM evaluation_runs WHERE id = 'legacy-run-1'")).fetchone()
        assert row is not None
        assert row[0] == "legacy-run-1"
        assert row[1] == "llama3.2:latest"
        assert row[2] == "COMPLETED"
        assert row[3] is None  # newly added column is present and defaults to None
        assert row[4] is None

        rep_row = conn.execute(text("SELECT id, title, dataset_id, generation_config FROM benchmark_reports WHERE id = 'legacy-rep-1'")).fetchone()
        assert rep_row is not None
        assert rep_row[0] == "legacy-rep-1"
        assert rep_row[1] == "Legacy Report"
        assert rep_row[2] is None
        assert rep_row[3] is None

    # Inspect indexes
    inspector = inspect(mem_engine)
    indexes_eval = {idx["name"] for idx in inspector.get_indexes("evaluation_runs")}
    assert "ix_evaluation_runs_dataset_id" in indexes_eval

    indexes_rep = {idx["name"] for idx in inspector.get_indexes("benchmark_reports")}
    assert "ix_benchmark_reports_dataset_id" in indexes_rep

    indexes_res = {idx["name"] for idx in inspector.get_indexes("benchmark_results")}
    assert "ix_benchmark_results_run_id" in indexes_res


def test_benchmarks_api_deterministic_tie_breaking(client, db_session):
    """
    Test: When multiple eligible runs for the same model share identical completed_at timestamps,
    _find_eligible_run deterministically selects the latest run using the unique secondary key (id).
    """
    from datetime import datetime
    fixed_time = datetime(2026, 11, 23, 12, 0, 0)

    m = Model(id="tie-model", name="tie-model")
    ds = Dataset(name="Tie-Breaker Suite")
    db_session.add_all([m, ds])
    db_session.commit()

    tc = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds.id, prompt="Prompt")
    db_session.add(tc)
    db_session.commit()

    # Two runs with identical completed_at timestamps, but different IDs
    run_a = EvaluationRun(
        id="run-aaa-111",
        model_id=m.id,
        dataset_id=ds.id,
        status="COMPLETED",
        tokens_per_second_avg=60.0,
        peak_vram_mb=2100.0,
        completed_at=fixed_time,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    run_b = EvaluationRun(
        id="run-zzz-999",  # higher lexicographical ID
        model_id=m.id,
        dataset_id=ds.id,
        status="COMPLETED",
        tokens_per_second_avg=90.0,
        peak_vram_mb=2100.0,
        completed_at=fixed_time,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    db_session.add_all([run_a, run_b])
    db_session.commit()

    res_a = EvaluationResult(run_id=run_a.id, test_case_id=tc.id, passed=True, score=1.0)
    res_b = EvaluationResult(run_id=run_b.id, test_case_id=tc.id, passed=True, score=1.0)
    db_session.add_all([res_a, res_b])
    db_session.commit()

    payload = {
        "title": "Tie Breaker Benchmark",
        "dataset_id": ds.id,
        "model_ids": [m.id],
        "temperature": 0.1,
        "num_predict": 256,
        "num_ctx": 2048,
        "concurrency": 1
    }
    res = client.post("/api/v1/benchmarks", json=payload)
    assert res.status_code == 202
    data = res.json()["data"]

    # Deterministic secondary key order: EvaluationRun.id.desc() selects run-zzz-999
    score = data["results"][0]
    assert score["run_id"] == "run-zzz-999"
    assert score["speed_tokens_sec"] == 90.0


def test_benchmarks_api_hardware_provenance_exposure(client, db_session):
    """
    Test: Hardware provenance (gpu_name, gpu_source) is stored in Metric details,
    propagated to BenchmarkResult, and exposed in API responses without breaking schema.
    Missing GPU telemetry remains None and is never fabricated as zero.
    """
    m = Model(id="hw-prov-model", name="hw-prov-model")
    ds = Dataset(name="Hardware Provenance Suite")
    db_session.add_all([m, ds])
    db_session.commit()

    tc = DatasetTestCase(id=str(uuid.uuid4()), dataset_id=ds.id, prompt="Prompt")
    db_session.add(tc)
    db_session.commit()

    run = EvaluationRun(
        id=str(uuid.uuid4()),
        model_id=m.id,
        dataset_id=ds.id,
        status="COMPLETED",
        tokens_per_second_avg=72.5,
        peak_vram_mb=3962.0,
        temperature=0.1,
        num_predict=256,
        num_ctx=2048,
        concurrency=1
    )
    db_session.add(run)
    db_session.commit()

    eval_res = EvaluationResult(run_id=run.id, test_case_id=tc.id, passed=True, score=1.0)
    # Metric with hardware provenance details
    vram_metric = Metric(
        run_id=run.id,
        metric_name="avg_vram_mb",
        metric_value=3900.0,
        details={
            "gpu_name": "NVIDIA GeForce RTX 3050 Laptop GPU",
            "source": "nvidia-smi",
            "sample_count": 12
        }
    )
    ollama_metric = Metric(
        run_id=run.id,
        metric_name="peak_ollama_vram_mb",
        metric_value=2238.0
    )
    db_session.add_all([eval_res, vram_metric, ollama_metric])
    db_session.commit()

    payload = {
        "title": "Hardware Provenance Benchmark",
        "dataset_id": ds.id,
        "model_ids": [m.id],
        "temperature": 0.1,
        "num_predict": 256,
        "num_ctx": 2048,
        "concurrency": 1
    }
    create_res = client.post("/api/v1/benchmarks", json=payload)
    assert create_res.status_code == 202
    data = create_res.json()["data"]

    score = data["results"][0]
    assert score["gpu_name"] == "NVIDIA GeForce RTX 3050 Laptop GPU"
    assert score["gpu_source"] == "nvidia-smi"
    assert score["peak_vram_mb"] == 3962.0
    assert score["peak_ollama_vram_mb"] == 2238.0

    # Also verify detail GET endpoint returns the hardware provenance
    get_res = client.get(f"/api/v1/benchmarks/{data['id']}")
    assert get_res.status_code == 200
    detail_score = get_res.json()["data"]["results"][0]
    assert detail_score["gpu_name"] == "NVIDIA GeForce RTX 3050 Laptop GPU"
    assert detail_score["gpu_source"] == "nvidia-smi"

