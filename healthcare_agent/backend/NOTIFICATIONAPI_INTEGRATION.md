# NotificationAPI Integration with FastAPI and Celery

## Overview

This document describes the complete integration of NotificationAPI for SMS dispatch in the Healthcare Agent system, using FastAPI, Celery, and Redis for asynchronous message queuing.

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
│  (notify_router)│
└────────┬────────┘
         │ Queues task
         ▼
┌─────────────────┐
│  Redis Broker   │
│  (Message Queue)│
└────────┬────────┘
         │ Picks up task
         ▼
┌─────────────────┐
│  Celery Worker  │
│   (sms_tasks)   │
└────────┬────────┘
         │ Sends SMS
         ▼
┌─────────────────┐
│ NotificationAPI │
│   (SMS Provider)│
└────────┬────────┘
         │ Webhook callback
         ▼
┌─────────────────┐
│   FastAPI App   │
│ (webhook handler)│
└─────────────────┘
```

## Key Components

### 1. NotificationAPI SMS Module (`app/notificationapi_sms.py`)

Core module for NotificationAPI integration:

- **Client Initialization**: Lazy-loads NotificationAPI SDK with credentials
- **SMS Sending**: `send_sms_notification()` - Main function to send SMS
- **Assignment Notifications**: Pre-formatted messages for volunteer assignments
- **Reminder Notifications**: Pre-formatted messages for camp reminders
- **Phone Number Normalization**: Converts phone numbers to E.164 format

**Key Functions:**

```python
async def send_sms_notification(
    volunteer_id: str,
    phone_number: str,
    message: str,
    notification_type: str = "volunteer_alert"
) -> Dict[str, Any]
```

### 2. Celery SMS Tasks (`app/tasks/sms_tasks.py`)

Asynchronous task definitions for Celery workers:

- **`send_sms_to_volunteer`**: Generic SMS sending task
- **`send_assignment_notification_task`**: Assignment-specific notification
- **`send_reminder_notification_task`**: Reminder-specific notification
- **`send_batch_sms_task`**: Batch SMS processing

**Features:**
- Automatic retry with exponential backoff (max 3 retries)
- Comprehensive logging with task IDs
- Error handling and failure recovery
- AsyncIO integration for async SDK calls

### 3. FastAPI Router (`app/notify_router.py`)

REST API endpoints for SMS notifications:

#### New Endpoints:

1. **`POST /notify/sms`** - Send generic SMS
   - Request: `{volunteer_id, phone, message, notification_type}`
   - Response: `{task_id, status, volunteer_id, phone, message}`

2. **`POST /notify/{volunteer_id}`** - Send SMS by volunteer ID
   - Looks up volunteer phone from database
   - Query param: `message`

3. **`POST /notify/assignment/{volunteer_id}`** - Assignment notification
   - Request: `{camp_name, role, slot, camp_location, camp_date}`
   - Auto-fetches missing data from database

4. **`POST /notify/batch/sms`** - Batch SMS sending
   - Request: `{notifications: [{volunteer_id, phone_number, message}]}`

5. **`POST /notify/webhook`** - NotificationAPI webhook handler
   - Receives delivery status callbacks
   - Handles events: SMS_DELIVERED, SMS_FAILED, SMS_BOUNCED, UNSUBSCRIBED

### 4. Celery Worker Configuration (`app/celery_worker.py`)

Updated to include SMS tasks:

```python
include=[
    "app.tasks.forecast_tasks",
    "app.tasks.planner_tasks",
    "app.tasks.notification_tasks",
    "app.tasks.scheduler_tasks",
    "app.tasks.sms_tasks"  # NEW
]
```

## Configuration

### Environment Variables

Required in `.env`:

```bash
# NotificationAPI Credentials
NOTIFICATIONAPI_CLIENT_ID=your_client_id_here
NOTIFICATIONAPI_CLIENT_SECRET=your_client_secret_here

# Redis for Celery
REDIS_URL=redis://localhost:6379/0
```

### NotificationAPI Setup

1. **Create Account**: https://app.notificationapi.com/signup
2. **Get Credentials**: https://app.notificationapi.com/settings
3. **Create Templates**:
   - `volunteer_alert` - Generic alerts
   - `volunteer_assignment` - Assignment notifications
   - `volunteer_reminder` - Reminder notifications
4. **Configure Webhook**: https://app.notificationapi.com/settings/webhooks
   - URL: `https://your-domain.com/notify/webhook`
   - Events: SMS_DELIVERED, SMS_FAILED, SMS_BOUNCED

## Usage Examples

### Example 1: Send Generic SMS

```bash
curl -X POST "http://localhost:8000/notify/sms" \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_id": "507f1f77bcf86cd799439011",
    "phone": "+919876543210",
    "message": "Hello from the system!",
    "notification_type": "volunteer_alert"
  }'
```

