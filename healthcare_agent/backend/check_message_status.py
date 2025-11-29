#!/usr/bin/env python3
"""
Check detailed message status and diagnose delivery issues.
"""
from twilio.rest import Client
from app.config import settings

client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

message_sid = "MMdd2318b952bd9678457480a2962002b1"
message = client.messages(message_sid).fetch()

print("=" * 70)
print("MESSAGE STATUS DETAILS")
print("=" * 70)
print()
print(f"Message SID: {message.sid}")
print(f"Status: {message.status}")
print(f"Error Code: {message.error_code}")
print(f"Error Message: {message.error_message or 'None'}")
print(f"To: {message.to}")
print(f"From: {message.from_}")
print(f"Date Sent: {message.date_sent}")
print(f"Date Updated: {message.date_updated}")
print()

# Twilio error code 63015 explanation
print("=" * 70)
print("ERROR CODE 63015 ANALYSIS")
print("=" * 70)
print()
print("Error Code 63015 typically means:")
print("  1. Recipient number is NOT opted in to receive WhatsApp messages")
print("  2. WhatsApp Business Account not fully configured")
print("  3. Content template not approved for production use")
print("  4. Sandbox mode restrictions (if using sandbox number)")
print()

# Check if using sandbox
if "+14155238886" in settings.twilio_whatsapp_from:
    print("⚠️  You are using Twilio WhatsApp Sandbox number (+14155238886)")
    print("   Sandbox restrictions:")
    print("   - Recipient must send 'join <keyword>' to your sandbox first")
    print("   - Only works with numbers that have opted in")
    print()
    print("To fix:")
    print("  1. Ask Anita to send 'join <your-keyword>' to +14155238886")
    print("  2. Or upgrade to a WhatsApp Business Account")
    print()

# Check content template
print("=" * 70)
print("CONTENT TEMPLATE CHECK")
print("=" * 70)
try:
    content = client.content.v1.contents(settings.twilio_content_sid).fetch()
    print(f"✅ Template found: {content.friendly_name}")
    print(f"   SID: {content.sid}")
    print(f"   Language: {content.language}")
except Exception as e:
    print(f"⚠️  Could not fetch template details: {e}")

print()
print("=" * 70)
print("SOLUTIONS")
print("=" * 70)
print()
print("Option 1: Opt-in recipient (for sandbox)")
print("  - Ask Anita to send 'join <keyword>' to +14155238886")
print()
print("Option 2: Use plain text message (no template)")
print("  - Use send_whatsapp_message() instead of template")
print()
print("Option 3: Upgrade WhatsApp Business Account")
print("  - Contact Twilio to set up full WhatsApp Business Account")

