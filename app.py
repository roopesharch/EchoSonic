import io
import wave
import threading
import os
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

ENGINE_DIR = "engine-python"

AVAILABLE_VOICES = {
    "en_US-amy-low.onnx": os.path.join(ENGINE_DIR, "en_US-amy-low.onnx"),
    "en_US-ryan-low.onnx": os.path.join(ENGINE_DIR, "en_US-ryan-low.onnx"),
}

def load_model(voice_name):
    if voice_name not in VOICE_MODELS:
        model_path = AVAILABLE_VOICES[voice_name]
        VOICE_MODELS[voice_name] = PiperVoice.load(model_path)
    return VOICE_MODELS[voice_name]

@app.get("/synthesize")
def synthesize(
    text: str = Query(..., min_length=1),
    voice: str = Query("en_US-amy-low.onnx")
):
    if voice not in AVAILABLE_VOICES:
        voice = "en_US-amy-low.onnx"

    voice_model = load_model(voice)
    buffer = io.BytesIO()

    with synth_lock:
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(voice_model.config.sample_rate)

            for chunk in voice_model.synthesize(text):
                if hasattr(chunk, "audio_int16_bytes"):
                    wav_file.writeframes(chunk.audio_int16_bytes)

    return Response(content=buffer.getvalue(), media_type="audio/wav")