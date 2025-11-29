"""Celery tasks for automatic planning and replanning operations."""
import asyncio
from typing import List, Dict
from bson import ObjectId
from datetime import datetime, timedelta

from app.celery_worker import celery_app
from app.database import connect_to_mongo, close_mongo_connection, get_collection
from app.models import Camp, Assignment
from app.planner import run_planner_for_camp
from app.replan import replan_camp
from app.activity import log_activity


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.planner_tasks.auto_plan_camp")
def auto_plan_camp(camp_id: str):
    """
    Automatically plan assignments for a camp.
    
    Args:
        camp_id: Camp ID string
        
    Returns:
        Dict with planning results
    """
    async def _run():
        try:
            await connect_to_mongo()
            
            # Validate ObjectId
            try:
                camp_object_id = ObjectId(camp_id)
            except Exception:
                return {"error": f"Invalid camp ID format: {camp_id}"}
            
            # Fetch camp
            camps_collection = get_collection("camps")
            camp_doc = await camps_collection.find_one({"_id": camp_object_id})
            if not camp_doc:
                return {"error": f"Camp not found: {camp_id}"}
            
            camp = Camp(**camp_doc)
            
            # Check if camp already has assignments
            assignments_collection = get_collection("assignments")
            existing_count = await assignments_collection.count_documents({"camp_id": camp_object_id})
            
            if existing_count > 0:
                return {
                    "success": False,
                    "message": f"Camp {camp_id} already has {existing_count} assignments. Use replan instead."
                }
            
            # Run planner
            created_assignments, unfilled_slots = await run_planner_for_camp(camp_object_id)
            
            # Log activity
            await log_activity(
                camp_id,
                f"Automated planning for camp {camp.name}",
                {
                    "assignments_created": len(created_assignments),
                    "unfilled_slots": unfilled_slots
                }
            )
            
            return {
                "success": True,
                "camp_id": camp_id,
                "camp_name": camp.name,
                "assignments_created": len(created_assignments),
                "unfilled_slots": unfilled_slots
            }
        except Exception as e:
            return {"error": f"Auto plan task failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())


@celery_app.task(name="app.tasks.planner_tasks.auto_replan_camp")
def auto_replan_camp(camp_id: str):
    """
    Automatically replan assignments for a camp (triggered by cancellations).
    
    Args:
        camp_id: Camp ID string
        
    Returns:
        Dict with replanning results
    """
    async def _run():
        try:
            await connect_to_mongo()
            
            # Validate ObjectId
            try:
                camp_object_id = ObjectId(camp_id)
            except Exception:
                return {"error": f"Invalid camp ID format: {camp_id}"}
            
            # Fetch camp
            camps_collection = get_collection("camps")
            camp_doc = await camps_collection.find_one({"_id": camp_object_id})
            if not camp_doc:
                return {"error": f"Camp not found: {camp_id}"}
            
            camp = Camp(**camp_doc)
            
            # Run replan
            new_assignments, unfilled_slots = await replan_camp(camp_object_id)
            
            # Log activity
            await log_activity(
                camp_id,
                f"Automated replanning for camp {camp.name}",
                {
                    "new_assignments": len(new_assignments),
                    "unfilled_slots": unfilled_slots
                }
            )
            
            return {
                "success": True,
                "camp_id": camp_id,
                "camp_name": camp.name,
                "new_assignments": len(new_assignments),
                "unfilled_slots": unfilled_slots
            }
        except Exception as e:
            return {"error": f"Auto replan task failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())


@celery_app.task(name="app.tasks.planner_tasks.replan_if_needed")
def replan_if_needed():
    """
    Check for camps that need replanning (scheduled every 30 minutes).
    
    Looks for camps with cancelled assignments that haven't been replanned recently.
    
    Returns:
        Dict with summary of replanning operations
    """
    async def _run():
        try:
            await connect_to_mongo()
            
            assignments_collection = get_collection("assignments")
            camps_collection = get_collection("camps")
            
            # Find camps with cancelled assignments
            cancelled_assignments = await assignments_collection.find(
                {"status": "cancelled"}
            ).to_list(length=100)
            
            if not cancelled_assignments:
                return {
                    "success": True,
                    "message": "No cancelled assignments found",
                    "camps_replanned": 0
                }
            
            # Group by camp_id
            camps_to_replan = set()
            for assign_doc in cancelled_assignments:
                camp_id = assign_doc.get("camp_id")
                if camp_id:
                    camps_to_replan.add(str(camp_id))
            
            replanned_camps = []
            errors = []
            
            for camp_id_str in camps_to_replan:
                try:
                    # Check if camp exists
                    camp_object_id = ObjectId(camp_id_str)
                    camp_doc = await camps_collection.find_one({"_id": camp_object_id})
                    if not camp_doc:
                        continue
                    
                    # Check if there are still cancelled assignments
                    cancelled_count = await assignments_collection.count_documents({
                        "camp_id": camp_object_id,
                        "status": "cancelled"
                    })
                    
                    if cancelled_count == 0:
                        continue
                    
                    # Trigger replan
                    new_assignments, unfilled_slots = await replan_camp(camp_object_id)
                    
                    replanned_camps.append({
                        "camp_id": camp_id_str,
                        "new_assignments": len(new_assignments),
                        "unfilled_slots": unfilled_slots
                    })
                except Exception as e:
                    errors.append({
                        "camp_id": camp_id_str,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "camps_replanned": len(replanned_camps),
                "details": replanned_camps,
                "errors": errors
            }
        except Exception as e:
            return {"error": f"Replan check failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())


@celery_app.task(name="app.tasks.planner_tasks.auto_plan_new_camps")
def auto_plan_new_camps():
    """
    Automatically plan assignments for newly created camps (scheduled every 15 minutes).
    
    Finds camps created in the last 24 hours that don't have assignments yet.
    
    Returns:
        Dict with summary of planning operations
    """
    async def _run():
        try:
            await connect_to_mongo()
            
            camps_collection = get_collection("camps")
            assignments_collection = get_collection("assignments")
            
            # Find camps created in last 24 hours
            # Note: We'll check all camps and see which ones need planning
            # (since we don't have a created_at field, we'll check for camps without assignments)
            
            cursor = camps_collection.find({})
            camps_to_plan = []
            
            async for camp_doc in cursor:
                camp_id = camp_doc.get("_id")
                if not camp_id:
                    continue
                
                # Check if camp has assignments
                assignment_count = await assignments_collection.count_documents({
                    "camp_id": camp_id
                })
                
                if assignment_count == 0:
                    # Camp has no assignments, needs planning
                    camps_to_plan.append(camp_id)
            
            planned_camps = []
            errors = []
            
            for camp_object_id in camps_to_plan[:10]:  # Limit to 10 per run
                try:
                    camp_doc = await camps_collection.find_one({"_id": camp_object_id})
                    if not camp_doc:
                        continue
                    
                    camp = Camp(**camp_doc)
                    
                    # Run planner
                    created_assignments, unfilled_slots = await run_planner_for_camp(camp_object_id)
                    
                    planned_camps.append({
                        "camp_id": str(camp_object_id),
                        "camp_name": camp.name,
                        "assignments_created": len(created_assignments),
                        "unfilled_slots": unfilled_slots
                    })
                except Exception as e:
                    errors.append({
                        "camp_id": str(camp_object_id),
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "camps_planned": len(planned_camps),
                "details": planned_camps,
                "errors": errors
            }
        except Exception as e:
            return {"error": f"Auto plan new camps failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())

