#!/usr/bin/env python3
"""
Debug Twilio Configuration - Concrete Code Proof

This script provides concrete proof of:
1. What's in .env file
2. What's loaded in settings
3. What works and what doesn't
4. Exact code to fix issues
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def show_env_file():
    """Show actual .env file content."""
    print("=" * 70)
    print("1. .env FILE CONTENT (Lines 5-8)")
    print("=" * 70)
    
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("❌ .env file not found!")
        return
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Show lines 5-8 (0-indexed: 4-7)
    print("\nLines 5-8 from .env file:")
    print("-" * 70)
    for i in range(4, min(8, len(lines))):
        line_num = i + 1
        line = lines[i].rstrip()
        print(f"Line {line_num}: {line}")
    
    # Show all Twilio-related lines
    print("\nAll TWILIO lines in .env:")
    print("-" * 70)
    for i, line in enumerate(lines, 1):
        if 'TWILIO' in line.upper():
            print(f"Line {i}: {line.rstrip()}")


def show_loaded_settings():
    """Show what's actually loaded."""
    print("\n" + "=" * 70)
    print("2. SETTINGS LOADED FROM app.config")
    print("=" * 70)
    
    try:
        from app.config import settings
        
        print("\nActual values loaded:")
        print("-" * 70)
        print(f"twilio_account_sid: '{settings.twilio_account_sid}'")
        print(f"  Length: {len(settings.twilio_account_sid)}")
        print(f"  Starts with AC: {settings.twilio_account_sid.startswith('AC')}")
        
        print(f"\ntwilio_auth_token: '{settings.twilio_auth_token[:4]}...{settings.twilio_auth_token[-4:]}'")
        print(f"  Length: {len(settings.twilio_auth_token)}")
        print(f"  Is set: {bool(settings.twilio_auth_token)}")
        
        print(f"\ntwilio_whatsapp_from: '{settings.twilio_whatsapp_from}'")
        print(f"  Is default: {settings.twilio_whatsapp_from == 'whatsapp:+14155238886'}")
        
        print(f"\ntwilio_content_sid: '{settings.twilio_content_sid}'")
        print(f"  Is set: {bool(settings.twilio_content_sid)}")
        
        print(f"\ntwilio_phone_number: '{settings.twilio_phone_number}'")
        
        return settings
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_twilio_client(settings):
    """Test Twilio client with concrete proof."""
    print("\n" + "=" * 70)
    print("3. TWILIO CLIENT TEST (Concrete Proof)")
    print("=" * 70)
    
    try:
        from app.notifications import get_twilio_client
        
        print("\nCreating Twilio client...")
        client = get_twilio_client()
        
        if not client:
            print("❌ Client is None - check credentials")
            return False
        
        print("✅ Client created successfully")
        
        # Test account fetch
        print(f"\nFetching account info for: {settings.twilio_account_sid}")
        try:
            account = client.api.accounts(settings.twilio_account_sid).fetch()
            print(f"✅ Account validated!")
            print(f"   Account Name: {account.friendly_name}")
            print(f"   Account SID: {account.sid}")
            print(f"   Status: {account.status}")
            return True
        except Exception as e:
            print(f"❌ Account fetch failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_sending(settings):
    """Test template sending capability."""
    print("\n" + "=" * 70)
    print("4. TEMPLATE SENDING TEST")
    print("=" * 70)
    
    if not settings.twilio_content_sid:
        print("⚠️  TWILIO_CONTENT_SID not set - templates will not work")
        print("\nTo fix, add to .env:")
        print('TWILIO_CONTENT_SID="HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"')
        return False
    
    print(f"✅ Content SID configured: {settings.twilio_content_sid}")
    
    # Test the function exists
    try:
        from app.notifications import send_whatsapp_message_with_template
        print("✅ Template function available")
        
        # Show function signature
        import inspect
        sig = inspect.signature(send_whatsapp_message_with_template)
        print(f"   Function signature: {sig}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def show_fixes_needed():
    """Show what needs to be fixed."""
    print("\n" + "=" * 70)
    print("5. FIXES NEEDED")
    print("=" * 70)
    
    from app.config import settings
    
    fixes = []
    
    if not settings.twilio_content_sid:
        fixes.append({
            "issue": "TWILIO_CONTENT_SID not set",
            "fix": 'Add to .env: TWILIO_CONTENT_SID="HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"',
            "line": "After TWILIO_PHONE_NUMBER line"
        })
    
    if settings.twilio_whatsapp_from == "whatsapp:+14155238886":
        fixes.append({
            "issue": "TWILIO_WHATSAPP_FROM using default",
            "fix": 'Add to .env: TWILIO_WHATSAPP_FROM="whatsapp:+14155238886" (or your Twilio number)',
            "line": "Optional - default works"
        })
    
    if fixes:
        print("\nIssues found:")
        for i, fix in enumerate(fixes, 1):
            print(f"\n{i}. {fix['issue']}")
            print(f"   Fix: {fix['fix']}")
            print(f"   Location: {fix['line']}")
    else:
        print("\n✅ No fixes needed - everything is configured!")
    
    return fixes


def show_working_code_example():
    """Show working code example."""
    print("\n" + "=" * 70)
    print("6. WORKING CODE EXAMPLE")
    print("=" * 70)
    
    from app.config import settings
    
    print("\nExample: Send template message")
    print("-" * 70)
    print("""
from app.notifications import send_whatsapp_message_with_template
import asyncio

async def send():
    result = await send_whatsapp_message_with_template(
        to="+918885625847",
        content_sid="HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        content_variables={
            "1": "12/1",  # Appointment date
            "2": "3pm"    # Appointment time
        }
    )
    print(f"Message SID: {result['sid']}")

asyncio.run(send())
""")
    
    print("\nCurrent Configuration:")
    print("-" * 70)
    print(f"Account SID: {settings.twilio_account_sid}")
    print(f"Auth Token: {'SET' if settings.twilio_auth_token else 'NOT SET'}")
    print(f"WhatsApp From: {settings.twilio_whatsapp_from}")
    print(f"Content SID: {settings.twilio_content_sid or 'NOT SET (add to .env)'}")


def main():
    """Run all debug checks."""
    print("\n" + "=" * 70)
    print("TWILIO CONFIGURATION DEBUG - CONCRETE CODE PROOF")
    print("=" * 70)
    
    # Step 1: Show .env file
    show_env_file()
    
    # Step 2: Show loaded settings
    settings = show_loaded_settings()
    if not settings:
        print("\n❌ Cannot continue - settings not loaded")
        sys.exit(1)
    
    # Step 3: Test Twilio client
    client_ok = test_twilio_client(settings)
    
    # Step 4: Test template
    template_ok = test_template_sending(settings)
    
    # Step 5: Show fixes
    fixes = show_fixes_needed()
    
    # Step 6: Show working example
    show_working_code_example()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Twilio Client: {'WORKING' if client_ok else 'FAILED'}")
    print(f"{'✅' if template_ok else '⚠️ '} Template Support: {'READY' if template_ok else 'NEEDS TWILIO_CONTENT_SID'}")
    print(f"{'⚠️ ' if fixes else '✅'} Configuration: {'NEEDS FIXES' if fixes else 'COMPLETE'}")
    
    if fixes:
        print("\n📝 ACTION REQUIRED:")
        print("   Add the missing configuration to your .env file")
        print("   See section 5 above for exact fixes")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

