import os
import requests
import time
from fastapi import APIRouter, Request, BackgroundTasks

router = APIRouter()

# Variables are pulled from your Cloud Run Environment Settings
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN")

# Global variable to track the last trigger time (cooldown in seconds)
last_trigger_time = 0
COOLDOWN_SECONDS = 60

def trigger_gitlab_pipeline():
    """Function to call the GitLab API using query parameters."""
    url = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/trigger/pipeline"
    
    # GitLab Trigger API accepts tokens and refs as query parameters
    params = {
        "token": GITLAB_TRIGGER_TOKEN,
        "ref": "main"  # Ensure 'main' is your project's default branch
    }
    
    try:
        response = requests.post(url, params=params, timeout=10)
        
        # Log status and the detailed response text from GitLab
        print(f"GitLab API Status: {response.status_code}")
        print(f"GitLab API Response Text: {response.text}")
        
    except Exception as exc:
        print(f"Pipeline trigger failed: {exc}")

@router.post("/webhook/gitlab")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    global last_trigger_time
    try:
        update = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    current_time = time.time()

    # Check for the specific command in the Telegram message
    message = update.get("message", {})
    text = message.get("text", "")

    if text == "/run_pipeline":
        # Cooldown logic: only trigger if more than 60 seconds have passed
        if current_time - last_trigger_time > COOLDOWN_SECONDS:
            last_trigger_time = current_time
            # Offload the blocking request to a background task
            background_tasks.add_task(trigger_gitlab_pipeline)
            print("Pipeline trigger initiated.")
        else:
            print("Command ignored: Cooldown active (wait 60s).")
    else:
        print(f"Command ignored: Received '{text}'")

    # Return immediately to acknowledge the webhook to Telegram
    return {"status": "OK"}
