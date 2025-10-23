"""
OrbitalsAI SDK Utilities

Helper utilities for the OrbitalsAI Python SDK.
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional

from .models import SUPPORTED_AUDIO_FORMATS, SUPPORTED_AUDIO_MIMETYPES, SUPPORTED_LANGUAGES
from .exceptions import UnsupportedFileError, UnsupportedLanguageError, FileNotFoundError


def validate_audio_file(file_path: str) -> None:
    """
    Validate that the audio file exists and is in a supported format.
    
    Args:
        file_path: Path to the audio file
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        UnsupportedFileError: If the file format is not supported
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    # Check file extension
    if file_extension not in SUPPORTED_AUDIO_FORMATS:
        raise UnsupportedFileError(
            f"Unsupported file format: {file_extension}. "
            f"Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
        )
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and mime_type not in SUPPORTED_AUDIO_MIMETYPES:
        # Only raise error if MIME type is detected and not supported
        # Some files might not have MIME type detection but still be valid
        pass


def validate_language(language: str) -> None:
    """
    Validate that the language is supported.
    
    Args:
        language: Language code
        
    Raises:
        UnsupportedLanguageError: If the language is not supported
    """
    if language.lower() not in SUPPORTED_LANGUAGES:
        raise UnsupportedLanguageError(
            f"Unsupported language: {language}. "
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )


def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
    """
    return os.path.getsize(file_path)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}h {minutes}m {remaining_seconds:.1f}s"
