"""REST API endpoints for Assignment CRUD operations."""
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.database import get_collection
from app.models import Assignment, AssignmentInput
from app.auth import get_current_user
from app.activity import log_activity

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_input: AssignmentInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new assignment.
    
    Requires authentication (admin role).
    
    Args:
        assignment_input: AssignmentInput with camp_id, volunteer_id, role, slot, status
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        Dictionary with created assignment data and id
        
    Raises:
        HTTPException 400: If validation fails or referenced entities not found
        HTTPException 401: If not authenticated
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId formats
        try:
            camp_object_id = ObjectId(assignment_input.camp_id)
            volunteer_object_id = ObjectId(assignment_input.volunteer_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid camp_id or volunteer_id format"
            )
        
        # Verify camp exists
        camps_collection = get_collection("camps")
        camp_doc = await camps_collection.find_one({"_id": camp_object_id})
        if not camp_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Camp not found: {assignment_input.camp_id}"
            )
        
        # Verify volunteer exists
        volunteers_collection = get_collection("volunteers")
        volunteer_doc = await volunteers_collection.find_one({"_id": volunteer_object_id})
        if not volunteer_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Volunteer not found: {assignment_input.volunteer_id}"
            )
        
        # Prepare assignment document
        from datetime import datetime
        assignment_data = {
            "camp_id": camp_object_id,
            "volunteer_id": volunteer_object_id,
            "role": assignment_input.role.strip(),
            "slot": assignment_input.slot.strip(),
            "status": assignment_input.status,
            "is_backup": assignment_input.is_backup,
            "created_at": datetime.utcnow()
        }
        
        # Insert assignment
        assignments_collection = get_collection("assignments")
        result = await assignments_collection.insert_one(assignment_data)
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create assignment"
            )
        
        # Fetch created assignment
        created_doc = await assignments_collection.find_one({"_id": result.inserted_id})
        assignment = Assignment(**created_doc)
        
        # Log activity
        try:
            await log_activity(
                assignment_input.camp_id,
                "assignment_created_via_rest",
                {
                    "assignment_id": str(assignment.id),
                    "volunteer_id": assignment_input.volunteer_id,
                    "role": assignment_input.role,
                    "created_by": current_user["email"]
                }
            )
        except Exception as e:
            print(f"Warning: Failed to log assignment creation: {e}")
        
        # Return assignment data
        return {
            "id": str(assignment.id),
            "camp_id": str(assignment.camp_id),
            "volunteer_id": str(assignment.volunteer_id),
            "role": assignment.role,
            "slot": assignment.slot,
            "status": assignment.status,
            "is_backup": assignment.is_backup,
            "created_at": assignment.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating assignment: {str(e)}"
        )


@router.get("/", response_model=List[dict])
async def list_assignments(camp_id: str = None, volunteer_id: str = None):
    """
    Get assignments, optionally filtered by camp_id or volunteer_id.
    
    Args:
        camp_id: Optional camp ID to filter by
        volunteer_id: Optional volunteer ID to filter by
        
    Returns:
        List of assignment dictionaries
        
    Raises:
        HTTPException 400: If camp_id or volunteer_id is invalid format
        HTTPException 500: If database operation fails
    """
    try:
        collection = get_collection("assignments")
        
        # Build query filter
        query = {}
        if camp_id:
            try:
                query["camp_id"] = ObjectId(camp_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid camp ID format: {camp_id}"
                )
        
        if volunteer_id:
            try:
                query["volunteer_id"] = ObjectId(volunteer_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid volunteer ID format: {volunteer_id}"
                )
        
        cursor = collection.find(query)
        assignments = []
        
        async for doc in cursor:
            try:
                assignment = Assignment(**doc)
                assignments.append({
                    "id": str(assignment.id),
                    "camp_id": str(assignment.camp_id),
                    "volunteer_id": str(assignment.volunteer_id),
                    "role": assignment.role,
                    "slot": assignment.slot,
                    "status": assignment.status,
                    "is_backup": assignment.is_backup,
                    "created_at": assignment.created_at.isoformat()
                })
            except Exception as e:
                print(f"Warning: Skipping invalid assignment document: {e}")
                continue
        
        return assignments
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching assignments: {str(e)}"
        )


