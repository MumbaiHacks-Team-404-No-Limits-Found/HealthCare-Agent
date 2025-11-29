"""REST API endpoints for Volunteer CRUD operations."""
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.database import get_collection
from app.models import Volunteer, VolunteerInput
from app.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_volunteer(volunteer_input: VolunteerInput):
    """
    Create a new volunteer.
    
    Args:
        volunteer_input: VolunteerInput with name, phone, skills, availability
        
    Returns:
        Dictionary with created volunteer data and id
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If database operation fails
    """
    try:
        collection = get_collection("volunteers")
        
        # Validate required fields
        if not volunteer_input.name or not volunteer_input.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volunteer name is required"
            )
        if not volunteer_input.phone or not volunteer_input.phone.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Volunteer phone is required"
            )
        
        # Validate no_show_rate
        if volunteer_input.no_show_rate < 0 or volunteer_input.no_show_rate > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="no_show_rate must be between 0 and 1"
            )
        
        # Prepare volunteer document
        volunteer_data = {
            "name": volunteer_input.name.strip(),
            "phone": volunteer_input.phone.strip(),
            "skills": volunteer_input.skills or [],
            "availability": [
                {"date": a.date, "slots": a.slots}
                for a in (volunteer_input.availability or [])
            ],
            "no_show_rate": volunteer_input.no_show_rate
        }
        
        # Insert volunteer
        result = await collection.insert_one(volunteer_data)
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create volunteer"
            )
        
        # Fetch created volunteer
        created_doc = await collection.find_one({"_id": result.inserted_id})
        volunteer = Volunteer(**created_doc)
        
        # Return volunteer data
        return {
            "id": str(volunteer.id),
            "name": volunteer.name,
            "phone": volunteer.phone,
            "skills": volunteer.skills,
            "availability": [
                {"date": a.date, "slots": a.slots}
                for a in volunteer.availability
            ],
            "no_show_rate": volunteer.no_show_rate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating volunteer: {str(e)}"
        )


@router.get("/", response_model=List[dict])
async def list_volunteers():
    """
    Get all volunteers.
    
    Returns:
        List of volunteer dictionaries
        
    Raises:
        HTTPException 500: If database operation fails
    """
    try:
        collection = get_collection("volunteers")
        cursor = collection.find({})
        volunteers = []
        
        async for doc in cursor:
            try:
                volunteer = Volunteer(**doc)
                volunteers.append({
                    "id": str(volunteer.id),
                    "name": volunteer.name,
                    "phone": volunteer.phone,
                    "skills": volunteer.skills,
                    "availability": [
                        {"date": a.date, "slots": a.slots}
                        for a in volunteer.availability
                    ],
                    "no_show_rate": volunteer.no_show_rate
                })
            except Exception as e:
                print(f"Warning: Skipping invalid volunteer document: {e}")
                continue
        
        return volunteers
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching volunteers: {str(e)}"
        )


@router.get("/{volunteer_id}", response_model=dict)
async def get_volunteer(volunteer_id: str):
    """
    Get a volunteer by ID.
    
    Args:
        volunteer_id: Volunteer ID (MongoDB ObjectId as string)
        
    Returns:
        Dictionary with volunteer data
        
    Raises:
        HTTPException 400: If volunteer_id is invalid format
        HTTPException 404: If volunteer not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(volunteer_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid volunteer ID format: {volunteer_id}"
            )
        
        collection = get_collection("volunteers")
        volunteer_doc = await collection.find_one({"_id": object_id})
        
        if not volunteer_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Volunteer not found: {volunteer_id}"
            )
        
        volunteer = Volunteer(**volunteer_doc)
        return {
            "id": str(volunteer.id),
            "name": volunteer.name,
            "phone": volunteer.phone,
            "skills": volunteer.skills,
            "availability": [
                {"date": a.date, "slots": a.slots}
                for a in volunteer.availability
            ],
            "no_show_rate": volunteer.no_show_rate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching volunteer: {str(e)}"
        )


@router.put("/{volunteer_id}", response_model=dict)
async def update_volunteer(volunteer_id: str, volunteer_input: VolunteerInput):
    """
    Update a volunteer by ID.
    
    Args:
        volunteer_id: Volunteer ID (MongoDB ObjectId as string)
        volunteer_input: VolunteerInput with updated data
        
    Returns:
        Dictionary with updated volunteer data
        
    Raises:
        HTTPException 400: If volunteer_id is invalid format or validation fails
        HTTPException 404: If volunteer not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(volunteer_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid volunteer ID format: {volunteer_id}"
            )
        
        collection = get_collection("volunteers")
        
        # Check if volunteer exists
        existing = await collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Volunteer not found: {volunteer_id}"
            )
        
        # Prepare update data
        update_data = {
            "name": volunteer_input.name.strip(),
            "phone": volunteer_input.phone.strip(),
            "skills": volunteer_input.skills or [],
            "availability": [
                {"date": a.date, "slots": a.slots}
                for a in (volunteer_input.availability or [])
            ],
            "no_show_rate": volunteer_input.no_show_rate
        }
        
        # Update volunteer
        result = await collection.find_one_and_update(
            {"_id": object_id},
            {"$set": update_data},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update volunteer"
            )
        
        volunteer = Volunteer(**result)
        return {
            "id": str(volunteer.id),
            "name": volunteer.name,
            "phone": volunteer.phone,
            "skills": volunteer.skills,
            "availability": [
                {"date": a.date, "slots": a.slots}
                for a in volunteer.availability
            ],
            "no_show_rate": volunteer.no_show_rate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating volunteer: {str(e)}"
        )


@router.delete("/{volunteer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_volunteer(volunteer_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a volunteer by ID.
    
    Requires authentication (admin role).
    Also deletes all associated assignments.
    
    Args:
        volunteer_id: Volunteer ID (MongoDB ObjectId as string)
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        No content (204)
        
    Raises:
        HTTPException 400: If volunteer_id is invalid format
        HTTPException 401: If not authenticated
        HTTPException 404: If volunteer not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate ObjectId format
        try:
            object_id = ObjectId(volunteer_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid volunteer ID format: {volunteer_id}"
            )
        
        volunteers_collection = get_collection("volunteers")
        
        # Check if volunteer exists
        existing = await volunteers_collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Volunteer not found: {volunteer_id}"
            )
        
        # Delete associated assignments
        assignments_collection = get_collection("assignments")
        await assignments_collection.delete_many({"volunteer_id": object_id})
        
        # Delete volunteer
        result = await volunteers_collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete volunteer"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting volunteer: {str(e)}"
        )