Response:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "volunteer_id": "507f1f77bcf86cd799439011",
  "phone": "+919876543210",
  "message": "Hello from the system!"
}
```

### Example 2: Send SMS by Volunteer ID

```bash
curl -X POST "http://localhost:8000/notify/507f1f77bcf86cd799439011?message=Test%20message" \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "status": "Queued",
  "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "volunteer_id": "507f1f77bcf86cd799439011",
  "volunteer_name": "John Doe",
  "phone": "+919876543210"
}
```

### Example 3: Send Assignment Notification

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

### Example 4: Send Batch SMS

```bash
curl -X POST "http://localhost:8000/notify/batch/sms" \
  -H "Content-Type: application/json" \
  -d '{
    "notifications": [
      {
        "volunteer_id": "507f1f77bcf86cd799439011",
        "phone_number": "+919876543210",
        "message": "Camp reminder 1"
      },
      {
        "volunteer_id": "507f1f77bcf86cd799439012",
        "phone_number": "+919876543211",
        "message": "Camp reminder 2"
      }
    ]
  }'
```

### Example 5: Python SDK Usage

```python
from app.tasks.sms_tasks import send_sms_to_volunteer

# Queue SMS task
task = send_sms_to_volunteer.delay(
    volunteer_id="507f1f77bcf86cd799439011",
    phone_number="+919876543210",
    message="Hello from Python!",
    notification_type="volunteer_alert"
)

# Get task ID
print(f"Task queued: {task.id}")

# Wait for result (optional)
result = task.get(timeout=30)
print(f"Result: {result}")
```

## Running the System

### Step 1: Start Redis

```bash
# macOS
brew services start redis

# Or run in foreground
redis-server

# Verify
redis-cli ping  # Should return: PONG
```

### Step 2: Start Celery Worker

```bash
cd healthcare_agent/backend
source ../venv/bin/activate

celery -A app.celery_worker worker --loglevel=info
```

Expected output:
```
[tasks]
  . send_assignment_notification
  . send_batch_sms
  . send_reminder_notification
  . send_sms_to_volunteer
```

### Step 3: Start FastAPI

```bash
cd healthcare_agent/backend
source ../venv/bin/activate

uvicorn app.main:app --reload --port 8000
```

### Step 4: Test Integration

```bash
# Run test suite
python test_notificationapi_integration.py
```

Or test via Swagger UI:
- Open: http://localhost:8000/docs
- Navigate to **notifications** section
- Try the `/notify/sms` endpoint

## Error Handling

### Retry Logic

All SMS tasks automatically retry on failure:

- **Max Retries**: 3
- **Backoff**: Exponential (60s, 120s, 240s)
- **Jitter**: Random delay added to prevent thundering herd
- **Auto-retry on**: ConnectionError, TimeoutError, Exception

### Error Types

1. **Configuration Error**: Missing NotificationAPI credentials
   - **Fix**: Set environment variables
   - **HTTP 400**: Configuration validation fails

2. **Network Error**: Cannot reach NotificationAPI
   - **Fix**: Check internet connection, firewall
   - **Auto-retry**: Yes (up to 3 times)

3. **Invalid Phone Number**: Phone not in E.164 format
   - **Fix**: Use format +[country code][number]
   - **Auto-retry**: No (permanent failure)

4. **Task Queuing Error**: Cannot connect to Redis
   - **Fix**: Start Redis server
   - **HTTP 500**: Task queuing fails

5. **Webhook Validation Error**: Invalid webhook payload
   - **Fix**: Check NotificationAPI webhook configuration
   - **Returns**: 200 (to avoid retries)

## Monitoring

### Celery Worker Logs

```
[INFO] [Task send_sms_to_volunteer[xyz]] Sending SMS to volunteer 123 at +91...
[INFO] SMS notification sent via NotificationAPI - Volunteer ID: 123, Phone: +91...
[INFO] [Task send_sms_to_volunteer[xyz]] SMS sent successfully
```

### FastAPI Logs

```
INFO:app.notify_router:SMS task queued - Task ID: xyz, Volunteer: 123, Phone: +91...
INFO:app.notificationapi_sms:SMS notification sent via NotificationAPI
```

### Flower (Celery Monitoring UI)

```bash
pip install flower
celery -A app.celery_worker flower --port=5555
```

Access: http://localhost:5555

### Redis Queue Inspection

```bash
redis-cli

# Check queue length
LLEN celery

# View queued tasks
LRANGE celery 0 -1

