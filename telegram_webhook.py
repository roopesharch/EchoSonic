import os
import requests
import time
from fastapi import APIRouter, Request, BackgroundTasks

router = APIRouter()

GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN")

# Global variable to track the last trigger time (cooldown in seconds)
last_trigger_time = 0
COOLDOWN_SECONDS = 60

def trigger_gitlab_pipeline():
    """Function to call the GitLab API in the background."""
    try:
        response = requests.post(
            f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/trigger/pipeline",
            data={
                "token": GITLAB_TRIGGER_TOKEN,
                "ref": "main",
            },
            timeout=10,
        )
        print(f"GitLab API Response: {response.status_code}")
    except Exception as exc:
        print(f"Pipeline trigger failed: {exc}")

@router.post("/webhook/gitlab")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    global last_trigger_time
    update = await request.json()
    current_time = time.time()

    # Check for the specific command
    if (
        update.get("message")
        and update["message"].get("text") == "/run_pipeline"
    ):
        # Cooldown logic: only trigger if more than 60 seconds have passed
        if current_time - last_trigger_time > COOLDOWN_SECONDS:
            last_trigger_time = current_time
            # Offload the blocking request to a background task
            background_tasks.add_task(trigger_gitlab_pipeline)
            print("Pipeline trigger initiated.")
        else:
            print("Command ignored: Cooldown active (wait 60s).")

    # Return immediately to acknowledge the webhook to Telegram
    return {"status": "OK"}
