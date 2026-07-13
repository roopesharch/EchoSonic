import os
import requests
from supabase import create_client, Client
from fastapi import APIRouter, Request, BackgroundTasks

router = APIRouter()

# Environment Variables
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_telegram_message(text):
    """Sends a message back to the Telegram user."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def trigger_gitlab_pipeline():
    """Triggers the GitLab pipeline."""
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/trigger/pipeline"
    params = {"token": GITLAB_TRIGGER_TOKEN, "ref": "main"}
    try:
        requests.post(url, params=params, timeout=15)
    except Exception as exc:
        print(f"Pipeline trigger failed: {exc}")

@router.post("/webhook/gitlab")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    # 1. Parse incoming Telegram update
    try:
        update = await request.json()
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))
        
        # Security: Only allow your authorized chat_id
        if chat_id != TELEGRAM_CHAT_ID:
            return {"status": "OK"}
    except:
        return {"status": "error"}

    # 2. Logic Commands
    if text == "/run_pipeline":
        background_tasks.add_task(trigger_gitlab_pipeline)
        send_telegram_message("Pipeline trigger initiated! 🚀")

    elif text == "/listholidays":
        try:
            # Query Supabase: Select all 'date' entries
            response = supabase.table("holidays").select("date").execute()
            hols = [item['date'] for item in response.data]
            msg = "📅 Current Holiday Manifest:\n• " + "\n• ".join(sorted(hols)) if hols else "Manifest is empty."
            send_telegram_message(msg)
        except Exception as e:
            send_telegram_message(f"Error fetching from DB: {e}")

    elif text.startswith("/addholiday "):
        new_date = text.replace("/addholiday ", "").strip()
        try:
            # Insert into Supabase
            supabase.table("holidays").insert({"date": new_date}).execute()
            send_telegram_message(f"✅ Added: {new_date}")
        except Exception as e:
            send_telegram_message(f"Error adding: {e}")

    elif text.startswith("/delholiday "):
        del_date = text.replace("/delholiday ", "").strip()
        try:
            # Delete from Supabase
            supabase.table("holidays").delete().eq("date", del_date).execute()
            send_telegram_message(f"🗑️ Removed: {del_date}")
        except Exception as e:
            send_telegram_message(f"Error deleting: {e}")

    return {"status": "OK"}
