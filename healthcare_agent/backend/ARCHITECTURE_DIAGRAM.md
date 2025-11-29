# NotificationAPI Integration - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Healthcare Agent System                          │
│                      Volunteer SMS Notification Flow                     │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                             CLIENT LAYER                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │   Frontend   │   │  Mobile App  │   │  Admin Panel │                │
│  │   (React)    │   │   (Mobile)   │   │    (Web)     │                │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘                │
│         │                   │                   │                         │
│         └───────────────────┼───────────────────┘                         │
│                             │                                             │
│                         HTTP POST                                         │
│                     /notify/sms, etc.                                     │
│                             │                                             │
└─────────────────────────────┼─────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI LAYER                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────┐      │
│  │                    app/notify_router.py                        │      │
│  │                                                                 │      │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐ │      │
│  │  │  POST /notify/  │  │ POST /notify/    │  │ POST /notify/ │ │      │
│  │  │       sms       │  │   {volunteer_id} │  │   assignment/ │ │      │
│  │  │                 │  │                  │  │  {volunteer}  │ │      │
│  │  │ - Validate req  │  │ - Fetch from DB  │  │ - Format msg │ │      │
│  │  │ - Queue task    │  │ - Queue task     │  │ - Queue task │ │      │
│  │  │ - Return 200    │  │ - Return 200     │  │ - Return 200 │ │      │
│  │  └────────┬────────┘  └────────┬─────────┘  └──────┬───────┘ │      │
│  │           │                     │                    │         │      │
│  │           └─────────────────────┼────────────────────┘         │      │
│  │                                 │                              │      │
│  │                         task.delay()                           │      │
│  │                                 │                              │      │
│  │  ┌──────────────────────────────▼───────────────────────────┐ │      │
│  │  │              app/tasks/sms_tasks.py                       │ │      │
│  │  │                                                            │ │      │
│  │  │  send_sms_to_volunteer.delay(volunteer_id, phone, msg)   │ │      │
│  │  └────────────────────────────┬───────────────────────────┬─┘ │      │
│  └───────────────────────────────┼───────────────────────────┼───┘      │
│                                  │                           │           │
│                                  │                           │           │
│  ┌───────────────────────────────┼───────────────────────────┼───┐      │
│  │        MongoDB                │     Response to Client    │   │      │
│  │                               │                           │   │      │
│  │  ┌──────────────┐             │     {                     │   │      │
│  │  │  volunteers  │◄────────────┘       "task_id": "xyz",  │   │      │
│  │  │  camps       │                     "status": "queued"  │   │      │
│  │  │  assignments │                   }                     │   │      │
│  │  └──────────────┘                                         │   │      │
│  └───────────────────────────────────────────────────────────┼───┘      │
│                                                               │           │
└───────────────────────────────────────────────────────────────┼───────────┘
                                                                │
                                                                ▼
                                                        ┌──────────────┐
                                                        │    Client    │
                                                        │  Receives:   │
                                                        │  task_id     │
                                                        │  status      │
                                                        └──────────────┘
                                                                │
        Task queued to Redis ──────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         REDIS BROKER LAYER                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      Redis Queue: "celery"                       │    │
