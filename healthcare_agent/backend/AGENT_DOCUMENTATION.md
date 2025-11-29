# AI Agent Workflow Documentation

## 📋 Overview

The AI Agent orchestrates the complete medical camp volunteer coordination workflow:
1. **CSV Data Validation** - Verifies data mappings
2. **Forecasting** - Poisson-based demand prediction
3. **Planning** - OR-Tools ILP optimal assignment
4. **Notification** - Twilio WhatsApp messaging
5. **Response Handling** - Webhook processing
6. **Replanning** - Automatic gap filling
7. **Activity Logging** - Complete audit trail

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Orchestrator                     │
│                    (app/agent.py)                            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Forecast    │   │   Planning   │   │ Notification │
│  (Poisson)   │   │  (OR-Tools)  │   │  (Twilio)    │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   MongoDB    │
                    │  + Activity  │
                    │    Logging   │
                    └──────────────┘
```

## 📊 Data Flow

### 1. CSV Data Validation

**Mappings:**
- `volunteers.csv` → `volunteers` collection
- `camps.csv` → `camps` collection
- `camp_requirements.csv` → embedded in `camp.requirements`
- `role_demand_history.csv` → `role_demand_history` collection
- `assignments_history.csv` → `assignments` collection (optional)

**Validation:**
```python
from app.agent import MedicalCampAgent

agent = MedicalCampAgent()
result = await agent.validate_csv_mappings()

# Check result.is_valid
# Access counts: result.volunteers_count, result.camps_count, etc.
```

### 2. Forecasting (Poisson Distribution)

**Algorithm:**
1. Query `role_demand_history` by role and slot
2. Compute lambda (mean) from historical counts
3. Calculate Poisson percentiles:
   - `mean` = lambda
   - `upper90` = 90th percentile
   - `lower10` = 10th percentile

**Usage:**
```python
forecast_results = await agent.forecast_demand(camp_id)
# Returns List[ForecastResult] with role, slot, mean, upper90, lower10
```

### 3. Planning (OR-Tools ILP)

**Algorithm:**
1. Fetch camp requirements
2. Fetch all volunteers
3. Build eligibility matrix (skill + availability match)
4. Solve ILP:
   - Variables: x[v, r] ∈ {0,1}
   - Constraints:
     * Σ_v x[v, r] ≥ requirement.count (for each requirement)
     * Σ_r x[v, r] ≤ 1 (each volunteer assigned to at most one requirement)
   - Objective: Maximize total assignments
5. Fallback to greedy if ILP fails
6. Preserve confirmed assignments

**Usage:**
```python
assignments, unfilled = await agent.plan_assignments(camp_id, use_celery=False)
# Returns (List[Assignment], int unfilled_slots)
```

### 4. Notification (Twilio WhatsApp)

**Template:**
```
Hi {name}, you've been assigned to {role} on {date}, {slot}. 
Reply YES to confirm or NO to cancel.
```

**Usage:**
```python
assignment_ids = [str(a.id) for a in assignments]
sent_count = await agent.notify_volunteers(assignment_ids, use_celery=True)
```

### 5. Response Handling (Webhook)

**Message Parsing:**
- "yes", "confirm", "confirmed" → status = "confirmed"
- "no", "cancel", "cancelled" → status = "cancelled" + trigger replan

**Usage:**
```python
result = await agent.handle_volunteer_response(phone_number, message_body)
# Returns dict with action taken
```

### 6. Replanning

**Strategy:**
1. Preserve confirmed assignments (never change)
2. Delete active (assigned/backup) assignments
3. Exclude cancelled volunteers
4. Fill remaining gaps using planner

**Usage:**
```python
new_assignments, unfilled = await agent.replan_camp(camp_id, use_celery=False)
```

### 7. Activity Logging

**All operations log to `activity_logs` collection:**
- Forecast runs
- Planning runs
- Notifications sent
- Status changes
- Replanning triggers

**Usage:**
```python
logs = await agent.get_activity_logs(camp_id)
# Returns List[Dict] with timestamp, event, meta
```

## 🚀 Complete Workflow

### Python API

```python
from app.agent import MedicalCampAgent

agent = MedicalCampAgent()

# Run full workflow
result = await agent.run_full_workflow(
    camp_id="...",
    notify_volunteers=True,
    use_celery=True  # Use Celery for async operations
)

# Check result.success
# Access: result.forecast_results, result.assignments_created, etc.
```

### GraphQL Mutation

```graphql
mutation {
  runAgentWorkflow(campId: "123", notifyVolunteers: true)
}
```

### CLI Command

```bash
# Validate CSV mappings
python run_agent.py validate

# Run forecast
python run_agent.py forecast <camp_id>

# Run planning
python run_agent.py plan <camp_id>

# Run full workflow
python run_agent.py workflow <camp_id>

# Replan camp
python run_agent.py replan <camp_id>

# View activity logs
python run_agent.py logs <camp_id>
```

## 🧪 Testing

```bash
# Run test suite
python test_agent.py

