"""
OrbitalsAI Python SDK

A simple and powerful Python SDK for the OrbitalsAI API.

Example:
    import orbitalsai
    
    # Synchronous usage
    client = orbitalsai.Client(api_key="your_api_key_here")
    transcript = client.transcribe("audio.mp3")
    print(transcript.text)
    
    # Asynchronous usage
    async with orbitalsai.AsyncClient(api_key="your_api_key_here") as client:
        transcript = await client.transcribe("audio.mp3")
        print(transcript.text)
"""

from .client import Client
from .async_client import AsyncClient
from .models import (
    TranscriptTask, Transcript, Balance, UsageHistory, DailyUsage, User,
    SUPPORTED_LANGUAGES, SUPPORTED_AUDIO_FORMATS, SUPPORTED_AUDIO_MIMETYPES
)
from .exceptions import (
    OrbitalsAIError, AuthenticationError, InsufficientBalanceError,
    FileNotFoundError, UnsupportedFileError, UnsupportedLanguageError,
    TaskNotFoundError, TranscriptionError, TimeoutError, APIError
)

__version__ = "1.0.0"
__author__ = "OrbitalsAI"
__email__ = "support@orbitalsai.com"

__all__ = [
    # Clients
    "Client",
    "AsyncClient",
    
    # Models
    "TranscriptTask",
    "Transcript", 
    "Balance",
    "UsageHistory",
    "DailyUsage",
    "User",
    
    # Constants
    "SUPPORTED_LANGUAGES",
    "SUPPORTED_AUDIO_FORMATS", 
    "SUPPORTED_AUDIO_MIMETYPES",
    
    # Exceptions
    "OrbitalsAIError",
    "AuthenticationError",
    "InsufficientBalanceError",
    "FileNotFoundError",
    "UnsupportedFileError",
    "UnsupportedLanguageError",
    "TaskNotFoundError",
    "TranscriptionError",
    "TimeoutError",
    "APIError",
]
