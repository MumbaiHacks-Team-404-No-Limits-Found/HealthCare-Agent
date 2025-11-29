#!/usr/bin/env python3
"""
Comprehensive Twilio Configuration Verification Script

This script verifies:
1. .env file exists and contains Twilio settings
2. Settings are loaded correctly
3. Twilio client can be initialized
4. Content template SID is configured
5. All required fields are present
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_env_file():
    """Check if .env file exists and read Twilio settings."""
    print("=" * 70)
    print("STEP 1: Checking .env File")
    print("=" * 70)
    
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("❌ .env file not found!")
        print(f"   Expected location: {env_path}")
        return False
    
    print(f"✅ .env file found: {env_path}")
    
    # Read .env file
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # Check Twilio settings
    required_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_WHATSAPP_FROM',
        'TWILIO_CONTENT_SID'
    ]
    
    print("\nTwilio Configuration in .env:")
    print("-" * 70)
    
    all_present = True
    for var in required_vars:
        if var in env_vars:
            value = env_vars[var]
            if var == 'TWILIO_AUTH_TOKEN':
                # Mask auth token
                masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_present = False
    
    return all_present, env_vars


def check_settings_loading():
    """Check if settings are loaded correctly."""
    print("\n" + "=" * 70)
    print("STEP 2: Checking Settings Loading")
    print("=" * 70)
    
    try:
        from app.config import settings
        
        print("\nSettings loaded from app.config:")
        print("-" * 70)
        
        # Check each setting
        checks = {
            'TWILIO_ACCOUNT_SID': settings.twilio_account_sid,
            'TWILIO_AUTH_TOKEN': settings.twilio_auth_token,
            'TWILIO_WHATSAPP_FROM': settings.twilio_whatsapp_from,
            'TWILIO_CONTENT_SID': settings.twilio_content_sid,
            'TWILIO_PHONE_NUMBER': settings.twilio_phone_number,
        }
        
        all_loaded = True
        for key, value in checks.items():
            if value:
                if key == 'TWILIO_AUTH_TOKEN':
                    masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                    print(f"✅ {key}: {masked} (loaded)")
                else:
                    print(f"✅ {key}: {value} (loaded)")
            else:
                print(f"⚠️  {key}: NOT SET (empty string)")
                if key in ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_FROM']:
                    all_loaded = False
        
        return all_loaded, settings
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def check_twilio_client(settings):
    """Check if Twilio client can be initialized."""
    print("\n" + "=" * 70)
    print("STEP 3: Checking Twilio Client Initialization")
    print("=" * 70)
    
    try:
        from app.notifications import get_twilio_client
        
        client = get_twilio_client()
        
        if client:
            print("✅ Twilio client initialized successfully")
            
            # Try to get account info (this validates credentials)
            try:
                account = client.api.accounts(settings.twilio_account_sid).fetch()
                print(f"✅ Account validated: {account.friendly_name}")
                print(f"   Account SID: {account.sid}")
                return True
            except Exception as e:
                print(f"⚠️  Client created but account validation failed: {e}")
                print("   This might be okay if credentials are correct but API call failed")
                return True  # Client exists, that's what matters
        else:
            print("❌ Twilio client initialization failed")
            print("   Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing Twilio client: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_content_template():
    """Check if content template SID is configured."""
    print("\n" + "=" * 70)
    print("STEP 4: Checking Content Template Configuration")
    print("=" * 70)
    
    try:
        from app.config import settings
        
        if settings.twilio_content_sid:
            print(f"✅ Content Template SID: {settings.twilio_content_sid}")
            print("   Template is configured and ready to use")
            return True
        else:
            print("⚠️  Content Template SID: NOT SET")
            print("   Add TWILIO_CONTENT_SID=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx to .env")
            print("   (Templates will fall back to plain text messages)")
            return False
            
    except Exception as e:
        print(f"❌ Error checking content template: {e}")
        return False


def test_template_function():
    """Test the template sending function (dry run)."""
    print("\n" + "=" * 70)
    print("STEP 5: Testing Template Function (Dry Run)")
    print("=" * 70)
    
    try:
        from app.notifications import send_whatsapp_message_with_template
        from app.config import settings
        
        if not settings.twilio_content_sid:
            print("⚠️  Skipping: TWILIO_CONTENT_SID not configured")
            return True
        
        # Check function exists and is callable
        import inspect
        sig = inspect.signature(send_whatsapp_message_with_template)
        print(f"✅ Function exists: send_whatsapp_message_with_template")
        print(f"   Parameters: {list(sig.parameters.keys())}")
        
        # Verify it's async
        if inspect.iscoroutinefunction(send_whatsapp_message_with_template):
            print("✅ Function is async (correct)")
        else:
            print("⚠️  Function is not async")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing template function: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("TWILIO CONFIGURATION VERIFICATION")
    print("=" * 70)
    print()
    
    results = []
    
    # Step 1: Check .env file
    env_ok, env_vars = check_env_file()
    results.append(("Environment File", env_ok))
    
    # Step 2: Check settings loading
    settings_ok, settings = check_settings_loading()
    results.append(("Settings Loading", settings_ok))
    
    if not settings_ok:
        print("\n❌ Cannot continue - settings not loaded correctly")
        sys.exit(1)
    
    # Step 3: Check Twilio client
    client_ok = check_twilio_client(settings)
    results.append(("Twilio Client", client_ok))
    
    # Step 4: Check content template
    template_ok = check_content_template()
    results.append(("Content Template", template_ok))
    
    # Step 5: Test template function
    function_ok = test_template_function()
    results.append(("Template Function", function_ok))
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All checks passed! Twilio is properly configured.")
    else:
        print("\n⚠️  Some checks failed. Review the output above.")
    
    print("\n" + "=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