# Tests:
# 1. CSV Validation
# 2. Forecast Functionality
# 3. Planning Functionality
# 4. Activity Logging
# 5. Full Workflow Integration
```

## 📦 Celery Tasks

### Scheduled Tasks

1. **Daily Forecast** (`run_daily_forecast_all_camps`)
   - Runs every day at midnight
   - Forecasts all active camps

2. **Auto Plan New Camps** (`auto_plan_new_camps`)
   - Runs every 15 minutes
   - Plans assignments for camps without assignments

3. **Replan If Needed** (`replan_if_needed`)
   - Runs every 30 minutes
   - Replans camps with cancelled assignments

4. **Reminder Batch** (`send_upcoming_reminder_batch`)
   - Runs every hour
   - Sends reminders at T-24h, T-6h, T-1h

### Triggered Tasks

1. **Camp Created** → `schedule_camp_forecast_and_plan`
2. **Assignment Cancelled** → `trigger_replan_on_cancellation`
3. **Batch Notifications** → `send_batch_notifications`

## 🔄 Integration Points

### GraphQL Mutations

- `runForecast(campId)` - Run forecast
- `runPlan(campId)` - Run planning
- `replanCamp(campId)` - Replan camp
- `runAgentWorkflow(campId, notifyVolunteers)` - Full workflow
- `markAssignmentStatus(assignmentId, status)` - Update status
- `sendWhatsApp(to, message)` - Send notification

### REST Endpoints

- `POST /api/camps/` - Create camp (triggers agent workflow)
- `POST /twilio/webhook` - Handle volunteer responses
- `POST /notify/whatsapp` - Send notification

### Webhook Flow

```
Volunteer SMS → Twilio → /twilio/webhook → 
  agent.handle_volunteer_response() →
    Update Assignment Status →
      Trigger Replan (if cancelled) →
        Log Activity
```

## 📝 Activity Log Examples

```json
{
  "camp_id": "123",
  "timestamp": "2024-11-29T07:00:00Z",
  "event": "Forecast run for camp Rural Health Camp",
  "meta": {
    "requirements_count": 5,
    "forecast_results_count": 5
  }
}

{
  "camp_id": "123",
  "timestamp": "2024-11-29T07:01:00Z",
  "event": "Plan run for camp Rural Health Camp",
  "meta": {
    "assignments_created": 12,
    "unfilled_slots": 2
  }
}

{
  "camp_id": "123",
  "timestamp": "2024-11-29T07:02:00Z",
  "event": "Assignment confirmed by Dr. John Smith",
  "meta": {
    "assignment_id": "456",
    "volunteer_id": "789"
  }
}
```

## ✅ Proof of Implementation

### Files Created

1. **`app/agent.py`** (600+ lines)
   - `MedicalCampAgent` class
   - Complete workflow orchestration
   - All integration points

2. **`run_agent.py`** (200+ lines)
   - CLI interface
   - All agent operations

3. **`test_agent.py`** (200+ lines)
   - Comprehensive test suite
   - Validation of all components

### Integration Points

✅ CSV Validation - `validate_csv_mappings()`
✅ Forecasting - `forecast_demand()` → `forecast.py`
✅ Planning - `plan_assignments()` → `planner.py`
✅ Notification - `notify_volunteers()` → `notifications.py`
✅ Response Handling - `handle_volunteer_response()` → `twilio_webhook.py`
✅ Replanning - `replan_camp()` → `replan.py`
✅ Activity Logging - `get_activity_logs()` → `activity.py`
✅ Celery Integration - All tasks in `app/tasks/`
✅ GraphQL Integration - `runAgentWorkflow` mutation

## 🎯 Usage Examples

### Example 1: Validate Data

```python
from app.agent import MedicalCampAgent

agent = MedicalCampAgent()
result = await agent.validate_csv_mappings()

if result.is_valid:
    print(f"✅ {result.volunteers_count} volunteers")
    print(f"✅ {result.camps_count} camps")
else:
    print("❌ Validation failed")
```

### Example 2: Run Full Workflow

```python
from app.agent import run_agent_workflow

result = await run_agent_workflow(
    camp_id="507f1f77bcf86cd799439011",
    notify_volunteers=True,
    use_celery=True
)

print(f"Success: {result['success']}")
print(f"Assignments: {result['assignments_created']}")
print(f"Unfilled: {result['unfilled_slots']}")
```

### Example 3: Handle Webhook Response

```python
from app.agent import MedicalCampAgent

agent = MedicalCampAgent()
result = await agent.handle_volunteer_response(
    phone_number="+919392664227",
    message_body="confirm"
)

if result["success"]:
    print(f"Action: {result['action']}")
    if result.get("replan_triggered"):
        print("Replanning triggered")
```

## 🔍 Monitoring

### Check Activity Logs

```python
logs = await agent.get_activity_logs(camp_id)
for log in logs:
    print(f"{log['timestamp']}: {log['event']}")
```

### Check Workflow Status

```python
result = await agent.run_full_workflow(camp_id)
if not result.success:
    for error in result.errors:
        print(f"Error: {error}")
```

## 🚨 Error Handling

All operations include:
- Try-catch blocks
- Detailed error logging
- Graceful degradation
- Activity logging for failures

## 📚 Related Documentation

- `forecast.py` - Poisson forecasting implementation
- `planner.py` - OR-Tools ILP planning
- `replan.py` - Replanning logic
- `notifications.py` - Twilio integration
- `activity.py` - Activity logging
- `tasks/` - Celery task definitions

