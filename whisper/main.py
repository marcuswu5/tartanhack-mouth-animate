from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import whisper
import os
import logging
import sys

# Path to the cache where the model is stored
cache_path = "/root/.cache"

# Load the model from that cache
model = whisper.load_model("turbo", download_root=cache_path)

app = FastAPI()



class TranscribeRequest(BaseModel):
    audio_path: str
    output_path: str


@app.post("/transcribe")
def transcribe(req: TranscribeRequest):
    logger.info("Received transcribe request: %s", req.audio_path)
    if not os.path.exists(req.audio_path):
        msg = f"Audio file not found: {req.audio_path}"
        logger.error(msg)
        raise HTTPException(status_code=400, detail=msg)
    try:
        result = model.transcribe(req.audio_path)
        text = result.get("text", "")
        with open(req.output_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info("Transcription completed, wrote to %s", req.output_path)
        return {"status": "ok", "text": text}
    except Exception as e:
        logger.exception("Transcription failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
