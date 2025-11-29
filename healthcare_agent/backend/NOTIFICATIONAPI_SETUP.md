# NotificationAPI Integration Setup Guide

This guide explains how to set up NotificationAPI for SMS notifications in the Healthcare Agent system.

## Overview

The system now supports NotificationAPI as an alternative to Twilio for SMS notifications. NotificationAPI integration uses:
- **FastAPI** for REST endpoints
- **Celery** for asynchronous task processing
- **Redis** as the message broker
- **NotificationAPI SDK** for sending SMS

## Prerequisites

1. **Python dependencies** (already in requirements.txt):
   ```
   notificationapi_python_server_sdk>=2.0.0
   celery==5.3.6
   redis==5.0.1
   ```

2. **Running services**:
   - Redis server (for Celery broker)
   - MongoDB (for volunteer data)
   - FastAPI application
   - Celery worker

## Environment Variables

Add these to your `.env` file:

```bash
# NotificationAPI Credentials
NOTIFICATIONAPI_CLIENT_ID=your_notificationapi_client_id_here
NOTIFICATIONAPI_CLIENT_SECRET=your_notificationapi_client_secret_here

# Redis URL (required for Celery)
REDIS_URL=redis://localhost:6379/0
```

### Complete .env File Template

```bash
# ============================================================================
# Application Configuration
# ============================================================================

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/agentic_volunteer
DATABASE_NAME=agentic_volunteer

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ============================================================================
# NotificationAPI Configuration (New - Primary SMS Provider)
# ============================================================================

# Get credentials from: https://app.notificationapi.com/settings
NOTIFICATIONAPI_CLIENT_ID=your_notificationapi_client_id_here
NOTIFICATIONAPI_CLIENT_SECRET=your_notificationapi_client_secret_here

# ============================================================================
# Redis/Celery Configuration (Required for Background Tasks)
# ============================================================================

REDIS_URL=redis://localhost:6379/0

# ============================================================================
# Twilio Configuration (Legacy - Optional)
# ============================================================================

TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_CONTENT_SID=

# ============================================================================
# CORS and Rate Limiting
# ============================================================================

CORS_ORIGINS=http://localhost:3000,http://localhost:8000
RATE_LIMIT_PER_MINUTE=60
```

## NotificationAPI Account Setup

### Step 1: Create NotificationAPI Account

1. Sign up at: https://app.notificationapi.com/signup
2. Verify your email address
3. Complete account setup

### Step 2: Get Your Credentials

1. Go to: https://app.notificationapi.com/settings
2. Navigate to **API Credentials** section
3. Copy your **Client ID** and **Client Secret**
4. Add them to your `.env` file:
   ```bash
   NOTIFICATIONAPI_CLIENT_ID=your_client_id_here
   NOTIFICATIONAPI_CLIENT_SECRET=your_client_secret_here
   ```

### Step 3: Create Notification Templates

Create the following notification templates in NotificationAPI:

#### Template 1: volunteer_alert (Generic Alerts)

1. Go to: https://app.notificationapi.com/notifications
2. Click **Create Notification**
3. Set **Notification ID**: `volunteer_alert`
4. Set **Name**: `Volunteer Alert`
5. Enable **SMS** channel
6. Set SMS template:
   ```
   {{message}}
   ```
7. Save the template

#### Template 2: volunteer_assignment (Assignment Notifications)

1. Create new notification with ID: `volunteer_assignment`
2. Enable **SMS** channel
3. Set SMS template:
   ```
   {{message}}
   ```
4. Save the template

#### Template 3: volunteer_reminder (Reminder Notifications)

1. Create new notification with ID: `volunteer_reminder`
2. Enable **SMS** channel
3. Set SMS template:
   ```
   {{message}}
   ```
4. Save the template

### Step 4: Configure Webhook (Optional but Recommended)

Webhooks allow you to receive delivery status updates for sent SMS messages.

1. Go to: https://app.notificationapi.com/settings/webhooks
2. Click **Add Webhook**
3. Set **Webhook URL**: `https://your-domain.com/notify/webhook`
   - For local testing: `http://localhost:8000/notify/webhook`
   - For production: Use your actual domain with HTTPS
4. Select events to subscribe to:
   - ✅ `SMS_DELIVERED` - SMS successfully delivered
   - ✅ `SMS_FAILED` - SMS failed to deliver
   - ✅ `SMS_BOUNCED` - SMS bounced (invalid number)
   - ✅ `UNSUBSCRIBED` - User unsubscribed
5. Save webhook configuration

**Note**: For local development, consider using a service like ngrok to expose your local server:
```bash
ngrok http 8000
# Use the ngrok URL for webhook: https://your-ngrok-id.ngrok.io/notify/webhook
```

## Running the System

### 1. Start Redis Server

```bash
# macOS (Homebrew)
brew services start redis

# Or run in foreground
redis-server

# Ubuntu/Debian
sudo systemctl start redis

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Start Celery Worker

Open a new terminal and run:

```bash
cd healthcare_agent/backend

