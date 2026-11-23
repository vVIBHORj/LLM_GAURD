from backend.app.db.models.model import Model
from backend.app.db.models.dataset import Dataset, DatasetTestCase
from backend.app.db.models.experiment import Experiment
from backend.app.db.models.evaluation import EvaluationRun
from backend.app.db.models.metric import Metric
from backend.app.db.models.security import SecurityTest

def test_db_entities_lifecycle(db_session):
    # 1. Model
    model = Model(
        id="llama3.2:latest",
        name="llama3.2:latest",
        family="llama",
        parameter_size="3B",
        quantization="Q4_K_M",
        context_window_default=2048,
        disk_size_bytes=2000000000,
        is_available=True
    )
    db_session.add(model)
    db_session.commit()

    # 2. Dataset & TestCase
    dataset = Dataset(name="Instruction Suite", task_type="general", version=1)
    db_session.add(dataset)
    db_session.commit()

    test_case = DatasetTestCase(
        dataset_id=dataset.id,
        prompt="Write a Python function to reverse a list.",
        expected_output="def reverse_list(l): return l[::-1]",
        assertions={"type": "contains", "value": "return"}
    )
    db_session.add(test_case)
    db_session.commit()

    # 3. Experiment
    exp = Experiment(name="Llama Baseline", dataset_id=dataset.id, status="PENDING")
    db_session.add(exp)
    db_session.commit()

    # 4. EvaluationRun
    run = EvaluationRun(
        experiment_id=exp.id,
        model_id=model.id,
        status="COMPLETED",
        total_duration_seconds=12.5,
        tokens_per_second_avg=104.2,
        peak_vram_mb=2238.9
    )
    db_session.add(run)
    db_session.commit()

    # 5. Metric
    metric = Metric(run_id=run.id, metric_name="accuracy", metric_value=0.95)
    db_session.add(metric)

    # 6. SecurityTest
    sec = SecurityTest(run_id=run.id, category="injection", defended=True, risk_level="LOW", attack_vector="DAN jailbreak")
    db_session.add(sec)
    db_session.commit()

    # Verify query
    saved_model = db_session.query(Model).filter_by(id="llama3.2:latest").first()
    assert saved_model is not None
    assert len(saved_model.evaluation_runs) == 1
    assert saved_model.evaluation_runs[0].metrics[0].metric_name == "accuracy"
    assert saved_model.evaluation_runs[0].security_tests[0].defended is True