@router.get("/{assignment_id}", response_model=dict)
async def get_assignment(assignment_id: str):
    """
    Get an assignment by ID.
    
    Args:
        assignment_id: Assignment ID (MongoDB ObjectId as string)
        
    Returns:
        Dictionary with assignment data
        
    Raises:
        HTTPException 400: If assignment_id is invalid format
        HTTPException 404: If assignment not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(assignment_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid assignment ID format: {assignment_id}"
            )
        
        collection = get_collection("assignments")
        assignment_doc = await collection.find_one({"_id": object_id})
        
        if not assignment_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment not found: {assignment_id}"
            )
        
        assignment = Assignment(**assignment_doc)
        return {
            "id": str(assignment.id),
            "camp_id": str(assignment.camp_id),
            "volunteer_id": str(assignment.volunteer_id),
            "role": assignment.role,
            "slot": assignment.slot,
            "status": assignment.status,
            "is_backup": assignment.is_backup,
            "created_at": assignment.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching assignment: {str(e)}"
        )


@router.patch("/{assignment_id}", response_model=dict)
async def update_assignment_status(
    assignment_id: str,
    status: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Update assignment status.
    
    Requires authentication (admin role).
    
    Args:
        assignment_id: Assignment ID (MongoDB ObjectId as string)
        status: New status (assigned, confirmed, cancelled, backup)
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        Dictionary with updated assignment data
        
    Raises:
        HTTPException 400: If assignment_id is invalid format or status is invalid
        HTTPException 401: If not authenticated
        HTTPException 404: If assignment not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate status
        valid_statuses = {"assigned", "confirmed", "cancelled", "backup"}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Validate ObjectId format
        try:
            object_id = ObjectId(assignment_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid assignment ID format: {assignment_id}"
            )
        
        collection = get_collection("assignments")
        
        # Check if assignment exists
        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment not found: {assignment_id}"
            )
        
        # Update status
        result = await collection.find_one_and_update(
            {"_id": object_id},
            {"$set": {"status": status}},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update assignment"
            )
        
        assignment = Assignment(**result)
        
        # Log activity
        try:
            await log_activity(
                str(assignment.camp_id),
                "assignment_status_updated_via_rest",
                {
                    "assignment_id": assignment_id,
                    "status": status,
                    "updated_by": current_user["email"]
                }
            )
        except Exception as e:
            print(f"Warning: Failed to log assignment status update: {e}")
        
        return {
            "id": str(assignment.id),
            "camp_id": str(assignment.camp_id),
            "volunteer_id": str(assignment.volunteer_id),
            "role": assignment.role,
            "slot": assignment.slot,
            "status": assignment.status,
            "is_backup": assignment.is_backup,
            "created_at": assignment.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating assignment: {str(e)}"
        )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(assignment_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete an assignment by ID.
    
    Requires authentication (admin role).
    
    Args:
        assignment_id: Assignment ID (MongoDB ObjectId as string)
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        No content (204)
        
    Raises:
        HTTPException 400: If assignment_id is invalid format
        HTTPException 401: If not authenticated
        HTTPException 404: If assignment not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(assignment_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid assignment ID format: {assignment_id}"
            )
        
        collection = get_collection("assignments")
        
        # Check if assignment exists
        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment not found: {assignment_id}"
            )
        
        # Delete assignment
        result = await collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete assignment"
            )
        
        # Log activity
        try:
            await log_activity(
                str(existing.get("camp_id")),
                "assignment_deleted_via_rest",
                {
                    "assignment_id": assignment_id,
                    "deleted_by": current_user["email"]
                }
            )
        except Exception as e:
            print(f"Warning: Failed to log assignment deletion: {e}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting assignment: {str(e)}"
        )

