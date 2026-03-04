import io
import wave
import threading
import os
import hashlib
import pyotp
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, HTTPException, Request
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

# Configuration
ENGINE_DIR = "engine-python"
OTP_SECRET = os.getenv("ADMIN_OTP_SECRET", "KRXW4Z3DPNUXIIDB") 
JWT_SECRET = os.getenv("JWT_SECRET", "echosonic-secure-jwt-2026")
ALGORITHM = "HS256"

AVAILABLE_VOICES = {
    "en_US-amy-low.onnx": os.path.join(ENGINE_DIR, "en_US-amy-low.onnx"),
    "en_US-ryan-low.onnx": os.path.join(ENGINE_DIR, "en_US-ryan-low.onnx"),
}

VOICE_MODELS = {}
CACHE = {}
# Quota tracking: { "IP": {"count": 0, "date": "YYYY-MM-DD"} }
USER_QUOTAS = {}
synth_lock = threading.Lock()

@app.on_event("startup")
def load_all_models():
    print("Loading voice models...")
    for voice_name, model_path in AVAILABLE_VOICES.items():
        if os.path.exists(model_path):
            VOICE_MODELS[voice_name] = PiperVoice.load(model_path)
    print("All models loaded.")

# --- UTILS ---
def get_client_ip(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def is_quota_available(ip: str):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if ip not in USER_QUOTAS or USER_QUOTAS[ip]["date"] != today:
        USER_QUOTAS[ip] = {"count": 0, "date": today}
    return USER_QUOTAS[ip]["count"] < 5

# --- ROUTES ---

@app.get("/verify-otp")
def verify_otp(code: str):
    totp = pyotp.TOTP(OTP_SECRET)
    if totp.verify(code):
        expires = datetime.utcnow() + timedelta(hours=4)
        to_encode = {"exp": expires, "sub": "admin"}
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
        return {"success": True, "token": encoded_jwt}
    else:
        raise HTTPException(status_code=401, detail="Invalid OTP code")

@app.get("/synthesize")
def synthesize(
    request: Request,
    text: str = Query(..., min_length=1),
    voice: str = Query("en_US-amy-low.onnx"),
    token: str = Query(None)
):
    is_admin = False
    client_ip = get_client_ip(request)

    # 1. AUTH CHECK & COUNTER RESET
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            if payload.get("sub") == "admin":
                is_admin = True
                # FEATURE: Admin login clears the counter for this IP
                today = datetime.utcnow().strftime("%Y-%m-%d")
                USER_QUOTAS[client_ip] = {"count": 0, "date": today}
        except JWTError:
            pass

    # 2. Logic Enforcement
    max_len = 5000 if is_admin else 500
    if len(text) > max_len:
        raise HTTPException(status_code=400, detail=f"Limit exceeded. Max {max_len} chars.")

    if not is_admin:
        if not is_quota_available(client_ip):
            raise HTTPException(status_code=429, detail="Daily limit reached.")

    # 3. Cache Check
    if voice not in VOICE_MODELS:
        voice = "en_US-amy-low.onnx"

    cache_key = hashlib.md5((voice + text).encode()).hexdigest()
    if cache_key in CACHE:
        if not is_admin: 
            USER_QUOTAS[client_ip]["count"] += 1
        return Response(content=CACHE[cache_key], media_type="audio/wav")

    # 4. Synthesis (Original Working Logic Restored)
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

    # 5. Increment Quota for Non-Admins
    if not is_admin:
        USER_QUOTAS[client_ip]["count"] += 1

    return Response(content=audio_data, media_type="audio/wav")