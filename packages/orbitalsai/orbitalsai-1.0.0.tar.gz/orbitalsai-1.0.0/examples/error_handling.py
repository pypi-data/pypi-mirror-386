"""
Error Handling Example

Example showing proper error handling with the SDK.
"""

import orbitalsai
from orbitalsai.exceptions import (
    AuthenticationError, InsufficientBalanceError, 
    UnsupportedFileError, UnsupportedLanguageError,
    TranscriptionError, TimeoutError
)

def main():
    # Initialize the client
    client = orbitalsai.Client(api_key="your_api_key_here")
    
    try:
        # Example 1: Unsupported file format
        try:
            transcript = client.transcribe("document.pdf")
        except UnsupportedFileError as e:
            print(f"File error: {e}")
        
        # Example 2: Unsupported language
        try:
            transcript = client.transcribe("audio.mp3", language="klingon")
        except UnsupportedLanguageError as e:
            print(f"Language error: {e}")
        
        # Example 3: File not found
        try:
            transcript = client.transcribe("nonexistent.mp3")
        except FileNotFoundError as e:
            print(f"File not found: {e}")
        
        # Example 4: Normal transcription with error handling
        try:
            transcript = client.transcribe("audio.mp3", language="hausa")
            print(f"Success: {transcript.text}")
        except TranscriptionError as e:
            print(f"Transcription failed: {e}")
        except TimeoutError as e:
            print(f"Transcription timed out: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            
    except AuthenticationError:
        print("Authentication failed. Please check your API key.")
    except InsufficientBalanceError:
        print("Insufficient balance. Please add credits to your account.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
