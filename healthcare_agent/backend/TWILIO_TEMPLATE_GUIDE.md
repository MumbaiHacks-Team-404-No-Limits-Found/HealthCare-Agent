# Twilio Content Template Integration Guide

## 📋 Overview

This guide shows how to use Twilio content templates for sending structured WhatsApp messages with appointment details.

## 🔧 Configuration

Add to your `.env` file:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_CONTENT_SID=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 📝 Python Code Example

### Simple Template Message

```python
from twilio.rest import Client
import json

account_sid = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
auth_token = 'your_auth_token'
content_sid = 'HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

client = Client(account_sid, auth_token)

message = client.messages.create(
    from_='whatsapp:+14155238886',
    to='whatsapp:+918885625847',
    content_sid=content_sid,
    content_variables=json.dumps({
        "1": "12/1",   # Appointment date
        "2": "3pm"     # Appointment time
    })
)

print(f"Message SID: {message.sid}")
print(f"Status: {message.status}")
```

## 🚀 Using the Updated Functions

### Method 1: Direct Function Call

```python
from app.notifications import send_whatsapp_message_with_template

result = await send_whatsapp_message_with_template(
    to="+918885625847",
    content_sid="HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    content_variables={
        "1": "12/1",  # Appointment date
        "2": "3pm"    # Appointment time
    }
)

print(f"Message SID: {result['sid']}")
print(f"Status: {result['status']}")
```

### Method 2: Assignment Notification with Template

```python
from app.notifications import send_assignment_notification

# Send with template (if TWILIO_CONTENT_SID is configured)
success = await send_assignment_notification(
    phone_number="+918885625847",
    volunteer_name="Dr. John Smith",
    camp_name="Rural Health Camp",
    role="doctor",
    slot="morning",
    appointment_date="12/1",
    appointment_time="3pm",
    use_template=True  # Enable template mode
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

## 📱 Template Variable Mapping

Based on your example template, the variables are:
- `"1"` = Appointment date (e.g., "12/1")
- `"2"` = Appointment time (e.g., "3pm")

You can extend this with more variables:
- `"3"` = Volunteer name
- `"4"` = Role
- `"5"` = Camp name
- etc.

## 🧪 Test Scripts

### Test 1: Simple Template Script

```bash
python send_twilio_template_example.py
```

### Test 2: Using Config

```bash
python send_whatsapp_template.py +918885625847 "12/1" "3pm"
```

## 🔄 Integration with Agent Workflow

The agent workflow now supports templates automatically:

```python
from app.agent import MedicalCampAgent

agent = MedicalCampAgent()

# When sending notifications, templates will be used if:
# 1. use_template=True is passed
# 2. TWILIO_CONTENT_SID is configured
# 3. appointment_date and appointment_time are provided

# The notification system will automatically:
# - Use template if configured
# - Fall back to plain text if template fails or not configured
```

## 📊 Updated Files

1. **`app/config.py`**
   - Added `twilio_content_sid` configuration

2. **`app/notifications.py`**
   - Added `send_whatsapp_message_with_template()` function
   - Updated `send_assignment_notification()` to support templates

3. **`app/notify_router.py`**
   - Added `/notify/whatsapp/template` endpoint

4. **`send_twilio_template_example.py`**
   - Standalone example matching your code structure

5. **`send_whatsapp_template.py`**
   - CLI script for testing templates

## ✅ Quick Test

```bash
# 1. Set content SID in .env
echo "TWILIO_CONTENT_SID=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" >> .env

# 2. Test template message
python send_twilio_template_example.py

# 3. Or use the CLI
python send_whatsapp_template.py +918885625847 "12/1" "3pm"
```

## 🎯 Template Structure

Your Twilio template should have variables like:
- Variable `1`: Appointment date
- Variable `2`: Appointment time

Example template message:
```
Your appointment is scheduled for {{1}} at {{2}}.
```

When you send:
```python
content_variables = {"1": "12/1", "2": "3pm"}
```

The message becomes:
```
Your appointment is scheduled for 12/1 at 3pm.
```

## 🔍 Troubleshooting

### Template Not Sending

1. **Check Content SID:**
   ```python
   from app.config import settings
   print(f"Content SID: {settings.twilio_content_sid}")
   ```

2. **Verify Template Variables:**
   - Ensure variable names match your template (e.g., "1", "2")
   - Variables must be JSON-serializable strings

3. **Check Twilio Console:**
   - Verify template is approved in Twilio Console
   - Check template variable names match

### Fallback to Plain Text

If template sending fails, the system automatically falls back to plain text messages. Check logs for details.

