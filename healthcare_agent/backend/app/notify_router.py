"""REST endpoints for outbound notifications."""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from bson import ObjectId

from app.notifications import send_whatsapp_message, send_whatsapp_message_with_template
from app.tasks.sms_tasks import (
    send_sms_to_volunteer,
    send_assignment_notification_task,
    send_reminder_notification_task,
    send_batch_sms_task
)
from app.database import get_collection

logger = logging.getLogger(__name__)
router = APIRouter()


class WhatsAppRequest(BaseModel):
    """Request model for sending WhatsApp message."""
    phone: str = Field(..., description="Recipient phone number (will be auto-formatted)")
    message: str = Field(..., description="Message body text")


class WhatsAppTemplateRequest(BaseModel):
    """Request model for sending WhatsApp message using content template."""
    phone: str = Field(..., description="Recipient phone number (will be auto-formatted)")
    content_sid: str = Field(..., description="Twilio content template SID")
    content_variables: Dict[str, str] = Field(..., description="Template variables as dictionary (e.g., {'1': '12/1', '2': '3pm'})")


class WhatsAppResponse(BaseModel):
    """Response model for WhatsApp message send."""
    sid: str
    status: str
    to: str
    timestamp: str
    delivered: bool


@router.post("/whatsapp", response_model=WhatsAppResponse)
async def send_whatsapp_notification(request: WhatsAppRequest):
    """
    Send outbound WhatsApp message via Twilio REST API.
    
    External Services:
        - Twilio REST API: Sends WhatsApp message via client.messages.create()
    
    Configuration Validation:
        - Validates TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
        - Raises ValueError with clear message if any are missing
        
    Phone Number Processing:
        - Auto-formats phone number with "whatsapp:" prefix using format_whatsapp_number()
        - Normalizes phone number to E.164 format first
        - Handles Indian numbers (10 digits starting with 9 -> +91)
        - Handles US numbers (10 digits -> +1)
    
    Side Effects:
        - Logs message SID for tracking
        - Calls Twilio REST API synchronously (via asyncio.to_thread)
    
    Args:
        request: WhatsAppRequest with:
            - phone: str (recipient phone number, will be auto-formatted)
            - message: str (message body text)
        
    Returns:
        WhatsAppResponse with:
        - sid: Twilio message SID (e.g., "SMxxxxxxxxxxxx")
        - status: Message status (e.g., "queued", "sent", "delivered")
        - to: Formatted recipient number (e.g., "whatsapp:+919800000001")
        - timestamp: ISO timestamp when message was sent
        - delivered: bool (True if status in ["delivered","sent","read"])
        
    Raises:
        HTTPException 400: If Twilio configuration is missing
            Detail: Clear error message indicating which env var is missing
        HTTPException 500: If message sending fails
            Detail: "Failed to send WhatsApp message: <error>"
    """
    try:
        result = await send_whatsapp_message(
            to=request.phone,
            body=request.message
        )
        
        return WhatsAppResponse(
            sid=result["sid"],
            status=result["status"],
            to=result["to"],
            timestamp=result["timestamp"],
            delivered=result["delivered"]
        )
        
    except ValueError as e:
        # Configuration error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Send error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send WhatsApp message: {str(e)}"
        )


