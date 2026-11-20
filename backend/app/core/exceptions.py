class LocalLLMGuardException(Exception):
    """Base exception for all LocalLLM Guard errors."""
    pass

class HardwareConstraintException(LocalLLMGuardException):
    """Raised when hardware capacity limits (RAM, VRAM) are breached."""
    pass

class OllamaServiceException(LocalLLMGuardException):
    """Raised when communication with the local Ollama instance fails."""
    pass

class PromptfooExecutionException(LocalLLMGuardException):
    """Raised when Promptfoo child subprocess execution fails or times out."""
    pass

class ModelNotFoundException(LocalLLMGuardException):
    """Raised when an expected model is not installed in Ollama."""
    pass
