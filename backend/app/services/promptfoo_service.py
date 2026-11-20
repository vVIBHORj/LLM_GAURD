import yaml
import json
import logging
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from backend.app.config import settings
from backend.app.core.exceptions import PromptfooExecutionException

logger = logging.getLogger(__name__)

class PromptfooService:
    """
    Manages Promptfoo configuration compilation, subprocess execution,
    timeouts, and output extraction.
    """

    @staticmethod
    def generate_config_file(
        run_id: str,
        model_id: str,
        test_cases: List[Dict[str, Any]],
        temperature: float = 0.1,
        num_predict: int = 256,
        num_ctx: int = 2048,
    ) -> Path:
        """
        Compiles test cases and model options into a validated Promptfoo YAML config.
        Binds explicitly to IPv4 http://127.0.0.1:11434.
        """
        config_path = settings.PROMPTFOO_CONFIG_DIR / f"eval_{run_id}.yaml"

        promptfoo_tests = []
        for tc in test_cases:
            prompt_text = tc.get("prompt", "")
            test_entry: Dict[str, Any] = {
                "vars": {
                    "prompt": prompt_text
                }
            }
            assertions = tc.get("assertions")
            if assertions and isinstance(assertions, list):
                test_entry["assert"] = assertions
            elif assertions and isinstance(assertions, dict):
                test_entry["assert"] = [assertions]
            elif tc.get("expected_output"):
                test_entry["assert"] = [
                    {"type": "contains", "value": tc["expected_output"]}
                ]
            promptfoo_tests.append(test_entry)

        config_data = {
            "description": f"LocalLLM Guard Evaluation Run {run_id}",
            "prompts": ["{{prompt}}"],
            "providers": [
                {
                    "id": f"ollama:chat:{model_id}",
                    "config": {
                        "host": "http://127.0.0.1:11434",
                        "temperature": temperature,
                        "options": {
                            "num_predict": num_predict,
                            "num_ctx": num_ctx
                        }
                    }
                }
            ],
            "tests": promptfoo_tests
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        logger.info("Generated Promptfoo config: %s with %d test cases", config_path, len(promptfoo_tests))
        return config_path

    @staticmethod
    async def run_evaluation(
        run_id: str,
        config_path: Path,
        concurrency: int = 1,
        timeout_seconds: Optional[int] = None
    ) -> Tuple[int, str, Path]:
        """
        Executes Promptfoo eval via managed child subprocess.
        Returns: (exit_code, stderr_output, json_output_path)
        """
        output_json_path = settings.PROMPTFOO_RUNS_DIR / f"{run_id}.json"
        effective_timeout = timeout_seconds or settings.PROMPTFOO_TIMEOUT_SECONDS

        cmd = [
            settings.PROMPTFOO_BINARY,
            "eval",
            "-c", str(config_path),
            "-o", str(output_json_path),
            "-j", str(concurrency),
            "--no-cache",
            "--no-write",
            "--no-progress-bar"
        ]

        logger.info("Executing Promptfoo command: %s (timeout: %ds)", " ".join(cmd), effective_timeout)

        # Execute using cmd.exe on Windows for clean PATH resolution of npm global binaries
        full_command = f'cmd.exe /c "{" ".join(cmd)}"'

        proc = await asyncio.create_subprocess_shell(
            full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=effective_timeout
            )
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            logger.info("Promptfoo process completed with exit code: %d", proc.returncode)
            if proc.returncode != 0:
                logger.warning("Promptfoo stderr: %s", stderr_str[:500])

            return proc.returncode, stderr_str or stdout_str, output_json_path

        except asyncio.TimeoutError:
            logger.error("Promptfoo evaluation timed out after %ds for run %s", effective_timeout, run_id)
            try:
                # Force kill process tree on Windows
                os.system(f"taskkill /F /T /PID {proc.pid} >nul 2>&1")
            except Exception:
                pass
            raise PromptfooExecutionException(f"Promptfoo evaluation timed out after {effective_timeout} seconds.")

promptfoo_service = PromptfooService()
