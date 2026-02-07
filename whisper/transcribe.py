import whisper
import string

with open("audiofilename.txt", "r") as file:
    filename = file.read()

input_file = "../audiofiles/" + filename + ".mp3"

model = whisper.load_model("turbo")
result = model.transcribe(input_file)

result = result['text'].lower()
result = result.translate(str.maketrans('', '', string.punctuation)).strip()


with open("../aligner/data" + filename + ".txt", "w") as file:
    file.write(result)