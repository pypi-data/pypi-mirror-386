"""
Simple Transcription Example

Basic example showing how to transcribe an audio file.
"""

import orbitalsai

def main():
    # Initialize the client
    client = orbitalsai.Client(api_key="your_api_key_here")
    
    # Transcribe an audio file (waits automatically)
    print("Transcribing audio file...")
    transcript = client.transcribe("path/to/your/audio.mp3")
    
    # Print the result
    print(f"Transcription: {transcript.text}")
    
    # Check balance
    balance = client.get_balance()
    print(f"Current balance: ${balance.balance:.2f}")

if __name__ == "__main__":
    main()
