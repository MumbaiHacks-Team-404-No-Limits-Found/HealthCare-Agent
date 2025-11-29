#!/usr/bin/env python3
"""
Send plain text WhatsApp message to Anita (works better in sandbox mode).
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import connect_to_mongo, get_collection
from app.notifications import send_whatsapp_message
from app.config import settings


async def send_plain_message():
    """Send plain text message to Anita."""
    await connect_to_mongo()
    
    print("=" * 70)
    print("SENDING PLAIN TEXT MESSAGE TO ANITA")
    print("=" * 70)
    print()
    
    # Find Anita
    volunteers = get_collection('volunteers')
    volunteer = await volunteers.find_one({'name': {'$regex': '^anita', '$options': 'i'}})
    
    if not volunteer:
        print("❌ Volunteer 'Anita' not found")
        return
    
    name = volunteer.get('name')
    phone = volunteer.get('phone')
    
    print(f"✅ Found: {name}")
    print(f"   Phone: {phone}")
    print()
    
    # Send plain text message
    message_text = """Hello Anita! 

This is a test message from the Medical Camp Volunteer Coordinator.

Your appointment details:
- Date: December 1st
- Time: 3:00 PM

Please reply with 'confirm' or 'cancel' to update your status.

Thank you!"""
    
    print("Sending plain text WhatsApp message...")
    print()
    
    try:
        result = await send_whatsapp_message(
            to=phone,
            body=message_text
        )
        
        print("=" * 70)
        print("✅ MESSAGE SENT!")
        print("=" * 70)
        print(f"SID: {result['sid']}")
        print(f"Status: {result['status']}")
        print(f"To: {result['to']}")
        print()
        
        if result['status'] == 'failed':
            print("⚠️  Message failed. Possible reasons:")
            print("   - Recipient not opted in to sandbox")
            print("   - Ask Anita to send 'join <keyword>' to +14155238886")
        elif result['status'] in ('queued', 'sent'):
            print("✅ Message queued/sent successfully!")
            print("   Note: In sandbox mode, recipient must opt in first")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(send_plain_message())

