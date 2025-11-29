"""NotificationAPI SMS notification helpers for sending outbound messages."""
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy import NotificationAPI client (only if credentials are available)
_notificationapi_client = None


def get_notificationapi_client():
    """
    Get or create NotificationAPI client instance.
    
    Returns:
        NotificationAPI client instance if credentials are configured, None otherwise
    """
    global _notificationapi_client
    
    if _notificationapi_client is not None:
        return _notificationapi_client
    
    # Check if NotificationAPI credentials are configured
    if not settings.notificationapi_client_id or not settings.notificationapi_client_secret:
        logger.warning("NotificationAPI credentials not configured. SMS notifications disabled.")
        return None
    
    try:
        from notificationapi_python_server_sdk import notificationapi
        
        # Initialize NotificationAPI with credentials
        notificationapi.init(
            settings.notificationapi_client_id,
            settings.notificationapi_client_secret
        )
        
        _notificationapi_client = notificationapi
        logger.info("NotificationAPI client initialized successfully")
        return _notificationapi_client
    except ImportError:
        logger.warning("NotificationAPI library not installed. SMS notifications disabled.")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize NotificationAPI client: {e}")
        return None


def validate_notificationapi_config() -> None:
    """
    Validate that NotificationAPI configuration is present.
    
    Raises:
        ValueError: If required NotificationAPI credentials are missing
    """
    if not settings.notificationapi_client_id:
        raise ValueError(
            "NOTIFICATIONAPI_CLIENT_ID is not configured. "
            "Please set it in environment variables or .env file."
        )
    
    if not settings.notificationapi_client_secret:
        raise ValueError(
            "NOTIFICATIONAPI_CLIENT_SECRET is not configured. "
            "Please set it in environment variables or .env file."
        )


async def send_sms_notification(
    volunteer_id: str,
    phone_number: str,
    message: str,
    notification_type: str = "volunteer_alert"
) -> Dict[str, Any]:
    """
    Send an SMS notification to a volunteer via NotificationAPI.
    
    Args:
        volunteer_id: Unique identifier for the volunteer (used as NotificationAPI user ID)
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
        ValueError: If NotificationAPI configuration is missing
        Exception: If message sending fails
    """
    # Validate configuration
    validate_notificationapi_config()
    
    # Get NotificationAPI client
    client = get_notificationapi_client()
    if not client:
        raise ValueError("NotificationAPI client initialization failed. Check credentials.")
    
    try:
        # Normalize phone number (remove spaces, dashes, etc.)
        normalized_phone = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Ensure E.164 format with + prefix
        if not normalized_phone.startswith("+"):
            # For Indian numbers, add +91 if it's 10 digits starting with 9
            if len(normalized_phone) == 10 and normalized_phone.startswith("9"):
                normalized_phone = "+91" + normalized_phone
            else:
                logger.warning(f"Phone number {phone_number} may not be in E.164 format")
        
        # Send notification via NotificationAPI
        await client.send({
            "notificationId": notification_type,
            "user": {
                "id": volunteer_id,
                "number": normalized_phone
            },
            "mergeTags": {
                "message": message
            }
        })
        
        logger.info(
            f"SMS notification sent via NotificationAPI - "
            f"Volunteer ID: {volunteer_id}, Phone: {normalized_phone}, Type: {notification_type}"
        )
        
        return {
            "success": True,
            "notification_id": f"notif_{volunteer_id}_{int(datetime.utcnow().timestamp())}",
            "status": "queued",
            "to": normalized_phone,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": None
        }
        
    except Exception as e:
        error_msg = f"Failed to send SMS via NotificationAPI: {str(e)}"
        logger.error(f"{error_msg} - Volunteer: {volunteer_id}, Phone: {phone_number}")
        
        return {
            "success": False,
            "notification_id": None,
            "status": "failed",
            "to": phone_number,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error_msg
        }


async def send_assignment_notification_via_notificationapi(
    volunteer_id: str,
    phone_number: str,
    volunteer_name: str,
    camp_name: str,
    role: str,
    slot: str,
    camp_location: Optional[str] = None,
    camp_date: Optional[str] = None
) -> bool:
    """
    Send SMS notification to volunteer about new assignment via NotificationAPI.
    
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
        True if message sent successfully, False otherwise
    """
    try:
        # Build message body
        message_parts = [
            f"Hi {volunteer_name}, you've been assigned to {camp_name}",
            f"as {role} for the {slot} slot."
        ]
        
        if camp_location:
            message_parts.append(f"Location: {camp_location}")
        
        if camp_date:
            message_parts.append(f"Date: {camp_date}")
        
        message_parts.append("Reply YES to confirm or NO to cancel.")
        
        message_body = " ".join(message_parts)
        
        # Send notification
        result = await send_sms_notification(
            volunteer_id=volunteer_id,
            phone_number=phone_number,
            message=message_body,
            notification_type="volunteer_assignment"
        )
        
        return result["success"]
        
    except Exception as e:
        logger.error(f"Failed to send assignment notification to {phone_number}: {e}")
        return False


async def send_reminder_notification_via_notificationapi(
    volunteer_id: str,
    phone_number: str,
    volunteer_name: str,
    camp_name: str,
    camp_location: str,
    role: str,
    slot: str,
    reminder_window: str
) -> bool:
    """
    Send reminder notification to volunteer about upcoming assignment.
    
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
        True if message sent successfully, False otherwise
    """
    try:
        message_body = (
            f"Reminder: Hi {volunteer_name}, you have an assignment at {camp_name} "
            f"({camp_location}) as {role} for {slot} slot. "
            f"Camp starts in {reminder_window}."
        )
        
        result = await send_sms_notification(
            volunteer_id=volunteer_id,
            phone_number=phone_number,
            message=message_body,
            notification_type="volunteer_reminder"
        )
        
        return result["success"]
        
    except Exception as e:
        logger.error(f"Failed to send reminder notification to {phone_number}: {e}")
        return False


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format (basic implementation).
    
    Handles:
    - Indian numbers: 10 digits starting with 9 -> +91
    - US numbers: 10 digits -> +1
    - Numbers already with country code -> keep as is
    
    Args:
        phone: Phone number string (may include spaces, dashes, etc.)
        
    Returns:
        Normalized phone number string
    """
    # Remove common separators
    normalized = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # If it doesn't start with +, try to determine country code
    if not normalized.startswith("+"):
        digits_only = ''.join(filter(str.isdigit, normalized))
        
        # Indian number: 10 digits starting with 9
        if len(digits_only) == 10 and digits_only.startswith("9"):
            normalized = "+91" + digits_only
        # US number: 10 digits
        elif len(digits_only) == 10:
            normalized = "+1" + digits_only
        # US number: 11 digits starting with 1
        elif len(digits_only) == 11 and digits_only.startswith("1"):
            normalized = "+" + digits_only
        # Keep as is if we can't determine
        else:
            normalized = digits_only if digits_only else normalized
    
    return normalized

