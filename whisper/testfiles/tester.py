import whisper

import os
print(f"Current directory: {os.getcwd()}")

print("Loading audio...")
audio = whisper.load_audio("/app/data/harvard.mp3")
print("Audio loaded...")

print("Loading model...")
model = whisper.load_model("turbo", download_root="/root/.cache")


print("Model loaded...")


result = model.transcribe("/app/data/harvard.mp3",verbose=True)
print(result)