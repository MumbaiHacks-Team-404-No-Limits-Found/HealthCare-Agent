# Quick Start: NotificationAPI SMS Integration

Get started with NotificationAPI SMS notifications in 5 minutes.

## Prerequisites

- Python 3.8+
- Redis installed and running
- NotificationAPI account

## Step 1: Install Dependencies (Already Done)

The required packages are already in `requirements.txt`:

```bash
notificationapi_python_server_sdk>=2.0.0
celery==5.3.6
redis==5.0.1
```

If not installed:
```bash
cd healthcare_agent/backend
source ../venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Get NotificationAPI Credentials

1. Sign up: https://app.notificationapi.com/signup
2. Go to Settings: https://app.notificationapi.com/settings
3. Copy your **Client ID** and **Client Secret**

## Step 3: Configure Environment Variables

Create/update `healthcare_agent/backend/.env`:

```bash
# NotificationAPI
NOTIFICATIONAPI_CLIENT_ID=your_client_id_here
NOTIFICATIONAPI_CLIENT_SECRET=your_client_secret_here

# Redis
REDIS_URL=redis://localhost:6379/0

# MongoDB (if not already set)
MONGO_URI=mongodb://localhost:27017/agentic_volunteer
DATABASE_NAME=agentic_volunteer

# JWT (if not already set)
JWT_SECRET_KEY=your-secret-key-here
```

## Step 4: Create NotificationAPI Templates

1. Go to: https://app.notificationapi.com/notifications
2. Create notification with ID: `volunteer_alert`
3. Enable **SMS** channel
4. Set template body: `{{message}}`
5. Save

Repeat for:
- `volunteer_assignment`
- `volunteer_reminder`

## Step 5: Start Services

### Terminal 1: Start Redis

```bash
redis-server
```

### Terminal 2: Start Celery Worker

```bash
cd healthcare_agent/backend
source ../venv/bin/activate
celery -A app.celery_worker worker --loglevel=info
```

### Terminal 3: Start FastAPI

```bash
cd healthcare_agent/backend
source ../venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Step 6: Test It!

### Option A: Test Script

```bash
cd healthcare_agent/backend

# Update phone number in test script first
nano test_notificationapi_integration.py
# Replace +919876543210 with your number

# Run tests
python test_notificationapi_integration.py
```

### Option B: Swagger UI

1. Open: http://localhost:8000/docs
2. Find `/notify/sms` endpoint
3. Click **Try it out**
4. Enter:
   ```json
   {
     "volunteer_id": "test_001",
     "phone": "+919876543210",
     "message": "Test SMS from NotificationAPI",
     "notification_type": "volunteer_alert"
   }
   ```
5. Click **Execute**

### Option C: cURL

```bash
curl -X POST "http://localhost:8000/notify/sms" \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_id": "test_001",
    "phone": "+919876543210",
    "message": "Test SMS",
    "notification_type": "volunteer_alert"
  }'
```

## Expected Response

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "volunteer_id": "test_001",
  "phone": "+919876543210",
  "message": "Test SMS"
}
```

## Verify Success

### Check Celery Worker Logs (Terminal 2)

```
[INFO] [Task send_sms_to_volunteer[xyz]] Sending SMS to volunteer test_001
[INFO] SMS notification sent via NotificationAPI
[INFO] [Task send_sms_to_volunteer[xyz]] SMS sent successfully
```

### Check NotificationAPI Dashboard

1. Go to: https://app.notificationapi.com/logs
2. See your sent notification
3. Check delivery status

### Check Your Phone

You should receive the SMS within a few seconds!

## What's Next?

- Read full documentation: `NOTIFICATIONAPI_INTEGRATION.md`
- Configure webhook for delivery receipts: `NOTIFICATIONAPI_SETUP.md`
- Explore all endpoints in Swagger UI: http://localhost:8000/docs

## Troubleshooting

### SMS not received?

- ✅ Check phone number format (must be E.164: +[country][number])
- ✅ Verify NotificationAPI template exists and SMS channel enabled
- ✅ Check NotificationAPI logs: https://app.notificationapi.com/logs
- ✅ Ensure account has SMS credits

### Task not processing?

- ✅ Check Redis is running: `redis-cli ping`
- ✅ Check Celery worker is running (see Terminal 2)
- ✅ Verify `.env` file has correct credentials
- ✅ Restart Celery worker

### Configuration error?

- ✅ Ensure `.env` file exists in `healthcare_agent/backend/`
- ✅ Check environment variables: `echo $NOTIFICATIONAPI_CLIENT_ID`
- ✅ Restart FastAPI after config changes

## API Endpoints

### Send SMS
```
POST /notify/sms
Body: {volunteer_id, phone, message, notification_type}
```

### Send by Volunteer ID
```
POST /notify/{volunteer_id}?message=Hello
```

### Send Assignment Notification
```
POST /notify/assignment/{volunteer_id}
Body: {camp_name, role, slot, camp_location, camp_date}
```

### Batch SMS
```
POST /notify/batch/sms
Body: {notifications: [{volunteer_id, phone_number, message}]}
```

### Webhook Handler
```
POST /notify/webhook
(Configured in NotificationAPI dashboard)
```

## Support

- Documentation: `NOTIFICATIONAPI_INTEGRATION.md`
- Setup Guide: `NOTIFICATIONAPI_SETUP.md`
- Test Script: `test_notificationapi_integration.py`
- NotificationAPI Support: https://notificationapi.com/support

## Success! 🎉

You're now sending SMS notifications via NotificationAPI with Celery and Redis!

The system will:
- ✅ Queue SMS tasks asynchronously
- ✅ Process them in background workers
- ✅ Retry automatically on failure
- ✅ Handle delivery status via webhooks
- ✅ Keep your FastAPI responsive

Happy coding! 🚀

