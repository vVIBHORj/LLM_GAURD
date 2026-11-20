import json
from pathlib import Path
from backend.app.services.result_parser import result_parser
from backend.app.services.jsonl_storage import jsonl_storage
from backend.app.config import settings

def test_parse_promptfoo_output(tmp_path):
    run_id = "test-parser-run"
    json_path = tmp_path / "sample_output.json"

    sample_promptfoo_json = {
        "results": {
            "version": 4,
            "table": {
                "head": {"prompts": ["test prompt"], "vars": ["prompt"]},
                "body": [
                    {
                        "vars": {"prompt": "Say hello"},
                        "outputs": [
                            {
                                "pass": True,
                                "score": 1.0,
                                "text": "Hello there!",
                                "latencyMs": 250.0,
                                "tokenUsage": {"prompt": 10, "completion": 5}
                            }
                        ]
                    },
                    {
                        "vars": {"prompt": "Say goodbye"},
                        "outputs": [
                            {
                                "pass": False,
                                "score": 0.0,
                                "text": "I am not leaving",
                                "latencyMs": 350.0,
                                "tokenUsage": {"prompt": 10, "completion": 8}
                            }
                        ]
                    }
                ]
            },
            "stats": {"successes": 1, "failures": 1}
        }
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sample_promptfoo_json, f)

    test_case_ids = ["tc-1", "tc-2"]
    parsed = result_parser.parse_promptfoo_output(
        run_id=run_id,
        json_path=json_path,
        test_case_ids=test_case_ids
    )

    assert parsed["total_tests"] == 2
    assert parsed["passed_tests"] == 1
    assert parsed["failed_tests"] == 1
    assert parsed["accuracy_rate"] == 0.5
    assert parsed["avg_latency_ms"] == 300.0
    assert parsed["total_completion_tokens"] == 13
    assert parsed["tokens_per_sec"] > 0

    # Verify JSONL artifact was written
    jsonl_path = Path(parsed["jsonl_artifact_path"])
    assert jsonl_path.exists()
    records = jsonl_storage.read_all(jsonl_path)
    assert len(records) == 2
    assert records[0]["raw_output"] == "Hello there!"
    assert records[0]["test_case_id"] == "tc-1"
    assert records[1]["raw_output"] == "I am not leaving"

    # Cleanup
    jsonl_path.unlink(missing_ok=True)


def test_parse_promptfoo_output_v126_format(tmp_path):
    run_id = "test-parser-v126"
    json_path = tmp_path / "sample_v126_output.json"

    sample_promptfoo_v126_json = {
        "results": {
            "version": 3,
            "results": [
                {
                    "vars": {"prompt": "Prompt 1"},
                    "gradingResult": {"pass": True, "score": 1.0, "reason": "All assertions passed"},
                    "response": {"output": "Response 1"},
                    "latencyMs": 150.0,
                    "tokenUsage": {"prompt": 8, "completion": 4}
                },
                {
                    "vars": {"prompt": "Prompt 2"},
                    "gradingResult": {"pass": False, "score": 0.0, "reason": "Assertion failed"},
                    "response": {"output": "Response 2"},
                    "latencyMs": 250.0,
                    "tokenUsage": {"prompt": 12, "completion": 6}
                }
            ],
            "stats": {"successes": 1, "failures": 1}
        }
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sample_promptfoo_v126_json, f)

    test_case_ids = ["tc-v1", "tc-v2"]
    parsed = result_parser.parse_promptfoo_output(
        run_id=run_id,
        json_path=json_path,
        test_case_ids=test_case_ids
    )

    assert parsed["total_tests"] == 2
    assert parsed["passed_tests"] == 1
    assert parsed["failed_tests"] == 1
    assert parsed["accuracy_rate"] == 0.5
    assert parsed["avg_latency_ms"] == 200.0
    assert parsed["total_completion_tokens"] == 10
    assert parsed["tokens_per_sec"] > 0

    jsonl_path = Path(parsed["jsonl_artifact_path"])
    assert jsonl_path.exists()
    records = jsonl_storage.read_all(jsonl_path)
    assert len(records) == 2
    assert records[0]["raw_output"] == "Response 1"
    assert records[0]["test_case_id"] == "tc-v1"
    assert records[1]["raw_output"] == "Response 2"

    jsonl_path.unlink(missing_ok=True)
