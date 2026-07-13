import os
import requests
from fastapi import APIRouter, Request, BackgroundTasks

router = APIRouter()

GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN")

# This is the function that will run in the background
def trigger_gitlab_pipeline():
    try:
        response = requests.post(
            f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/trigger/pipeline",
            data={
                "token": GITLAB_TRIGGER_TOKEN,
                "ref": "main",
            },
            timeout=10,
        )
        # Optional: Print the result to your Google Cloud Logs
        print(f"GitLab API Response: {response.status_code}")
    except Exception as exc:
        print(f"Pipeline trigger failed: {exc}")

@router.post("/webhook/gitlab")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    update = await request.json()

    # Check for the message
    if (
        update.get("message")
        and update["message"].get("text") == "/run_pipeline"
    ):
        # Add the trigger function to background tasks
        background_tasks.add_task(trigger_gitlab_pipeline)

    # Return immediately so Telegram gets an instant 200 OK
    return {"status": "OK"}
