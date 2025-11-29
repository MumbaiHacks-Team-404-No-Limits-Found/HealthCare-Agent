"""Celery tasks for SMS notifications via NotificationAPI."""
import asyncio
from typing import Optional
import logging

from app.celery_worker import celery_app
from app.notificationapi_sms import (
    send_sms_notification,
    send_assignment_notification_via_notificationapi,
    send_reminder_notification_via_notificationapi
)

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Helper to run async functions in Celery tasks.
    
    Creates a new event loop if one doesn't exist, runs the coroutine,
    and returns the result.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


@celery_app.task(
    name="send_sms_to_volunteer",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, Exception),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,
    max_retries=3
)
def send_sms_to_volunteer(self, volunteer_id: str, phone_number: str, message: str, notification_type: str = "volunteer_alert"):
    """
    Celery task to send an SMS notification to a volunteer via NotificationAPI.
    
    This task is designed to be queued and executed asynchronously by Celery workers.
    It handles retry logic automatically for transient failures.
    
    Args:
        volunteer_id: Unique identifier for the volunteer
        phone_number: Recipient phone number in E.164 format (e.g., +919800000001)
        message: SMS message text to send
        notification_type: NotificationAPI notification type/template ID (default: "volunteer_alert")
        
    Returns:
        Dictionary with:
        - success: bool - Whether the SMS was sent successfully
        - notification_id: str - NotificationAPI notification ID (if successful)
        - status: str - Status of the notification
        - to: str - Recipient phone number
        - timestamp: str - ISO timestamp when message was sent
        - error: str - Error message (if failed)
        
    Raises:
        Exception: If message sending fails after all retries
    """
    try:
        logger.info(
            f"[Task {self.request.id}] Sending SMS to volunteer {volunteer_id} "
            f"at {phone_number} (attempt {self.request.retries + 1}/{self.max_retries + 1})"
        )
        
        # Run the async notification function
        result = run_async(
            send_sms_notification(
                volunteer_id=volunteer_id,
                phone_number=phone_number,
                message=message,
                notification_type=notification_type
            )
        )
        
        if result["success"]:
            logger.info(
                f"[Task {self.request.id}] SMS sent successfully to {phone_number} - "
                f"Notification ID: {result.get('notification_id')}"
            )
        else:
            logger.error(
                f"[Task {self.request.id}] SMS failed to send to {phone_number} - "
                f"Error: {result.get('error')}"
            )
            # Raise exception to trigger retry
            raise Exception(result.get("error", "Unknown error sending SMS"))
        
        return result
        
    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] SMS task failed for volunteer {volunteer_id}: {exc}"
        )
        
        # If we've exhausted retries, log and return failure result
        if self.request.retries >= self.max_retries:
            logger.error(
                f"[Task {self.request.id}] Max retries reached. SMS to {phone_number} permanently failed."
            )
            return {
                "success": False,
                "notification_id": None,
                "status": "failed",
                "to": phone_number,
                "error": f"Max retries exceeded: {str(exc)}"
            }
        
        # Otherwise, retry with exponential backoff
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries * 60, 600))


@celery_app.task(
    name="send_assignment_notification",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, Exception),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3
)
def send_assignment_notification_task(
    self,
    volunteer_id: str,
    phone_number: str,
    volunteer_name: str,
    camp_name: str,
    role: str,
    slot: str,
    camp_location: Optional[str] = None,
    camp_date: Optional[str] = None
):
    """
    Celery task to send assignment notification to a volunteer.
    
    Args:
        volunteer_id: Volunteer's unique identifier
        phone_number: Volunteer phone number (E.164 format preferred)
        volunteer_name: Volunteer's name
        camp_name: Camp name
        role: Assigned role
        slot: Assigned time slot
        camp_location: Optional camp location
        camp_date: Optional camp date
        
    Returns:
        Dictionary with success status and details
    """
    try:
        logger.info(
            f"[Task {self.request.id}] Sending assignment notification to {volunteer_name} "
            f"({phone_number}) for {camp_name}"
        )
        
        success = run_async(
            send_assignment_notification_via_notificationapi(
                volunteer_id=volunteer_id,
                phone_number=phone_number,
                volunteer_name=volunteer_name,
                camp_name=camp_name,
                role=role,
                slot=slot,
                camp_location=camp_location,
                camp_date=camp_date
            )
        )
        
        if success:
            logger.info(
                f"[Task {self.request.id}] Assignment notification sent successfully to {volunteer_name}"
            )
            return {
                "success": True,
                "volunteer_id": volunteer_id,
                "volunteer_name": volunteer_name,
                "camp_name": camp_name
            }
        else:
            raise Exception("Failed to send assignment notification")
        
    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] Assignment notification failed for {volunteer_name}: {exc}"
        )
        
        if self.request.retries >= self.max_retries:
            logger.error(
                f"[Task {self.request.id}] Max retries reached for assignment notification"
            )
            return {
                "success": False,
                "volunteer_id": volunteer_id,
                "error": str(exc)
            }
        
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries * 60, 600))