│  │                                                                   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │    │
│  │  │ Task 1   │  │ Task 2   │  │ Task 3   │  │ Task N   │ ...   │    │
│  │  │ (queued) │  │ (queued) │  │ (queued) │  │ (queued) │       │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │    │
│  │                                                                   │    │
│  │  Task Format:                                                    │    │
│  │  {                                                                │    │
│  │    "task": "send_sms_to_volunteer",                              │    │
│  │    "args": ["volunteer_id", "phone", "message"],                 │    │
│  │    "kwargs": {"notification_type": "volunteer_alert"},           │    │
│  │    "id": "task-uuid"                                             │    │
│  │  }                                                                │    │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                       │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │
                         Worker picks up task
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       CELERY WORKER LAYER                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              Celery Worker Process (Background)                  │    │
│  │                                                                   │    │
│  │  1. Pick task from Redis queue                                   │    │
│  │  2. Deserialize task parameters                                  │    │
│  │  3. Execute: send_sms_to_volunteer()                             │    │
│  │     ├─ Log: "Sending SMS to volunteer X"                         │    │
│  │     ├─ Call: run_async(send_sms_notification(...))              │    │
│  │     ├─ Log: "SMS sent successfully"                              │    │
│  │     └─ Return result                                             │    │
│  │  4. Acknowledge task completion to Redis                         │    │
│  │                                                                   │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │         app/tasks/sms_tasks.py                          │     │    │
│  │  │                                                          │     │    │
│  │  │  @celery_app.task(bind=True, max_retries=3)            │     │    │
│  │  │  def send_sms_to_volunteer(self, ...):                 │     │    │
│  │  │      try:                                               │     │    │
│  │  │          result = run_async(                           │     │    │
│  │  │              send_sms_notification(...)                │     │    │
│  │  │          )                                              │     │    │
│  │  │          return result                                 │     │    │
│  │  │      except Exception as exc:                          │     │    │
│  │  │          if retries < max_retries:                     │     │    │
│  │  │              self.retry(exc=exc, countdown=60)         │     │    │
│  │  │          else:                                          │     │    │
│  │  │              return {"success": False, "error": ...}   │     │    │
│  │  └────────────────────────────────────────────────────────┘     │    │
│  │                               │                                  │    │
│  │                               │ Call async function              │    │
│  │                               ▼                                  │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │      app/notificationapi_sms.py                         │     │    │
│  │  │                                                          │     │    │
│  │  │  async def send_sms_notification(...):                 │     │    │
│  │  │      # Initialize NotificationAPI client               │     │    │
│  │  │      client = get_notificationapi_client()             │     │    │
│  │  │                                                          │     │    │
│  │  │      # Normalize phone number to E.164                 │     │    │
│  │  │      phone = normalize_phone_number(phone_number)      │     │    │
│  │  │                                                          │     │    │
│  │  │      # Send via NotificationAPI SDK                    │     │    │
│  │  │      await client.send({                               │     │    │
│  │  │          "notificationId": notification_type,          │     │    │
│  │  │          "user": {                                     │     │    │
│  │  │              "id": volunteer_id,                       │     │    │
│  │  │              "number": phone                           │     │    │
│  │  │          },                                             │     │    │
│  │  │          "mergeTags": {"message": message}            │     │    │
│  │  │      })                                                 │     │    │
│  │  │                                                          │     │    │
│  │  │      return {"success": True, ...}                     │     │    │
│  │  └──────────────────────┬───────────────────────────────┘     │    │
│  └─────────────────────────┼───────────────────────────────────────┘    │
│                            │                                             │
└────────────────────────────┼─────────────────────────────────────────────┘
                             │
                    HTTP POST to NotificationAPI
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     NOTIFICATIONAPI LAYER                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │               NotificationAPI Service                            │    │
│  │               https://api.notificationapi.com                    │    │
│  │                                                                   │    │
│  │  1. Receive notification request                                 │    │
│  │  2. Validate credentials (client_id, client_secret)              │    │
│  │  3. Load notification template: "volunteer_alert"                │    │
│  │  4. Merge tags: {{message}} → actual message text                │    │
│  │  5. Select SMS channel                                           │    │
│  │  6. Format SMS according to template                             │    │
│  │  7. Send to SMS carrier (Twilio, AWS SNS, etc.)                  │    │
│  │  8. Return success response                                      │    │
│  │  9. Trigger webhook callback (async)                             │    │
│  │                                                                   │    │
│  └───────────────────────────┬───────────────────┬──────────────────┘   │
│                              │                   │                       │
│                              │                   │                       │
└──────────────────────────────┼───────────────────┼───────────────────────┘
                               │                   │
                  Sends SMS to carrier     Webhook callback (async)
                               │                   │
                               ▼                   │
                    ┌─────────────────┐            │
                    │   SMS Carrier   │            │
                    │  (Twilio, AWS)  │            │
                    └────────┬────────┘            │
                             │                     │
                    Delivers to phone              │
                             │                     │
                             ▼                     │
                    ┌─────────────────┐            │
                    │   📱 Phone      │            │
                    │   Receives SMS  │            │
                    └─────────────────┘            │
                                                   │
                                                   │
                       Webhook: Delivery status   │
                                                   │
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     WEBHOOK HANDLER LAYER                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │             POST /notify/webhook (FastAPI)                       │    │
│  │                                                                   │    │
│  │  Receives from NotificationAPI:                                  │    │
│  │  {                                                                │    │
│  │    "eventType": "SMS_DELIVERED",                                 │    │
│  │    "userId": "volunteer_id",                                     │    │
│  │    "notificationId": "notification_id",                          │    │
│  │    "status": "delivered",                                        │    │
│  │    "timestamp": "2024-01-01T12:00:00Z"                           │    │
│  │  }                                                                │    │
│  │                                                                   │    │
│  │  Processing:                                                      │    │
│  │  1. Parse webhook payload                                        │    │
│  │  2. Validate event type                                          │    │
│  │  3. Log event (SMS_DELIVERED, SMS_FAILED, etc.)                  │    │
│  │  4. Update database (optional):                                  │    │
│  │     - Mark notification as delivered/failed                      │    │
│  │     - Update volunteer record                                    │    │
│  │     - Log to activity timeline                                   │    │
│  │  5. Trigger alerts if failed                                     │    │
│  │  6. Return 200 OK to acknowledge                                 │    │
│  │                                                                   │    │
│  │  Event Types Handled:                                            │    │
│  │  - SMS_DELIVERED: Success ✅                                     │    │
│  │  - SMS_FAILED: Retry or alert ⚠️                                │    │
│  │  - SMS_BOUNCED: Invalid number ❌                                │    │
│  │  - UNSUBSCRIBED: User opted out 🚫                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────┐
│                         ERROR HANDLING FLOW                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Task Execution Error (Network, API, etc.)                               │
│         │                                                                 │
│         ▼                                                                 │
│  ┌──────────────┐                                                        │
│  │ Retry Logic  │                                                        │
│  └──────┬───────┘                                                        │
│         │                                                                 │
│         ├─ Attempt 1: Immediate (0s)                                     │
│         │   └─ Fails → Wait 60s                                          │
│         │                                                                 │
│         ├─ Attempt 2: After 60s                                          │
│         │   └─ Fails → Wait 120s (exponential backoff)                   │
│         │                                                                 │
│         ├─ Attempt 3: After 120s                                         │
│         │   └─ Fails → Wait 240s                                         │
│         │                                                                 │
│         ├─ Attempt 4 (Final): After 240s                                 │
│         │   └─ Fails → Mark as permanent failure                         │
│         │                                                                 │
│         ▼                                                                 │
│  ┌────────────────────────────────┐                                      │
│  │  Permanent Failure             │                                      │
│  │  - Log error                   │                                      │
│  │  - Update database             │                                      │
│  │  - Send alert to admin         │                                      │
│  │  - Return error result         │                                      │
│  └────────────────────────────────┘                                      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────┐
│                        MONITORING & LOGGING                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────────┐ │
│  │  Celery Logs      │  │  FastAPI Logs     │  │ NotificationAPI     │ │
│  │                   │  │                   │  │ Dashboard           │ │
│  │  - Task received  │  │  - Request logs   │  │                     │ │
│  │  - Task executing │  │  - Response logs  │  │  - SMS logs         │ │
│  │  - Task success   │  │  - Error logs     │  │  - Delivery status  │ │
│  │  - Task retry     │  │  - Performance    │  │  - Error tracking   │ │
│  │  - Task failed    │  │                   │  │  - Analytics        │ │
│  └───────────────────┘  └───────────────────┘  └─────────────────────┘ │
│                                                                           │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────────┐ │
│  │  Redis Monitor    │  │  Flower UI        │  │ Application Metrics │ │
│  │                   │  │                   │  │                     │ │
│  │  - Queue depth    │  │  - Active workers │  │  - Success rate     │ │
│  │  - Task count     │  │  - Task status    │  │  - Latency          │ │
│  │  - Memory usage   │  │  - Task history   │  │  - Error rate       │ │
│  └───────────────────┘  └───────────────────┘  └─────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. FastAPI Layer
- **Purpose**: REST API for SMS requests
- **Components**: notify_router.py
- **Endpoints**: /notify/sms, /notify/{id}, /notify/assignment/{id}, /notify/batch/sms, /notify/webhook
- **Responsibilities**: Request validation, task queuing, immediate response