@router.post("/whatsapp/template", response_model=WhatsAppResponse)
async def send_whatsapp_template_notification(request: WhatsAppTemplateRequest):
    """
    Send outbound WhatsApp message using Twilio content template.
    
    Uses Twilio's content template system for structured messages.
    This is useful for appointment confirmations and notifications.
    
    External Services:
        - Twilio REST API: Sends WhatsApp message with content_sid and content_variables
    
    Configuration Validation:
        - Validates TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
        - Raises ValueError if any are missing
        
    Phone Number Processing:
        - Auto-formats phone number with "whatsapp:" prefix
        - Normalizes phone number to E.164 format
    
    Args:
        request: WhatsAppTemplateRequest with:
            - phone: str (recipient phone number, will be auto-formatted)
            - content_sid: str (Twilio content template SID, e.g., 'HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
            - content_variables: dict (template variables, e.g., {"1": "12/1", "2": "3pm"})
        
    Returns:
        WhatsAppResponse with:
        - sid: Twilio message SID
        - status: Message status
        - to: Formatted recipient number
        - timestamp: ISO timestamp
        - delivered: bool
        
    Raises:
        HTTPException 400: If Twilio configuration is missing
        HTTPException 500: If message sending fails
    """
    try:
        result = await send_whatsapp_message_with_template(
            to=request.phone,
            content_sid=request.content_sid,
            content_variables=request.content_variables
        )
        
        return WhatsAppResponse(
            sid=result["sid"],
            status=result["status"],
            to=result["to"],
            timestamp=result["timestamp"],
            delivered=result["delivered"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send WhatsApp template message: {str(e)}"
        )


# ============================================================================
# NotificationAPI SMS Endpoints (New)
# ============================================================================


class SMSRequest(BaseModel):
    """Request model for sending SMS via NotificationAPI."""
    volunteer_id: str = Field(..., description="Volunteer unique identifier")
    phone: str = Field(..., description="Recipient phone number in E.164 format (e.g., +919800000001)")
    message: str = Field(..., description="SMS message text")
    notification_type: str = Field(default="volunteer_alert", description="NotificationAPI notification type/template ID")


class SMSResponse(BaseModel):
    """Response model for SMS send via NotificationAPI."""
    task_id: str
    status: str
    volunteer_id: str
    phone: str
    message: str


class AssignmentNotificationRequest(BaseModel):
    """Request model for sending assignment notification."""
    volunteer_id: str = Field(..., description="Volunteer's unique identifier")
    camp_name: Optional[str] = Field(None, description="Camp name (if not provided, will be fetched)")
    role: Optional[str] = Field(None, description="Assigned role (if not provided, will be fetched)")
    slot: Optional[str] = Field(None, description="Assigned slot (if not provided, will be fetched)")
    camp_location: Optional[str] = Field(None, description="Camp location")
    camp_date: Optional[str] = Field(None, description="Camp date")


class BatchSMSRequest(BaseModel):
    """Request model for sending batch SMS."""
    notifications: List[Dict[str, str]] = Field(
        ...,
        description="List of notifications, each with volunteer_id, phone_number, message, and optional notification_type"
    )


class WebhookEventRequest(BaseModel):
    """Request model for NotificationAPI webhook events."""
    eventType: str
    userId: str
    notificationId: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/sms", response_model=SMSResponse)
async def send_sms_notification(request: SMSRequest):
    """
    Send SMS notification to a volunteer via NotificationAPI (async with Celery).
    
    This endpoint queues the SMS sending task to Celery, which processes it asynchronously.
    The API responds immediately with a task ID for tracking.
    
    External Services:
        - NotificationAPI: Sends SMS via NotificationAPI SDK
        - Celery/Redis: Queues the task for asynchronous processing
    
    Configuration Validation:
        - Validates NOTIFICATIONAPI_CLIENT_ID and NOTIFICATIONAPI_CLIENT_SECRET
        - Raises ValueError if any are missing
        
    Phone Number Processing:
        - Expects phone number in E.164 format (e.g., +919800000001)
        - Normalizes phone number automatically
    
    Args:
        request: SMSRequest with:
            - volunteer_id: str (volunteer's unique identifier)
            - phone: str (recipient phone number in E.164 format)
            - message: str (SMS message text)
            - notification_type: str (optional, defaults to "volunteer_alert")
        
    Returns:
        SMSResponse with:
        - task_id: Celery task ID for tracking
        - status: "queued" indicating the task is queued for processing
        - volunteer_id: Volunteer ID
        - phone: Recipient phone number
        - message: Message text
        
    Raises:
        HTTPException 400: If NotificationAPI configuration is missing
        HTTPException 500: If task queuing fails
    """
    try:
        # Queue the SMS sending task
        task = send_sms_to_volunteer.delay(
            volunteer_id=request.volunteer_id,
            phone_number=request.phone,
            message=request.message,
            notification_type=request.notification_type
        )
        
        logger.info(
            f"SMS task queued - Task ID: {task.id}, Volunteer: {request.volunteer_id}, Phone: {request.phone}"
        )
        
        return SMSResponse(
            task_id=task.id,
            status="queued",
            volunteer_id=request.volunteer_id,
            phone=request.phone,
            message=request.message
        )
        
    except Exception as e:
        logger.error(f"Failed to queue SMS task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue SMS notification: {str(e)}"
        )


@router.post("/notify/{volunteer_id}")
async def notify_volunteer(volunteer_id: str, message: str):
    """
    Send SMS alert to a volunteer by ID (background task via Celery).
    
    Looks up the volunteer in the database, retrieves their phone number,
    and queues an SMS notification task.
    
    Args:
        volunteer_id: Volunteer's MongoDB ObjectId
        message: SMS message text to send
        
    Returns:
        JSON response with task ID and status
        
    Raises:
        HTTPException 404: If volunteer not found
        HTTPException 500: If task queuing fails
    """
    try:
        # Look up volunteer in MongoDB by ID
        volunteers_collection = get_collection("volunteers")
        volunteer = await volunteers_collection.find_one({"_id": ObjectId(volunteer_id)})
        
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")
        
        # Queue the SMS sending task
        task = send_sms_to_volunteer.delay(
            volunteer_id=str(volunteer_id),
            phone_number=volunteer["phone"],
            message=message
        )
        
        logger.info(
            f"Volunteer notification queued - Task ID: {task.id}, "
            f"Volunteer: {volunteer.get('name')}, Phone: {volunteer['phone']}"
        )
        
        return {
            "status": "Queued",
            "task_id": task.id,
            "volunteer_id": str(volunteer_id),
            "volunteer_name": volunteer.get("name"),
            "phone": volunteer["phone"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue volunteer notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue notification: {str(e)}"
        )


@router.post("/assignment/{volunteer_id}")
async def send_assignment_notification(volunteer_id: str, request: AssignmentNotificationRequest):
    """
    Send assignment notification to a volunteer.
    
    If camp details are not provided in the request, they will be fetched from the database
    using the volunteer's latest assignment.
    
    Args:
        volunteer_id: Volunteer's MongoDB ObjectId
        request: AssignmentNotificationRequest with optional camp details
        
    Returns:
        JSON response with task ID and status
        
    Raises:
        HTTPException 404: If volunteer not found
        HTTPException 500: If task queuing fails
    """
    try:
        # Look up volunteer in MongoDB by ID
        volunteers_collection = get_collection("volunteers")
        volunteer = await volunteers_collection.find_one({"_id": ObjectId(volunteer_id)})
        
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")
        
        # If camp details not provided, fetch from latest assignment
        camp_name = request.camp_name
        role = request.role
        slot = request.slot
        
        if not all([camp_name, role, slot]):
            assignments_collection = get_collection("assignments")
            latest_assignment = await assignments_collection.find_one(
                {"volunteer_id": ObjectId(volunteer_id)},
                sort=[("created_at", -1)]
            )
            
            if latest_assignment:
                # Fetch camp details if we have an assignment
                if not camp_name and latest_assignment.get("camp_id"):
                    camps_collection = get_collection("camps")
                    camp = await camps_collection.find_one({"_id": latest_assignment["camp_id"]})
                    if camp:
                        camp_name = camp.get("name", "Unknown Camp")
                
                role = role or latest_assignment.get("role", "Volunteer")
                slot = slot or latest_assignment.get("slot", "TBD")
        
        # Defaults if still not found
        camp_name = camp_name or "Medical Camp"
        role = role or "Volunteer"
        slot = slot or "TBD"
        
        # Queue the assignment notification task
        task = send_assignment_notification_task.delay(
            volunteer_id=str(volunteer_id),
            phone_number=volunteer["phone"],
            volunteer_name=volunteer.get("name", "Volunteer"),
            camp_name=camp_name,
            role=role,
            slot=slot,
            camp_location=request.camp_location,
            camp_date=request.camp_date
        )
        
        logger.info(
            f"Assignment notification queued - Task ID: {task.id}, "
            f"Volunteer: {volunteer.get('name')}, Camp: {camp_name}"
        )
        
        return {
            "status": "Queued",
            "task_id": task.id,
            "volunteer_id": str(volunteer_id),
            "volunteer_name": volunteer.get("name"),
            "camp_name": camp_name,
            "role": role,
            "slot": slot
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue assignment notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue assignment notification: {str(e)}"
        )


@router.post("/batch/sms")
async def send_batch_sms(request: BatchSMSRequest):
    """
    Send a batch of SMS notifications.
    
    Queues multiple SMS sending tasks to Celery for parallel processing.
    
    Args:
        request: BatchSMSRequest with list of notifications
        
    Returns:
        JSON response with batch task ID and status
        
    Raises:
        HTTPException 500: If batch task queuing fails
    """
    try:
        # Queue the batch SMS task
        task = send_batch_sms_task.delay(request.notifications)
        
        logger.info(f"Batch SMS task queued - Task ID: {task.id}, Count: {len(request.notifications)}")
        
        return {
            "status": "Queued",
            "task_id": task.id,
            "count": len(request.notifications)
        }
        
    except Exception as e:
        logger.error(f"Failed to queue batch SMS task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue batch SMS: {str(e)}"
        )


@router.post("/webhook")
async def notificationapi_webhook_handler(request: Request):
    """
    Webhook endpoint for NotificationAPI events (delivery receipts, etc.).
    
    NotificationAPI sends webhook callbacks to this endpoint to notify about:
    - SMS delivered
    - SMS failed
    - SMS bounced
    - User unsubscribed
    - Other notification-related events
    
    Configure this webhook URL in your NotificationAPI dashboard:
    https://app.notificationapi.com/settings/webhooks
    
    Args:
        request: FastAPI Request object containing the webhook payload
        
    Returns:
        JSON response acknowledging receipt
    """
    try:
        # Parse the webhook payload
        payload = await request.json()
        
        event_type = payload.get("eventType", "unknown")
        user_id = payload.get("userId")
        notification_id = payload.get("notificationId")
        event_status = payload.get("status")
        
        logger.info(
            f"NotificationAPI webhook received - "
            f"Event: {event_type}, User: {user_id}, Notification: {notification_id}, Status: {event_status}"
        )
        
        # Log the full payload for debugging
        logger.debug(f"Webhook payload: {payload}")
        
        # TODO: Implement event-specific handling
        # For example:
        # - Update database with delivery status
        # - Trigger follow-up actions for failed deliveries
        # - Track unsubscribe events
        # - Log metrics for monitoring
        
        if event_type == "SMS_DELIVERED":
            logger.info(f"SMS successfully delivered to user {user_id}")
            # Update database: mark notification as delivered
            
        elif event_type == "SMS_FAILED":
            logger.warning(f"SMS failed to deliver to user {user_id}")
            # Update database: mark notification as failed
            # Optionally: trigger retry or alternative notification method
            
        elif event_type == "SMS_BOUNCED":
            logger.warning(f"SMS bounced for user {user_id}")
            # Update database: mark phone number as invalid
            
        elif event_type == "UNSUBSCRIBED":
            logger.info(f"User {user_id} unsubscribed from notifications")
            # Update database: mark user as unsubscribed
        
        # Always return success to acknowledge receipt
        return {
            "status": "received",
            "eventType": event_type,
            "userId": user_id,
            "notificationId": notification_id
        }
        
    except Exception as e:
        logger.error(f"Failed to process NotificationAPI webhook: {e}")
        # Still return 200 to avoid webhook retries for parsing errors
        return {"status": "error", "message": str(e)}

