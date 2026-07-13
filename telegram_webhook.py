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
HOLIDAY_FILE = 'tests/v2soft_attendance/holidays.json'

def send_telegram_message(text):
    """Sends a message back to the Telegram user."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Telegram API response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def trigger_gitlab_pipeline():
    """Triggers the GitLab pipeline using the correct query parameters."""
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/trigger/pipeline"
    
    # GitLab Trigger API expects token and ref as query parameters
    params = {
        "token": GITLAB_TRIGGER_TOKEN,
        "ref": "main"
    }
    
    try:
        print(f"Triggering GitLab pipeline for Project ID: {GITLAB_PROJECT_ID}...")
        response = requests.post(url, params=params, timeout=15)
        
        # Logging for Cloud Run debugging
        print(f"GitLab API Status Code: {response.status_code}")
        if response.status_code == 201:
            print("Successfully triggered GitLab pipeline!")
        else:
            print(f"GitLab API Error Response: {response.text}")
            
    except Exception as exc:
        print(f"Pipeline trigger failed due to exception: {exc}")

@router.post("/webhook/gitlab")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        update = await request.json()
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))
        
        # Debugging: Log the incoming message
        print(f"Received message: '{text}' from chat_id: {chat_id}")
        
        if chat_id != TELEGRAM_CHAT_ID:
            print(f"Unauthorized chat_id: {chat_id}")
            return {"status": "OK"}
    except Exception as e:
        print(f"Error parsing request: {e}")
        return {"status": "error"}

    # 1. Pipeline Trigger
    if text == "/run_pipeline":
        background_tasks.add_task(trigger_gitlab_pipeline)
        send_telegram_message("Pipeline trigger initiated! 🚀")

    # 2. List Holidays
    elif text == "/listholidays":
        try:
            with open(HOLIDAY_FILE, 'r') as f:
                data = json.load(f)
                hols = data.get("holidays", [])
                msg = "📅 Current Holiday Manifest:\n• " + "\n• ".join(hols) if hols else "Manifest is empty."
                send_telegram_message(msg)
        except Exception as e:
            send_telegram_message(f"Error reading holidays: {e}")

    # 3. Add Holiday
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
                else:
                    send_telegram_message("Date already exists.")
        except Exception as e:
            send_telegram_message(f"Error adding holiday: {e}")

    # 4. Delete Holiday
    elif text.startswith("/delholiday "):
        del_date = text.replace("/delholiday ", "").strip()
        try:
            with open(HOLIDAY_FILE, 'r+') as f:
                data = json.load(f)
                if del_date in data["holidays"]:
                    data["holidays"].remove(del_date)
                    f.seek(0); json.dump(data, f, indent=2); f.truncate()
                    send_telegram_message(f"🗑️ Removed: {del_date}")
                else:
                    send_telegram_message("Date not found.")
        except Exception as e:
            send_telegram_message(f"Error deleting holiday: {e}")

    return {"status": "OK"}
