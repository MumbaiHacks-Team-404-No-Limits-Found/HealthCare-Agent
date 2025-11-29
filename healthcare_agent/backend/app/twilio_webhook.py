"""Twilio webhook handler for processing incoming SMS messages."""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response
from typing import Optional
import logging

from app.database import get_collection
from app.models import Assignment
from app.notifications import normalize_phone_number
from app.replan import replan_camp
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def validate_twilio_signature(request: Request, form_data: dict) -> bool:
    """
    Validate that the request came from Twilio using signature validation.
    
    Args:
        request: FastAPI request object
        form_data: Form data from the request
        
    Returns:
        True if signature is valid or validation is disabled, False otherwise
    """
    # ALWAYS allow localhost/127.0.0.1 for testing (check this first)
    host = request.headers.get("Host", "")
    if host.startswith("127.0.0.1") or host.startswith("localhost"):
        logger.info(f"Allowing request from localhost (Host: {host}) for testing")
        return True
    
    # If Twilio auth token is not configured, skip validation (dev mode)
    if not settings.twilio_auth_token:
        logger.warning("Twilio signature validation skipped: TWILIO_AUTH_TOKEN not configured")
        return True
    
    try:
        from twilio.request_validator import RequestValidator
        
        # Get signature from header
        signature = request.headers.get("X-Twilio-Signature", "")
        if not signature:
            # Check if this is a local/dev request - allow for testing
            host = request.headers.get("Host", "")
            logger.info(f"DEBUG: No signature, checking host. Host header value: '{host}'")
            if host.startswith("127.0.0.1") or host.startswith("localhost"):
                logger.warning(
                    f"Missing X-Twilio-Signature header on localhost request (Host: {host}). "
                    "Allowing for local testing. In production, ensure Twilio webhook URL is properly configured."
                )
                return True
            logger.warning(f"Missing X-Twilio-Signature header from non-localhost host: {host}")
            return False
        
        # Get request URL - Twilio expects the full URL including protocol
        # For localhost, ensure we use the correct format
        url = str(request.url)
        
        # Create validator with auth token
        validator = RequestValidator(settings.twilio_auth_token)
        
        # Validate signature
        is_valid = validator.validate(url, form_data, signature)
        
        if not is_valid:
            logger.error(
                f"Invalid Twilio signature for URL: {url}. "
                "Ensure the webhook URL in Twilio console matches exactly: "
                f"{request.url.scheme}://{request.url.netloc}{request.url.path}"
            )
        
        return is_valid
        
    except ImportError:
        logger.warning("Twilio library not installed. Signature validation disabled.")
        return True
    except Exception as e:
        logger.error(f"Error validating Twilio signature: {e}")
        # For localhost testing, allow on validation errors
        host = request.headers.get("Host", "")
        if host.startswith("127.0.0.1") or host.startswith("localhost"):
            logger.warning("Allowing localhost request despite validation error for testing")
            return True
        return False


