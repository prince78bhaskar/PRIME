"""
P.R.I.M.E. Ollama Exceptions.

Defines custom exception classes for local Ollama runtime interactions,
including connection failures, timeouts, model absence, and hardware guardrails.
"""


class OllamaError(Exception):
    """Base exception for all Ollama-related operations."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class OllamaConnectionError(OllamaError):
    """Raised when the local Ollama service is unreachable or offline."""

    def __init__(
        self,
        message: str = "Local Ollama service is unreachable",
        base_url: str = "http://127.0.0.1:11434",
        detail: str | None = None,
    ) -> None:
        full_detail = detail or f"Could not connect to Ollama daemon at {base_url}. Ensure Ollama is running."
        super().__init__(message, detail=full_detail)
        self.base_url = base_url


class OllamaTimeoutError(OllamaError):
    """Raised when an inference or health check request exceeds the configured timeout."""

    def __init__(
        self,
        message: str = "Ollama request timed out",
        timeout_seconds: float = 30.0,
        detail: str | None = None,
    ) -> None:
        full_detail = detail or f"Inference request exceeded timeout of {timeout_seconds}s."
        super().__init__(message, detail=full_detail)
        self.timeout_seconds = timeout_seconds


class OllamaModelNotFoundError(OllamaError):
    """Raised when the requested model is not installed in the local Ollama instance."""

    def __init__(
        self,
        model: str,
        available_models: list[str] | None = None,
        detail: str | None = None,
    ) -> None:
        available_str = ", ".join(available_models) if available_models else "none"
        full_detail = (
            detail
            or f"Model '{model}' is not installed in local Ollama. Available: [{available_str}]. "
            f"Run 'ollama pull {model}' to install."
        )
        message = f"Model '{model}' is not installed"
        super().__init__(message, detail=full_detail)
        self.model = model
        self.available_models = available_models or []


class OllamaHardwareLimitError(OllamaError):
    """Raised when a requested model exceeds the 4GB VRAM / 16GB RAM hardware envelope."""

    def __init__(
        self,
        model: str,
        reason: str | None = None,
        detail: str | None = None,
    ) -> None:
        full_reason = reason or "Model size exceeds target hardware constraints (4GB VRAM ceiling)."
        full_detail = (
            detail
            or f"Model '{model}' was rejected: {full_reason}. "
            "P.R.I.M.E. restricts models to small quantized checkpoints (<=7B/8B, recommended 3B)."
        )
        message = f"Model '{model}' violates hardware safety constraints"
        super().__init__(message, detail=full_detail)
        self.model = model
