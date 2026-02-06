import whisper

model = whisper.load_model("turbo")
result = model.transcribe("audiofiles/harvard.mp3")
print(result)