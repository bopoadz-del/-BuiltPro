"""Fast queue tasks - Quick operations that should complete quickly."""

from datetime import datetime, timedelta
from backend.jobs.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_notification(self, user_id: int, message: str, notification_type: str = "info"):
    """Send a notification to a user."""
    try:
        logger.info(f"Sending {notification_type} notification to user {user_id}")
        return {"status": "sent", "user_id": user_id, "type": notification_type}
    except Exception as exc:
        logger.error(f"Failed to send notification: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task
def cleanup_old_sessions():
    """Cleanup expired or old conversation sessions."""
    try:
        logger.info("Running session cleanup")
        cutoff = datetime.utcnow() - timedelta(days=30)
        return {"status": "completed", "cutoff": cutoff.isoformat()}
    except Exception as exc:
        logger.error(f"Session cleanup failed: {exc}")
        return {"status": "error", "error": str(exc)}


@celery_app.task
def log_audit_event(event_type: str, user_id: int, details: dict):
    """Log an audit event."""
    logger.info(f"Audit: {event_type} by user {user_id}")
    return {"status": "logged", "event": event_type}
