"""Twilio SMS and WhatsApp notification helpers for sending outbound messages."""
from typing import Optional, Dict, Any
import logging
import asyncio
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy import Twilio client (only if credentials are available)
_twilio_client = None


def get_twilio_client():
    """
    Get or create Twilio client instance.
    
    Returns:
        Twilio Client instance if credentials are configured, None otherwise
    """
    global _twilio_client
    
    if _twilio_client is not None:
        return _twilio_client
    
    # Check if Twilio credentials are configured
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning("Twilio credentials not configured. SMS notifications disabled.")
        return None
    
    try:
        from twilio.rest import Client
        _twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        return _twilio_client
    except ImportError:
        logger.warning("Twilio library not installed. SMS notifications disabled.")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")
        return None


async def send_assignment_notification(
    phone_number: str,
    volunteer_name: str,
    camp_name: str,
    role: str,
    slot: str,
    appointment_date: Optional[str] = None,
    appointment_time: Optional[str] = None,
    use_template: bool = False
) -> bool:
    """
    Send WhatsApp/SMS notification to volunteer about new assignment.
    
    Supports both plain text and content template modes.
    
    Args:
        phone_number: Volunteer phone number (E.164 format preferred)
        volunteer_name: Volunteer's name
        camp_name: Camp name
        role: Assigned role
        slot: Assigned time slot
        appointment_date: Appointment date (e.g., "12/1") - for template
        appointment_time: Appointment time (e.g., "3pm") - for template
        use_template: If True, use content template (requires content_sid in config)
        
    Returns:
        True if message sent successfully, False otherwise
    """
    client = get_twilio_client()
    if not client:
        logger.warning(f"Skipping notification to {phone_number}: Twilio not configured")
        return False
    
    # Check if we should use content template
    if use_template and settings.twilio_content_sid:
        try:
            # Use content template
            content_variables = {}
            
            # Map template variables (adjust based on your template structure)
            # Template variable "1" = appointment date (e.g., "12/1")
            # Template variable "2" = appointment time (e.g., "3pm")
            if appointment_date:
                content_variables["1"] = appointment_date
            else:
                # Try to extract date from camp start time if available
                # This would need camp object passed in - for now use "TBD"
                content_variables["1"] = "TBD"
            
            if appointment_time:
                content_variables["2"] = appointment_time
            else:
                # Use slot as time (e.g., "morning" -> "9am", "afternoon" -> "2pm")
                slot_to_time = {
                    "morning": "9am",
                    "afternoon": "2pm",
                    "evening": "6pm"
                }
                content_variables["2"] = slot_to_time.get(slot.lower(), slot)
            
            # Optional: Add more variables if your template supports them
            # content_variables["3"] = volunteer_name
            # content_variables["4"] = role
            # content_variables["5"] = camp_name
            
            result = await send_whatsapp_message_with_template(
                to=phone_number,
                content_sid=settings.twilio_content_sid,
                content_variables=content_variables
            )
            
            logger.info(
                f"WhatsApp template notification sent to {phone_number}: "
                f"SID={result['sid']}, Status={result['status']}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send template notification, falling back to plain text: {e}")
            # Fall through to plain text
    
    # Fallback to plain text message
    try:
        message_body = (
            f"Hi {volunteer_name}, you've been assigned to {camp_name} "
            f"as {role} for the {slot} slot. "
            f"Reply YES to confirm or NO to cancel."
        )
        
        # Use WhatsApp if configured, otherwise SMS
        if settings.twilio_whatsapp_from:
            result = await send_whatsapp_message(to=phone_number, body=message_body)
            logger.info(f"WhatsApp notification sent to {phone_number}: {result['sid']}")
        elif settings.twilio_phone_number:
            # Use asyncio.to_thread to avoid blocking the event loop
            def send_sync():
                from twilio.rest import Client as TwilioClient
                client_instance = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
                message = client_instance.messages.create(
                    body=message_body,
                    from_=settings.twilio_phone_number,
                    to=phone_number
                )
                return message.sid
            
            message_sid = await asyncio.to_thread(send_sync)
            logger.info(f"SMS notification sent to {phone_number}: {message_sid}")
        else:
            logger.warning(f"No Twilio phone number configured for notifications")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send notification to {phone_number}: {e}")
        return False


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format (basic implementation).
    
    This is a simple implementation. For production, consider using
    a library like phonenumbers for proper international formatting.
    
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


def format_whatsapp_number(phone: str) -> str:
    """
    Format phone number for WhatsApp messaging.
    
    Auto-prefixes with "whatsapp:" if not already prefixed.
    Normalizes the phone number first.
    
    Args:
        phone: Phone number (raw or normalized)
        
    Returns:
        WhatsApp-formatted number (e.g., "whatsapp:+919800000001")
    """
    # Remove whatsapp: prefix if present (we'll add it back)
    if phone.startswith("whatsapp:"):
        phone = phone[9:]  # Remove "whatsapp:" prefix
    
    # Normalize the phone number
    normalized = normalize_phone_number(phone)
    
    # Add whatsapp: prefix
    return f"whatsapp:{normalized}"


