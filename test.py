# test.py - Test Whisper and Aligner APIs directly
import requests
import os
import json

# File paths
audio_path = os.path.join(os.path.dirname(__file__), "aligner", "data", "harvard.wav")
transcript_path = os.path.join(os.path.dirname(__file__), "shared-data", "test_transcript.txt")
alignment_path = os.path.join(os.path.dirname(__file__), "shared-data", "test_alignment.json")

# API URLs
WHISPER_URL = "http://localhost:8001/transcribe"
ALIGNER_URL = "http://localhost:8002/align"
MAIN_API_URL = "http://localhost:8000/process"

print("=" * 60)
print("Testing Whisper and Aligner APIs")
print("=" * 60)

# Step 1: Call Whisper API for transcription
print(f"\n1. Calling Whisper API...")
print(f"   Audio file: {audio_path}")
print(f"   Output: {transcript_path}")

whisper_payload = {
    "audio_path": audio_path,
    "output_path": transcript_path
}

try:
    whisper_response = requests.post(WHISPER_URL, json=whisper_payload)
    print(f"   Status: {whisper_response.status_code}")
    if whisper_response.status_code == 200:
        whisper_result = whisper_response.json()
        print(f"   Response: {whisper_result}")
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
                print(f"   Transcript: {transcript_text[:100]}...")
    else:
        print(f"   Error: {whisper_response.text}")
except Exception as e:
    print(f"   Error calling Whisper API: {e}")

# Step 2: Call Aligner API for alignment
print(f"\n2. Calling Aligner API...")
print(f"   Audio file: {audio_path}")
print(f"   Transcript: {transcript_path}")
print(f"   Output: {alignment_path}")

aligner_payload = {
    "audio_path": audio_path,
    "transcript_path": transcript_path,
    "output_path": alignment_path
}

try:
    aligner_response = requests.post(ALIGNER_URL, json=aligner_payload)
    print(f"   Status: {aligner_response.status_code}")
    if aligner_response.status_code == 200:
        aligner_result = aligner_response.json()
        print(f"   Response: {aligner_result}")
        if os.path.exists(alignment_path):
            with open(alignment_path, 'r') as f:
                alignment_data = f.read()
                print(f"   Alignment: {alignment_data[:100]}...")
    else:
        print(f"   Error: {aligner_response.text}")
except Exception as e:
    print(f"   Error calling Aligner API: {e}")

# Step 3: Call main API endpoint (uploads file)
print(f"\n3. Calling Main API (file upload)...")
print(f"   Uploading: {audio_path}")

try:
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        main_response = requests.post(MAIN_API_URL, files=files)

    print(f"   Status: {main_response.status_code}")
    if main_response.status_code == 200:
        main_result = main_response.json()
        print(f"   Response: {json.dumps(main_result, indent=2)}")
    else:
        print(f"   Error: {main_response.text}")
except Exception as e:
    print(f"   Error calling Main API: {e}")

print("\n" + "=" * 60)
print("Testing complete!")
print("=" * 60)
