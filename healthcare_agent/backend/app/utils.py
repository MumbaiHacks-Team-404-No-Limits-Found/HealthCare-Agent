"""Shared utility functions for validation and error handling."""
from bson import ObjectId
from typing import Optional


def validate_object_id(id_str: str, entity_name: str = "Entity") -> ObjectId:
    """
    Validate and convert a string to ObjectId.
    
    Args:
        id_str: String to validate
        entity_name: Name of the entity (for error messages)
        
    Returns:
        ObjectId instance
        
    Raises:
        ValueError: If id_str is not a valid ObjectId format
    """
    try:
        return ObjectId(id_str)
    except Exception:
        raise ValueError(f"Invalid {entity_name} ID format: {id_str}")


async def get_camp_or_raise(camp_id: str):
    """
    Get a camp by ID or raise a clear error.
    
    Args:
        camp_id: Camp ID string
        
    Returns:
        Camp object
        
    Raises:
        ValueError: If camp_id is invalid or camp not found
    """
    from app.replan import get_camp_by_id
    
    # Validate ObjectId format
    validate_object_id(camp_id, "Camp")
    
    # Fetch camp
    try:
        return await get_camp_by_id(camp_id)
    except ValueError as e:
        # Re-raise with clearer message if needed
        if "not found" in str(e).lower():
            raise ValueError(f"Camp not found: {camp_id}")
        raise


async def get_assignment_or_raise(assignment_id: str):
    """
    Get an assignment by ID or raise a clear error.
    
    Args:
        assignment_id: Assignment ID string
        
    Returns:
        Assignment object
        
    Raises:
        ValueError: If assignment_id is invalid or assignment not found
    """
    from app.database import get_collection
    from app.models import Assignment
    
    # Validate ObjectId format
    object_id = validate_object_id(assignment_id, "Assignment")
    
    # Fetch assignment
    collection = get_collection("assignments")
    assignment_doc = await collection.find_one({"_id": object_id})
    
    if not assignment_doc:
        raise ValueError(f"Assignment not found: {assignment_id}")
    
    return Assignment(**assignment_doc)

