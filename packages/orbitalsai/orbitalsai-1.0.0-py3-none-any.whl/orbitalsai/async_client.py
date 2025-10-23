"""
OrbitalsAI Asynchronous Client

Asynchronous client for the OrbitalsAI API.
"""

import asyncio
import aiohttp
from typing import Optional, List
from datetime import datetime, date

from .models import (
    TranscriptTask, Transcript, Balance, UsageHistory, DailyUsage, 
    User, APIKey, UsageRecord, DailyUsageRecord
)
from .exceptions import (
    OrbitalsAIError, AuthenticationError, InsufficientBalanceError,
    FileNotFoundError, UnsupportedFileError, UnsupportedLanguageError,
    TaskNotFoundError, TranscriptionError, TimeoutError, APIError
)
from .utils import validate_audio_file, validate_language, get_file_size


class AsyncClient:
    """
    Asynchronous client for the OrbitalsAI API.
    
    Example:
        async with orbitalsai.AsyncClient(api_key="your_api_key_here") as client:
            transcript = await client.transcribe("audio.mp3")
            print(transcript.text)
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.orbitalsai.com/api/v1"):
        """
        Initialize the OrbitalsAI async client.
        
        Args:
            api_key: Your OrbitalsAI API key
            base_url: Base URL for the API (default: localhost for development)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "orbitalsai-python-sdk/1.0.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for aiohttp
            
        Returns:
            JSON response data
            
        Raises:
            APIError: If the API returns an error
        """
        if not self.session:
            raise OrbitalsAIError("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 402:
                    raise InsufficientBalanceError("Insufficient balance")
                elif response.status == 404:
                    raise TaskNotFoundError("Task not found")
                elif response.status >= 400:
                    try:
                        error_data = await response.json()
                        raise APIError(
                            error_data.get("detail", f"HTTP {response.status}"),
                            status_code=response.status,
                            response_data=error_data
                        )
                    except ValueError:
                        raise APIError(f"HTTP {response.status}", status_code=response.status)
                
                return await response.json()
        except aiohttp.ClientError as e:
            raise OrbitalsAIError(f"Request failed: {str(e)}")
    
    async def transcribe(
        self, 
        file_path: str, 
        language: str = "english", 
        generate_srt: bool = False,
        wait: bool = True,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Transcript:
        """
        Transcribe an audio file.
        
        Args:
            file_path: Path to the audio file
            language: Language of the audio (default: "english")
            generate_srt: Whether to generate SRT subtitles (default: False)
            wait: Whether to wait for completion (default: True)
            timeout: Maximum time to wait in seconds (default: 300)
            poll_interval: Seconds to wait between status checks (default: 5)
            
        Returns:
            Transcript object with the result
            
        Raises:
            FileNotFoundError: If the audio file is not found
            UnsupportedFileError: If the file format is not supported
            UnsupportedLanguageError: If the language is not supported
            TimeoutError: If the operation times out
            TranscriptionError: If transcription fails
        """
        # Validate inputs
        validate_audio_file(file_path)
        validate_language(language)
        
        # Prepare file upload
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=file_path.split('/')[-1], content_type='audio/mpeg')
            data.add_field('language', language)
            data.add_field('generate_srt', str(generate_srt).lower())
            
            # Upload file
            response = await self._make_request("POST", "/audio/upload", data=data)
            task_id = response["task_id"]
        
        if not wait:
            # Return task immediately
            task = await self.get_task(task_id)
            return Transcript(
                text=task.result_text or "",
                srt_content=task.srt_content,
                task_id=task_id,
                original_filename=task.original_filename,
                audio_url=task.audio_url
            )
        
        # Wait for completion
        return await self.wait_for_task(task_id, timeout, poll_interval)
    
    async def get_task(self, task_id: int) -> TranscriptTask:
        """
        Get the status of a transcription task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            TranscriptTask object with current status
        """
        response = await self._make_request("GET", f"/audio/status/{task_id}")
        
        return TranscriptTask(
            task_id=task_id,
            status=response["status"],
            original_filename=response["original_filename"],
            audio_url=response.get("audio_url"),
            srt_requested=response["srt_requested"],
            result_text=response.get("result_text"),
            srt_content=response.get("srt_content"),
            error=response.get("error")
        )
    
    async def wait_for_task(
        self, 
        task_id: int, 
        timeout: int = 300, 
        poll_interval: int = 5
    ) -> Transcript:
        """
        Wait for a transcription task to complete.
        
        Args:
            task_id: ID of the task
            timeout: Maximum time to wait in seconds
            poll_interval: Seconds to wait between status checks
            
        Returns:
            Transcript object with the result
            
        Raises:
            TimeoutError: If the operation times out
            TranscriptionError: If transcription fails
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            task = await self.get_task(task_id)
            
            if task.status == "completed":
                return Transcript(
                    text=task.result_text or "",
                    srt_content=task.srt_content,
                    task_id=task_id,
                    original_filename=task.original_filename,
                    audio_url=task.audio_url
                )
            elif task.status == "failed":
                raise TranscriptionError(f"Transcription failed: {task.error}")
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
    
    async def list_tasks(self) -> List[TranscriptTask]:
        """
        Get all transcription tasks for the current user.
        
        Returns:
            List of TranscriptTask objects
        """
        response = await self._make_request("GET", "/audio/tasks")
        
        tasks = []
        for task_data in response:
            tasks.append(TranscriptTask(
                task_id=task_data["task_id"],
                status=task_data["status"],
                original_filename=task_data["original_filename"],
                audio_url=task_data.get("task_blob_directory"),
                srt_requested=task_data["srt_requested"],
                created_at=datetime.fromisoformat(task_data["created_at"].replace('Z', '+00:00'))
            ))
        
        return tasks
    
    async def get_balance(self) -> Balance:
        """
        Get the current user's balance.
        
        Returns:
            Balance object with current balance information
        """
        response = await self._make_request("GET", "/billing/balance")
        
        return Balance(
            balance=response["balance"],
            last_updated=datetime.fromisoformat(response["last_updated"].replace('Z', '+00:00'))
        )
    
    async def get_usage_history(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> UsageHistory:
        """
        Get usage history for the current user.
        
        Args:
            start_date: Start date for the history (default: 30 days ago)
            end_date: End date for the history (default: now)
            page: Page number (default: 1)
            page_size: Number of records per page (default: 50)
            
        Returns:
            UsageHistory object with usage records
        """
        params = {"page": page, "page_size": page_size}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        response = await self._make_request("GET", "/billing/usage-history", params=params)
        
        records = []
        for record_data in response["records"]:
            records.append(UsageRecord(
                id=record_data["id"],
                service_type=record_data["service_type"],
                usage_amount=record_data["total_audio_usage"],
                cost=record_data["cost"],
                timestamp=datetime.fromisoformat(record_data["timestamp"].replace('Z', '+00:00')),
                api_key_id=record_data.get("api_key_id")
            ))
        
        return UsageHistory(
            records=records,
            total_records=response["total_records"],
            total_pages=response["total_pages"],
            current_page=response["current_page"],
            start_date=datetime.fromisoformat(response["start_date"].replace('Z', '+00:00')),
            end_date=datetime.fromisoformat(response["end_date"].replace('Z', '+00:00')),
            period_summary=response["period_summary"]
        )
    
    async def get_daily_usage(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 30
    ) -> DailyUsage:
        """
        Get daily usage history for the current user.
        
        Args:
            start_date: Start date for the history (default: 30 days ago)
            end_date: End date for the history (default: today)
            page: Page number (default: 1)
            page_size: Number of records per page (default: 30)
            
        Returns:
            DailyUsage object with daily usage records
        """
        params = {"page": page, "page_size": page_size}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        response = await self._make_request("GET", "/billing/daily-usage", params=params)
        
        daily_records = []
        for record_data in response["records"]:
            daily_records.append(DailyUsageRecord(
                date=date.fromisoformat(record_data["date"]),
                total_cost=record_data["total_cost"],
                total_audio_usage=record_data["transcription_usage"],
                record_count=1,  # Each record represents one day
                transcription_usage=record_data.get("transcription_usage", 0.0),
                transcription_cost=record_data.get("transcription_cost", 0.0),
                translation_usage=record_data.get("translation_usage", 0.0),
                translation_cost=record_data.get("translation_cost", 0.0),
                summarization_usage=record_data.get("summarization_usage", 0.0),
                summarization_cost=record_data.get("summarization_cost", 0.0)
            ))
        
        return DailyUsage(
            daily_records=daily_records,
            total_records=response["total_records"],
            total_pages=response["total_pages"],
            current_page=response["current_page"],
            start_date=date.fromisoformat(response["start_date"]),
            end_date=date.fromisoformat(response["end_date"]),
            total_cost=response["period_summary"]["total_cost"],
            total_audio_seconds=response["period_summary"]["total_transcription_usage"]
        )
    
    async def get_user(self) -> User:
        """
        Get current user details.
        
        Returns:
            User object with user information
        """
        response = await self._make_request("GET", "/user/")
        
        return User(
            id=response["id"],
            email=response["email"],
            first_name=response["first_name"],
            last_name=response["last_name"],
            is_verified=response["is_verified"]
        )
