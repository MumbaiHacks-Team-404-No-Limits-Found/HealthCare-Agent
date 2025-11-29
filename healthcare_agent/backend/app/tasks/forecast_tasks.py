"""Celery tasks for automatic forecasting operations."""
import asyncio
from typing import List
from bson import ObjectId

from app.celery_worker import celery_app
from app.database import connect_to_mongo, close_mongo_connection, get_collection
from app.models import Camp
from app.forecast import run_forecast_for_camp
from app.activity import log_activity


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.forecast_tasks.run_daily_forecast")
def run_daily_forecast(camp_id: str):
    """
    Run forecast for a specific camp.
    
    This task is triggered automatically or can be called manually.
    
    Args:
        camp_id: Camp ID string
        
    Returns:
        Dict with forecast results or error message
    """
    async def _run():
        try:
            # Ensure MongoDB connection
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
            
            # Run forecast
            results = await run_forecast_for_camp(camp)
            
            # Log activity
            await log_activity(
                camp_id,
                f"Automated forecast run for camp {camp.name}",
                {
                    "requirements_count": len(camp.requirements),
                    "forecast_results_count": len(results)
                }
            )
            
            return {
                "success": True,
                "camp_id": camp_id,
                "camp_name": camp.name,
                "results_count": len(results),
                "results": [
                    {
                        "role": r.role,
                        "slot": r.slot,
                        "mean": r.mean,
                        "upper90": r.upper_90,
                        "lower10": r.lower_10
                    }
                    for r in results
                ]
            }
        except Exception as e:
            return {"error": f"Forecast task failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())


@celery_app.task(name="app.tasks.forecast_tasks.run_daily_forecast_all_camps")
def run_daily_forecast_all_camps():
    """
    Run forecast for all active camps (scheduled daily).
    
    Finds all camps and runs forecast for each one.
    
    Returns:
        Dict with summary of forecasts run
    """
    async def _run():
        try:
            await connect_to_mongo()
            
            camps_collection = get_collection("camps")
            cursor = camps_collection.find({})
            
            camps_processed = []
            errors = []
            
            async for camp_doc in cursor:
                try:
                    camp = Camp(**camp_doc)
                    camp_id = str(camp.id)
                    
                    # Run forecast
                    results = await run_forecast_for_camp(camp)
                    
                    # Log activity
                    await log_activity(
                        camp_id,
                        f"Daily automated forecast for camp {camp.name}",
                        {
                            "requirements_count": len(camp.requirements),
                            "forecast_results_count": len(results)
                        }
                    )
                    
                    camps_processed.append({
                        "camp_id": camp_id,
                        "camp_name": camp.name,
                        "results_count": len(results)
                    })
                except Exception as e:
                    errors.append({
                        "camp_id": str(camp_doc.get("_id", "unknown")),
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "camps_processed": len(camps_processed),
                "errors": len(errors),
                "details": camps_processed,
                "error_details": errors
            }
        except Exception as e:
            return {"error": f"Daily forecast batch failed: {str(e)}"}
        finally:
            await close_mongo_connection()
    
    return run_async(_run())

