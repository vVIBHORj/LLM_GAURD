import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.evaluation import EvaluationRun, EvaluationResult
from backend.app.db.models.model import Model
from backend.app.db.models.dataset import Dataset
from backend.app.db.models.metric import Metric
from backend.app.core.queue import execution_queue
from backend.app.schemas.common import APIResponse
from backend.app.schemas.evaluation import (
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationResultRead,
    RunProgress,
    MetricRead
)
from backend.app.services.jsonl_storage import jsonl_storage

router = APIRouter()

@router.post("", response_model=APIResponse[EvaluationRunRead], status_code=202)
async def submit_evaluation_run(payload: EvaluationRunCreate, db: Session = Depends(get_db)):
    """
    Submits an evaluation run to the sequential queue.
    Validates model and dataset existence.
    """
    model = db.query(Model).filter_by(id=payload.model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{payload.model_id}' is not registered.")

    dataset = db.query(Dataset).filter_by(id=payload.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if not dataset.test_cases:
        raise HTTPException(status_code=400, detail="Cannot evaluate an empty dataset.")

    run_id = str(uuid.uuid4())
    run = EvaluationRun(
        id=run_id,
        model_id=payload.model_id,
        status="QUEUED"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Enqueue to background worker
    queue_payload = {
        "model_id": payload.model_id,
        "dataset_id": payload.dataset_id,
        "temperature": payload.temperature,
        "num_predict": payload.num_predict,
        "num_ctx": payload.num_ctx,
        "concurrency": payload.concurrency
    }
    await execution_queue.enqueue(run_id=run_id, payload=queue_payload, priority=payload.priority)

    run_read = EvaluationRunRead.model_validate(run)
    return APIResponse(
        success=True,
        message=f"Evaluation run {run_id} enqueued successfully",
        data=run_read
    )

@router.get("", response_model=APIResponse[List[EvaluationRunRead]])
def list_evaluation_runs(db: Session = Depends(get_db)):
    """Lists recent evaluation runs."""
    runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(50).all()
    results = []
    for r in runs:
        item = EvaluationRunRead.model_validate(r)
        if r.results:
            passed = sum(1 for res in r.results if res.passed)
            item.progress = RunProgress(
                total_tests=len(r.results),
                completed_tests=len(r.results),
                passed_tests=passed,
                failed_tests=len(r.results) - passed
            )
        results.append(item)

    return APIResponse(success=True, data=results)

@router.get("/{run_id}", response_model=APIResponse[EvaluationRunRead])
def get_evaluation_run(run_id: str, db: Session = Depends(get_db)):
    """Retrieves status, execution metadata, and summary metrics for a run."""
    run = db.query(EvaluationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")

    run_read = EvaluationRunRead.model_validate(run)
    if run.results:
        passed = sum(1 for res in run.results if res.passed)
        run_read.progress = RunProgress(
            total_tests=len(run.results),
            completed_tests=len(run.results),
            passed_tests=passed,
            failed_tests=len(run.results) - passed
        )
    run_read.metrics = [MetricRead.model_validate(m) for m in run.metrics]

    return APIResponse(success=True, data=run_read)

@router.get("/{run_id}/results", response_model=APIResponse[List[EvaluationResultRead]])
def get_run_results(
    run_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Retrieves paginated test results for a run, enriching with raw completions
    from the corresponding JSONL artifact.
    """
    run = db.query(EvaluationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")

    results_query = (
        db.query(EvaluationResult)
        .filter_by(run_id=run_id)
        .order_by(EvaluationResult.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    enriched_results: List[EvaluationResultRead] = []
    jsonl_path = run.result_artifact_path

    for r in results_query:
        item = EvaluationResultRead.model_validate(r)
        if jsonl_path and r.jsonl_line_index is not None:
            raw_record = jsonl_storage.read_line(jsonl_path, r.jsonl_line_index)
            if raw_record:
                item.raw_output = raw_record.get("raw_output")
                vars_dict = raw_record.get("vars", {})
                item.prompt_text = vars_dict.get("prompt")
        enriched_results.append(item)

    return APIResponse(
        success=True,
        message=f"Fetched {len(enriched_results)} results for run {run_id}",
        data=enriched_results
    )
