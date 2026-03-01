import io
import wave
import threading
import os
import hashlib
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

ENGINE_DIR = "engine-python"

AVAILABLE_VOICES = {
    "en_US-amy-low.onnx": os.path.join(ENGINE_DIR, "en_US-amy-low.onnx"),
    "en_US-ryan-low.onnx": os.path.join(ENGINE_DIR, "en_US-ryan-low.onnx"),
}

VOICE_MODELS = {}
CACHE = {}
synth_lock = threading.Lock()

# 🔥 Preload all models at startup
@app.on_event("startup")
def load_all_models():
    print("Loading voice models...")
    for voice_name, model_path in AVAILABLE_VOICES.items():
        VOICE_MODELS[voice_name] = PiperVoice.load(model_path)
    print("All models loaded.")

@app.get("/synthesize")
def synthesize(
    text: str = Query(..., min_length=1),
    voice: str = Query("en_US-amy-low.onnx")
):
    if voice not in VOICE_MODELS:
        voice = "en_US-amy-low.onnx"

    # 🔥 Create cache key
    cache_key = hashlib.md5((voice + text).encode()).hexdigest()

    # If already generated → return instantly
    if cache_key in CACHE:
        return Response(content=CACHE[cache_key], media_type="audio/wav")

    voice_model = VOICE_MODELS[voice]
    buffer = io.BytesIO()

    with synth_lock:
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(voice_model.config.sample_rate)

            for chunk in voice_model.synthesize(text):
                if hasattr(chunk, "audio_int16_bytes"):
                    wav_file.writeframes(chunk.audio_int16_bytes)

    audio_data = buffer.getvalue()

    # 🔥 Store in memory cache
    CACHE[cache_key] = audio_data

    return Response(content=audio_data, media_type="audio/wav")