"""
Basic tests for the OrbitalsAI SDK
"""

import pytest
from unittest.mock import Mock, patch
from orbitalsai import Client, AsyncClient
from orbitalsai.exceptions import AuthenticationError, UnsupportedFileError


class TestClient:
    """Test the synchronous client."""
    
    def test_client_initialization(self):
        """Test client initialization."""
        client = Client(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.base_url == "http://localhost:8000/api/v1"
    
    def test_client_initialization_custom_url(self):
        """Test client initialization with custom URL."""
        client = Client(api_key="test_key", base_url="https://api.orbitalsai.com/v1")
        assert client.base_url == "https://api.orbitalsai.com/v1"
    
    @patch('orbitalsai.client.Client._make_request')
    def test_transcribe_success(self, mock_request):
        """Test successful transcription."""
        # Mock the upload response
        mock_request.return_value = {"task_id": 123}
        
        client = Client(api_key="test_key")
        
        # Mock file validation
        with patch('orbitalsai.utils.validate_audio_file'):
            with patch('builtins.open', mock_open_file()):
                with patch('orbitalsai.client.Client.get_task') as mock_get_task:
                    mock_get_task.return_value = Mock(
                        status="completed",
                        result_text="Hello world",
                        srt_content=None,
                        original_filename="test.mp3",
                        audio_url=None
                    )
                    
                    transcript = client.transcribe("test.mp3")
                    assert transcript.text == "Hello world"
    
    @patch('orbitalsai.client.Client._make_request')
    def test_transcribe_authentication_error(self, mock_request):
        """Test authentication error handling."""
        from requests.exceptions import HTTPError
        from unittest.mock import Mock
        
        # Mock HTTP 401 error
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.side_effect = HTTPError(response=mock_response)
        
        client = Client(api_key="invalid_key")
        
        with patch('orbitalsai.utils.validate_audio_file'):
            with patch('builtins.open', mock_open_file()):
                with pytest.raises(AuthenticationError):
                    client.transcribe("test.mp3")
    
    def test_validate_file_not_found(self):
        """Test file validation with non-existent file."""
        client = Client(api_key="test_key")
        
        with pytest.raises(FileNotFoundError):
            client.transcribe("nonexistent.mp3")
    
    @patch('orbitalsai.client.Client._make_request')
    def test_get_balance(self, mock_request):
        """Test getting balance."""
        mock_request.return_value = {
            "balance": 50.0,
            "last_updated": "2024-01-01T00:00:00Z"
        }
        
        client = Client(api_key="test_key")
        balance = client.get_balance()
        
        assert balance.balance == 50.0
        assert balance.last_updated is not None


class TestAsyncClient:
    """Test the asynchronous client."""
    
    @pytest.mark.asyncio
    async def test_async_client_initialization(self):
        """Test async client initialization."""
        async with AsyncClient(api_key="test_key") as client:
            assert client.api_key == "test_key"
            assert client.base_url == "http://localhost:8000/api/v1"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_async_transcribe_success(self, mock_request):
        """Test successful async transcription."""
        # Mock the response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {"task_id": 123}
        mock_request.return_value.__aenter__.return_value = mock_response
        
        async with AsyncClient(api_key="test_key") as client:
            with patch('orbitalsai.utils.validate_audio_file'):
                with patch('builtins.open', mock_open_file()):
                    with patch('orbitalsai.async_client.AsyncClient.get_task') as mock_get_task:
                        mock_get_task.return_value = Mock(
                            status="completed",
                            result_text="Hello world",
                            srt_content=None,
                            original_filename="test.mp3",
                            audio_url=None
                        )
                        
                        transcript = await client.transcribe("test.mp3")
                        assert transcript.text == "Hello world"


def mock_open_file():
    """Mock file opening for tests."""
    return Mock()


if __name__ == "__main__":
    pytest.main([__file__])