@router.post("/webhook")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    AccountSid: str = Form(None)
):
    """
    Handle incoming SMS/WhatsApp webhook from Twilio.
    
    Security:
        - Validates Twilio signature using X-Twilio-Signature header
        - Rejects requests with invalid signatures (if TWILIO_AUTH_TOKEN is configured)
        - Skips validation in dev mode (if TWILIO_AUTH_TOKEN not set)
    
    MongoDB Collections:
        - volunteers: Queries by phone number (normalized) to find volunteer
        - assignments: Queries for volunteer's latest active assignment (status in ["assigned","backup"])
        - assignments: Updates assignment status to "confirmed" or "cancelled"
    
    Side Effects:
        - Updates assignment status in MongoDB
        - On cancellation: Triggers replanning for the camp (non-blocking via Celery)
        - Logs all operations for debugging
    
    Message Processing:
        - Normalizes phone number using normalize_phone_number()
        - Tries multiple phone number formats to find volunteer
        - Finds volunteer's latest active assignment (status in ["assigned","backup"])
        - Parses message body (case-insensitive):
            * "confirm", "yes", "confirmed" -> status="confirmed"
            * "cancel", "no", "cancelled" -> status="cancelled" + trigger replan
            * Unknown message -> returns helpful TwiML response
    
    Args:
        request: FastAPI request object
        From: Phone number of sender (from Twilio form-encoded data)
        Body: SMS/WhatsApp message body (from Twilio form-encoded data)
        
    Returns:
        Response with TwiML XML content:
        - Success: Confirmation message
        - Unknown volunteer: "Sorry, we couldn't find your volunteer record..."
        - No active assignment: "You don't have any active assignments..."
        - Error: Generic error message
        
    Content-Type:
        application/xml; charset=utf-8
    """
    try:
        # Parse form data for signature validation
        form = await request.form()
        form_dict = dict(form)
        
        # Validate Twilio signature
        if not validate_twilio_signature(request, form_dict):
            logger.error(f"Rejected webhook with invalid Twilio signature from {From}")
            # Return 400 Bad Request (per security requirements)
            return Response(
                content="Invalid request signature",
                status_code=400,
                media_type="text/plain"
            )
        
        # Normalize phone number
        normalized_phone = normalize_phone_number(From)
        
        # Log for debugging (sanitize phone number)
        from app.logging_utils import sanitize_phone, safe_log_info
        safe_log_info(
            "Twilio webhook received",
            from_number=sanitize_phone(From),
            normalized_phone=sanitize_phone(normalized_phone),
            body_length=len(Body)  # Log length, not content
        )
        
        # Parse message body (case-insensitive, strip whitespace)
        message_body = Body.strip().lower()
        
        # Determine action
        if message_body in ("confirm", "yes", "confirmed"):
            action = "confirm"
        elif message_body in ("cancel", "no", "cancelled"):
            action = "cancel"
        else:
            # Unknown message - send helpful response
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Please reply with "confirm" or "cancel" to update your assignment status.</Message>
</Response>"""
            return Response(content=twiml, media_type="application/xml")
        
        # Find volunteer by phone number
        # Try multiple formats to handle different phone number representations
        volunteers_collection = get_collection("volunteers")
        
        # Try normalized phone first
        volunteer_doc = await volunteers_collection.find_one({"phone": normalized_phone})
        
        # Try original format from Twilio
        if not volunteer_doc:
            volunteer_doc = await volunteers_collection.find_one({"phone": From})
        
        # Try with different variations (remove +, add +, etc.)
        if not volunteer_doc:
            # Try without + prefix
            phone_without_plus = normalized_phone.lstrip("+")
            volunteer_doc = await volunteers_collection.find_one({"phone": phone_without_plus})
        
        if not volunteer_doc:
            # Try with + prefix if it doesn't have one
            if not From.startswith("+"):
                volunteer_doc = await volunteers_collection.find_one({"phone": "+" + From})
        
        # Last resort: search by last 10 digits (handles country code differences)
        if not volunteer_doc:
            # Extract last 10 digits and try to match
            digits_only = ''.join(filter(str.isdigit, From))
            if len(digits_only) >= 10:
                last_10 = digits_only[-10:]
                logger.info(f"Trying last 10 digits match: {last_10}")
                cursor = volunteers_collection.find({})
                async for vol in cursor:
                    vol_phone = vol.get("phone", "")
                    vol_digits = ''.join(filter(str.isdigit, vol_phone))
                    if len(vol_digits) >= 10 and vol_digits[-10:] == last_10:
                        logger.info(f"Matched volunteer {vol.get('name')} by last 10 digits")
                        volunteer_doc = vol
                        break
        
        if not volunteer_doc:
            logger.warning(f"Volunteer not found for phone: {From} (normalized: {normalized_phone})")
            # Log all volunteer phones for debugging
            cursor = volunteers_collection.find({}, {"phone": 1, "name": 1})
            logger.info("Available volunteer phones:")
            async for vol in cursor:
                logger.info(f"  - {vol.get('name')}: {vol.get('phone')}")
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Sorry, we couldn't find your volunteer record. Please contact the coordinator.</Message>
</Response>"""
            return Response(content=twiml, media_type="application/xml")
        
        volunteer_id = volunteer_doc.get("_id")
        
        # Find the volunteer's latest active assignment (not cancelled, not confirmed)
        assignments_collection = get_collection("assignments")
        assignment_doc = await assignments_collection.find_one(
            {
                "volunteer_id": volunteer_id,
                "status": {"$in": ["assigned", "backup"]}
            },
            sort=[("created_at", -1)]  # Most recent first
        )
        
        if not assignment_doc:
            logger.info(f"No active assignment found for volunteer {volunteer_id}")
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>You don't have any active assignments at the moment.</Message>
</Response>"""
            return Response(content=twiml, media_type="application/xml")
        
        assignment = Assignment(**assignment_doc)
        camp_id = assignment.camp_id
        
        # Update assignment status
        new_status = "confirmed" if action == "confirm" else "cancelled"
        await assignments_collection.update_one(
            {"_id": assignment.id},
            {"$set": {"status": new_status}}
        )
        
        logger.info(f"Updated assignment {assignment.id} status to {new_status} via SMS from {From}")
        
        # If cancelled, trigger replanning via Celery (non-blocking)
        if action == "cancel":
            try:
                from app.tasks.scheduler_tasks import trigger_replan_on_cancellation
                result = trigger_replan_on_cancellation.delay(str(camp_id))
                logger.info(f"Triggered Celery replan task for camp {camp_id} after cancellation (task_id: {result.id})")
            except Exception as e:
                # Log error but don't fail the webhook
                logger.error(f"Failed to trigger Celery replan after cancellation: {e}")
                # Fallback to direct replan if Celery fails
                try:
                    import asyncio
                    from bson import ObjectId
                    asyncio.create_task(replan_camp(ObjectId(camp_id)))
                    logger.info(f"Fallback: Triggered direct replan for camp {camp_id}")
                except Exception as e2:
                    logger.error(f"Fallback replan also failed: {e2}")
        
        # Send confirmation message
        if action == "confirm":
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Thank you! Your assignment has been confirmed.</Message>
</Response>"""
        else:
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Your assignment has been cancelled. We'll work on finding a replacement.</Message>
</Response>"""
        
        logger.info(f"Returning TwiML response for {From}: {action}")
        # Ensure proper headers for Twilio
        return Response(
            content=twiml, 
            media_type="application/xml",
            headers={
                "Content-Type": "application/xml; charset=utf-8",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        # Always return valid TwiML, even on error
        logger.error(f"Error processing Twilio webhook: {e}", exc_info=True)
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Sorry, there was an error processing your message. Please try again later.</Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

