#!/usr/bin/env python
"""Update volunteer phone numbers to match the actual data."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['agentic_volunteer']
    volunteers = db['volunteers']
    
    # Update with the real phone numbers from the user's database
    updates = [
        (ObjectId("692a6a3fe412d1839324f74b"), "+918125817577"),  # Anita Rao
        (ObjectId("692a6a3fe412d1839324f74c"), "+919441313134"),  # Rohit Sharma
        (ObjectId("692a6a3fe412d1839324f74d"), "+919441780009"),  # Meera Iyer
    ]
    
    print("Updating volunteer phone numbers...")
    for vol_id, phone in updates:
        result = await volunteers.update_one(
            {"_id": vol_id},
            {"$set": {"phone": phone}}
        )
        if result.modified_count > 0:
            vol = await volunteers.find_one({"_id": vol_id})
            print(f"✓ Updated {vol['name']}: {phone}")
        else:
            print(f"✗ Could not find volunteer with ID {vol_id}")
    
    # Verify the updates
    print("\n=== UPDATED VOLUNTEERS ===")
    async for vol in volunteers.find({}, {'name': 1, 'phone': 1}).limit(5):
        print(f"{vol['name']}: {vol['phone']}")
    
    client.close()

if __name__ == '__main__':
    asyncio.run(main())

