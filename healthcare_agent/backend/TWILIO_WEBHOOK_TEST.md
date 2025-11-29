# Twilio Webhook Testing Guide

## 🧪 Quick Test Commands

### Test 1: Volunteer Confirms Assignment

```bash
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=confirm"
```

**Expected Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Thank you! Your assignment has been confirmed.</Message>
</Response>
```

### Test 2: Volunteer Cancels Assignment

```bash
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=cancel"
```

**Expected Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Your assignment has been cancelled. We'll work on finding a replacement.</Message>
</Response>
```

### Test 3: Alternative Confirm Messages

```bash
# Using "yes"
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=yes"

# Using "confirmed"
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=confirmed"
```

### Test 4: Alternative Cancel Messages

```bash
# Using "no"
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=no"

# Using "cancelled"
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=cancelled"
```

### Test 5: Unknown Message (Help Response)

```bash
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=hello"
```

**Expected Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Please reply with "confirm" or "cancel" to update your assignment status.</Message>
</Response>
```

## 📋 Complete Test Script

Run all tests at once:

```bash
bash test_twilio_webhook.sh
```

## 🔍 What Happens Behind the Scenes

### When Volunteer Confirms:

1. **Webhook receives** `From=+919392664227`, `Body=confirm`
2. **Normalizes phone** to E.164 format
3. **Finds volunteer** in `volunteers` collection
4. **Finds active assignment** (status: "assigned" or "backup")
5. **Updates assignment** status to "confirmed"
6. **Logs activity** to `activity_logs`
7. **Returns TwiML** confirmation message

### When Volunteer Cancels:

1. **Webhook receives** `From=+919392664227`, `Body=cancel`
2. **Normalizes phone** to E.164 format
3. **Finds volunteer** in `volunteers` collection
4. **Finds active assignment** (status: "assigned" or "backup")
5. **Updates assignment** status to "cancelled"
6. **Triggers replan** via Celery (non-blocking)
7. **Logs activity** to `activity_logs`
8. **Returns TwiML** cancellation message

## ✅ Prerequisites for Testing

1. **Volunteer exists** in database with phone `+919392664227`
2. **Active assignment** exists for that volunteer (status: "assigned" or "backup")
3. **Backend server running** on `http://localhost:8000`

### Check Volunteer Exists

```python
from app.database import connect_to_mongo, get_collection
import asyncio

async def check():
    await connect_to_mongo()
    volunteers = get_collection("volunteers")
    doc = await volunteers.find_one({"phone": "+919392664227"})
    if doc:
        print(f"✅ Volunteer found: {doc.get('name')}")
    else:
        print("❌ Volunteer not found")

asyncio.run(check())
```

### Check Active Assignment

```python
from app.database import connect_to_mongo, get_collection
from bson import ObjectId
import asyncio

async def check():
    await connect_to_mongo()
    volunteers = get_collection("volunteers")
    assignments = get_collection("assignments")
    
    # Find volunteer
    vol_doc = await volunteers.find_one({"phone": "+919392664227"})
    if not vol_doc:
        print("❌ Volunteer not found")
        return
    
    vol_id = vol_doc["_id"]
    
    # Find active assignment
    assign_doc = await assignments.find_one({
        "volunteer_id": vol_id,
        "status": {"$in": ["assigned", "backup"]}
    })
    
    if assign_doc:
        print(f"✅ Active assignment found: {assign_doc.get('role')} - {assign_doc.get('slot')}")
    else:
        print("❌ No active assignment found")

asyncio.run(check())
```

## 🎯 Testing Different Scenarios

### Scenario 1: Volunteer Not Found

```bash
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+911234567890" \
  -d "Body=confirm"
```

**Expected:** "Sorry, we couldn't find your volunteer record..."

### Scenario 2: No Active Assignment

```bash
# Use a volunteer with no active assignments
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=confirm"
```

**Expected:** "You don't have any active assignments at the moment."

## 📊 Verify Results

### Check Assignment Status Changed

```python
from app.database import connect_to_mongo, get_collection
from bson import ObjectId
import asyncio

async def check():
    await connect_to_mongo()
    volunteers = get_collection("volunteers")
    assignments = get_collection("assignments")
    
    vol_doc = await volunteers.find_one({"phone": "+919392664227"})
    if not vol_doc:
        return
    
    vol_id = vol_doc["_id"]
    assign_doc = await assignments.find_one({
        "volunteer_id": vol_id
    }, sort=[("created_at", -1)])
    
    if assign_doc:
        print(f"Assignment status: {assign_doc.get('status')}")

asyncio.run(check())
```

### Check Activity Logs

```python
from app.database import connect_to_mongo, get_collection
import asyncio

async def check():
    await connect_to_mongo()
    logs = get_collection("activity_logs")
    
    # Get latest logs
    cursor = logs.find({}).sort("timestamp", -1).limit(5)
    async for log in cursor:
        print(f"{log.get('timestamp')}: {log.get('event')}")

asyncio.run(check())
```

## 🔐 Security Note

**Localhost Testing:**
- Signature validation is **bypassed** for localhost requests
- This allows testing without Twilio's signature header
- **Production:** Real Twilio webhooks will include `X-Twilio-Signature` header

## 📱 Real Twilio Webhook Format

When Twilio sends a real webhook, it includes:
- `X-Twilio-Signature` header (for validation)
- Form-encoded data with additional fields:
  - `From`, `Body`, `MessageSid`, `AccountSid`, `To`, etc.

Our endpoint handles both:
- **Localhost testing** (no signature, bypasses validation)
- **Production** (with signature, validates request)

## 🚀 Quick Test Command (Copy-Paste Ready)

```bash
# Confirm assignment
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=confirm"

# Cancel assignment  
curl -X POST "http://localhost:8000/twilio/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=cancel"
```

