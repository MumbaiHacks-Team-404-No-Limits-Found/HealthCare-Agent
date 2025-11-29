"""Activity log helpers for writing and reading logs."""
from datetime import datetime
from typing import List, Dict, Any
from bson import ObjectId

from app.database import get_collection
from app.models import ActivityLog


async def log_activity(
    camp_id: str,
    event: str,
    meta: Dict[str, Any] = None
) -> ActivityLog:
    """
    Write an activity log entry.
    
    Args:
        camp_id: Camp ID
        event: Event description
        meta: Additional metadata
        
    Returns:
        Created ActivityLog object
    """
    collection = get_collection("activity_logs")
    
    log_entry = ActivityLog(
        camp_id=ObjectId(camp_id),
        timestamp=datetime.utcnow(),
        event=event,
        meta=meta or {}
    )
    
    result = await collection.insert_one(log_entry.dict(by_alias=True))
    log_entry.id = result.inserted_id
    
    return log_entry


async def get_camp_activity(camp_id: str) -> List[ActivityLog]:
    """
    Get activity logs for a camp, ordered by timestamp descending.
    
    Args:
        camp_id: Camp ID
        
    Returns:
        List of ActivityLog objects
    """
    collection = get_collection("activity_logs")
    cursor = collection.find({"camp_id": ObjectId(camp_id)}).sort("timestamp", -1)
    
    logs = []
    async for doc in cursor:
        logs.append(ActivityLog(**doc))
    
    return logs

