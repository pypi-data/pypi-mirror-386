"""
Async Transcription Example

Example showing how to transcribe multiple files asynchronously.
"""

import asyncio
import orbitalsai

async def transcribe_file(client, file_path):
    """Transcribe a single file."""
    try:
        transcript = await client.transcribe(file_path)
        return f"✅ {file_path}: {transcript.text[:100]}..."
    except Exception as e:
        return f"❌ {file_path}: {str(e)}"

async def main():
    # Initialize the async client
    async with orbitalsai.AsyncClient(api_key="your_api_key_here") as client:
        # List of audio files to transcribe
        audio_files = [
            "audio1.mp3",
            "audio2.wav", 
            "audio3.m4a"
        ]
        
        print("Transcribing multiple files...")
        
        # Transcribe all files concurrently
        results = await asyncio.gather(
            *[transcribe_file(client, file_path) for file_path in audio_files],
            return_exceptions=True
        )
        
        # Print results
        for result in results:
            print(result)
        
        # Check balance
        balance = await client.get_balance()
        print(f"\nCurrent balance: ${balance.balance:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
