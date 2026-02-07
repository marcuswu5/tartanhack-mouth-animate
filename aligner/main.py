from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()

class AlignRequest(BaseModel):
    audio_path: str
    transcript_path: str
    output_path: str

@app.post("/align")
def align(req: AlignRequest):
    # Replace with MFA logic
    with open(req.output_path, "w") as f:
        f.write("alignment placeholder")
    return {"status": "ok"}
