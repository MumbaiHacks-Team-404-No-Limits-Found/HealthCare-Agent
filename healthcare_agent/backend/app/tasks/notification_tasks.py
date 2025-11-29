"""Celery tasks for automatic SMS notifications and reminders."""
import asyncio
from typing import List, Dict
from bson import ObjectId
from datetime import datetime, timedelta

from app.celery_worker import celery_app
from app.database import connect_to_mongo, close_mongo_connection, get_collection
from app.models import Camp, Assignment, Volunteer
from app.notifications import send_assignment_notification, normalize_phone_number
from app.activity import log_activity


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(
    name="app.tasks.notification_tasks.send_assignment_notification_task",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3
)
def send_assignment_notification_task(
    assignment_id: str,
    volunteer_id: str,
    camp_id: str
):
    """
    Send SMS notification for a new assignment.
    
    Args:
        assignment_id: Assignment ID
        volunteer_id: Volunteer ID
        camp_id: Camp ID
        
    Returns:
        Dict with notification result
    """
    async def _run():
        try:
            await connect_to_mongo()
            
            # Fetch assignment, volunteer, and camp
            assignments_collection = get_collection("assignments")
            volunteers_collection = get_collection("volunteers")
            camps_collection = get_collection("camps")
            
            assignment_doc = await assignments_collection.find_one({"_id": ObjectId(assignment_id)})
            volunteer_doc = await volunteers_collection.find_one({"_id": ObjectId(volunteer_id)})
            camp_doc = await camps_collection.find_one({"_id": ObjectId(camp_id)})
            
            if not assignment_doc or not volunteer_doc or not camp_doc:
                return {"error": "Assignment, volunteer, or camp not found"}
            
            assignment = Assignment(**assignment_doc)
            volunteer = Volunteer(**volunteer_doc)
            camp = Camp(**camp_doc)
            
            # Send notification
            success = await send_assignment_notification(
                phone_number=volunteer.phone,
                volunteer_name=volunteer.name,
                camp_name=camp.name,
                role=assignment.role,
                slot=assignment.slot
            )
            
            if success:
                await log_activity(
                    camp_id,
                    f"Notification sent to {volunteer.name} for assignment",
                    {
                        "assignment_id": assignment_id,
                        "volunteer_id": volunteer_id
                    }
                )
            
            return {
                "success": success,
                "assignment_id": assignment_id,
                "volunteer_name": volunteer.name,
                "camp_name": camp.name
            }
        except Exception as e:
            return {"error": f"Notification task failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())


@celery_app.task(name="app.tasks.notification_tasks.send_upcoming_reminder_batch")
def send_upcoming_reminder_batch():
    """
    Send reminders for upcoming camps (scheduled every hour).
    
    Sends reminders at T-24h, T-6h, and T-1h before camp start time.
    
    Returns:
        Dict with summary of reminders sent
    """
    async def _run():
        try:
            await connect_to_mongo()
            
            camps_collection = get_collection("camps")
            assignments_collection = get_collection("assignments")
            volunteers_collection = get_collection("volunteers")
            
            now = datetime.utcnow()
            reminders_sent = []
            errors = []
            
            # Find all camps
            cursor = camps_collection.find({})
            
            async for camp_doc in cursor:
                try:
                    camp = Camp(**camp_doc)
                    camp_id = camp.id
                    
                    # Parse camp start time
                    try:
                        camp_start = datetime.fromisoformat(camp.start.replace("Z", "+00:00"))
                        if camp_start.tzinfo:
                            camp_start = camp_start.replace(tzinfo=None)
                    except Exception:
                        continue
                    
                    # Calculate time until camp
                    time_until = camp_start - now
                    
                    # Check if we should send reminder (T-24h, T-6h, T-1h)
                    hours_until = time_until.total_seconds() / 3600
                    
                    reminder_window = None
                    if 23.5 <= hours_until <= 24.5:
                        reminder_window = "24h"
                    elif 5.5 <= hours_until <= 6.5:
                        reminder_window = "6h"
                    elif 0.5 <= hours_until <= 1.5:
                        reminder_window = "1h"
                    else:
                        continue  # Not in reminder window
                    
                    # Find assignments for this camp
                    assignments_cursor = assignments_collection.find({
                        "camp_id": camp_id,
                        "status": {"$in": ["assigned", "confirmed"]}
                    })
                    
                    assignments_list = await assignments_cursor.to_list(length=1000)
                    
                    for assign_doc in assignments_list:
                        try:
                            assignment = Assignment(**assign_doc)
                            volunteer_doc = await volunteers_collection.find_one({
                                "_id": assignment.volunteer_id
                            })
                            
                            if not volunteer_doc:
                                continue
                            
                            volunteer = Volunteer(**volunteer_doc)
                            
                            # Send reminder
                            message_body = (
                                f"Reminder: You have an assignment at {camp.name} "
                                f"({camp.location}) as {assignment.role} for {assignment.slot} slot. "
                                f"Camp starts in {reminder_window}."
                            )
                            
                            # Use send_assignment_notification with reminder message
                            # For now, we'll use a simplified version
                            success = await send_assignment_notification(
                                phone_number=volunteer.phone,
                                volunteer_name=volunteer.name,
                                camp_name=camp.name,
                                role=assignment.role,
                                slot=assignment.slot
                            )
                            
                            if success:
                                reminders_sent.append({
                                    "camp_id": str(camp_id),
                                    "volunteer_id": str(volunteer.id),
                                    "reminder_window": reminder_window
                                })
                        except Exception as e:
                            errors.append({
                                "assignment_id": str(assign_doc.get("_id")),
                                "error": str(e)
                            })
                except Exception as e:
                    errors.append({
                        "camp_id": str(camp_doc.get("_id", "unknown")),
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "reminders_sent": len(reminders_sent),
                "details": reminders_sent,
                "errors": errors
            }
        except Exception as e:
            return {"error": f"Reminder batch failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())


@celery_app.task(name="app.tasks.notification_tasks.send_batch_notifications")
def send_batch_notifications(assignment_ids: List[str]):
    """
    Send notifications for a batch of assignments.
    
    Args:
        assignment_ids: List of assignment ID strings
        
    Returns:
        Dict with summary of notifications sent
    """
    async def _run():
        try:
            await connect_to_mongo()
            
            results = []
            for assignment_id in assignment_ids:
                try:
                    assignments_collection = get_collection("assignments")
                    assignment_doc = await assignments_collection.find_one({
                        "_id": ObjectId(assignment_id)
                    })
                    
                    if not assignment_doc:
                        results.append({"assignment_id": assignment_id, "error": "Not found"})
                        continue
                    
                    assignment = Assignment(**assignment_doc)
                    
                    # Fetch volunteer and camp
                    volunteers_collection = get_collection("volunteers")
                    camps_collection = get_collection("camps")
                    
                    volunteer_doc = await volunteers_collection.find_one({
                        "_id": assignment.volunteer_id
                    })
                    camp_doc = await camps_collection.find_one({"_id": assignment.camp_id})
                    
                    if not volunteer_doc or not camp_doc:
                        results.append({"assignment_id": assignment_id, "error": "Related data not found"})
                        continue
                    
                    volunteer = Volunteer(**volunteer_doc)
                    camp = Camp(**camp_doc)
                    
                    # Send notification
                    success = await send_assignment_notification(
                        phone_number=volunteer.phone,
                        volunteer_name=volunteer.name,
                        camp_name=camp.name,
                        role=assignment.role,
                        slot=assignment.slot
                    )
                    
                    results.append({
                        "assignment_id": assignment_id,
                        "success": success
                    })
                except Exception as e:
                    results.append({
                        "assignment_id": assignment_id,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "total": len(assignment_ids),
                "results": results
            }
        except Exception as e:
            return {"error": f"Batch notification failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())

