"""Library-specific exceptions to avoid swallowing errors.

Define clear, typed exceptions that callers can handle precisely.
"""


class LoopBotError(Exception):
    """Base exception for all library-specific errors."""


class CliNotFoundError(LoopBotError):
    """Raised when the 'opencode' executable is not found on PATH."""


class CliExitError(LoopBotError):
    """Raised when the 'opencode' CLI exits with a non-zero status code."""

    def __init__(self, message: str, return_code: int, stderr: str) -> None:
        super().__init__(message)
        self.return_code = return_code
        self.stderr = stderr
