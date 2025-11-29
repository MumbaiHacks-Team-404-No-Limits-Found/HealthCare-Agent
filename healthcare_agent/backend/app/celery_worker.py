"""Celery worker configuration for background tasks and scheduled automation."""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Create Celery app
celery_app = Celery(
    "agentic_coordinator",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.forecast_tasks",
        "app.tasks.planner_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.scheduler_tasks",
        "app.tasks.sms_tasks"
    ]
)

# Celery configuration for production resilience
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Prevent workers from reserving too many tasks
    worker_max_tasks_per_child=50,
    task_acks_late=True,  # Acknowledge tasks only after completion (allows retry on worker death)
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    # Retry configuration for transient failures
    task_autoretry_for=(ConnectionError, TimeoutError, Exception),  # Retry on network errors
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max 10 minutes between retries
    task_retry_jitter=True,  # Add randomness to backoff
    task_max_retries=3,  # Maximum 3 retries
)

# Periodic task schedule (Celery Beat)
celery_app.conf.beat_schedule = {
    # Daily forecast for all active camps
    "daily-forecast": {
        "task": "app.tasks.forecast_tasks.run_daily_forecast_all_camps",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight UTC
        "args": []
    },
    # Auto-replan check every 30 minutes
    "auto-replan": {
        "task": "app.tasks.planner_tasks.replan_if_needed",
        "schedule": 1800.0,  # Every 30 minutes (in seconds)
        "args": []
    },
    # Send upcoming reminders every hour
    "send-upcoming-reminders": {
        "task": "app.tasks.notification_tasks.send_upcoming_reminder_batch",
        "schedule": 3600.0,  # Every hour (in seconds)
        "args": []
    },
    # Check for camps needing initial planning (every 15 minutes)
    "auto-plan-new-camps": {
        "task": "app.tasks.planner_tasks.auto_plan_new_camps",
        "schedule": 900.0,  # Every 15 minutes
        "args": []
    }
}

