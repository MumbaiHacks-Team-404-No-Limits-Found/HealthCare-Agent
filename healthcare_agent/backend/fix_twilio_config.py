#!/usr/bin/env python3
"""
Fix Twilio Configuration - Concrete Code Proof and Fix Instructions

This script:
1. Analyzes current .env configuration (lines 5-8)
2. Verifies what's working and what's missing
3. Provides exact code to fix issues
4. Tests the configuration after fixes
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def analyze_current_config():
    """Analyze current .env configuration."""
    print("=" * 70)
    print("TWILIO CONFIGURATION ANALYSIS - CONCRETE CODE PROOF")
    print("=" * 70)
    
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    print("\n1. CURRENT .env FILE (Lines 5-8):")
    print("-" * 70)
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Show lines 5-8
    for i in range(4, min(8, len(lines))):
        print(f"Line {i+1}: {lines[i].rstrip()}")
    
    # Check what's loaded
    print("\n2. LOADED SETTINGS (from app.config):")
    print("-" * 70)
    
    try:
        from app.config import settings
        
        config_status = {
            "TWILIO_ACCOUNT_SID": {
                "value": settings.twilio_account_sid,
                "status": "✅" if settings.twilio_account_sid else "❌",
                "loaded": bool(settings.twilio_account_sid)
            },
            "TWILIO_AUTH_TOKEN": {
                "value": f"{settings.twilio_auth_token[:4]}...{settings.twilio_auth_token[-4:]}" if settings.twilio_auth_token else "NOT SET",
                "status": "✅" if settings.twilio_auth_token else "❌",
                "loaded": bool(settings.twilio_auth_token)
            },
            "TWILIO_WHATSAPP_FROM": {
                "value": settings.twilio_whatsapp_from,
                "status": "✅" if settings.twilio_whatsapp_from else "⚠️",
                "loaded": bool(settings.twilio_whatsapp_from),
                "is_default": settings.twilio_whatsapp_from == "whatsapp:+14155238886"
            },
            "TWILIO_CONTENT_SID": {
                "value": settings.twilio_content_sid or "NOT SET",
                "status": "✅" if settings.twilio_content_sid else "❌",
                "loaded": bool(settings.twilio_content_sid)
            },
            "TWILIO_PHONE_NUMBER": {
                "value": settings.twilio_phone_number,
                "status": "✅" if settings.twilio_phone_number else "❌",
                "loaded": bool(settings.twilio_phone_number)
            }
        }
        
        for key, info in config_status.items():
            status = info["status"]
            value = info["value"]
            if key == "TWILIO_WHATSAPP_FROM" and info.get("is_default"):
                print(f"{status} {key}: {value} (using default)")
            else:
                print(f"{status} {key}: {value}")
        
        return config_status, settings
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_twilio_connection(settings):
    """Test Twilio connection with concrete proof."""
    print("\n3. TWILIO CONNECTION TEST:")
    print("-" * 70)
    
    try:
        from app.notifications import get_twilio_client
        
        client = get_twilio_client()
        
        if not client:
            print("❌ Twilio client is None")
            return False
        
        print("✅ Twilio client created")
        
        # Validate account
        try:
            account = client.api.accounts(settings.twilio_account_sid).fetch()
            print(f"✅ Account validated: {account.friendly_name}")
            print(f"   Account SID: {account.sid}")
            print(f"   Status: {account.status}")
            return True
        except Exception as e:
            print(f"⚠️  Account validation failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_webhook_configuration():
    """Verify webhook uses From and Body correctly."""
    print("\n4. WEBHOOK CONFIGURATION CHECK:")
    print("-" * 70)
    
    webhook_path = Path(__file__).parent / "app" / "twilio_webhook.py"
    
    if not webhook_path.exists():
        print("❌ twilio_webhook.py not found")
        return False
    
    with open(webhook_path, 'r') as f:
        content = f.read()
    
    # Check if From and Body are used
    uses_from = "From: str = Form(...)" in content or "From = Form" in content
    uses_body = "Body: str = Form(...)" in content or "Body = Form" in content
    
    if uses_from and uses_body:
        print("✅ Webhook correctly uses 'From' parameter from request body")
        print("✅ Webhook correctly uses 'Body' parameter from request body")
        
        # Show the exact lines
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if "From:" in line and "Form" in line:
                print(f"   Line {i}: {line.strip()}")
            if "Body:" in line and "Form" in line:
                print(f"   Line {i}: {line.strip()}")
        
        return True
    else:
        print("❌ Webhook configuration issue")
        return False


def show_required_fixes():
    """Show what needs to be fixed."""
    print("\n5. REQUIRED FIXES:")
    print("-" * 70)
    
    print("\nAdd these lines to your .env file after line 8:")
    print()
    print('TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"')
    print('TWILIO_CONTENT_SID="HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"')
    print()
    print("Your .env file should look like this (lines 5-10):")
    print()
    print('# Twilio SMS (optional - only needed for SMS notifications)')
    print('TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"')
    print('TWILIO_AUTH_TOKEN="your_auth_token_here"')
    print('TWILIO_PHONE_NUMBER="whatsapp:+14155238886"')
    print('TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"')
    print('TWILIO_CONTENT_SID="HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"')


def show_test_code():
    """Show test code to verify everything works."""
    print("\n6. TEST CODE (After adding fixes):")
    print("-" * 70)
    
    print("""
# Test template message sending
from app.notifications import send_whatsapp_message_with_template
import asyncio

async def test_template():
    result = await send_whatsapp_message_with_template(
        to="+918885625847",
        content_sid="HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        content_variables={
            "1": "12/1",  # Appointment date
            "2": "3pm"    # Appointment time
        }
    )
    print(f"✅ Message sent! SID: {result['sid']}")

asyncio.run(test_template())
""")


def main():
    """Run complete analysis."""
    # Step 1: Analyze current config
    config_status, settings = analyze_current_config()
    
    if not settings:
        print("\n❌ Cannot continue - settings not loaded")
        sys.exit(1)
    
    # Step 2: Test Twilio connection
    connection_ok = test_twilio_connection(settings)
    
    # Step 3: Check webhook
    webhook_ok = check_webhook_configuration()
    
    # Step 4: Show fixes
    show_required_fixes()
    
    # Step 5: Show test code
    show_test_code()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if config_status:
        missing = [k for k, v in config_status.items() 
                  if not v["loaded"] and k in ["TWILIO_CONTENT_SID"]]
        
        if missing:
            print(f"⚠️  Missing configuration: {', '.join(missing)}")
        else:
            print("✅ All required configuration present")
    
    print(f"✅ Twilio Connection: {'WORKING' if connection_ok else 'FAILED'}")
    print(f"✅ Webhook Configuration: {'CORRECT' if webhook_ok else 'ISSUES'}")
    
    if missing or not connection_ok:
        print("\n📝 ACTION REQUIRED:")
        print("   1. Add missing configuration to .env (see section 5)")
        print("   2. Restart the backend server")
        print("   3. Run this script again to verify")
    else:
        print("\n🎉 Everything is configured correctly!")
    
    print("=" * 70)


if __name__ == "__main__":
    main()