@celery_app.task(
    name="send_reminder_notification",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, Exception),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3
)
def send_reminder_notification_task(
    self,
    volunteer_id: str,
    phone_number: str,
    volunteer_name: str,
    camp_name: str,
    camp_location: str,
    role: str,
    slot: str,
    reminder_window: str
):
    """
    Celery task to send reminder notification to a volunteer.
    
    Args:
        volunteer_id: Volunteer's unique identifier
        phone_number: Volunteer phone number (E.164 format preferred)
        volunteer_name: Volunteer's name
        camp_name: Camp name
        camp_location: Camp location
        role: Assigned role
        slot: Assigned time slot
        reminder_window: Time window for reminder (e.g., "24h", "6h", "1h")
        
    Returns:
        Dictionary with success status and details
    """
    try:
        logger.info(
            f"[Task {self.request.id}] Sending {reminder_window} reminder to {volunteer_name} "
            f"({phone_number}) for {camp_name}"
        )
        
        success = run_async(
            send_reminder_notification_via_notificationapi(
                volunteer_id=volunteer_id,
                phone_number=phone_number,
                volunteer_name=volunteer_name,
                camp_name=camp_name,
                camp_location=camp_location,
                role=role,
                slot=slot,
                reminder_window=reminder_window
            )
        )
        
        if success:
            logger.info(
                f"[Task {self.request.id}] Reminder notification sent successfully to {volunteer_name}"
            )
            return {
                "success": True,
                "volunteer_id": volunteer_id,
                "volunteer_name": volunteer_name,
                "reminder_window": reminder_window
            }
        else:
            raise Exception("Failed to send reminder notification")
        
    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] Reminder notification failed for {volunteer_name}: {exc}"
        )
        
        if self.request.retries >= self.max_retries:
            logger.error(
                f"[Task {self.request.id}] Max retries reached for reminder notification"
            )
            return {
                "success": False,
                "volunteer_id": volunteer_id,
                "error": str(exc)
            }
        
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries * 60, 600))


@celery_app.task(name="send_batch_sms")
def send_batch_sms_task(notifications: list):
    """
    Send a batch of SMS notifications.
    
    Args:
        notifications: List of dictionaries, each containing:
            - volunteer_id: str
            - phone_number: str
            - message: str
            - notification_type: str (optional, defaults to "volunteer_alert")
            
    Returns:
        Dictionary with batch results
    """
    results = []
    
    for notif in notifications:
        try:
            # Queue individual SMS task
            task = send_sms_to_volunteer.delay(
                volunteer_id=notif["volunteer_id"],
                phone_number=notif["phone_number"],
                message=notif["message"],
                notification_type=notif.get("notification_type", "volunteer_alert")
            )
            
            results.append({
                "volunteer_id": notif["volunteer_id"],
                "task_id": task.id,
                "status": "queued"
            })
        except Exception as e:
            logger.error(f"Failed to queue SMS for volunteer {notif['volunteer_id']}: {e}")
            results.append({
                "volunteer_id": notif["volunteer_id"],
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "success": True,
        "total": len(notifications),
        "results": results
    }

