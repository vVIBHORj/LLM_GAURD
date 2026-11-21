import yaml
import asyncio
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.services.promptfoo_service import promptfoo_service, PromptfooService, _kill_process_tree
from backend.app.config import settings
from backend.app.core.exceptions import PromptfooExecutionException

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


def test_resolve_cli_command():
    cmd = PromptfooService.resolve_cli_command(["eval", "-c", "test.yaml"])
    assert isinstance(cmd, list)
    assert len(cmd) >= 4
    # The first token must be node, promptfoo, or cmd.exe (never an unseparated shell string)
    assert any(term in cmd[0].lower() for term in ("node", "promptfoo", "cmd"))
    assert cmd[-1] == "test.yaml"


def test_run_evaluation_invalid_config_path():
    async def _run():
        with pytest.raises(PromptfooExecutionException, match="not found"):
            await promptfoo_service.run_evaluation(
                run_id="valid-run-id",
                config_path=Path("non_existent_config_file_12345.yaml")
            )

        # Invalid extension
        temp_txt = settings.PROMPTFOO_CONFIG_DIR / "invalid_ext.txt"
        temp_txt.write_text("dummy")
        try:
            with pytest.raises(PromptfooExecutionException, match="Invalid Promptfoo config extension"):
                await promptfoo_service.run_evaluation(
                    run_id="valid-run-id",
                    config_path=temp_txt
                )
        finally:
            temp_txt.unlink(missing_ok=True)

    asyncio.run(_run())


def test_run_evaluation_invalid_run_id(tmp_path):
    async def _run():
        dummy_yaml = tmp_path / "valid.yaml"
        dummy_yaml.write_text("description: test")

        with pytest.raises(PromptfooExecutionException, match="Invalid run_id format"):
            await promptfoo_service.run_evaluation(
                run_id="../../traversal_id",
                config_path=dummy_yaml
            )

    asyncio.run(_run())


def test_run_evaluation_mocked_normal_path(tmp_path):
    async def _run():
        dummy_yaml = tmp_path / "eval_normal.yaml"
        dummy_yaml.write_text("description: test")

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"promptfoo evaluation completed", b"")
        mock_proc.returncode = 0
        mock_proc.pid = 99999

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            exit_code, output, out_path = await promptfoo_service.run_evaluation(
                run_id="run-normal-100",
                config_path=dummy_yaml,
                concurrency=2
            )

            assert exit_code == 0
            assert "evaluation completed" in output
            assert out_path.name == "run-normal-100.json"
            # Verify create_subprocess_exec was called with separated argument list (no shell)
            mock_exec.assert_called_once()
            args, kwargs = mock_exec.call_args
            assert kwargs.get("cwd") is not None
            assert "-j" in args
            assert "2" in args

    asyncio.run(_run())


def test_run_evaluation_from_path_with_spaces(tmp_path):
    async def _run():
        space_dir = tmp_path / "directory with spaces in name"
        space_dir.mkdir(parents=True, exist_ok=True)
        dummy_yaml = space_dir / "eval config with spaces.yaml"
        dummy_yaml.write_text("description: test with spaces")

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"success with spaces", b"")
        mock_proc.returncode = 0
        mock_proc.pid = 88888

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            exit_code, output, _ = await promptfoo_service.run_evaluation(
                run_id="run-spaces-200",
                config_path=dummy_yaml,
                concurrency=1
            )

            assert exit_code == 0
            assert output == "success with spaces"
            # Ensure the path with spaces was passed as a distinct argument without shell mangling
            args, _ = mock_exec.call_args
            assert str(dummy_yaml.resolve()) in args

    asyncio.run(_run())


def test_run_evaluation_non_zero_exit_code(tmp_path):
    async def _run():
        dummy_yaml = tmp_path / "eval_error.yaml"
        dummy_yaml.write_text("description: error test")

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"Error: Configuration validation error")
        mock_proc.returncode = 1
        mock_proc.pid = 77777

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            exit_code, output, _ = await promptfoo_service.run_evaluation(
                run_id="run-error-300",
                config_path=dummy_yaml
            )

            assert exit_code == 1
            assert "Configuration validation error" in output

    asyncio.run(_run())


def test_run_evaluation_timeout_and_process_tree_termination(tmp_path):
    async def _run():
        dummy_yaml = tmp_path / "eval_timeout.yaml"
        dummy_yaml.write_text("description: timeout test")

        mock_proc = AsyncMock()
        mock_proc.pid = 66666
        # Simulate wait_for raising TimeoutError
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
             patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()), \
             patch("backend.app.services.promptfoo_service._kill_process_tree") as mock_kill:

            with pytest.raises(PromptfooExecutionException, match="timed out"):
                await promptfoo_service.run_evaluation(
                    run_id="run-timeout-400",
                    config_path=dummy_yaml,
                    timeout_seconds=5
                )

            mock_kill.assert_called_once_with(66666)

    asyncio.run(_run())


def test_run_evaluation_cancellation_and_process_tree_termination(tmp_path):
    async def _run():
        dummy_yaml = tmp_path / "eval_cancel.yaml"
        dummy_yaml.write_text("description: cancel test")

        mock_proc = AsyncMock()
        mock_proc.pid = 55555
        # Simulate task cancellation raising CancelledError during wait_for
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
             patch("asyncio.wait_for", side_effect=asyncio.CancelledError()), \
             patch("backend.app.services.promptfoo_service._kill_process_tree") as mock_kill:

            with pytest.raises(asyncio.CancelledError):
                await promptfoo_service.run_evaluation(
                    run_id="run-cancel-500",
                    config_path=dummy_yaml
                )

            mock_kill.assert_called_once_with(55555)

    asyncio.run(_run())


def test_kill_process_tree_windows():
    with patch("os.name", "nt"), patch("subprocess.run") as mock_subproc:
        _kill_process_tree(12345)
        mock_subproc.assert_called_once()
        args = mock_subproc.call_args[0][0]
        assert args == ["taskkill", "/F", "/T", "/PID", "12345"]
