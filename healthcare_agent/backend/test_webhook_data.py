#!/usr/bin/env python
"""Quick script to check volunteers and assignments in the database."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['agentic_volunteer']
    volunteers = db['volunteers']
    assignments = db['assignments']
    
    print('=== VOLUNTEERS IN DATABASE ===')
    async for vol in volunteers.find({}, {'name': 1, 'phone': 1}).limit(10):
        print(f"Name: {vol.get('name')}, Phone: {vol.get('phone')}")
    
    print('\n=== ACTIVE ASSIGNMENTS (assigned/backup status) ===')
    async for assign in assignments.find(
        {'status': {'$in': ['assigned', 'backup']}}, 
        {'volunteer_id': 1, 'status': 1, 'role': 1, 'slot': 1}
    ).limit(5):
        vol = await volunteers.find_one({'_id': assign['volunteer_id']})
        if vol:
            print(f"Volunteer: {vol.get('name')} ({vol.get('phone')})")
            print(f"  Status: {assign['status']}, Role: {assign['role']}, Slot: {assign.get('slot')}")
            print()
    
    client.close()

if __name__ == '__main__':
    asyncio.run(main())

