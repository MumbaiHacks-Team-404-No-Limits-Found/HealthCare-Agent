"""REST API endpoints for Activity Log operations."""
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from bson.errors import InvalidId

from app.models import ActivityLog
from app.auth import get_current_user
from app.activity import get_camp_activity

router = APIRouter()


@router.get("/camp/{camp_id}", response_model=List[ActivityLog])
async def get_activity_logs(camp_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get activity logs for a specific camp.
    
    Requires authentication.
    
    Args:
        camp_id: Camp ID
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        List of ActivityLog objects for the camp
        
    Raises:
        HTTPException 400: If camp_id is invalid
        HTTPException 401: If not authenticated
    """
    try:
        logs = await get_camp_activity(camp_id)
        return logs
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid camp_id format: {camp_id}"
        )

