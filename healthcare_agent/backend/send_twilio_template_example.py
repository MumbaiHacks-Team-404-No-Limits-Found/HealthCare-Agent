#!/usr/bin/env python3
"""
Twilio WhatsApp Content Template Example

This script demonstrates how to send WhatsApp messages using Twilio content templates.
Matches the structure you provided.

Usage:
    python send_twilio_template_example.py
"""

from twilio.rest import Client
from app.config import settings
import json


def send_whatsapp_with_template(
    to_phone: str,
    appointment_date: str,
    appointment_time: str
):
    """
    Send WhatsApp message using Twilio content template.
    
    Args:
        to_phone: Recipient phone number (e.g., '+918885625847')
        appointment_date: Appointment date (e.g., '12/1')
        appointment_time: Appointment time (e.g., '3pm')
    """
    # Get credentials from settings
    account_sid = settings.twilio_account_sid
    auth_token = settings.twilio_auth_token
    
    if not account_sid or not auth_token:
        print("❌ Error: Twilio credentials not configured")
        print("   Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env file")
        return None
    
    # Content template SID (configure in .env as TWILIO_CONTENT_SID)
    content_sid = settings.twilio_content_sid or 'HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    
    # Format phone number for WhatsApp
    if not to_phone.startswith('whatsapp:'):
        whatsapp_to = f'whatsapp:{to_phone}'
    else:
        whatsapp_to = to_phone
    
    # WhatsApp from number (Twilio's number)
    whatsapp_from = settings.twilio_whatsapp_from or 'whatsapp:+14155238886'
    
    # Prepare content variables as JSON string
    # Template variables: "1" = date, "2" = time
    content_variables = {
        "1": appointment_date,
        "2": appointment_time
    }
    content_variables_json = json.dumps(content_variables)
    
    try:
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Send message with content template
        message = client.messages.create(
            from_=whatsapp_from,
            to=whatsapp_to,
            content_sid=content_sid,
            content_variables=content_variables_json
        )
        
        print("✅ Message sent successfully!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        print(f"   To: {message.to}")
        print(f"   From: {message.from_}")
        
        return message
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Example usage
    print("=" * 70)
    print("Twilio WhatsApp Content Template Example")
    print("=" * 70)
    print()
    
    # Example: Send appointment notification
    result = send_whatsapp_with_template(
        to_phone='+918885625847',  # Volunteer's phone number
        appointment_date='12/1',   # Appointment date
        appointment_time='3pm'     # Appointment time
    )
    
    if result:
        print(f"\n✅ Success! Message SID: {result.sid}")
    else:
        print("\n❌ Failed to send message")

