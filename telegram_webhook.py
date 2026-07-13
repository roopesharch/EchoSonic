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
# Note: Ensure this path is correct relative to where your container runs
HOLIDAY_FILE = 'tests/v2soft_attendance/holidays.json'

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    requests.post(url, json=payload)

def trigger_gitlab_pipeline():
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/trigger/pipeline"
    params = {"token": GITLAB_TRIGGER_TOKEN, "ref": "main"}
    try:
        requests.post(url, params=params, timeout=10)
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

    # 1. Pipeline Trigger
    if text == "/run_pipeline":
        background_tasks.add_task(trigger_gitlab_pipeline)
        send_telegram_message("Pipeline trigger initiated! 🚀")

    # 2. List Holidays
    elif text == "/listholidays":
        with open(HOLIDAY_FILE, 'r') as f:
            data = json.load(f)
            hols = data.get("holidays", [])
            msg = "📅 Current Holiday Manifest:\n• " + "\n• ".join(hols) if hols else "Manifest is empty."
            send_telegram_message(msg)

    # 3. Add Holiday
    elif text.startswith("/addholiday "):
        new_date = text.replace("/addholiday ", "").strip()
        with open(HOLIDAY_FILE, 'r+') as f:
            data = json.load(f)
            if new_date not in data["holidays"]:
                data["holidays"].append(new_date)
                data["holidays"].sort()
                f.seek(0); json.dump(data, f, indent=2); f.truncate()
                send_telegram_message(f"✅ Added: {new_date}")
            else:
                send_telegram_message("Date already exists.")

    # 4. Delete Holiday
    elif text.startswith("/delholiday "):
        del_date = text.replace("/delholiday ", "").strip()
        with open(HOLIDAY_FILE, 'r+') as f:
            data = json.load(f)
            if del_date in data["holidays"]:
                data["holidays"].remove(del_date)
                f.seek(0); json.dump(data, f, indent=2); f.truncate()
                send_telegram_message(f"🗑️ Removed: {del_date}")
            else:
                send_telegram_message("Date not found.")

    return {"status": "OK"}
