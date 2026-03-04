import os
import hashlib
import time
from datetime import datetime
from threading import Lock
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from piper.voice import PiperVoice
from jose import JWTError, jwt
import pyotp

app = FastAPI()

# --- CONFIGURATION ---
# Use environment variables for production; these are defaults for development
ADMIN_OTP_SECRET = os.getenv("ADMIN_OTP_SECRET", "JBSWY3DPEHPK3PXP")
JWT_SECRET = os.getenv("JWT_SECRET", "echo-sonic-gold-master-2026")
ALGORITHM = "HS256"

# --- CACHE & QUOTA STORAGE ---
synthesis_lock = Lock()
audio_cache_dir = "cache"
os.makedirs(audio_cache_dir, exist_ok=True)

# Daily Quota Tracker: { "IP": {"count": 0, "date": "YYYY-MM-DD"} }
user_quotas = {}

# --- VOICE MODELS ---
MODEL_PATH = "engine-python"
voices = {
    "en_US-amy-low.onnx": PiperVoice.load(os.path.join(MODEL_PATH, "en_US-amy-low.onnx")),
    "en_US-ryan-low.onnx": PiperVoice.load(os.path.join(MODEL_PATH, "en_US-ryan-low.onnx"))
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UTILS ---
def get_client_ip(request: Request):
    """Detects real user IP even behind Cloud Run or Codespace proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can be a list; the first one is the original client
        return forwarded.split(",")[0].strip()
    return request.client.host

def is_quota_available(ip: str):
    """Checks if a non-admin user has exceeded their daily limit of 5 requests."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Initialize or Reset if the date has changed (Daily Reset)
    if ip not in user_quotas or user_quotas[ip]["date"] != today:
        user_quotas[ip] = {"count": 0, "date": today}
    
    return user_quotas[ip]["count"] < 5

# --- ROUTES ---

@app.get("/verify-otp")
async def verify_otp(code: str):
    totp = pyotp.TOTP(ADMIN_OTP_SECRET)
    if totp.verify(code):
        # Admin token valid for 24 hours
        token = jwt.encode({"sub": "admin", "exp": time.time() + 86400}, JWT_SECRET, algorithm=ALGORITHM)
        return {"success": True, "token": token}
    return {"success": False}

@app.get("/synthesize")
async def synthesize(request: Request, text: str, voice: str = "en_US-amy-low.onnx", token: str = None):
    is_admin = False
    client_ip = get_client_ip(request)

    # 1. ADMIN AUTHENTICATION CHECK
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            if payload.get("sub") == "admin":
                is_admin = True
        except JWTError:
            is_admin = False

    # 2. ENFORCE LIMITS FOR NON-ADMIN USERS
    if not is_admin:
        # Character Limit Check
        if len(text) > 500:
            raise HTTPException(status_code=400, detail="Text exceeds 500 character limit.")
        
        # IP Quota Check (5 requests/day)
        if not is_quota_available(client_ip):
            raise HTTPException(status_code=429, detail="Daily limit of 5 reached. Use Admin mode.")

    # 3. AUDIO CACHING (MD5 of text + voice)
    cache_key = hashlib.md5(f"{text}_{voice}".encode()).hexdigest()
    cache_path = os.path.join(audio_cache_dir, f"{cache_key}.wav")

    # If already synthesized, serve from cache and increment count for non-admins
    if os.path.exists(cache_path):
        if not is_admin:
            user_quotas[client_ip]["count"] += 1
        return FileResponse(cache_path)

    # 4. SYNTHESIS ENGINE
    if voice not in voices:
        raise HTTPException(status_code=404, detail="Voice model not found")

    # Synthesis is wrapped in a lock for thread safety
    with synthesis_lock:
        with open(cache_path, "wb") as wav_file:
            voices[voice].synthesize(text, wav_file)

    # 5. INCREMENT QUOTA AFTER SUCCESSFUL SYNTHESIS
    if not is_admin:
        user_quotas[client_ip]["count"] += 1

    return FileResponse(cache_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)