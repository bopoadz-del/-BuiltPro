"""Celery configuration with 3 queues and beat scheduler."""

from celery import Celery
from celery.schedules import crontab
import os

# Broker and backend URLs
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "builtpro",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "backend.tasks.fast_tasks",
        "backend.tasks.slow_tasks",
        "backend.tasks.event_tasks",
    ],
)

# Configure queues
celery_app.conf.task_routes = {
    "backend.tasks.fast_tasks.*": {"queue": "fast"},
    "backend.tasks.slow_tasks.*": {"queue": "slow"},
    "backend.tasks.event_tasks.*": {"queue": "trigger_events"},
}

# Default queue
celery_app.conf.task_default_queue = "fast"
celery_app.conf.task_default_exchange = "fast"
celery_app.conf.task_default_routing_key = "fast"

# Serialization
celery_app.conf.task_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.result_serializer = "json"

# Result backend settings
celery_app.conf.result_expires = 3600  # 1 hour
celery_app.conf.result_backend = REDIS_URL

# Task execution settings
celery_app.conf.task_track_started = True
celery_app.conf.task_time_limit = 3600  # 1 hour hard limit
celery_app.conf.task_soft_time_limit = 300  # 5 minutes soft limit

# Worker settings
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.worker_max_tasks_per_child = 1000

# Beat schedule
celery_app.conf.beat_schedule = {
    "cleanup-old-sessions": {
        "task": "backend.tasks.fast_tasks.cleanup_old_sessions",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "process-scheduled-events": {
        "task": "backend.tasks.event_tasks.process_scheduled_events",
        "schedule": 60.0,  # Every minute
    },
    "sync-connector-status": {
        "task": "backend.tasks.slow_tasks.sync_connector_status",
        "schedule": 300.0,  # Every 5 minutes
    },
}

# Timezone
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True
