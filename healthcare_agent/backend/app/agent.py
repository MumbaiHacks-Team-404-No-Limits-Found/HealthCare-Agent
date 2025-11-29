"""
AI Agent Orchestrator for Medical Camp Volunteer Coordination

This module provides a unified interface for the complete agent workflow:
1. CSV Data Validation
2. Forecasting (Poisson)
3. Planning (OR-Tools ILP)
4. Notification (Twilio WhatsApp)
5. Response Handling (Webhook)
6. Replanning (on cancellation)
7. Activity Logging

All operations are async, use MongoDB (Motor), and integrate with:
- Strawberry GraphQL
- Celery + Redis
- Twilio WhatsApp
- Activity logging

Usage:
    from app.agent import MedicalCampAgent
    
    agent = MedicalCampAgent()
    
    # Validate data
    validation = await agent.validate_csv_mappings()
    
    # Run full workflow for a camp
    result = await agent.run_full_workflow(camp_id="...")
    
    # Or run individual steps
    forecast = await agent.forecast_demand(camp_id="...")
    assignments = await agent.plan_assignments(camp_id="...")
    await agent.notify_volunteers(assignment_ids=[...])
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from bson import ObjectId

from app.database import get_collection, connect_to_mongo
from app.models import Camp, Volunteer, Assignment, ForecastResult
from app.forecast import run_forecast_for_camp
from app.planner import run_planner_for_camp
from app.replan import replan_camp
from app.activity import log_activity, get_camp_activity
from app.notifications import send_assignment_notification
from app.utils import validate_object_id

logger = logging.getLogger(__name__)


class AgentWorkflowResult:
    """Result of agent workflow execution."""
    
    def __init__(self):
        self.success: bool = False
        self.camp_id: Optional[str] = None
        self.forecast_results: List[ForecastResult] = []
        self.assignments_created: List[Assignment] = []
        self.notifications_sent: int = 0
        self.unfilled_slots: int = 0
        self.errors: List[str] = []
        self.activity_logs: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for logging/API responses."""
        return {
            "success": self.success,
            "camp_id": self.camp_id,
            "forecast_count": len(self.forecast_results),
            "assignments_created": len(self.assignments_created),
            "notifications_sent": self.notifications_sent,
            "unfilled_slots": self.unfilled_slots,
            "errors": self.errors,
            "activity_logs_count": len(self.activity_logs)
        }


class CSVValidationResult:
    """Result of CSV data validation."""
    
    def __init__(self):
        self.volunteers_count: int = 0
        self.camps_count: int = 0
        self.requirements_count: int = 0
        self.role_demand_history_count: int = 0
        self.assignments_history_count: int = 0
        self.is_valid: bool = False
        self.errors: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "volunteers": self.volunteers_count,
            "camps": self.camps_count,
            "requirements": self.requirements_count,
            "role_demand_history": self.role_demand_history_count,
            "assignments_history": self.assignments_history_count,
            "errors": self.errors
        }


