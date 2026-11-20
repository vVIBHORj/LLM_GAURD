import yaml
from pathlib import Path
from backend.app.services.promptfoo_service import promptfoo_service
from backend.app.config import settings

def test_generate_config_file():
    run_id = "test-run-123"
    model_id = "llama3.2:latest"
    test_cases = [
        {
            "prompt": "What is 2+2?",
            "expected_output": "4",
            "assertions": [{"type": "contains", "value": "4"}]
        },
        {
            "prompt": "Say Ready",
            "expected_output": "Ready"
        }
    ]

    config_path = promptfoo_service.generate_config_file(
        run_id=run_id,
        model_id=model_id,
        test_cases=test_cases,
        temperature=0.2,
        num_predict=128,
        num_ctx=2048
    )

    assert config_path.exists()

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["prompts"] == ["{{prompt}}"]
    assert len(data["providers"]) == 1
    provider = data["providers"][0]
    assert provider["id"] == "ollama:chat:llama3.2:latest"
    assert provider["config"]["host"] == "http://127.0.0.1:11434"
    assert provider["config"]["temperature"] == 0.2
    assert provider["config"]["options"]["num_predict"] == 128
    assert len(data["tests"]) == 2
    assert data["tests"][0]["vars"]["prompt"] == "What is 2+2?"

    # Cleanup
    config_path.unlink(missing_ok=True)
