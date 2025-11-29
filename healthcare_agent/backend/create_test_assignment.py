"""Create a test assignment for a volunteer to test the webhook."""
import asyncio
from datetime import datetime
from bson import ObjectId
from app.database import connect_to_mongo, close_mongo_connection, get_collection


async def create_test_assignment(phone: str):
    """Create a test assignment for the volunteer with given phone."""
    await connect_to_mongo()
    
    volunteers_collection = get_collection("volunteers")
    camps_collection = get_collection("camps")
    assignments_collection = get_collection("assignments")
    
    # Find volunteer by phone (try multiple formats)
    phone_variants = [
        phone,
        f"+91{phone}" if not phone.startswith("+") else phone,
        phone.lstrip("+")
    ]
    
    volunteer_doc = None
    for variant in phone_variants:
        volunteer_doc = await volunteers_collection.find_one({"phone": variant})
        if volunteer_doc:
            break
    
    if not volunteer_doc:
        print(f"ERROR: Volunteer with phone {phone} not found")
        await close_mongo_connection()
        return
    
    volunteer_id = volunteer_doc.get("_id")
    print(f"Found volunteer: {volunteer_doc.get('name')} (ID: {volunteer_id})")
    
    # Find or create a test camp
    camp_doc = await camps_collection.find_one({})
    if not camp_doc:
        print("ERROR: No camps found. Please seed camps first with: python seed_from_csv.py")
        await close_mongo_connection()
        return
    
    camp_id = camp_doc.get("_id")
    print(f"Using camp: {camp_doc.get('name')} (ID: {camp_id})")
    
    # Check if assignment already exists
    existing = await assignments_collection.find_one({
        "volunteer_id": volunteer_id,
        "camp_id": camp_id,
        "status": {"$in": ["assigned", "backup"]}
    })
    
    if existing:
        print(f"Active assignment already exists:")
        print(f"  Assignment ID: {existing.get('_id')}")
        print(f"  Role: {existing.get('role')}")
        print(f"  Slot: {existing.get('slot')}")
        print(f"  Status: {existing.get('status')}")
        await close_mongo_connection()
        return
    
    # Create test assignment
    assignment_doc = {
        "camp_id": camp_id,
        "volunteer_id": volunteer_id,
        "role": "doctor",  # Use a role from camp requirements if available
        "slot": "morning",
        "status": "assigned",
        "is_backup": False,
        "created_at": datetime.utcnow()
    }
    
    result = await assignments_collection.insert_one(assignment_doc)
    print(f"SUCCESS: Created test assignment")
    print(f"  Assignment ID: {result.inserted_id}")
    print(f"  Role: {assignment_doc['role']}")
    print(f"  Slot: {assignment_doc['slot']}")
    print(f"  Status: {assignment_doc['status']}")
    print(f"\nYou can now test the webhook with:")
    print(f"  From={phone}&Body=confirm")
    
    await close_mongo_connection()


if __name__ == "__main__":
    import sys
    phone = sys.argv[1] if len(sys.argv) > 1 else "9392664227"
    asyncio.run(create_test_assignment(phone))

