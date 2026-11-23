import os
from dotenv import load_dotenv
load_dotenv()  # <--- THIS IS THE FIX: Loads your API keys from .env

from celery import Celery

# Connect to the Redis container running on port 6379
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "course_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)