# Activate virtual environment
source ../venv/bin/activate  # macOS/Linux
# or
../venv/Scripts/activate  # Windows

# Start Celery worker
celery -A app.celery_worker worker --loglevel=info
```

You should see output like:
```
-------------- celery@hostname v5.3.6 (emerald-rush)
--- ***** ----- 
-- ******* ---- [config]
- *** --- * --- .> broker:   redis://localhost:6379/0
- ** ---------- .> result backend: redis://localhost:6379/0
...
[tasks]
  . send_assignment_notification
  . send_batch_sms
  . send_reminder_notification
  . send_sms_to_volunteer
```

### 3. Start FastAPI Application

Open another terminal and run:

```bash
cd healthcare_agent/backend

# Activate virtual environment
source ../venv/bin/activate  # macOS/Linux

# Start FastAPI with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 4. Verify Setup

Visit the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Check the new SMS endpoints under **notifications** tag:
- `POST /notify/sms` - Send generic SMS
- `POST /notify/{volunteer_id}` - Send SMS to volunteer by ID
- `POST /notify/assignment/{volunteer_id}` - Send assignment notification
- `POST /notify/batch/sms` - Send batch SMS
- `POST /notify/webhook` - Webhook for delivery status

## Testing the Integration

### Test 1: Send Generic SMS

Using curl:
```bash
curl -X POST "http://localhost:8000/notify/sms" \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_id": "507f1f77bcf86cd799439011",
    "phone": "+919876543210",
    "message": "Test SMS from NotificationAPI",
    "notification_type": "volunteer_alert"
  }'
```

Expected response:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "volunteer_id": "507f1f77bcf86cd799439011",
  "phone": "+919876543210",
  "message": "Test SMS from NotificationAPI"
}
```

### Test 2: Send SMS to Volunteer by ID

First, create a test volunteer in MongoDB or use an existing volunteer ID:

```bash
curl -X POST "http://localhost:8000/notify/507f1f77bcf86cd799439011?message=Hello%20from%20the%20system!" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "status": "Queued",
  "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "volunteer_id": "507f1f77bcf86cd799439011",
  "volunteer_name": "John Doe",
  "phone": "+919876543210"
}
```

### Test 3: Send Assignment Notification

```bash
curl -X POST "http://localhost:8000/notify/assignment/507f1f77bcf86cd799439011" \
  -H "Content-Type: application/json" \
  -d '{
    "camp_name": "Community Health Camp",
    "role": "Nurse",
    "slot": "morning",
    "camp_location": "City Hospital",
    "camp_date": "2024-01-15"
  }'
```

Expected response:
```json
{
  "status": "Queued",
  "task_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "volunteer_id": "507f1f77bcf86cd799439011",
  "volunteer_name": "John Doe",
  "camp_name": "Community Health Camp",
  "role": "Nurse",
  "slot": "morning"
}
```

### Test 4: Monitor Celery Worker Logs

In the Celery worker terminal, you should see logs like:
```
[INFO] [Task send_sms_to_volunteer[a1b2c3d4-e5f6-7890-abcd-ef1234567890]] Sending SMS to volunteer 507f1f77bcf86cd799439011 at +919876543210 (attempt 1/4)
[INFO] SMS notification sent via NotificationAPI - Volunteer ID: 507f1f77bcf86cd799439011, Phone: +919876543210, Type: volunteer_alert
[INFO] [Task send_sms_to_volunteer[a1b2c3d4-e5f6-7890-abcd-ef1234567890]] SMS sent successfully to +919876543210
```

### Test 5: Verify in NotificationAPI Dashboard

1. Go to: https://app.notificationapi.com/logs
2. You should see your sent notifications
3. Check delivery status and any errors

## API Endpoints Reference

### POST /notify/sms
Send a generic SMS notification.

**Request Body:**
```json
{
  "volunteer_id": "string",
  "phone": "string",
  "message": "string",
  "notification_type": "volunteer_alert"
}
```

**Response:**
```json
{
  "task_id": "string",
  "status": "queued",
  "volunteer_id": "string",
  "phone": "string",
  "message": "string"
}
```

### POST /notify/{volunteer_id}
Send SMS to a volunteer by looking up their phone number.

**Path Parameters:**
- `volunteer_id`: MongoDB ObjectId of the volunteer

**Query Parameters:**
- `message`: SMS message text

**Response:**
```json
{
  "status": "Queued",
  "task_id": "string",
  "volunteer_id": "string",
  "volunteer_name": "string",
  "phone": "string"
}
```

### POST /notify/assignment/{volunteer_id}
Send assignment notification to a volunteer.

**Path Parameters:**
- `volunteer_id`: MongoDB ObjectId of the volunteer

**Request Body:**
```json
{
  "camp_name": "string",
  "role": "string",
  "slot": "string",
  "camp_location": "string",
  "camp_date": "string"
}
```

**Response:**
```json
{
  "status": "Queued",
  "task_id": "string",
  "volunteer_id": "string",
  "volunteer_name": "string",
  "camp_name": "string",
  "role": "string",
  "slot": "string"
}
```

### POST /notify/batch/sms
Send multiple SMS notifications in parallel.

**Request Body:**
```json
{
  "notifications": [
    {
      "volunteer_id": "string",
      "phone_number": "string",
      "message": "string",
      "notification_type": "volunteer_alert"
    }
  ]
}
```

**Response:**
```json
{
  "status": "Queued",
  "task_id": "string",
  "count": 0
}
```

### POST /notify/webhook
Webhook endpoint for NotificationAPI delivery status updates.

**Request Body** (sent by NotificationAPI):
```json
{
  "eventType": "SMS_DELIVERED",
  "userId": "string",
  "notificationId": "string",
  "status": "string",
  "timestamp": "string"
}
```

**Response:**
```json
{
  "status": "received",
  "eventType": "string",
  "userId": "string",
  "notificationId": "string"
}
```

## Monitoring and Debugging

### Check Celery Task Status

You can use Flower (Celery monitoring tool) to monitor tasks:

```bash
# Install Flower
pip install flower

