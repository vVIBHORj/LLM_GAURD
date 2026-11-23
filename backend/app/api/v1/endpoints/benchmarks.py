import uuid
from typing import List, Optional, Tuple, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.benchmark import BenchmarkReport, BenchmarkResult
from backend.app.db.models.dataset import Dataset, DatasetTestCase
from backend.app.db.models.evaluation import EvaluationRun
from backend.app.schemas.common import APIResponse
from backend.app.schemas.benchmark import (
    BenchmarkCreate,
    BenchmarkReportRead,
    ModelBenchmarkScore,
    ParetoPoint
)
from backend.app.services.benchmark_service import benchmark_service

router = APIRouter()

def _find_eligible_run(
    model_id: str,
    target_dataset_id: str,
    target_gen_config: Dict[str, Any],
    db: Session
) -> Tuple[Optional[EvaluationRun], str]:
    """
    Finds the latest valid completed evaluation run for a model and target dataset
    that strictly satisfies configuration equivalence:
    - Verifies that all test cases evaluated in the run belong to target_dataset_id.
    - If a run evaluated test cases spanning multiple datasets, it is marked INELIGIBLE.
    - Historical runs without verifiable provenance or generation settings are marked INELIGIBLE.
    - Runs whose generation settings (temperature, num_predict, num_ctx, concurrency) do not match
      the target benchmark specification are rejected from comparison.
    """
    runs = (
        db.query(EvaluationRun)
        .filter_by(model_id=model_id, status="COMPLETED")
        .order_by(EvaluationRun.completed_at.desc(), EvaluationRun.id.desc())
        .all()
    )

    has_mixed_run = False
    has_config_mismatch = False
    has_unverified_run = False

    for run in runs:
        if not run.results:
            continue

        test_case_ids = [r.test_case_id for r in run.results if r.test_case_id]
        if not test_case_ids:
            continue

        # Check distinct datasets for the evaluated test cases
        dataset_rows = (
            db.query(DatasetTestCase.dataset_id)
            .filter(DatasetTestCase.id.in_(test_case_ids))
            .distinct()
            .all()
        )
        dataset_ids = {row[0] for row in dataset_rows if row[0]}

        if len(dataset_ids) > 1:
            # Run evaluated test cases from multiple datasets; cannot attribute throughput/telemetry to one dataset
            has_mixed_run = True
            continue

        if len(dataset_ids) == 1:
            evaluated_dataset_id = next(iter(dataset_ids))
            if evaluated_dataset_id != target_dataset_id:
                continue

            # If run.dataset_id is explicitly set and conflicts, skip
            if run.dataset_id is not None and run.dataset_id != target_dataset_id:
                continue

            # Validate generation configuration equivalence
            if (
                run.temperature is None
                or run.num_predict is None
                or run.num_ctx is None
                or run.concurrency is None
            ):
                has_unverified_run = True
                continue

            temp_match = abs(run.temperature - target_gen_config.get("temperature", 0.1)) < 1e-4
            predict_match = run.num_predict == target_gen_config.get("num_predict", 256)
            ctx_match = run.num_ctx == target_gen_config.get("num_ctx", 2048)
            concurrency_match = run.concurrency == target_gen_config.get("concurrency", 1)

            if not (temp_match and predict_match and ctx_match and concurrency_match):
                has_config_mismatch = True
                continue

            if run.tokens_per_second_avg is not None:
                return run, "BENCHMARKED"

    if has_mixed_run or has_config_mismatch or has_unverified_run:
        return None, "INELIGIBLE"

    return None, "UNBENCHMARKED"


def _build_pareto_frontier_from_results(benchmark_results: List[BenchmarkResult]) -> List[ParetoPoint]:
    """Builds the empirical Pareto frontier from completed benchmark results."""
    pareto_inputs = []
    for br in benchmark_results:
        if (
            br.status == "BENCHMARKED"
            and br.speed_tokens_sec is not None
            and br.accuracy_score is not None
            and br.peak_vram_mb is not None
        ):
            pareto_inputs.append({
                "model_id": br.model_id,
                "run_id": br.run_id,
                "tokens_per_sec": br.speed_tokens_sec,
                "accuracy_rate": br.accuracy_score,
                "peak_vram_mb": br.peak_vram_mb
            })

    if not pareto_inputs:
        return []
    return benchmark_service.calculate_pareto_frontier(pareto_inputs)


