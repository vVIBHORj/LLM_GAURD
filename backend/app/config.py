from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "LocalLLM Guard"
    APP_ENV: str = "development"
    DEBUG: bool = True

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'localllm_guard.db'}"

    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_TIMEOUT_SECONDS: float = 120.0

    # Hardware Thresholds for 16GB RAM / 4GB VRAM
    MIN_FREE_RAM_MB: int = 1500
    MAX_VRAM_USAGE_PERCENT: float = 90.0
    DEFAULT_CONTEXT_LENGTH: int = 2048
    DEFAULT_INFERENCE_CONCURRENCY: int = 1
    COOL_DOWN_SECONDS: float = 2.0
    TELEMETRY_SAMPLE_INTERVAL_SECONDS: float = 1.0

    PROMPTFOO_BINARY: str = "promptfoo"
    PROMPTFOO_TIMEOUT_SECONDS: int = 300
    PROMPTFOO_CONFIG_DIR: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "configs")
    PROMPTFOO_RUNS_DIR: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "runs")

    def ensure_directories(self) -> None:
        """Create required local data folders if they do not exist."""
        (PROJECT_ROOT / "data").mkdir(exist_ok=True)
        self.PROMPTFOO_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.PROMPTFOO_RUNS_DIR.mkdir(parents=True, exist_ok=True)
        (PROJECT_ROOT / "data" / "rag_docs").mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
