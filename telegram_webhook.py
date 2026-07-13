import os
import requests
import json
from fastapi import APIRouter, Request, BackgroundTasks

router = APIRouter()

# Environment Variables
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Calculate absolute path: 
# This assumes the script is in the root and 'tests' folder is also in the root
BASE_DIR = os.getcwd() 
HOLIDAY_FILE = os.path.join(BASE_DIR, 'tests', 'v2soft_attendance', 'holidays.json')

# Debugging path
print(f"DEBUG: Looking for holiday file at: {HOLIDAY_FILE}")
print(f"DEBUG: File exists: {os.path.exists(HOLIDAY_FILE)}")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def trigger_gitlab_pipeline():
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/trigger/pipeline"
    params = {"token": GITLAB_TRIGGER_TOKEN, "ref": "main"}
    try:
        requests.post(url, params=params, timeout=15)
    except Exception as exc:
        print(f"Pipeline trigger failed: {exc}")

@router.post("/webhook/gitlab")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        update = await request.json()
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))
        
        if chat_id != TELEGRAM_CHAT_ID:
            return {"status": "OK"}
    except:
        return {"status": "error"}

    if text == "/run_pipeline":
        background_tasks.add_task(trigger_gitlab_pipeline)
        send_telegram_message("Pipeline trigger initiated! 🚀")

    elif text == "/listholidays":
        try:
            with open(HOLIDAY_FILE, 'r') as f:
                data = json.load(f)
                hols = data.get("holidays", [])
                msg = "📅 Current Holiday Manifest:\n• " + "\n• ".join(hols) if hols else "Manifest is empty."
                send_telegram_message(msg)
        except Exception as e:
            send_telegram_message(f"Error reading: {e}")

    elif text.startswith("/addholiday "):
        new_date = text.replace("/addholiday ", "").strip()
        try:
            with open(HOLIDAY_FILE, 'r+') as f:
                data = json.load(f)
                if new_date not in data["holidays"]:
                    data["holidays"].append(new_date)
                    data["holidays"].sort()
                    f.seek(0); json.dump(data, f, indent=2); f.truncate()
                    send_telegram_message(f"✅ Added: {new_date}")
        except Exception as e:
            send_telegram_message(f"Error adding: {e}")

    elif text.startswith("/delholiday "):
        del_date = text.replace("/delholiday ", "").strip()
        try:
            with open(HOLIDAY_FILE, 'r+') as f:
                data = json.load(f)
                if del_date in data["holidays"]:
                    data["holidays"].remove(del_date)
                    f.seek(0); json.dump(data, f, indent=2); f.truncate()
                    send_telegram_message(f"🗑️ Removed: {del_date}")
        except Exception as e:
            send_telegram_message(f"Error deleting: {e}")

    return {"status": "OK"}
