import asyncio
import logging
from datetime import datetime
from backend.app.core.queue import execution_queue
from backend.app.core.hardware_gate import HardwareGate
from backend.app.services.ollama_service import ollama_service
from backend.app.services.promptfoo_service import promptfoo_service
from backend.app.services.result_parser import result_parser
from backend.app.services.hardware_monitor import hardware_monitor
from backend.app.db.session import SessionLocal
from backend.app.db.models.evaluation import EvaluationRun, EvaluationResult
from backend.app.db.models.dataset import Dataset
from backend.app.db.models.metric import Metric

logger = logging.getLogger(__name__)

class ExecutionWorker:
    """
    Background worker processing evaluation runs sequentially.
    Enforces hardware safety gates, single-model Ollama isolation,
    Promptfoo subprocess execution, and database persistence.
    """

    def __init__(self):
        self.gate = HardwareGate()
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Starts the worker loop in the background."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("ExecutionWorker background task started.")

    async def stop(self):
        """Gracefully halts the background worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ExecutionWorker background task stopped.")

    async def _run_loop(self):
        while self._running:
            try:
                item = await execution_queue.dequeue()
                run_id = item.run_id
                logger.info("Worker picked up evaluation run: %s", run_id)

                db = SessionLocal()
                try:
                    run = db.query(EvaluationRun).filter_by(id=run_id).first()
                    if not run:
                        logger.error("Run %s not found in database.", run_id)
                        await execution_queue.task_done()
                        continue

                    # Update status to RUNNING
                    run.status = "RUNNING"
                    run.started_at = datetime.utcnow()
                    db.commit()

                    # 1. Pre-Flight Hardware Gate
                    allowed, reason, telemetry = self.gate.check_preflight()
                    if not allowed:
                        run.status = "FAILED"
                        run.error_message = f"Hardware Pre-Flight Rejected: {reason}"
                        run.completed_at = datetime.utcnow()
                        db.commit()
                        logger.warning("Run %s aborted due to hardware constraints: %s", run_id, reason)
                        await execution_queue.task_done()
                        continue

                    # 2. Retrieve Dataset & Test Cases
                    dataset_id = item.payload.get("dataset_id")
                    dataset = db.query(Dataset).filter_by(id=dataset_id).first()
                    if not dataset or not dataset.test_cases:
                        run.status = "FAILED"
                        run.error_message = "Dataset has no test cases configured."
                        run.completed_at = datetime.utcnow()
                        db.commit()
                        await execution_queue.task_done()
                        continue

                    test_cases = [
                        {
                            "id": tc.id,
                            "prompt": tc.prompt,
                            "expected_output": tc.expected_output,
                            "assertions": tc.assertions
                        }
                        for tc in dataset.test_cases
                    ]
                    test_case_ids = [tc["id"] for tc in test_cases]

                    # 3. Model Switch Protocol: Ensure only target model is loaded in Ollama
                    await ollama_service.ensure_single_model(run.model_id)

                    # 4. Generate Promptfoo Configuration
                    config_path = promptfoo_service.generate_config_file(
                        run_id=run_id,
                        model_id=run.model_id,
                        test_cases=test_cases,
                        temperature=item.payload.get("temperature", 0.1),
                        num_predict=item.payload.get("num_predict", 256),
                        num_ctx=item.payload.get("num_ctx", 2048)
                    )

                    # 5. Execute Promptfoo Subprocess
                    exit_code, stderr_output, json_output_path = await promptfoo_service.run_evaluation(
                        run_id=run_id,
                        config_path=config_path,
                        concurrency=item.payload.get("concurrency", 1)
                    )

                    # Sample peak telemetry
                    final_telemetry = hardware_monitor.sample_telemetry()
                    peak_ram = final_telemetry["ram"]["total_mb"] - final_telemetry["ram"]["free_mb"]
                    peak_vram = final_telemetry.get("gpu", {}).get("allocated_mb", 0.0)

                    # 6. Parse Results and Persist
                    parsed = result_parser.parse_promptfoo_output(
                        run_id=run_id,
                        json_path=json_output_path,
                        test_case_ids=test_case_ids
                    )

                    # Insert individual test results
                    for res_item in parsed["results"]:
                        eval_res = EvaluationResult(
                            run_id=run_id,
                            test_case_id=res_item["test_case_id"],
                            passed=res_item["passed"],
                            score=res_item["score"],
                            latency_ms=res_item["latency_ms"],
                            prompt_tokens=res_item["prompt_tokens"],
                            completion_tokens=res_item["completion_tokens"],
                            jsonl_line_index=res_item["jsonl_line_index"]
                        )
                        db.add(eval_res)

                    # Insert summary metrics
                    db.add(Metric(run_id=run_id, metric_name="accuracy_rate", metric_value=parsed["accuracy_rate"]))
                    db.add(Metric(run_id=run_id, metric_name="avg_latency_ms", metric_value=parsed["avg_latency_ms"]))
                    db.add(Metric(run_id=run_id, metric_name="tokens_per_second", metric_value=parsed["tokens_per_sec"]))

                    # Update Run record
                    run.status = "COMPLETED"
                    run.completed_at = datetime.utcnow()
                    run.total_duration_seconds = (run.completed_at - run.started_at).total_seconds()
                    run.tokens_per_second_avg = parsed["tokens_per_sec"]
                    run.peak_vram_mb = peak_vram
                    run.peak_ram_mb = peak_ram
                    run.result_artifact_path = parsed["jsonl_artifact_path"]

                    db.commit()
                    logger.info("Run %s COMPLETED successfully in %.2fs", run_id, run.total_duration_seconds)

                except Exception as e:
                    logger.error("Error executing run %s: %s", run_id, e, exc_info=True)
                    try:
                        run = db.query(EvaluationRun).filter_by(id=run_id).first()
                        if run:
                            run.status = "FAILED"
                            run.error_message = str(e)
                            run.completed_at = datetime.utcnow()
                            db.commit()
                    except Exception:
                        pass
                finally:
                    db.close()
                    await execution_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Unhandled error in execution worker loop: %s", e, exc_info=True)
                await asyncio.sleep(1.0)

execution_worker = ExecutionWorker()
