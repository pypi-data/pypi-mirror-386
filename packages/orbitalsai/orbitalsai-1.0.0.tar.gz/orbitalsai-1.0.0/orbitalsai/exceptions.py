"""
OrbitalsAI SDK Exceptions

Custom exceptions for the OrbitalsAI Python SDK.
"""


class OrbitalsAIError(Exception):
    """Base exception for all OrbitalsAI SDK errors."""
    pass


class AuthenticationError(OrbitalsAIError):
    """Raised when API key authentication fails."""
    pass


class InsufficientBalanceError(OrbitalsAIError):
    """Raised when user has insufficient balance for the operation."""
    pass


class FileNotFoundError(OrbitalsAIError):
    """Raised when the specified audio file is not found."""
    pass


class UnsupportedFileError(OrbitalsAIError):
    """Raised when the audio file format is not supported."""
    pass


class UnsupportedLanguageError(OrbitalsAIError):
    """Raised when the specified language is not supported."""
    pass


class TaskNotFoundError(OrbitalsAIError):
    """Raised when the specified task ID is not found."""
    pass


class TranscriptionError(OrbitalsAIError):
    """Raised when transcription processing fails."""
    pass


class TimeoutError(OrbitalsAIError):
    """Raised when an operation times out."""
    pass


class APIError(OrbitalsAIError):
    """Raised when the API returns an error response."""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
