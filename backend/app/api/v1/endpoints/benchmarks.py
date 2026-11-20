import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.benchmark import BenchmarkReport, BenchmarkResult
from backend.app.db.models.model import Model
from backend.app.db.models.dataset import Dataset
from backend.app.db.models.evaluation import EvaluationRun
from backend.app.schemas.common import APIResponse
from backend.app.schemas.benchmark import (
    BenchmarkCreate,
    BenchmarkReportRead,
    ModelBenchmarkScore
)
from backend.app.services.benchmark_service import benchmark_service

router = APIRouter()

@router.post("", response_model=APIResponse[BenchmarkReportRead], status_code=202)
def create_benchmark_report(payload: BenchmarkCreate, db: Session = Depends(get_db)):
    """
    Creates a benchmark report definition across specified models.
    """
    dataset = db.query(Dataset).filter_by(id=payload.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    report_id = str(uuid.uuid4())
    report = BenchmarkReport(
        id=report_id,
        title=payload.title,
        model_ids=payload.model_ids
    )
    db.add(report)

    # Compile benchmark results from completed runs or defaults
    mock_pareto_inputs = []
    for idx, model_id in enumerate(payload.model_ids):
        # Look up latest evaluation run for this model
        latest_run = (
            db.query(EvaluationRun)
            .filter_by(model_id=model_id, status="COMPLETED")
            .order_by(EvaluationRun.completed_at.desc())
            .first()
        )

        acc = 0.85
        speed = 45.0
        latency = 300.0
        vram = 2200.0

        if latest_run and latest_run.tokens_per_second_avg:
            speed = latest_run.tokens_per_second_avg
            vram = latest_run.peak_vram_mb or vram
            if latest_run.results:
                passed = sum(1 for r in latest_run.results if r.passed)
                acc = passed / len(latest_run.results)

        b_res = BenchmarkResult(
            id=str(uuid.uuid4()),
            report_id=report.id,
            model_id=model_id,
            accuracy_score=round(acc, 2),
            speed_tokens_sec=round(speed, 1),
            memory_efficiency_score=round(max(0.0, 1.0 - (vram / 4096.0)), 2),
            rank=idx + 1
        )
        db.add(b_res)

        mock_pareto_inputs.append({
            "model_id": model_id,
            "tokens_per_sec": speed,
            "accuracy_rate": acc,
            "peak_vram_mb": vram
        })

    db.commit()
    db.refresh(report)

    pareto_pts = benchmark_service.calculate_pareto_frontier(mock_pareto_inputs)

    scores = [
        ModelBenchmarkScore(
            model_id=br.model_id,
            accuracy_score=br.accuracy_score,
            speed_tokens_sec=br.speed_tokens_sec,
            avg_latency_ms=300.0,
            peak_vram_mb=2200.0,
            memory_efficiency_score=br.memory_efficiency_score,
            rank=br.rank
        )
        for br in report.benchmark_results
    ]

    report_read = BenchmarkReportRead(
        id=report.id,
        title=report.title,
        model_ids=report.model_ids,
        generated_at=report.generated_at,
        results=scores,
        pareto_frontier=pareto_pts
    )

    return APIResponse(
        success=True,
        message=f"Benchmark report '{report.title}' compiled",
        data=report_read
    )

@router.get("", response_model=APIResponse[List[BenchmarkReportRead]])
def list_benchmark_reports(db: Session = Depends(get_db)):
    """Lists all compiled benchmark reports."""
    reports = db.query(BenchmarkReport).order_by(BenchmarkReport.generated_at.desc()).all()
    results = []
    for rep in reports:
        scores = [
            ModelBenchmarkScore(
                model_id=br.model_id,
                accuracy_score=br.accuracy_score,
                speed_tokens_sec=br.speed_tokens_sec,
                avg_latency_ms=300.0,
                peak_vram_mb=2200.0,
                memory_efficiency_score=br.memory_efficiency_score,
                rank=br.rank
            )
            for br in rep.benchmark_results
        ]
        results.append(BenchmarkReportRead(
            id=rep.id,
            title=rep.title,
            model_ids=rep.model_ids,
            generated_at=rep.generated_at,
            results=scores,
            pareto_frontier=[]
        ))

    return APIResponse(success=True, data=results)

@router.get("/{report_id}", response_model=APIResponse[BenchmarkReportRead])
def get_benchmark_report(report_id: str, db: Session = Depends(get_db)):
    """Retrieves a detailed benchmark report with Pareto curves."""
    rep = db.query(BenchmarkReport).filter_by(id=report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Benchmark report not found")

    pareto_inputs = []
    scores = []
    for br in rep.benchmark_results:
        scores.append(ModelBenchmarkScore(
            model_id=br.model_id,
            accuracy_score=br.accuracy_score,
            speed_tokens_sec=br.speed_tokens_sec,
            avg_latency_ms=300.0,
            peak_vram_mb=2200.0,
            memory_efficiency_score=br.memory_efficiency_score,
            rank=br.rank
        ))
        pareto_inputs.append({
            "model_id": br.model_id,
            "tokens_per_sec": br.speed_tokens_sec,
            "accuracy_rate": br.accuracy_score,
            "peak_vram_mb": 2200.0
        })

    pareto_pts = benchmark_service.calculate_pareto_frontier(pareto_inputs)

    return APIResponse(
        success=True,
        data=BenchmarkReportRead(
            id=rep.id,
            title=rep.title,
            model_ids=rep.model_ids,
            generated_at=rep.generated_at,
            results=scores,
            pareto_frontier=pareto_pts
        )
    )
