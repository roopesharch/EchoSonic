import os
import requests
from fastapi import APIRouter, Request

router = APIRouter()

GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN")

@router.post("/webhook/gitlab")
async def telegram_webhook(request: Request):
    update = await request.json()

    if (
        update.get("message")
        and update["message"].get("text") == "/run_pipeline"
    ):
        try:
            requests.post(
                f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}/trigger/pipeline",
                data={
                    "token": GITLAB_TRIGGER_TOKEN,
                    "ref": "main",
                },
                timeout=10,
            )
        except Exception as exc:
            print(f"Pipeline trigger failed: {exc}")

    return {"status": "OK"}
