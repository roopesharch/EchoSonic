import io
import wave
import threading
import os
import hashlib
import pyotp
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from piper.voice import PiperVoice

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from Environment Variables (GCP Cloud Run)
ENGINE_DIR = "engine-python"
# The secret you added to Cloud Run
OTP_SECRET = os.getenv("ADMIN_OTP_SECRET", "KRXW4Z3DPNUXIIDB") 
# Recommended: Set a custom JWT_SECRET in GCP Variables for production
JWT_SECRET = os.getenv("JWT_SECRET", "echosonic-secure-jwt-2026")
ALGORITHM = "HS256"

AVAILABLE_VOICES = {
    "en_US-amy-low.onnx": os.path.join(ENGINE_DIR, "en_US-amy-low.onnx"),
    "en_US-ryan-low.onnx": os.path.join(ENGINE_DIR, "en_US-ryan-low.onnx"),
}

VOICE_MODELS = {}
CACHE = {}
synth_lock = threading.Lock()

@app.on_event("startup")
def load_all_models():
    print("Loading voice models...")
    for voice_name, model_path in AVAILABLE_VOICES.items():
        if os.path.exists(model_path):
            VOICE_MODELS[voice_name] = PiperVoice.load(model_path)
    print("All models loaded.")

@app.get("/verify-otp")
def verify_otp(code: str):
    totp = pyotp.TOTP(OTP_SECRET)
    if totp.verify(code):
        # Token valid for 4 hours
        expires = datetime.utcnow() + timedelta(hours=4)
        to_encode = {"exp": expires, "sub": "admin"}
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
        return {"success": True, "token": encoded_jwt}
    else:
        raise HTTPException(status_code=401, detail="Invalid OTP code")

@app.get("/synthesize")
def synthesize(
    text: str = Query(..., min_length=1),
    voice: str = Query("en_US-amy-low.onnx"),
    token: str = Query(None)
):
    is_admin = False
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            if payload.get("sub") == "admin":
                is_admin = True
        except JWTError:
            pass

    # Logic enforcement
    max_len = 5000 if is_admin else 250
    if len(text) > max_len:
        raise HTTPException(status_code=400, detail=f"Limit exceeded. Max {max_len} chars.")

    if voice not in VOICE_MODELS:
        voice = "en_US-amy-low.onnx"

    cache_key = hashlib.md5((voice + text).encode()).hexdigest()
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
    CACHE[cache_key] = audio_data

    return Response(content=audio_data, media_type="audio/wav")