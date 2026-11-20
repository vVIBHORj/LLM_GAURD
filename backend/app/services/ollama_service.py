import logging
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.core.exceptions import OllamaServiceException

logger = logging.getLogger(__name__)

class OllamaService:
    """
    Client for the local Ollama HTTP API.
    Explicitly binds to IPv4 (127.0.0.1) and enforces the Model Switch Unload Protocol.
    """

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def get_version(self) -> Dict[str, Any]:
        """Returns Ollama version and connectivity check."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                if res.status_code == 200:
                    return res.json()
                raise OllamaServiceException(f"Ollama returned HTTP {res.status_code}")
        except Exception as e:
            logger.warning("Failed to reach Ollama at %s: %s", self.base_url, e)
            raise OllamaServiceException(f"Could not connect to Ollama at {self.base_url}: {e}")

    async def is_healthy(self) -> bool:
        """Returns True if the Ollama API is reachable."""
        try:
            await self.get_version()
            return True
        except Exception:
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """Retrieves all locally installed models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = data.get("models", [])
                    return models
                raise OllamaServiceException(f"Ollama returned HTTP {res.status_code} on tags query")
        except Exception as e:
            logger.error("Error retrieving Ollama models: %s", e)
            raise OllamaServiceException(f"Failed to list Ollama models: {e}")

    async def get_active_models(self) -> List[Dict[str, Any]]:
        """Queries /api/ps to see which models are currently loaded in VRAM/RAM."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/ps")
                if res.status_code == 200:
                    return res.json().get("models", [])
                return []
        except Exception as e:
            logger.warning("Could not query Ollama active models: %s", e)
            return []

    async def unload_model(self, model_name: str) -> bool:
        """
        Forces Ollama to release a model from memory immediately by setting keep_alive: 0.
        Essential for staying within the 4GB VRAM ceiling.
        """
        logger.info("Triggering explicit unload for model: %s", model_name)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": model_name, "keep_alive": 0}
                )
                if res.status_code == 200:
                    await asyncio.sleep(settings.COOL_DOWN_SECONDS)
                    return True
                return False
        except Exception as e:
            logger.warning("Failed to unload model %s: %s", model_name, e)
            return False

    async def ensure_single_model(self, target_model: str) -> None:
        """
        Ensures that only the target model is loaded in Ollama.
        Unloads any other resident models.
        """
        active_models = await self.get_active_models()
        for m in active_models:
            name = m.get("name")
            if name and name != target_model:
                logger.info("Unloading resident model %s before running %s", name, target_model)
                await self.unload_model(name)

ollama_service = OllamaService()
