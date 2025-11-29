"""360 Dialog webhook handler for processing incoming WhatsApp messages."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from pydantic import BaseModel

from app.database import get_collection
from app.models import Assignment
from app.notifications import normalize_phone_number
from app.replan import replan_camp
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class Dialog360WebhookMessage(BaseModel):
    """360 Dialog webhook message model."""
    from_number: str
    text: Optional[str] = None
    message_id: Optional[str] = None
    timestamp: Optional[str] = None


def validate_dialog360_webhook(request: Request) -> bool:
    """
    Validate that the request came from 360 Dialog.
    
    In production, you should validate the webhook signature.
    For now, we'll allow all requests (you can add signature validation later).
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if request is valid, False otherwise
    """
    # TODO: Add signature validation if 360 Dialog provides it
    # For now, allow all requests
    return True


@router.post("/webhook")
async def dialog360_webhook(request: Request):
    """
    Handle incoming WhatsApp webhook from 360 Dialog.
    
    Security:
        - Validates webhook (signature validation can be added)
        - Rejects requests with invalid signatures (if configured)
    
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
            * Unknown message -> returns helpful response
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON response with status and optional message
    """
    try:
        # Validate webhook
        if not validate_dialog360_webhook(request):
            logger.error("Rejected webhook with invalid signature")
            return JSONResponse(
                content={"error": "Invalid request signature"},
                status_code=400
            )
        
        # Parse JSON body (360 Dialog sends JSON, not form data)
        body = await request.json()
        
        # Extract message data from 360 Dialog webhook format
        # 360 Dialog webhook format may vary, adjust based on actual format
        messages = body.get("messages", [])
        if not messages:
            # Some webhooks send data directly
            from_number = body.get("from", {}).get("phone_number") or body.get("from_number") or body.get("from")
            text = body.get("text", {}).get("body") if isinstance(body.get("text"), dict) else body.get("text") or body.get("body")
            message_id = body.get("id") or body.get("message_id")
        else:
            # Multiple messages (take first)
            msg = messages[0]
            from_number = msg.get("from", {}).get("phone_number") if isinstance(msg.get("from"), dict) else msg.get("from")
            text = msg.get("text", {}).get("body") if isinstance(msg.get("text"), dict) else msg.get("text") or msg.get("body")
            message_id = msg.get("id") or msg.get("message_id")
        
        if not from_number:
            logger.warning(f"Webhook received without from number: {body}")
            return JSONResponse(content={"status": "ok"}, status_code=200)
        
        # Normalize phone number
        normalized_phone = normalize_phone_number(from_number)
        
        # Log for debugging (sanitize phone number)
        from app.logging_utils import sanitize_phone, safe_log_info
        safe_log_info(
            "360 Dialog webhook received",
            from_number=sanitize_phone(from_number),
            normalized_phone=sanitize_phone(normalized_phone),
            body_length=len(text) if text else 0
        )
        
        # Parse message body (case-insensitive, strip whitespace)
        if not text:
            return JSONResponse(content={"status": "ok"}, status_code=200)
        
        message_body = text.strip().lower()
        
        # Determine action
        if message_body in ("confirm", "yes", "confirmed"):
            action = "confirm"
        elif message_body in ("cancel", "no", "cancelled"):
            action = "cancel"
        else:
            # Unknown message - send helpful response
            # Note: 360 Dialog requires you to send a response via API, not in webhook response
            logger.info(f"Unknown message from {from_number}: {message_body}")
            return JSONResponse(content={"status": "ok"}, status_code=200)
        
        # Find volunteer by phone number
        # Try multiple formats to handle different phone number representations
        volunteers_collection = get_collection("volunteers")
        
        # Try normalized phone first
        volunteer_doc = await volunteers_collection.find_one({"phone": normalized_phone})
        
        # Try original format
        if not volunteer_doc:
            volunteer_doc = await volunteers_collection.find_one({"phone": from_number})
        
        # Try with different variations (remove +, add +, etc.)
        if not volunteer_doc:
            # Try without + prefix
            phone_without_plus = normalized_phone.lstrip("+")
            volunteer_doc = await volunteers_collection.find_one({"phone": phone_without_plus})
        
        if not volunteer_doc:
            # Try with + prefix if it doesn't have one
            if not from_number.startswith("+"):
                volunteer_doc = await volunteers_collection.find_one({"phone": "+" + from_number})
        
        # Last resort: search by last 10 digits (handles country code differences)
        if not volunteer_doc:
            # Extract last 10 digits and try to match
            digits_only = ''.join(filter(str.isdigit, from_number))
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
            logger.warning(f"Volunteer not found for phone: {from_number} (normalized: {normalized_phone})")
            # Log all volunteer phones for debugging
            cursor = volunteers_collection.find({}, {"phone": 1, "name": 1})
            logger.info("Available volunteer phones:")
            async for vol in cursor:
                logger.info(f"  - {vol.get('name')}: {vol.get('phone')}")
            return JSONResponse(content={"status": "ok"}, status_code=200)
        
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
            return JSONResponse(content={"status": "ok"}, status_code=200)
        
        assignment = Assignment(**assignment_doc)
        camp_id = assignment.camp_id
        
        # Update assignment status
        new_status = "confirmed" if action == "confirm" else "cancelled"
        await assignments_collection.update_one(
            {"_id": assignment.id},
            {"$set": {"status": new_status}}
        )
        
        logger.info(f"Updated assignment {assignment.id} status to {new_status} via WhatsApp from {from_number}")
        
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
        
        # Return success (360 Dialog doesn't use response body for messages)
        return JSONResponse(content={"status": "ok"}, status_code=200)
        
    except Exception as e:
        # Always return success to avoid retries
        logger.error(f"Error processing 360 Dialog webhook: {e}", exc_info=True)
        return JSONResponse(content={"status": "error"}, status_code=200)

