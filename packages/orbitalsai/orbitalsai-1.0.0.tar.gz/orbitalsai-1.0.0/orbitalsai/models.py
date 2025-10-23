"""
OrbitalsAI SDK Data Models

Data models for API requests and responses.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, date


@dataclass
class TranscriptTask:
    """Represents a transcription task status."""
    task_id: int
    status: str
    original_filename: str
    audio_url: Optional[str] = None
    srt_requested: bool = False
    result_text: Optional[str] = None
    srt_content: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Transcript:
    """Represents a completed transcription result."""
    text: str
    srt_content: Optional[str] = None
    task_id: int = None
    original_filename: str = None
    audio_url: Optional[str] = None
    processing_time: Optional[float] = None


@dataclass
class Balance:
    """Represents user balance information."""
    balance: float
    last_updated: datetime


@dataclass
class UsageRecord:
    """Represents a single usage record."""
    id: int
    service_type: str
    usage_amount: float
    cost: float
    timestamp: datetime
    api_key_id: Optional[int] = None


@dataclass
class UsageHistory:
    """Represents usage history response."""
    records: List[UsageRecord]
    total_records: int
    total_pages: int
    current_page: int
    start_date: datetime
    end_date: datetime
    period_summary: dict


@dataclass
class DailyUsageRecord:
    """Represents daily usage record."""
    date: date
    total_cost: float
    total_audio_usage: float
    record_count: int
    transcription_usage: float = 0.0
    transcription_cost: float = 0.0
    translation_usage: float = 0.0
    translation_cost: float = 0.0
    summarization_usage: float = 0.0
    summarization_cost: float = 0.0


@dataclass
class DailyUsage:
    """Represents daily usage response."""
    daily_records: List[DailyUsageRecord]
    total_records: int
    total_pages: int
    current_page: int
    start_date: date
    end_date: date
    total_cost: float
    total_audio_seconds: float


@dataclass
class User:
    """Represents user information."""
    id: int
    email: str
    first_name: str
    last_name: str
    is_verified: bool


@dataclass
class APIKey:
    """Represents API key information."""
    id: int
    name: str
    key_prefix: str
    permissions: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None


# Supported languages and file formats
SUPPORTED_LANGUAGES = [
    "english", "hausa", "igbo", "yoruba", "swahili", "pidgin", "kinyarwanda"
]

SUPPORTED_AUDIO_FORMATS = [
    ".wav", ".wave", ".mp3", ".mpeg", ".ogg", ".oga", ".opus",
    ".flac", ".aac", ".m4a", ".wma", ".amr", ".3gp"
]

SUPPORTED_AUDIO_MIMETYPES = [
    "audio/wav", "audio/wave", "audio/x-wav", "audio/vnd.wave",
    "audio/mp3", "audio/mpeg", "audio/mpeg3", "audio/x-mpeg-3",
    "audio/ogg", "audio/vorbis", "audio/x-vorbis+ogg",
    "audio/opus", "audio/flac", "audio/x-flac",
    "audio/aac", "audio/x-aac", "audio/mp4", "audio/m4a", "audio/x-m4a",
    "audio/x-ms-wma", "audio/amr", "audio/3gpp", "audio/3gpp2",
    "application/octet-stream"
]
