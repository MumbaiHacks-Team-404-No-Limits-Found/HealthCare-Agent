"""Add a test volunteer with a specific phone number for webhook testing."""
import asyncio
from app.database import connect_to_mongo, close_mongo_connection, get_collection


async def add_test_volunteer(phone: str, name: str = "Test Volunteer"):
    """Add a test volunteer with the given phone number."""
    await connect_to_mongo()
    
    collection = get_collection("volunteers")
    
    # Check if volunteer already exists
    existing = await collection.find_one({"phone": phone})
    if existing:
        print(f"Volunteer with phone {phone} already exists: {existing.get('name')}")
        await close_mongo_connection()
        return
    
    # Also check with +91 prefix
    phone_with_prefix = f"+91{phone}" if not phone.startswith("+") else phone
    existing = await collection.find_one({"phone": phone_with_prefix})
    if existing:
        print(f"Volunteer with phone {phone_with_prefix} already exists: {existing.get('name')}")
        await close_mongo_connection()
        return
    
    # Create test volunteer
    volunteer_doc = {
        "name": name,
        "phone": phone_with_prefix,  # Store with +91 prefix
        "skills": ["doctor", "nurse"],  # Give some skills
        "availability": [
            {
                "date": "2025-12-01",
                "slots": ["morning", "afternoon"]
            }
        ],
        "no_show_rate": 0.1
    }
    
    result = await collection.insert_one(volunteer_doc)
    print(f"SUCCESS: Added test volunteer: {name}")
    print(f"  Phone: {phone_with_prefix}")
    print(f"  ID: {result.inserted_id}")
    print(f"\nYou can now test the webhook with:")
    print(f"  From={phone}&Body=confirm")
    print(f"  or")
    print(f"  From={phone_with_prefix}&Body=confirm")
    
    await close_mongo_connection()


if __name__ == "__main__":
    import sys
    phone = sys.argv[1] if len(sys.argv) > 1 else "9392664227"
    name = sys.argv[2] if len(sys.argv) > 2 else "Test Volunteer"
    asyncio.run(add_test_volunteer(phone, name))