### 2. Redis Broker
- **Purpose**: Message queue for Celery tasks
- **Type**: In-memory data store
- **Queue Name**: "celery"
- **Responsibilities**: Store tasks, deliver to workers, persist results

### 3. Celery Worker
- **Purpose**: Background task processing
- **Components**: sms_tasks.py, notificationapi_sms.py
- **Responsibilities**: Execute tasks, retry on failure, log results

### 4. NotificationAPI
- **Purpose**: SMS delivery service
- **Type**: External API
- **Responsibilities**: Send SMS to carriers, track delivery, trigger webhooks

### 5. Webhook Handler
- **Purpose**: Receive delivery status updates
- **Endpoint**: POST /notify/webhook
- **Responsibilities**: Log events, update database, trigger alerts

## Data Flow Summary

1. **Client → FastAPI**: HTTP POST with SMS request
2. **FastAPI → Redis**: Queue task with parameters
3. **Redis → Celery**: Deliver task to worker
4. **Celery → NotificationAPI**: Send SMS via SDK
5. **NotificationAPI → Carrier**: Deliver SMS to phone network
6. **Carrier → Phone**: SMS delivered to recipient
7. **NotificationAPI → FastAPI**: Webhook with delivery status
8. **FastAPI → Database**: Update delivery status (optional)

## Timing

- **FastAPI Response**: < 50ms (immediate)
- **Task Queue**: < 10ms
- **Celery Pickup**: < 1s
- **NotificationAPI Call**: < 1s
- **SMS Delivery**: 1-5s
- **Webhook Callback**: < 30s
- **Total (end-to-end)**: 3-37s

## Scaling

### Horizontal Scaling

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Worker  │     │ Worker  │     │ Worker  │
│    1    │     │    2    │     │    N    │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
              ┌──────▼──────┐
              │    Redis    │
              │   Cluster   │
              └─────────────┘
```

### Load Distribution

- **Worker 1**: Assignment notifications
- **Worker 2**: Reminder notifications
- **Worker 3**: Generic SMS
- **Worker N**: Batch processing

---

**Legend**:
- → : Synchronous flow
- ⇢ : Asynchronous flow
- ◄─ : Database query
- ⚡ : Fast operation (< 100ms)
- ⏱ : Normal operation (< 1s)
- 🐌 : Slow operation (> 1s)