# Start Flower
celery -A app.celery_worker flower --port=5555
```

Access Flower UI at: http://localhost:5555

### Check Redis Queue

```bash
# Connect to Redis CLI
redis-cli

# Check queue length
LLEN celery

# View queued tasks
LRANGE celery 0 -1

# Clear queue (if needed)
DEL celery
```

### View Application Logs

Logs are written to stdout by default. Check the FastAPI terminal for logs like:
```
INFO:app.notify_router:SMS task queued - Task ID: xyz, Volunteer: 123, Phone: +91...
INFO:app.notificationapi_sms:SMS notification sent via NotificationAPI - Volunteer ID: 123...
```

### Common Issues and Solutions

#### Issue: "NotificationAPI credentials not configured"

**Solution**: Ensure environment variables are set:
```bash
echo $NOTIFICATIONAPI_CLIENT_ID
echo $NOTIFICATIONAPI_CLIENT_SECRET
```

If empty, add them to `.env` and restart FastAPI.

#### Issue: "Connection refused" when queuing tasks

**Solution**: Check if Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

If not running, start Redis:
```bash
redis-server
```

#### Issue: Tasks are queued but not processed

**Solution**: Check if Celery worker is running:
```bash
# In Celery worker terminal, you should see:
[INFO] Task send_sms_to_volunteer received
```

If not, restart Celery worker:
```bash
celery -A app.celery_worker worker --loglevel=info
```

#### Issue: SMS not received by recipient

**Solution**:
1. Check NotificationAPI logs: https://app.notificationapi.com/logs
2. Verify phone number format (must be E.164: +[country code][number])
3. Check NotificationAPI account has SMS credits
4. Verify notification template exists and SMS channel is enabled

## Production Deployment Considerations

### Security

1. **Environment Variables**: Never commit `.env` file to version control
2. **Redis Password**: Use password-protected Redis in production:
   ```bash
   REDIS_URL=redis://password@redis-host:6379/0
   ```
3. **Webhook Authentication**: Add signature verification in webhook handler
4. **HTTPS**: Always use HTTPS for webhook URLs in production

### Scaling

1. **Multiple Workers**: Run multiple Celery workers for higher throughput:
   ```bash
   celery -A app.celery_worker worker --concurrency=4
   ```

2. **Queue Monitoring**: Use Flower or Celery events for monitoring

3. **Redis Clustering**: For high availability, use Redis Cluster or Sentinel

### Error Handling

1. **Retry Logic**: Tasks automatically retry up to 3 times with exponential backoff
2. **Dead Letter Queue**: Failed tasks after max retries should be logged
3. **Alerting**: Set up alerts for failed tasks in production

### Performance

1. **Connection Pooling**: Redis client uses connection pooling by default
2. **Task Prefetching**: Configured via `worker_prefetch_multiplier` in celery_worker.py
3. **Rate Limiting**: Consider NotificationAPI rate limits when sending bulk SMS

## Migration from Twilio

If you're migrating from Twilio to NotificationAPI:

1. **Parallel Running**: Both systems can run in parallel
2. **Gradual Migration**: Migrate one endpoint at a time
3. **Fallback**: Keep Twilio as fallback if NotificationAPI fails
4. **Testing**: Test thoroughly before disabling Twilio

To use NotificationAPI as primary with Twilio fallback, modify the notification logic to try NotificationAPI first, then fall back to Twilio if it fails.

## Support and Resources

- **NotificationAPI Documentation**: https://docs.notificationapi.com
- **NotificationAPI Dashboard**: https://app.notificationapi.com
- **Celery Documentation**: https://docs.celeryq.dev
- **FastAPI Documentation**: https://fastapi.tiangolo.com

## License

This integration is part of the Healthcare Agent system.

