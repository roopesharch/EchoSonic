import io
import wave
import threading
from fastapi import FastAPI, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from piper.voice import PiperVoice

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICE_MODELS = {}
synth_lock = threading.Lock()
MODEL_PATH = "engine-python/en_US-amy-low.onnx"

def load_model():
    if MODEL_PATH not in VOICE_MODELS:
        VOICE_MODELS[MODEL_PATH] = PiperVoice.load(MODEL_PATH)
    return VOICE_MODELS[MODEL_PATH]

@app.get("/synthesize")
def synthesize(text: str = Query(..., min_length=1)):
    voice = load_model()
    buffer = io.BytesIO()

    with synth_lock:
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(voice.config.sample_rate)

            for chunk in voice.synthesize(text):
                if hasattr(chunk, "audio_int16_bytes"):
                    wav_file.writeframes(chunk.audio_int16_bytes)

    return Response(content=buffer.getvalue(), media_type="audio/wav")