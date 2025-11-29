"""REST API endpoints for Camp CRUD operations."""
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.database import get_collection
from app.models import Camp, CampInput
from app.auth import get_current_user
from app.activity import log_activity

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_camp(camp_input: CampInput, current_user: dict = Depends(get_current_user)):
    """
    Create a new camp.
    
    Requires authentication (admin role).
    
    Args:
        camp_input: CampInput with name, location, start, end, requirements
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        Dictionary with created camp data and id
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 401: If not authenticated
        HTTPException 500: If database operation fails
    """
    try:
        collection = get_collection("camps")
        
        # Validate required fields
        if not camp_input.name or not camp_input.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Camp name is required"
            )
        if not camp_input.location or not camp_input.location.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Camp location is required"
            )
        
        # Prepare camp document
        camp_data = {
            "name": camp_input.name.strip(),
            "location": camp_input.location.strip(),
            "start": camp_input.start.strip(),
            "end": camp_input.end.strip(),
            "requirements": [
                {"role": r.role.strip(), "count": r.count, "slot": r.slot.strip()}
                for r in (camp_input.requirements or [])
            ]
        }
        
        # Insert camp
        result = await collection.insert_one(camp_data)
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create camp"
            )
        
        # Fetch created camp
        created_doc = await collection.find_one({"_id": result.inserted_id})
        camp = Camp(**created_doc)
        
        # Log activity
        try:
            await log_activity(
                str(camp.id),
                "camp_created_via_rest",
                {"name": camp.name, "created_by": current_user["email"]}
            )
        except Exception as e:
            print(f"Warning: Failed to log camp creation: {e}")
        
        # Return camp data
        return {
            "id": str(camp.id),
            "name": camp.name,
            "location": camp.location,
            "start": camp.start,
            "end": camp.end,
            "requirements": [
                {"role": r.role, "count": r.count, "slot": r.slot}
                for r in camp.requirements
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating camp: {str(e)}"
        )


@router.get("/", response_model=List[dict])
async def list_camps():
    """
    Get all camps.
    
    Returns:
        List of camp dictionaries with id, name, location, start, end, requirements
        
    Raises:
        HTTPException 500: If database operation fails
    """
    try:
        collection = get_collection("camps")
        cursor = collection.find({})
        camps = []
        
        async for doc in cursor:
            try:
                camp = Camp(**doc)
                camps.append({
                    "id": str(camp.id),
                    "name": camp.name,
                    "location": camp.location,
                    "start": camp.start,
                    "end": camp.end,
                    "requirements": [
                        {"role": r.role, "count": r.count, "slot": r.slot}
                        for r in camp.requirements
                    ]
                })
            except Exception as e:
                print(f"Warning: Skipping invalid camp document: {e}")
                continue
        
        return camps
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching camps: {str(e)}"
        )


@router.get("/{camp_id}", response_model=dict)
async def get_camp(camp_id: str):
    """
    Get a camp by ID.
    
    Args:
        camp_id: Camp ID (MongoDB ObjectId as string)
        
    Returns:
        Dictionary with camp data
        
    Raises:
        HTTPException 400: If camp_id is invalid format
        HTTPException 404: If camp not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(camp_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid camp ID format: {camp_id}"
            )
        
        collection = get_collection("camps")
        camp_doc = await collection.find_one({"_id": object_id})
        
        if not camp_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camp not found: {camp_id}"
            )
        
        camp = Camp(**camp_doc)
        return {
            "id": str(camp.id),
            "name": camp.name,
            "location": camp.location,
            "start": camp.start,
            "end": camp.end,
            "requirements": [
                {"role": r.role, "count": r.count, "slot": r.slot}
                for r in camp.requirements
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching camp: {str(e)}"
        )


@router.put("/{camp_id}", response_model=dict)
async def update_camp(
    camp_id: str,
    camp_input: CampInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a camp by ID.
    
    Requires authentication (admin role).
    
    Args:
        camp_id: Camp ID (MongoDB ObjectId as string)
        camp_input: CampInput with updated data
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        Dictionary with updated camp data
        
    Raises:
        HTTPException 400: If camp_id is invalid format or validation fails
        HTTPException 401: If not authenticated
        HTTPException 404: If camp not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(camp_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid camp ID format: {camp_id}"
            )
        
        collection = get_collection("camps")
        
        # Check if camp exists
        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camp not found: {camp_id}"
            )
        
        # Prepare update data
        update_data = {
            "name": camp_input.name.strip(),
            "location": camp_input.location.strip(),
            "start": camp_input.start.strip(),
            "end": camp_input.end.strip(),
            "requirements": [
                {"role": r.role.strip(), "count": r.count, "slot": r.slot.strip()}
                for r in (camp_input.requirements or [])
            ]
        }
        
        # Update camp
        result = await collection.find_one_and_update(
            {"_id": object_id},
            {"$set": update_data},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update camp"
            )
        
        camp = Camp(**result)
        
        # Log activity
        try:
            await log_activity(
                str(camp.id),
                "camp_updated_via_rest",
                {"name": camp.name, "updated_by": current_user["email"]}
            )
        except Exception as e:
            print(f"Warning: Failed to log camp update: {e}")
        
        return {
            "id": str(camp.id),
            "name": camp.name,
            "location": camp.location,
            "start": camp.start,
            "end": camp.end,
            "requirements": [
                {"role": r.role, "count": r.count, "slot": r.slot}
                for r in camp.requirements
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating camp: {str(e)}"
        )


@router.delete("/{camp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camp(camp_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a camp by ID.
    
    Requires authentication (admin role).
    Also deletes all associated assignments.
    
    Args:
        camp_id: Camp ID (MongoDB ObjectId as string)
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        No content (204)
        
    Raises:
        HTTPException 400: If camp_id is invalid format
        HTTPException 401: If not authenticated
        HTTPException 404: If camp not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(camp_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid camp ID format: {camp_id}"
            )
        
        camps_collection = get_collection("camps")
        
        # Check if camp exists
        existing = await camps_collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camp not found: {camp_id}"
            )
        
        # Delete associated assignments
        assignments_collection = get_collection("assignments")
        await assignments_collection.delete_many({"camp_id": object_id})
        
        # Delete camp
        result = await camps_collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete camp"
            )
        
        # Log activity
        try:
            await log_activity(
                camp_id,
                "camp_deleted_via_rest",
                {
                    "name": existing.get("name"),
                    "deleted_by": current_user["email"]
                }
            )
        except Exception as e:
            print(f"Warning: Failed to log camp deletion: {e}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting camp: {str(e)}"
        )

