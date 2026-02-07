from fastapi import FastAPI, UploadFile, File
import shutil
import requests
import uuid
import os

app = FastAPI()

DATA_DIR = "/data"
WHISPER_URL = "http://whisper:8001/transcribe"
ALIGNER_URL = "http://aligner:8002/align"

@app.post("/process")
def process_audio(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())

    audio_path = f"{DATA_DIR}/{job_id}.wav"
    transcript_path = f"{DATA_DIR}/{job_id}.txt"
    alignment_path = f"{DATA_DIR}/{job_id}.json"

    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Call Whisper
    requests.post(
        WHISPER_URL,
        json={
            "audio_path": audio_path,
            "output_path": transcript_path
        }
    )

    # Call Aligner
    requests.post(
        ALIGNER_URL,
        json={
            "audio_path": audio_path,
            "transcript_path": transcript_path,
            "output_path": alignment_path
        }
    )

    return {
        "job_id": job_id,
        "transcript": transcript_path,
        "alignment": alignment_path
    }