@router.post("", response_model=APIResponse[BenchmarkReportRead], status_code=202)
def create_benchmark_report(payload: BenchmarkCreate, db: Session = Depends(get_db)):
    """
    Creates a benchmark report definition across specified models for a specific dataset.
    Enforces dataset isolation and removes synthetic fallback values.
    """
    dataset = db.query(Dataset).filter_by(id=payload.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    gen_config = {
        "temperature": payload.temperature,
        "num_predict": payload.num_predict,
        "num_ctx": payload.num_ctx,
        "concurrency": payload.concurrency
    }

    report_id = str(uuid.uuid4())
    report = BenchmarkReport(
        id=report_id,
        title=payload.title,
        dataset_id=payload.dataset_id,
        model_ids=payload.model_ids,
        generation_config=gen_config
    )
    db.add(report)

    benchmarked_items = []
    unbenchmarked_items = []

    for model_id in payload.model_ids:
        eligible_run, status = _find_eligible_run(
            model_id=model_id,
            target_dataset_id=payload.dataset_id,
            target_gen_config=gen_config,
            db=db
        )

        if eligible_run and status == "BENCHMARKED":
            # Extract actual measured metrics
            passed = sum(1 for r in eligible_run.results if r.passed)
            acc = round(passed / len(eligible_run.results), 4) if eligible_run.results else None
            speed = round(eligible_run.tokens_per_second_avg, 1) if eligible_run.tokens_per_second_avg is not None else None
            vram = round(eligible_run.peak_vram_mb, 1) if eligible_run.peak_vram_mb is not None else None

            # Retrieve auxiliary hardware telemetry from Metric table
            metrics_dict = {m.metric_name: m.metric_value for m in eligible_run.metrics}
            latency = metrics_dict.get("avg_latency_ms")
            if latency is None and eligible_run.results:
                latencies = [r.latency_ms for r in eligible_run.results if r.latency_ms is not None and r.latency_ms > 0]
                if latencies:
                    latency = sum(latencies) / len(latencies)
            latency = round(latency, 1) if (latency is not None and latency > 0) else None
            ollama_vram = metrics_dict.get("peak_ollama_vram_mb")
            ollama_vram = round(ollama_vram, 1) if ollama_vram is not None else None

            # Retrieve GPU hardware provenance from metric details
            vram_metric = next((m for m in eligible_run.metrics if m.metric_name in ("avg_vram_mb", "peak_vram_mb") and m.details), None)
            gpu_name = vram_metric.details.get("gpu_name") if vram_metric and vram_metric.details else None
            gpu_source = vram_metric.details.get("source") if vram_metric and vram_metric.details else None

            mem_eff = round(max(0.0, 1.0 - (vram / 4096.0)), 3) if vram is not None else None

            b_res = BenchmarkResult(
                id=str(uuid.uuid4()),
                report_id=report.id,
                model_id=model_id,
                run_id=eligible_run.id,
                status="BENCHMARKED",
                accuracy_score=acc,
                speed_tokens_sec=speed,
                avg_latency_ms=latency,
                peak_vram_mb=vram,
                peak_ollama_vram_mb=ollama_vram,
                gpu_name=gpu_name,
                gpu_source=gpu_source,
                memory_efficiency_score=mem_eff,
                rank=1
            )
            benchmarked_items.append((b_res, (acc or 0.0) * 0.5 + ((speed or 0.0) / 100.0) * 0.5))
        else:
            # Model has no eligible run; do NOT invent synthetic metrics
            b_res = BenchmarkResult(
                id=str(uuid.uuid4()),
                report_id=report.id,
                model_id=model_id,
                run_id=None,
                status=status,
                accuracy_score=None,
                speed_tokens_sec=None,
                avg_latency_ms=None,
                peak_vram_mb=None,
                peak_ollama_vram_mb=None,
                gpu_name=None,
                gpu_source=None,
                memory_efficiency_score=None,
                rank=None
            )
            unbenchmarked_items.append(b_res)

    # Rank measured models by composite score descending
    benchmarked_items.sort(key=lambda x: x[1], reverse=True)
    all_results = []
    for idx, (res, _) in enumerate(benchmarked_items):
        res.rank = idx + 1
        db.add(res)
        all_results.append(res)

    for res in unbenchmarked_items:
        db.add(res)
        all_results.append(res)

    db.commit()
    db.refresh(report)

    pareto_pts = _build_pareto_frontier_from_results(all_results)

    scores = [
        ModelBenchmarkScore(
            model_id=br.model_id,
            run_id=br.run_id,
            status=br.status,
            accuracy_score=br.accuracy_score,
            speed_tokens_sec=br.speed_tokens_sec,
            avg_latency_ms=br.avg_latency_ms,
            peak_vram_mb=br.peak_vram_mb,
            peak_ollama_vram_mb=br.peak_ollama_vram_mb,
            gpu_name=br.gpu_name,
            gpu_source=br.gpu_source,
            memory_efficiency_score=br.memory_efficiency_score,
            rank=br.rank
        )
        for br in all_results
    ]

    report_read = BenchmarkReportRead(
        id=report.id,
        title=report.title,
        dataset_id=report.dataset_id,
        model_ids=report.model_ids,
        generation_config=report.generation_config,
        generated_at=report.generated_at,
        results=scores,
        pareto_frontier=pareto_pts
    )

    return APIResponse(
        success=True,
        message=f"Benchmark report '{report.title}' compiled with empirical metrics",
        data=report_read
    )


@router.get("", response_model=APIResponse[List[BenchmarkReportRead]])
def list_benchmark_reports(dataset_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Lists compiled benchmark reports with optional dataset filtering."""
    query = db.query(BenchmarkReport)
    if dataset_id:
        query = query.filter(BenchmarkReport.dataset_id == dataset_id)

    reports = query.order_by(BenchmarkReport.generated_at.desc()).all()
    results = []
    for rep in reports:
        scores = [
            ModelBenchmarkScore(
                model_id=br.model_id,
                run_id=br.run_id,
                status=br.status,
                accuracy_score=br.accuracy_score,
                speed_tokens_sec=br.speed_tokens_sec,
                avg_latency_ms=br.avg_latency_ms,
                peak_vram_mb=br.peak_vram_mb,
                peak_ollama_vram_mb=br.peak_ollama_vram_mb,
                gpu_name=br.gpu_name,
                gpu_source=br.gpu_source,
                memory_efficiency_score=br.memory_efficiency_score,
                rank=br.rank
            )
            for br in rep.benchmark_results
        ]
        pareto_pts = _build_pareto_frontier_from_results(rep.benchmark_results)
        results.append(BenchmarkReportRead(
            id=rep.id,
            title=rep.title,
            dataset_id=rep.dataset_id,
            model_ids=rep.model_ids,
            generation_config=rep.generation_config,
            generated_at=rep.generated_at,
            results=scores,
            pareto_frontier=pareto_pts
        ))

    return APIResponse(success=True, data=results)


@router.get("/{report_id}", response_model=APIResponse[BenchmarkReportRead])
def get_benchmark_report(report_id: str, db: Session = Depends(get_db)):
    """Retrieves a detailed benchmark report with live empirical Pareto curves."""
    rep = db.query(BenchmarkReport).filter_by(id=report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Benchmark report not found")

    scores = [
        ModelBenchmarkScore(
            model_id=br.model_id,
            run_id=br.run_id,
            status=br.status,
            accuracy_score=br.accuracy_score,
            speed_tokens_sec=br.speed_tokens_sec,
            avg_latency_ms=br.avg_latency_ms,
            peak_vram_mb=br.peak_vram_mb,
            peak_ollama_vram_mb=br.peak_ollama_vram_mb,
            gpu_name=br.gpu_name,
            gpu_source=br.gpu_source,
            memory_efficiency_score=br.memory_efficiency_score,
            rank=br.rank
        )
        for br in rep.benchmark_results
    ]
    pareto_pts = _build_pareto_frontier_from_results(rep.benchmark_results)

    return APIResponse(
        success=True,
        data=BenchmarkReportRead(
            id=rep.id,
            title=rep.title,
            dataset_id=rep.dataset_id,
            model_ids=rep.model_ids,
            generation_config=rep.generation_config,
            generated_at=rep.generated_at,
            results=scores,
            pareto_frontier=pareto_pts
        )
    )
