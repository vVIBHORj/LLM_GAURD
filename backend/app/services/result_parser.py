import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.services.jsonl_storage import jsonl_storage
from backend.app.config import settings

logger = logging.getLogger(__name__)

class ResultParser:
    """
    Parses raw Promptfoo JSON outputs, streams detailed traces into
    append-only JSONL files, and extracts normalized evaluation records.
    """

    @staticmethod
    def parse_promptfoo_output(
        run_id: str,
        json_path: Path,
        test_case_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Parses output JSON from Promptfoo and returns normalized evaluation items and summary metrics.
        """
        if not json_path.exists():
            raise FileNotFoundError(f"Promptfoo output file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        results_data = raw_data.get("results", raw_data)
        table = results_data.get("table", {})
        body = table.get("body", [])
        stats = results_data.get("stats", {})

        jsonl_artifact_path = settings.PROMPTFOO_RUNS_DIR / f"{run_id}.jsonl"

        parsed_results = []
        total_latency_ms = 0.0
        total_completion_tokens = 0
        total_prompt_tokens = 0
        passed_count = 0

        for row_idx, row in enumerate(body):
            outputs = row.get("outputs", [])
            output_entry = outputs[0] if outputs else {}

            passed = bool(output_entry.get("pass", False))
            score = float(output_entry.get("score", 1.0 if passed else 0.0))
            raw_text = str(output_entry.get("text", ""))
            latency_ms = float(output_entry.get("latencyMs", 0.0))

            token_usage = output_entry.get("tokenUsage", {})
            prompt_tokens = token_usage.get("prompt", 0)
            comp_tokens = token_usage.get("completion", 0)

            total_latency_ms += latency_ms
            total_completion_tokens += comp_tokens
            total_prompt_tokens += prompt_tokens
            if passed:
                passed_count += 1

            test_case_id = test_case_ids[row_idx] if test_case_ids and row_idx < len(test_case_ids) else None

            # Stream detailed trace to JSONL
            jsonl_record = {
                "run_id": run_id,
                "row_index": row_idx,
                "test_case_id": test_case_id,
                "vars": row.get("vars", {}),
                "raw_output": raw_text,
                "passed": passed,
                "score": score,
                "latency_ms": latency_ms,
                "grading": output_entry.get("gradingResult")
            }
            line_idx = jsonl_storage.append_record(jsonl_artifact_path, jsonl_record)

            parsed_results.append({
                "test_case_id": test_case_id,
                "passed": passed,
                "score": score,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": comp_tokens,
                "jsonl_line_index": line_idx
            })

        total_tests = len(body)
        avg_latency_ms = (total_latency_ms / total_tests) if total_tests > 0 else 0.0
        accuracy_rate = (passed_count / total_tests) if total_tests > 0 else 0.0

        # Calculate tokens/sec across completion tokens
        total_seconds = total_latency_ms / 1000.0
        tokens_per_sec = (total_completion_tokens / total_seconds) if total_seconds > 0 else 0.0

        # Clean up the large raw JSON file now that JSONL is written
        try:
            json_path.unlink(missing_ok=True)
            temp_config = settings.PROMPTFOO_CONFIG_DIR / f"eval_{run_id}.yaml"
            temp_config.unlink(missing_ok=True)
        except Exception as e:
            logger.warning("Could not delete ephemeral config/output: %s", e)

        return {
            "results": parsed_results,
            "total_tests": total_tests,
            "passed_tests": passed_count,
            "failed_tests": total_tests - passed_count,
            "accuracy_rate": accuracy_rate,
            "avg_latency_ms": avg_latency_ms,
            "tokens_per_sec": tokens_per_sec,
            "total_completion_tokens": total_completion_tokens,
            "total_prompt_tokens": total_prompt_tokens,
            "jsonl_artifact_path": str(jsonl_artifact_path)
        }

result_parser = ResultParser()
