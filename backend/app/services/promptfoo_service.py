import yaml
import json
import logging
import asyncio
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from backend.app.config import settings, PROJECT_ROOT
from backend.app.core.exceptions import PromptfooExecutionException

logger = logging.getLogger(__name__)

SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")

def _kill_process_tree(pid: int) -> None:
    """Terminates a process and all its child processes cleanly on Windows and Unix."""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        else:
            import signal
            os.killpg(os.getpgid(pid), signal.SIGTERM)
    except Exception as e:
        logger.warning("Could not terminate process tree for PID %s: %s", pid, e)

class PromptfooService:
    """
    Manages Promptfoo configuration compilation, secure subprocess execution
    (no-shell, argument-separated invocation), timeouts, and output extraction.
    """

    @staticmethod
    def resolve_cli_command(eval_args: List[str]) -> List[str]:
        """
        Resolves the safest command list to execute Promptfoo on the host system.
        Prioritizes invoking Node.js directly with the Promptfoo JavaScript entrypoint,
        avoiding Windows shell command shims and arbitrary shell string execution.
        """
        node_exe = shutil.which("node")

        # 1. Look for Promptfoo JavaScript entrypoint
        candidates: List[Path] = []
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "npm" / "node_modules" / "promptfoo" / "dist" / "src" / "entrypoint.js")

        candidates.append(PROJECT_ROOT / "node_modules" / "promptfoo" / "dist" / "src" / "entrypoint.js")

        pf_path = shutil.which(settings.PROMPTFOO_BINARY) or shutil.which("promptfoo")
        if pf_path:
            pf_parent = Path(pf_path).parent
            candidates.append(pf_parent / "node_modules" / "promptfoo" / "dist" / "src" / "entrypoint.js")
            candidates.append(pf_parent / ".." / "node_modules" / "promptfoo" / "dist" / "src" / "entrypoint.js")

        if node_exe:
            for cand in candidates:
                try:
                    resolved = cand.resolve()
                    if resolved.exists() and resolved.is_file():
                        logger.debug("Resolved Promptfoo via Node.js entrypoint: %s", resolved)
                        return [node_exe, str(resolved)] + eval_args
                except Exception:
                    continue

        # 2. Check for native executable (promptfoo.exe)
        pf_exe = shutil.which("promptfoo.exe")
        if pf_exe:
            logger.debug("Resolved Promptfoo via native executable: %s", pf_exe)
            return [pf_exe] + eval_args

        if pf_path and pf_path.lower().endswith(".exe"):
            logger.debug("Resolved Promptfoo via PATH executable: %s", pf_path)
            return [pf_path] + eval_args

        # 3. If Windows command shim (.cmd) and Node is unavailable, invoke cmd.exe with separate args
        if os.name == "nt" and pf_path and pf_path.lower().endswith((".cmd", ".bat")):
            logger.debug("Resolved Promptfoo via Windows command shim: %s", pf_path)
            return ["cmd.exe", "/c", pf_path] + eval_args

        # 4. Fallback to binary name
        return [settings.PROMPTFOO_BINARY] + eval_args

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

    @classmethod
    async def run_evaluation(
        cls,
        run_id: str,
        config_path: Path,
        concurrency: int = 1,
        timeout_seconds: Optional[int] = None
    ) -> Tuple[int, str, Path]:
        """
        Executes Promptfoo eval via managed child subprocess using create_subprocess_exec.
        Passes arguments safely as a list without shell execution.
        Returns: (exit_code, stderr_output, json_output_path)
        """
        # Validate run_id to prevent path manipulation
        if not run_id or not SAFE_ID_REGEX.match(run_id):
            raise PromptfooExecutionException(f"Invalid run_id format: '{run_id}'. Must be alphanumeric with hyphens/underscores.")

        # Validate config_path
        config_path_obj = Path(config_path).resolve()
        if not config_path_obj.exists() or not config_path_obj.is_file():
            raise PromptfooExecutionException(f"Promptfoo configuration file not found: {config_path}")
        if config_path_obj.suffix.lower() not in (".yaml", ".yml"):
            raise PromptfooExecutionException(f"Invalid Promptfoo config extension: {config_path_obj.suffix}. Expected .yaml/.yml")

        # Validate & clamp concurrency
        safe_concurrency = max(1, min(int(concurrency), 4))

        output_json_path = (settings.PROMPTFOO_RUNS_DIR / f"{run_id}.json").resolve()
        effective_timeout = timeout_seconds or settings.PROMPTFOO_TIMEOUT_SECONDS

        eval_args = [
            "eval",
            "-c", str(config_path_obj),
            "-o", str(output_json_path),
            "-j", str(safe_concurrency),
            "--no-cache",
            "--no-write",
            "--no-progress-bar"
        ]

        cmd = cls.resolve_cli_command(eval_args)
        logger.info("Executing Promptfoo command: %s (timeout: %ds)", " ".join(cmd), effective_timeout)

        # Execute using create_subprocess_exec (NO SHELL STRING INTERPOLATION)
        proc = await asyncio.create_subprocess_exec(
            cmd[0],
            *cmd[1:],
            cwd=str(PROJECT_ROOT),
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
            _kill_process_tree(proc.pid)
            raise PromptfooExecutionException(f"Promptfoo evaluation timed out after {effective_timeout} seconds.")
        except asyncio.CancelledError:
            logger.warning("Promptfoo evaluation cancelled for run %s", run_id)
            _kill_process_tree(proc.pid)
            raise

promptfoo_service = PromptfooService()
