# Twilio Content Template Usage Guide

## 🎯 Quick Reference

### Your Original Code Structure

```python
from twilio.rest import Client

account_sid = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)

message = client.messages.create(
    from_='whatsapp:+14155238886',
    content_sid='HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    content_variables='{"1":"12/1","2":"3pm"}',
    to='whatsapp:+918885625847'
)
```

## ✅ Updated Implementation

### Method 1: Using the Standalone Script (Matches Your Code)

```python
# File: send_twilio_template_example.py
python send_twilio_template_example.py
```

This script uses your exact structure with settings from `.env` file.

### Method 2: Using the Notification Function

```python
from app.notifications import send_whatsapp_message_with_template

result = await send_whatsapp_message_with_template(
    to="+918885625847",  # Volunteer's phone (From in your example)
        content_sid="HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    content_variables={
        "1": "12/1",  # Appointment date
        "2": "3pm"    # Appointment time
    }
)
```

### Method 3: REST API Endpoint

```bash
curl -X POST "http://localhost:8000/notify/whatsapp/template" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "phone": "+918885625847",
    "content_sid": "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "content_variables": {
      "1": "12/1",
      "2": "3pm"
    }
  }'
```

### Method 4: Automatic in Assignment Notifications

```python
from app.notifications import send_assignment_notification

# Automatically uses template if TWILIO_CONTENT_SID is set
await send_assignment_notification(
    phone_number="+918885625847",
    volunteer_name="Dr. John Smith",
    camp_name="Rural Health Camp",
    role="doctor",
    slot="morning",
    appointment_date="12/1",      # Template variable "1"
    appointment_time="3pm",       # Template variable "2"
    use_template=True             # Enable template mode
)
```

## 📋 Configuration

Add to `.env`:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_CONTENT_SID=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 🔄 Request Body Mapping

**Your Request:**
- `From` = Volunteer's phone number (`+918885625847`)
- `Body` = Message content

**In Twilio API:**
- `from_` = Twilio's WhatsApp number (`whatsapp:+14155238886`)
- `to` = Volunteer's phone number (`whatsapp:+918885625847`)
- `content_sid` = Template SID
- `content_variables` = Template variables as JSON string

**Note:** The `From` in your request body is actually the recipient (`to`) in Twilio's API.

## 📝 Complete Example Script

```python
#!/usr/bin/env python3
from twilio.rest import Client
import json
from app.config import settings

# Get credentials from config
account_sid = settings.twilio_account_sid
auth_token = settings.twilio_auth_token
content_sid = settings.twilio_content_sid or 'HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Create client
client = Client(account_sid, auth_token)

# Send message with template
message = client.messages.create(
    from_='whatsapp:+14155238886',  # Twilio's WhatsApp number
    to='whatsapp:+918885625847',    # Volunteer's phone (From in request body)
    content_sid=content_sid,
    content_variables=json.dumps({
        "1": "12/1",  # Appointment date
        "2": "3pm"    # Appointment time
    })
)

print(f"Message SID: {message.sid}")
print(f"Status: {message.status}")
```

## 🧪 Testing

### Test 1: Direct Script

```bash
python send_twilio_template_example.py
```

### Test 2: CLI Script

```bash
python send_whatsapp_template.py +918885625847 "12/1" "3pm"
```

### Test 3: REST API

```bash
curl -X POST "http://localhost:8000/notify/whatsapp/template" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "phone": "+918885625847",
    "content_sid": "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "content_variables": {"1": "12/1", "2": "3pm"}
  }'
```

## 🔍 Key Differences from Your Code

1. **Phone Number Format:**
   - Your code: `to='whatsapp:+918885625847'`
   - Our function: Auto-formats with `format_whatsapp_number()`

2. **Content Variables:**
   - Your code: `content_variables='{"1":"12/1","2":"3pm"}'` (JSON string)
   - Our function: Accepts dict, converts to JSON internally

3. **Configuration:**
   - Your code: Hardcoded credentials
   - Our function: Uses `settings` from `.env` file

4. **Error Handling:**
   - Your code: Basic try-catch
   - Our function: Comprehensive error handling with logging

## ✅ All Files Updated

1. ✅ `app/config.py` - Added `twilio_content_sid`
2. ✅ `app/notifications.py` - Added `send_whatsapp_message_with_template()`
3. ✅ `app/notifications.py` - Updated `send_assignment_notification()` to support templates
4. ✅ `app/notify_router.py` - Added `/notify/whatsapp/template` endpoint
5. ✅ `send_twilio_template_example.py` - Standalone example matching your code
6. ✅ `send_whatsapp_template.py` - CLI script for testing

## 🚀 Ready to Use

All code is ready and matches your requirements. Just:

1. Add `TWILIO_CONTENT_SID` to `.env`
2. Run: `python send_twilio_template_example.py`
3. Or use the REST API endpoint

The webhook (`twilio_webhook.py`) doesn't need changes - it handles incoming messages, not outgoing ones.