# Clear queue
DEL celery
```

## Testing

### Run Test Suite

```bash
python test_notificationapi_integration.py
```

Tests include:
1. Configuration validation
2. Direct SMS send (without Celery)
3. Assignment notification
4. Celery task queuing and execution

### Manual Testing

```bash
# Test 1: Simple SMS
curl -X POST "http://localhost:8000/notify/sms" \
  -H "Content-Type: application/json" \
  -d '{"volunteer_id":"test","phone":"+919876543210","message":"Test"}'

# Test 2: Check task status via Flower
# Visit: http://localhost:5555/task/{task_id}

# Test 3: Verify webhook
# Send test webhook from NotificationAPI dashboard
# Or use curl:
curl -X POST "http://localhost:8000/notify/webhook" \
  -H "Content-Type: application/json" \
  -d '{"eventType":"SMS_DELIVERED","userId":"test","notificationId":"xyz"}'
```

## Security Best Practices

1. **Environment Variables**: Never commit `.env` to version control
2. **Webhook Verification**: Add signature verification in production
3. **HTTPS**: Use HTTPS for all webhook URLs
4. **Redis Password**: Use authenticated Redis in production
5. **Rate Limiting**: Implement API rate limiting
6. **Input Validation**: Validate all phone numbers and message content

## Performance Considerations

### Throughput

- **Celery Workers**: Run multiple workers for parallel processing
  ```bash
  celery -A app.celery_worker worker --concurrency=4
  ```

- **Task Prefetching**: Controlled via `worker_prefetch_multiplier`
- **Connection Pooling**: Redis client uses connection pooling

### Scalability

- **Horizontal Scaling**: Run Celery workers on multiple machines
- **Redis Clustering**: Use Redis Cluster for high availability
- **Load Balancing**: Use load balancer for FastAPI instances

### Optimization

- **Batch Processing**: Use `/notify/batch/sms` for bulk sends
- **Task Routing**: Route different task types to specialized workers
- **Result Backend**: Consider disabling if not needed for performance

## Migration from Twilio

Both Twilio and NotificationAPI can run in parallel:

### Parallel Operation

```python
# Try NotificationAPI first, fallback to Twilio
try:
    result = await send_sms_notification(...)
except Exception:
    result = await send_whatsapp_message(...)
```

### Gradual Migration

1. **Week 1**: Test NotificationAPI in development
2. **Week 2**: Run parallel in production (5% traffic)
3. **Week 3**: Increase to 50% traffic
4. **Week 4**: Full migration, keep Twilio as fallback
5. **Week 5**: Disable Twilio

## Troubleshooting

### Common Issues

#### SMS not received

1. Check phone number format (must be E.164: +[country][number])
2. Verify NotificationAPI template exists
3. Check NotificationAPI logs: https://app.notificationapi.com/logs
4. Ensure SMS channel is enabled in template
5. Verify account has SMS credits

#### Tasks stuck in queue

1. Check if Celery worker is running
2. Verify Redis connection
3. Check worker logs for errors
4. Restart Celery worker

#### Configuration errors

1. Verify `.env` file exists
2. Check environment variables are loaded
3. Restart FastAPI after config changes
4. Validate credentials in NotificationAPI dashboard

## Files Created/Modified

### New Files

1. `app/notificationapi_sms.py` - NotificationAPI SMS module
2. `app/tasks/sms_tasks.py` - Celery SMS tasks
3. `NOTIFICATIONAPI_SETUP.md` - Setup guide
4. `NOTIFICATIONAPI_INTEGRATION.md` - This file
5. `test_notificationapi_integration.py` - Test suite

### Modified Files

1. `app/notify_router.py` - Added NotificationAPI endpoints
2. `app/celery_worker.py` - Added sms_tasks to includes
3. `app/config.py` - Already had NotificationAPI settings

## API Reference

### SMS Request Model

```python
class SMSRequest(BaseModel):
    volunteer_id: str
    phone: str  # E.164 format
    message: str
    notification_type: str = "volunteer_alert"
```

### SMS Response Model

```python
class SMSResponse(BaseModel):
    task_id: str
    status: str
    volunteer_id: str
    phone: str
    message: str
```

### Webhook Event Model

```python
class WebhookEventRequest(BaseModel):
    eventType: str  # SMS_DELIVERED, SMS_FAILED, etc.
    userId: str
    notificationId: Optional[str]
    status: Optional[str]
    timestamp: Optional[str]
    metadata: Optional[Dict[str, Any]]
```

## Resources

- **NotificationAPI Docs**: https://docs.notificationapi.com
- **NotificationAPI Dashboard**: https://app.notificationapi.com
- **Celery Docs**: https://docs.celeryq.dev
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Redis Docs**: https://redis.io/documentation

## Support

For issues or questions:
1. Check this documentation
2. Review NotificationAPI logs
3. Check Celery worker logs
4. Review FastAPI application logs
5. Contact NotificationAPI support: https://notificationapi.com/support

## License

Part of the Healthcare Agent system.

