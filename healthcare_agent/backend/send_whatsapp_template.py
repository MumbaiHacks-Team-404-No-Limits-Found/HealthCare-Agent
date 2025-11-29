#!/usr/bin/env python3
"""
Script to send WhatsApp message using Twilio content template.

Usage:
    python send_whatsapp_template.py <phone_number> <appointment_date> <appointment_time>
    
Example:
    python send_whatsapp_template.py +918885625847 "12/1" "3pm"
"""

import sys
import asyncio
import json
from app.database import connect_to_mongo, close_mongo_connection
from app.notifications import send_whatsapp_message_with_template
from app.config import settings


async def send_template_message(phone: str, date: str, time: str):
    """Send WhatsApp message using content template."""
    
    # Check if content_sid is configured
    if not settings.twilio_content_sid:
        print("❌ Error: TWILIO_CONTENT_SID not configured in .env file")
        print("   Add: TWILIO_CONTENT_SID=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        return False
    
    print(f"Sending WhatsApp template message to: {phone}")
    print(f"Content SID: {settings.twilio_content_sid}")
    print(f"Template Variables:")
    print(f"  Date: {date}")
    print(f"  Time: {time}")
    print("-" * 70)
    
    try:
        # Prepare content variables
        # Adjust variable names based on your Twilio template structure
        content_variables = {
            "1": date,   # Template variable 1 = appointment date
            "2": time    # Template variable 2 = appointment time
        }
        
        # Send message
        result = await send_whatsapp_message_with_template(
            to=phone,
            content_sid=settings.twilio_content_sid,
            content_variables=content_variables
        )
        
        print("\n✅ Message sent successfully!")
        print(f"   SID: {result['sid']}")
        print(f"   Status: {result['status']}")
        print(f"   To: {result['to']}")
        print(f"   Delivered: {result['delivered']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error sending message: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print(__doc__)
        print("\nUsage:")
        print("  python send_whatsapp_template.py <phone> <date> <time>")
        print("\nExample:")
        print("  python send_whatsapp_template.py +918885625847 \"12/1\" \"3pm\"")
        sys.exit(1)
    
    phone = sys.argv[1]
    date = sys.argv[2]
    time = sys.argv[3]
    
    try:
        await connect_to_mongo()
        success = await send_template_message(phone, date, time)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())

