"""Quick script to check volunteers in the database."""
import asyncio
from app.database import connect_to_mongo, close_mongo_connection, get_collection


async def check_volunteers():
    """Check what volunteers exist in the database."""
    await connect_to_mongo()
    
    collection = get_collection("volunteers")
    cursor = collection.find({})
    
    print("Volunteers in database:")
    print("=" * 60)
    count = 0
    async for vol in cursor:
        count += 1
        print(f"{count}. Name: {vol.get('name')}")
        print(f"   Phone: {vol.get('phone')}")
        print(f"   Skills: {vol.get('skills', [])}")
        print()
    
    if count == 0:
        print("⚠ No volunteers found in database!")
        print("\nTo seed volunteers, run:")
        print("  python seed_from_csv.py")
    else:
        print(f"Total: {count} volunteers")
    
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(check_volunteers())

