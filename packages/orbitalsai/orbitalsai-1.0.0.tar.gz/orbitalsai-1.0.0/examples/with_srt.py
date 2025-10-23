"""
SRT Subtitles Example

Example showing how to generate SRT subtitles with transcription.
"""

import orbitalsai

def main():
    # Initialize the client
    client = orbitalsai.Client(api_key="your_api_key_here")
    
    # Transcribe with SRT subtitles
    print("Transcribing with SRT subtitles...")
    transcript = client.transcribe(
        "path/to/your/audio.mp3",
        language="hausa",  # Specify language
        generate_srt=True  # Generate SRT subtitles
    )
    
    # Print the transcription
    print(f"Transcription: {transcript.text}")
    
    # Print SRT content if available
    if transcript.srt_content:
        print("\nSRT Subtitles:")
        print(transcript.srt_content)
    else:
        print("No SRT content generated")
    
    # Save SRT to file
    if transcript.srt_content:
        with open("transcript.srt", "w", encoding="utf-8") as f:
            f.write(transcript.srt_content)
        print("\nSRT saved to transcript.srt")

if __name__ == "__main__":
    main()
