#!/usr/bin/env python3
"""
Send WhatsApp message to volunteer Anitha using content template.
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect_to_mongo, get_collection
from app.notifications import send_whatsapp_message_with_template
from app.config import settings


async def find_and_send():
    """Find Anitha and send message."""
    # Connect to database
    await connect_to_mongo()
    
    print("=" * 70)
    print("SENDING MESSAGE TO VOLUNTEER ANITHA")
    print("=" * 70)
    print()
    
    # Find Anitha or Anita
    volunteers = get_collection('volunteers')
    # Try "Anitha" first, then "Anita"
    volunteer = await volunteers.find_one({'name': {'$regex': 'anitha', '$options': 'i'}})
    if not volunteer:
        volunteer = await volunteers.find_one({'name': {'$regex': '^anita', '$options': 'i'}})
    
    if not volunteer:
        print("❌ Volunteer 'Anitha' or 'Anita' not found in database.")
        print("\nAvailable volunteers:")
        cursor = volunteers.find({})
        async for vol in cursor:
            print(f"  - {vol.get('name')}: {vol.get('phone')}")
        return
    
    name = volunteer.get('name')
    phone = volunteer.get('phone')
    
    print(f"✅ Found volunteer: {name}")
    print(f"   Phone: {phone}")
    print()
    
    # Send message using content template
    print("Sending WhatsApp message using content template...")
    print(f"   Content SID: {settings.twilio_content_sid}")
    print(f"   To: {phone}")
    print()
    
    try:
        result = await send_whatsapp_message_with_template(
            to=phone,
            content_sid=settings.twilio_content_sid,
            content_variables={
                "1": "12/1",  # Appointment date - adjust as needed
                "2": "3pm"    # Appointment time - adjust as needed
            }
        )
        
        print("=" * 70)
        print("✅ MESSAGE SENT SUCCESSFULLY!")
        print("=" * 70)
        print(f"Message SID: {result['sid']}")
        print(f"Status: {result['status']}")
        print(f"To: {result['to']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Delivered: {result['delivered']}")
        print()
        print("Anitha should receive the WhatsApp message shortly.")
        
    except Exception as e:
        print("=" * 70)
        print("❌ ERROR SENDING MESSAGE")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(find_and_send())

