"""Helper functions to recompute assignments given camp_id."""
from typing import List, Dict, Tuple, Set
from datetime import datetime
from bson import ObjectId

from app.database import get_collection
from app.models import Camp, Volunteer, Assignment
from app.planner import plan_assignments, calculate_unfilled_slots


async def get_camp_by_id(camp_id: str) -> Camp:
    """Fetch a camp by ID."""
    collection = get_collection("camps")
    doc = await collection.find_one({"_id": ObjectId(camp_id)})
    if not doc:
        raise ValueError(f"Camp not found: {camp_id}")
    return Camp(**doc)


async def get_volunteers_for_replan(camp_id: str) -> List[Volunteer]:
    """Fetch all volunteers for replanning."""
    collection = get_collection("volunteers")
    cursor = collection.find({})
    volunteers = []
    async for doc in cursor:
        volunteers.append(Volunteer(**doc))
    return volunteers


async def get_existing_assignments(camp_id: str) -> List[Assignment]:
    """Fetch existing assignments for a camp."""
    collection = get_collection("assignments")
    cursor = collection.find({"camp_id": ObjectId(camp_id)})
    assignments = []
    async for doc in cursor:
        assignments.append(Assignment(**doc))
    return assignments


async def replan_camp(camp_id: ObjectId) -> Tuple[List[Assignment], int]:
    """
    Replan assignments for a camp.
    
    Strategy (Simple and Safe):
    - Treat CONFIRMED assignments as fixed (never changed or deleted)
    - Treat everything else (assigned/backup/cancelled) as "to be recomputed"
    - For each camp requirement (role, slot, count), subtract the number of 
      CONFIRMED assignments for that (role, slot)
    - The remainder is the unfilled demand to be handled by replanning
    - Exclude cancelled volunteers from being assigned again
    - Exclude volunteers already confirmed for this camp (they stay where they are)
    
    Args:
        camp_id: Camp ObjectId
        
    Returns:
        Tuple of (list of NEW assignments created, unfilled_slots_count)
        
    Raises:
        ValueError: If camp not found
    """
    camp_id_str = str(camp_id)
    
    # 1. Load camp
    camp = await get_camp_by_id(camp_id_str)
    
    # 2. Load existing assignments
    existing_assignments = await get_existing_assignments(camp_id_str)
    
    # 3. Classify assignments by status
    confirmed_assignments = [
        assign for assign in existing_assignments
        if assign.status == "confirmed"
    ]
    
    cancelled_assignments = [
        assign for assign in existing_assignments
        if assign.status == "cancelled"
    ]
    
    active_assignments = [
        assign for assign in existing_assignments
        if assign.status in ("assigned", "backup")
    ]
    
    # 4. Get cancelled volunteer IDs (they are unavailable for this camp)
    cancelled_volunteer_ids: Set[str] = {
        str(assign.volunteer_id) for assign in cancelled_assignments
    }
    
    # 5. Get confirmed volunteer IDs for this camp (they are already assigned and fixed)
    # These volunteers should NOT be considered for new assignments in this camp
    confirmed_volunteer_ids_for_camp: Set[str] = {
        str(assign.volunteer_id) for assign in confirmed_assignments
    }
    
    # 6. Load all volunteers
    all_volunteers = await get_volunteers_for_replan(camp_id_str)
    
    # 7. Filter eligible volunteers:
    # - Exclude cancelled volunteers (they cancelled for this camp)
    # - Exclude volunteers already confirmed for this camp (they're fixed in their current role/slot)
    eligible_volunteers = [
        v for v in all_volunteers
        if str(v.id) not in cancelled_volunteer_ids
        and str(v.id) not in confirmed_volunteer_ids_for_camp
    ]
    
    # 8. Delete old non-confirmed assignments (assigned/backup) - they will be replaced
    if active_assignments:
        assignment_collection = get_collection("assignments")
        active_ids = [assign.id for assign in active_assignments]
        await assignment_collection.delete_many({
            "_id": {"$in": active_ids}
        })
    
    # 9. Call planner with confirmed assignments as existing
    # The planner will:
    # - Respect confirmed assignments (treat them as already filled)
    # - Calculate remaining demand per requirement (count - confirmed_count)
    # - Fill gaps with eligible volunteers
    all_assignments = await plan_assignments(
        camp=camp,
        volunteers=eligible_volunteers,
        existing_assignments=confirmed_assignments
    )
    
    # 10. Separate new assignments from confirmed ones
    # Use a set of (role, slot, volunteer_id) tuples to identify confirmed assignments
    confirmed_assignment_keys: Set[Tuple[str, str, str]] = {
        (assign.role, assign.slot, str(assign.volunteer_id))
        for assign in confirmed_assignments
    }
    
    new_assignments = [
        assign for assign in all_assignments
        if (assign.role, assign.slot, str(assign.volunteer_id)) not in confirmed_assignment_keys
    ]
    
    # 11. Persist new assignments to MongoDB
    if new_assignments:
        assignment_collection = get_collection("assignments")
        for assignment in new_assignments:
            # Set created_at if not set
            if not hasattr(assignment, 'created_at') or assignment.created_at is None:
                assignment.created_at = datetime.utcnow()
            
            # Ensure status is "assigned" and is_backup is False for new assignments
            assignment.status = "assigned"
            assignment.is_backup = False
            
            # Insert assignment
            result = await assignment_collection.insert_one(assignment.dict(by_alias=True))
            assignment.id = result.inserted_id
    
    # 12. Calculate unfilled slots (remaining demand after all assignments)
    all_final_assignments = confirmed_assignments + new_assignments
    unfilled_slots = calculate_unfilled_slots(camp.requirements, all_final_assignments)
    
    return new_assignments, unfilled_slots
