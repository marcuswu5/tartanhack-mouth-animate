from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import whisper
import os
import logging
import sys
import string

# Path to the cache where the model is stored
cache_path = "/root/.cache"



app = FastAPI()

model = None

class TranscribeRequest(BaseModel):
    audio_path: str
    output_path: str


@app.post("/transcribe")
def transcribe(req: TranscribeRequest):
    # Load the model from that cache
    global model
    if model is None:
        print("Loading model...")
        model = whisper.load_model("turbo", download_root=cache_path, local_files_only=True)
        print("Model loaded!")
    if not os.path.exists(req.audio_path):
        msg = f"Audio file not found: {req.audio_path}"
        raise HTTPException(status_code=400, detail=msg)
    
    val = req.audio_path.split('.')[0]
    filename = val

    input_file = "/data/" + filename + ".mp3"

    model = whisper.load_model("turbo")
    result = model.transcribe(input_file)

    result = result['text'].lower()
    result = result.translate(str.maketrans('', '', string.punctuation)).strip()


    with open("/data/audio-transcript/" + filename + ".txt", "w") as file:
        file.write(result)
