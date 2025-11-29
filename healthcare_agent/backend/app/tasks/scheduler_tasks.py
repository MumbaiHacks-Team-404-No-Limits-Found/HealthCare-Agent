"""Celery tasks for scheduled automation triggers."""
import asyncio
from typing import List, Dict
from bson import ObjectId
from datetime import datetime

from app.celery_worker import celery_app
from app.database import connect_to_mongo, close_mongo_connection, get_collection
from app.models import Camp


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.scheduler_tasks.schedule_camp_forecast_and_plan")
def schedule_camp_forecast_and_plan(camp_id: str):
    """
    Schedule forecast and planning for a newly created camp.
    
    This task is triggered when a camp is created.
    It runs forecast first, then planning.
    
    Args:
        camp_id: Camp ID string
        
    Returns:
        Dict with scheduling results
    """
    from app.tasks.forecast_tasks import run_daily_forecast
    from app.tasks.planner_tasks import auto_plan_camp
    
    # Schedule forecast (immediate)
    forecast_result = run_daily_forecast.delay(camp_id)
    
    # Schedule planning after forecast (with delay)
    plan_result = auto_plan_camp.apply_async(args=[camp_id], countdown=60)  # 60 seconds delay
    
    return {
        "success": True,
        "camp_id": camp_id,
        "forecast_task_id": forecast_result.id,
        "plan_task_id": plan_result.id,
        "message": "Forecast and planning scheduled"
    }


@celery_app.task(name="app.tasks.scheduler_tasks.trigger_replan_on_cancellation")
def trigger_replan_on_cancellation(camp_id: str):
    """
    Trigger replanning when a volunteer cancels (called from webhook).
    
    Args:
        camp_id: Camp ID string
        
    Returns:
        Dict with replanning trigger result
    """
    from app.tasks.planner_tasks import auto_replan_camp
    
    # Trigger replan immediately
    replan_result = auto_replan_camp.delay(camp_id)
    
    return {
        "success": True,
        "camp_id": camp_id,
        "replan_task_id": replan_result.id,
        "message": "Replanning triggered"
    }

