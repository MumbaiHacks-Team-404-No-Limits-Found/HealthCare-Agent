"""Script to verify Twilio webhook configuration and test connectivity."""
import asyncio
import os
from app.config import settings
from app.database import connect_to_mongo, get_collection

async def verify_twilio_setup():
    """Comprehensive verification of Twilio webhook setup."""
    print("=" * 70)
    print("TWILIO WEBHOOK VERIFICATION")
    print("=" * 70)
    
    # 1. Check Environment Variables
    print("\n1. ENVIRONMENT CONFIGURATION")
    print("-" * 70)
    
    account_sid_ok = bool(settings.twilio_account_sid)
    auth_token_ok = bool(settings.twilio_auth_token)
    phone_ok = bool(settings.twilio_phone_number)
    
    print(f"TWILIO_ACCOUNT_SID: {'✓ SET' if account_sid_ok else '✗ NOT SET'}")
    if account_sid_ok:
        print(f"  Value: {settings.twilio_account_sid[:10]}...{settings.twilio_account_sid[-4:]}")
    
    print(f"TWILIO_AUTH_TOKEN: {'✓ SET' if auth_token_ok else '✗ NOT SET'}")
    if auth_token_ok:
        masked = settings.twilio_auth_token[:4] + "..." + settings.twilio_auth_token[-4:]
        print(f"  Value: {masked}")
    
    print(f"TWILIO_PHONE_NUMBER: {'✓ SET' if phone_ok else '✗ NOT SET'}")
    if phone_ok:
        print(f"  Value: {settings.twilio_phone_number}")
    
    # 2. Check Webhook Endpoint
    print("\n2. WEBHOOK ENDPOINT")
    print("-" * 70)
    webhook_url = "http://127.0.0.1:8000/twilio/webhook"
    print(f"Local URL: {webhook_url}")
    print(f"Endpoint: POST /twilio/webhook")
    print("\n⚠️  IMPORTANT: For Twilio to reach your local server:")
    print("   • Use ngrok: ngrok http 8000")
    print("   • Configure Twilio webhook URL to: https://<ngrok-url>/twilio/webhook")
    print("   • The URL in Twilio console MUST match exactly (including https://)")
    
    # 3. Check Signature Validation
    print("\n3. SIGNATURE VALIDATION")
    print("-" * 70)
    if auth_token_ok:
        print("✓ Validation ENABLED (secure)")
        print("  • Real Twilio webhooks will be validated")
        print("  • Localhost requests are allowed for testing (bypass validation)")
        print("  • Production: Ensure webhook URL in Twilio matches your server URL")
    else:
        print("✗ Validation DISABLED (dev mode)")
        print("  • All requests will be accepted")
        print("  • ⚠️  NOT SECURE for production!")
    
    # 4. Check Database Connection
    print("\n4. DATABASE CONNECTION")
    print("-" * 70)
    try:
        await connect_to_mongo()
        print("✓ MongoDB connection successful")
        
        # Check volunteers
        volunteers_collection = get_collection("volunteers")
        volunteer_count = await volunteers_collection.count_documents({})
        print(f"✓ Volunteers in database: {volunteer_count}")
        
        if volunteer_count > 0:
            print("\n  Sample volunteers (phone numbers):")
            cursor = volunteers_collection.find({}, {"name": 1, "phone": 1}).limit(5)
            async for vol in cursor:
                print(f"    • {vol.get('name', 'N/A')}: {vol.get('phone', 'N/A')}")
        else:
            print("  ⚠️  No volunteers found! Run: python seed_from_csv.py")
        
        # Check assignments
        assignments_collection = get_collection("assignments")
        active_count = await assignments_collection.count_documents(
            {"status": {"$in": ["assigned", "backup"]}}
        )
        print(f"\n✓ Active assignments: {active_count}")
        
        if active_count == 0:
            print("  ⚠️  No active assignments! Run: python demo_agent_run.py")
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
    
    # 5. Test Phone Number Format
    print("\n5. PHONE NUMBER FORMAT CHECK")
    print("-" * 70)
    test_phone = "9392664227"  # From your test
    print(f"Test phone from request: {test_phone}")
    print("Expected format in database: E.164 format (e.g., +19392664227)")
    print("\nThe webhook will try multiple formats:")
    print("  • Normalized format (E.164)")
    print("  • Original format from Twilio")
    print("  • With/without + prefix")
    print("  • Last 10 digits match")
    
    # 6. Recommendations
    print("\n6. RECOMMENDATIONS")
    print("-" * 70)
    
    if not all([account_sid_ok, auth_token_ok, phone_ok]):
        print("✗ Missing Twilio credentials in .env file")
        print("  Add to .env:")
        print("    TWILIO_ACCOUNT_SID=AC...")
        print("    TWILIO_AUTH_TOKEN=...")
        print("    TWILIO_PHONE_NUMBER=+1...")
    
    print("\n✓ For Local Testing (Swagger UI/FastAPI docs):")
    print("  • The endpoint now allows localhost requests without signature")
    print("  • You can test with: From=9392664227, Body=confirm")
    print("  • Ensure volunteer exists in database with matching phone")
    
    print("\n✓ For Production Testing:")
    print("  1. Start ngrok: ngrok http 8000")
    print("  2. Copy the https URL (e.g., https://abc123.ngrok.io)")
    print("  3. In Twilio Console → Phone Numbers → Manage → Active Numbers")
    print("  4. Find your number → Messaging → Webhook URL")
    print("  5. Set: https://abc123.ngrok.io/twilio/webhook")
    print("  6. Save and test by sending SMS to your Twilio number")
    
    print("\n✓ Verify Twilio Console Configuration:")
    print("  • Account SID matches: AC05ee03c2...")
    print("  • Auth Token matches (first 4 chars): cfc8...")
    print("  • Phone number matches: +918885625847")
    print("  • Webhook URL is set correctly (for production)")
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_twilio_setup())