class MedicalCampAgent:
    """
    AI Agent for Medical Camp Volunteer Coordination.
    
    Orchestrates the complete workflow:
    1. CSV Data Validation
    2. Forecasting (Poisson distribution)
    3. Planning (OR-Tools ILP with greedy fallback)
    4. Notification (Twilio WhatsApp)
    5. Response Handling (via webhook)
    6. Replanning (on cancellation)
    7. Activity Logging
    """
    
    def __init__(self):
        """Initialize the agent."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def validate_csv_mappings(self) -> CSVValidationResult:
        """
        Validate that CSV data has been properly seeded into MongoDB.
        
        Checks:
        - volunteers.csv → volunteers collection
        - camps.csv → camps collection
        - camp_requirements.csv → embedded in camp.requirements
        - role_demand_history.csv → role_demand_history collection
        - assignments_history.csv → assignments collection (optional)
        
        Returns:
            CSVValidationResult with counts and validation status
        """
        result = CSVValidationResult()
        
        try:
            # Check volunteers collection
            volunteers_collection = get_collection("volunteers")
            result.volunteers_count = await volunteers_collection.count_documents({})
            
            # Check camps collection
            camps_collection = get_collection("camps")
            result.camps_count = await camps_collection.count_documents({})
            
            # Count requirements (embedded in camps)
            total_requirements = 0
            async for camp_doc in camps_collection.find({}):
                requirements = camp_doc.get("requirements", [])
                total_requirements += len(requirements)
            result.requirements_count = total_requirements
            
            # Check role_demand_history collection
            role_demand_collection = get_collection("role_demand_history")
            result.role_demand_history_count = await role_demand_collection.count_documents({})
            
            # Check assignments_history (optional, may not be seeded)
            assignments_collection = get_collection("assignments")
            result.assignments_history_count = await assignments_collection.count_documents({})
            
            # Validation: At minimum, we need volunteers and camps
            result.is_valid = (
                result.volunteers_count > 0 and
                result.camps_count > 0
            )
            
            if not result.is_valid:
                result.errors.append(
                    f"Missing required data: volunteers={result.volunteers_count}, "
                    f"camps={result.camps_count}"
                )
            
            self.logger.info(f"CSV validation: {result.to_dict()}")
            
        except Exception as e:
            result.errors.append(f"Validation error: {str(e)}")
            self.logger.error(f"CSV validation failed: {e}", exc_info=True)
        
        return result
    
    async def forecast_demand(self, camp_id: str) -> List[ForecastResult]:
        """
        Run Poisson-based demand forecast for a camp.
        
        Uses:
        - role_demand_history collection (primary data source)
        - scipy.stats.poisson for percentile calculations
        
        Args:
            camp_id: Camp ID string (ObjectId format)
            
        Returns:
            List of ForecastResult with role, slot, mean, upper90, lower10
            
        Raises:
            ValueError: If camp not found or has no requirements
        """
        try:
            # Validate and fetch camp
            camp_object_id = validate_object_id(camp_id, "Camp")
            camps_collection = get_collection("camps")
            camp_doc = await camps_collection.find_one({"_id": camp_object_id})
            
            if not camp_doc:
                raise ValueError(f"Camp not found: {camp_id}")
            
            camp = Camp(**camp_doc)
            
            if not camp.requirements:
                raise ValueError(f"Camp {camp_id} has no requirements to forecast")
            
            # Run forecast
            results = await run_forecast_for_camp(camp)
            
            # Log activity
            try:
                await log_activity(
                    camp_id,
                    f"Forecast run for camp {camp.name}",
                    {
                        "requirements_count": len(camp.requirements),
                        "forecast_results_count": len(results),
                        "camp_name": camp.name
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to log forecast activity: {e}")
            
            self.logger.info(f"Forecast completed for camp {camp_id}: {len(results)} results")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Forecast failed for camp {camp_id}: {e}", exc_info=True)
            raise
    
    async def plan_assignments(
        self,
        camp_id: str,
        use_celery: bool = False
    ) -> Tuple[List[Assignment], int]:
        """
        Plan optimal volunteer assignments using OR-Tools ILP.
        
        Uses:
        - OR-Tools Integer Linear Programming (ILP)
        - Greedy fallback if ILP fails
        - Respects confirmed assignments
        
        Args:
            camp_id: Camp ID string (ObjectId format)
            use_celery: If True, schedules via Celery instead of running directly
            
        Returns:
            Tuple of (list of created assignments, unfilled_slots_count)
            
        Raises:
            ValueError: If camp not found or has no requirements
        """
        try:
            camp_object_id = validate_object_id(camp_id, "Camp")
            
            if use_celery:
                # Schedule via Celery (non-blocking)
                from app.tasks.planner_tasks import auto_plan_camp
                result = auto_plan_camp.delay(camp_id)
                self.logger.info(f"Scheduled planning via Celery for camp {camp_id} (task_id: {result.id})")
                # Return empty list - actual results will be in Celery task
                return [], 0
            else:
                # Run directly (blocking)
                assignments, unfilled_slots = await run_planner_for_camp(camp_object_id)
                
                # Log activity
                try:
                    camps_collection = get_collection("camps")
                    camp_doc = await camps_collection.find_one({"_id": camp_object_id})
                    camp_name = camp_doc.get("name", "Unknown") if camp_doc else "Unknown"
                    
                    await log_activity(
                        camp_id,
                        f"Plan run for camp {camp_name}",
                        {
                            "assignments_created": len(assignments),
                            "unfilled_slots": unfilled_slots
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to log plan activity: {e}")
                
                self.logger.info(
                    f"Planning completed for camp {camp_id}: "
                    f"{len(assignments)} assignments, {unfilled_slots} unfilled slots"
                )
                
                return assignments, unfilled_slots
                
        except Exception as e:
            self.logger.error(f"Planning failed for camp {camp_id}: {e}", exc_info=True)
            raise
    
    async def notify_volunteers(
        self,
        assignment_ids: List[str],
        use_celery: bool = True
    ) -> int:
        """
        Send WhatsApp notifications to volunteers for their assignments.
        
        Uses:
        - Twilio WhatsApp API
        - Template: "Hi {name}, you've been assigned to {role} on {date}, {slot}. Reply YES to confirm or NO to cancel."
        
        Args:
            assignment_ids: List of assignment ID strings
            use_celery: If True, schedules via Celery (recommended for batches)
            
        Returns:
            Number of notifications successfully sent
        """
        if not assignment_ids:
            return 0
        
        try:
            if use_celery:
                # Schedule via Celery (non-blocking, recommended for batches)
                from app.tasks.notification_tasks import send_batch_notifications
                result = send_batch_notifications.delay(assignment_ids)
                self.logger.info(
                    f"Scheduled batch notifications via Celery for {len(assignment_ids)} assignments "
                    f"(task_id: {result.id})"
                )
                # Return count - actual results will be in Celery task
                return len(assignment_ids)
            else:
                # Send directly (blocking, for small batches)
                assignments_collection = get_collection("assignments")
                volunteers_collection = get_collection("volunteers")
                camps_collection = get_collection("camps")
                
                sent_count = 0
                
                for assignment_id in assignment_ids:
                    try:
                        assignment_doc = await assignments_collection.find_one({
                            "_id": ObjectId(assignment_id)
                        })
                        
                        if not assignment_doc:
                            self.logger.warning(f"Assignment {assignment_id} not found")
                            continue
                        
                        assignment = Assignment(**assignment_doc)
                        
                        # Fetch volunteer and camp
                        volunteer_doc = await volunteers_collection.find_one({
                            "_id": assignment.volunteer_id
                        })
                        camp_doc = await camps_collection.find_one({"_id": assignment.camp_id})
                        
                        if not volunteer_doc or not camp_doc:
                            self.logger.warning(
                                f"Related data not found for assignment {assignment_id}"
                            )
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
                        
                        if success:
                            sent_count += 1
                            # Log activity
                            try:
                                await log_activity(
                                    str(assignment.camp_id),
                                    f"Notification sent to {volunteer.name}",
                                    {
                                        "assignment_id": assignment_id,
                                        "volunteer_id": str(volunteer.id)
                                    }
                                )
                            except Exception as e:
                                self.logger.warning(f"Failed to log notification activity: {e}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to send notification for {assignment_id}: {e}")
                
                self.logger.info(f"Sent {sent_count}/{len(assignment_ids)} notifications")
                return sent_count
                
        except Exception as e:
            self.logger.error(f"Notification batch failed: {e}", exc_info=True)
            raise
    
    async def handle_volunteer_response(
        self,
        phone_number: str,
        message_body: str
    ) -> Dict[str, Any]:
        """
        Handle volunteer response via WhatsApp webhook.
        
        This is typically called from the Twilio webhook endpoint.
        
        Args:
            phone_number: Volunteer phone number (from Twilio)
            message_body: Message content (e.g., "yes", "confirm", "no", "cancel")
            
        Returns:
            Dict with action taken and result
        """
        from app.notifications import normalize_phone_number
        from app.database import get_collection
        
        try:
            # Normalize phone number
            normalized_phone = normalize_phone_number(phone_number)
            
            # Find volunteer
            volunteers_collection = get_collection("volunteers")
            volunteer_doc = await volunteers_collection.find_one({"phone": normalized_phone})
            
            if not volunteer_doc:
                # Try other formats
                volunteer_doc = await volunteers_collection.find_one({"phone": phone_number})
            
            if not volunteer_doc:
                return {
                    "success": False,
                    "action": "volunteer_not_found",
                    "message": "Volunteer not found"
                }
            
            volunteer = Volunteer(**volunteer_doc)
            
            # Find active assignment
            assignments_collection = get_collection("assignments")
            assignment_doc = await assignments_collection.find_one(
                {
                    "volunteer_id": volunteer.id,
                    "status": {"$in": ["assigned", "backup"]}
                },
                sort=[("created_at", -1)]
            )
            
            if not assignment_doc:
                return {
                    "success": False,
                    "action": "no_active_assignment",
                    "message": "No active assignment found"
                }
            
            assignment = Assignment(**assignment_doc)
            
            # Parse message
            message_lower = message_body.strip().lower()
            
            if message_lower in ("confirm", "yes", "confirmed"):
                # Confirm assignment
                await assignments_collection.update_one(
                    {"_id": assignment.id},
                    {"$set": {"status": "confirmed"}}
                )
                
                await log_activity(
                    str(assignment.camp_id),
                    f"Assignment confirmed by {volunteer.name}",
                    {
                        "assignment_id": str(assignment.id),
                        "volunteer_id": str(volunteer.id)
                    }
                )
                
                return {
                    "success": True,
                    "action": "confirmed",
                    "assignment_id": str(assignment.id),
                    "camp_id": str(assignment.camp_id)
                }
            
            elif message_lower in ("cancel", "no", "cancelled"):
                # Cancel assignment and trigger replan
                await assignments_collection.update_one(
                    {"_id": assignment.id},
                    {"$set": {"status": "cancelled"}}
                )
                
                await log_activity(
                    str(assignment.camp_id),
                    f"Assignment cancelled by {volunteer.name}",
                    {
                        "assignment_id": str(assignment.id),
                        "volunteer_id": str(volunteer.id),
                        "replan_triggered": True
                    }
                )
                
                # Trigger replan via Celery
                try:
                    from app.tasks.scheduler_tasks import trigger_replan_on_cancellation
                    replan_result = trigger_replan_on_cancellation.delay(str(assignment.camp_id))
                    self.logger.info(
                        f"Triggered replan for camp {assignment.camp_id} "
                        f"(task_id: {replan_result.id})"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to trigger replan: {e}")
                
                return {
                    "success": True,
                    "action": "cancelled",
                    "assignment_id": str(assignment.id),
                    "camp_id": str(assignment.camp_id),
                    "replan_triggered": True
                }
            
            else:
                return {
                    "success": False,
                    "action": "unknown_message",
                    "message": "Please reply with 'confirm' or 'cancel'"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to handle volunteer response: {e}", exc_info=True)
            return {
                "success": False,
                "action": "error",
                "message": str(e)
            }
    
    async def replan_camp(
        self,
        camp_id: str,
        use_celery: bool = False
    ) -> Tuple[List[Assignment], int]:
        """
        Replan assignments for a camp (typically after cancellation).
        
        Preserves confirmed assignments and fills gaps.
        
        Args:
            camp_id: Camp ID string (ObjectId format)
            use_celery: If True, schedules via Celery instead of running directly
            
        Returns:
            Tuple of (list of new assignments created, unfilled_slots_count)
        """
        try:
            camp_object_id = validate_object_id(camp_id, "Camp")
            
            if use_celery:
                # Schedule via Celery
                from app.tasks.planner_tasks import auto_replan_camp
                result = auto_replan_camp.delay(camp_id)
                self.logger.info(f"Scheduled replan via Celery for camp {camp_id} (task_id: {result.id})")
                return [], 0
            else:
                # Run directly
                new_assignments, unfilled_slots = await replan_camp(camp_object_id)
                
                # Log activity
                try:
                    camps_collection = get_collection("camps")
                    camp_doc = await camps_collection.find_one({"_id": camp_object_id})
                    camp_name = camp_doc.get("name", "Unknown") if camp_doc else "Unknown"
                    
                    await log_activity(
                        camp_id,
                        f"Replan run for camp {camp_name}",
                        {
                            "new_assignments": len(new_assignments),
                            "still_unfilled_slots": unfilled_slots
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to log replan activity: {e}")
                
                self.logger.info(
                    f"Replan completed for camp {camp_id}: "
                    f"{len(new_assignments)} new assignments, {unfilled_slots} unfilled slots"
                )
                
                return new_assignments, unfilled_slots
                
        except Exception as e:
            self.logger.error(f"Replan failed for camp {camp_id}: {e}", exc_info=True)
            raise
    
    async def get_activity_logs(self, camp_id: str) -> List[Dict[str, Any]]:
        """
        Get activity logs for a camp.
        
        Args:
            camp_id: Camp ID string (ObjectId format)
            
        Returns:
            List of activity log dictionaries
        """
        try:
            logs = await get_camp_activity(camp_id)
            return [
                {
                    "id": str(log.id),
                    "camp_id": str(log.camp_id),
                    "timestamp": log.timestamp.isoformat(),
                    "event": log.event,
                    "meta": log.meta
                }
                for log in logs
            ]
        except Exception as e:
            self.logger.error(f"Failed to get activity logs for camp {camp_id}: {e}")
            return []
    
    async def run_full_workflow(
        self,
        camp_id: str,
        notify_volunteers: bool = True,
        use_celery: bool = True
    ) -> AgentWorkflowResult:
        """
        Run the complete agent workflow for a camp.
        
        Workflow:
        1. Validate camp exists
        2. Run forecast
        3. Run planning
        4. Notify volunteers (if requested)
        5. Log all activities
        
        Args:
            camp_id: Camp ID string (ObjectId format)
            notify_volunteers: If True, send notifications after planning
            use_celery: If True, use Celery for async operations
            
        Returns:
            AgentWorkflowResult with complete workflow results
        """
        result = AgentWorkflowResult()
        result.camp_id = camp_id
        
        try:
            # Step 1: Validate camp
            camp_object_id = validate_object_id(camp_id, "Camp")
            camps_collection = get_collection("camps")
            camp_doc = await camps_collection.find_one({"_id": camp_object_id})
            
            if not camp_doc:
                result.errors.append(f"Camp not found: {camp_id}")
                return result
            
            camp = Camp(**camp_doc)
            
            # Step 2: Run forecast
            try:
                result.forecast_results = await self.forecast_demand(camp_id)
                await log_activity(
                    camp_id,
                    "Agent workflow: Forecast completed",
                    {"forecast_results_count": len(result.forecast_results)}
                )
            except Exception as e:
                error_msg = f"Forecast failed: {str(e)}"
                result.errors.append(error_msg)
                self.logger.error(error_msg)
            
            # Step 3: Run planning
            try:
                assignments, unfilled_slots = await self.plan_assignments(
                    camp_id,
                    use_celery=use_celery
                )
                result.assignments_created = assignments
                result.unfilled_slots = unfilled_slots
                
                await log_activity(
                    camp_id,
                    "Agent workflow: Planning completed",
                    {
                        "assignments_created": len(assignments),
                        "unfilled_slots": unfilled_slots
                    }
                )
            except Exception as e:
                error_msg = f"Planning failed: {str(e)}"
                result.errors.append(error_msg)
                self.logger.error(error_msg)
            
            # Step 4: Notify volunteers (if requested and assignments created)
            if notify_volunteers and result.assignments_created:
                try:
                    assignment_ids = [str(assign.id) for assign in result.assignments_created]
                    notifications_sent = await self.notify_volunteers(
                        assignment_ids,
                        use_celery=use_celery
                    )
                    result.notifications_sent = notifications_sent
                    
                    await log_activity(
                        camp_id,
                        "Agent workflow: Notifications sent",
                        {"notifications_sent": notifications_sent}
                    )
                except Exception as e:
                    error_msg = f"Notification failed: {str(e)}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg)
            
            # Step 5: Get activity logs
            result.activity_logs = await self.get_activity_logs(camp_id)
            
            # Mark as successful if no critical errors
            result.success = len(result.errors) == 0 or (
                len(result.errors) < 3  # Allow some non-critical errors
            )
            
            # Log final workflow result
            await log_activity(
                camp_id,
                "Agent workflow: Complete",
                result.to_dict()
            )
            
            self.logger.info(f"Agent workflow completed for camp {camp_id}: {result.to_dict()}")
            
        except Exception as e:
            result.errors.append(f"Workflow error: {str(e)}")
            self.logger.error(f"Agent workflow failed for camp {camp_id}: {e}", exc_info=True)
        
        return result


# Convenience function for direct usage
async def run_agent_workflow(
    camp_id: str,
    notify_volunteers: bool = True,
    use_celery: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to run the complete agent workflow.
    
    Args:
        camp_id: Camp ID string
        notify_volunteers: If True, send notifications
        use_celery: If True, use Celery for async operations
        
    Returns:
        Dictionary with workflow results
    """
    agent = MedicalCampAgent()
    result = await agent.run_full_workflow(camp_id, notify_volunteers, use_celery)
    return result.to_dict()