def validate_twilio_config() -> None:
    """
    Validate that Twilio configuration is present.
    
    Raises:
        ValueError: If required Twilio credentials are missing
    """
    if not settings.twilio_account_sid:
        raise ValueError(
            "TWILIO_ACCOUNT_SID is not configured. "
            "Please set it in environment variables or .env file."
        )
    
    if not settings.twilio_auth_token:
        raise ValueError(
            "TWILIO_AUTH_TOKEN is not configured. "
            "Please set it in environment variables or .env file."
        )
    
    if not settings.twilio_whatsapp_from:
        raise ValueError(
            "TWILIO_WHATSAPP_FROM is not configured. "
            "Please set it in environment variables or .env file (e.g., whatsapp:+14155238886)."
        )


async def send_whatsapp_message_with_template(
    to: str,
    content_sid: str,
    content_variables: Dict[str, str]
) -> Dict[str, Any]:
    """
    Send WhatsApp message using Twilio content template.
    
    Uses Twilio's content template system for structured messages.
    This is useful for appointment confirmations and notifications.
    
    Args:
        to: Recipient phone number (will be auto-formatted with whatsapp: prefix)
        content_sid: Twilio content template SID (e.g., 'HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        content_variables: Dictionary of template variables (e.g., {"1": "12/1", "2": "3pm"})
        
    Returns:
        Dictionary with:
        - sid: Twilio message SID
        - status: Message status
        - to: Formatted recipient number
        - timestamp: ISO timestamp
        - delivered: Boolean
        
    Raises:
        ValueError: If Twilio configuration is missing
        Exception: If message sending fails
    """
    # Validate configuration
    validate_twilio_config()
    
    # Format phone number for WhatsApp
    whatsapp_to = format_whatsapp_number(to)
    
    # Get Twilio client
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client initialization failed. Check credentials.")
    
    try:
        # Convert content_variables dict to JSON string
        import json
        content_variables_json = json.dumps(content_variables)
        
        # Send message using asyncio.to_thread to avoid blocking
        def send_sync():
            from twilio.rest import Client as TwilioClient
            client_instance = TwilioClient(
                settings.twilio_account_sid,
                settings.twilio_auth_token
            )
            message = client_instance.messages.create(
                from_=settings.twilio_whatsapp_from,
                to=whatsapp_to,
                content_sid=content_sid,
                content_variables=content_variables_json
            )
            return {
                "sid": message.sid,
                "status": message.status,
                "to": whatsapp_to,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
        
        result = await asyncio.to_thread(send_sync)
        
        # Determine if delivered (status-based)
        delivered = result["status"] in ("delivered", "sent", "read")
        
        response = {
            "sid": result["sid"],
            "status": result["status"],
            "to": whatsapp_to,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "delivered": delivered
        }
        
        logger.info(
            f"WhatsApp template message sent - SID: {result['sid']}, "
            f"To: {whatsapp_to}, Status: {result['status']}, Content SID: {content_sid}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp template message to {whatsapp_to}: {e}")
        raise


async def send_whatsapp_message(to: str, body: str) -> Dict[str, Any]:
    """
    Send WhatsApp message via Twilio.
    
    Primary API for outbound WhatsApp messaging.
    Auto-formats phone number with "whatsapp:" prefix.
    Validates Twilio configuration before sending.
    
    Args:
        to: Recipient phone number (will be auto-formatted with whatsapp: prefix)
        body: Message body text
        
    Returns:
        Dictionary with:
        - sid: Twilio message SID
        - status: Message status (queued, sent, delivered, etc.)
        - to: Formatted recipient number
        - timestamp: ISO timestamp when message was sent
        - delivered: Boolean indicating if message was delivered (may be None if status unknown)
        
    Raises:
        ValueError: If Twilio configuration is missing
        Exception: If message sending fails
    """
    # Validate configuration
    validate_twilio_config()
    
    # Format phone number for WhatsApp
    whatsapp_to = format_whatsapp_number(to)
    
    # Get Twilio client
    client = get_twilio_client()
    if not client:
        raise ValueError("Twilio client initialization failed. Check credentials.")
    
    try:
        # Send message using asyncio.to_thread to avoid blocking
        def send_sync():
            from twilio.rest import Client as TwilioClient
            client_instance = TwilioClient(
                settings.twilio_account_sid,
                settings.twilio_auth_token
            )
            message = client_instance.messages.create(
                body=body,
                from_=settings.twilio_whatsapp_from,
                to=whatsapp_to
            )
            return {
                "sid": message.sid,
                "status": message.status,
                "to": whatsapp_to,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
        
        result = await asyncio.to_thread(send_sync)
        
        # Determine if delivered (status-based)
        delivered = result["status"] in ("delivered", "sent", "read")
        
        response = {
            "sid": result["sid"],
            "status": result["status"],
            "to": whatsapp_to,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "delivered": delivered
        }
        
        logger.info(
            f"WhatsApp message sent - SID: {result['sid']}, "
            f"To: {whatsapp_to}, Status: {result['status']}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {whatsapp_to}: {e}")
        raise
