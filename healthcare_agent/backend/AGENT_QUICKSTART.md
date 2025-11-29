# AI Agent Quick Start Guide

## 🚀 Quick Start

### 1. Validate CSV Data

```bash
cd healthcare_agent/backend
source ../venv/bin/activate
python run_agent.py validate
```

**Expected Output:**
```
✅ Volunteers: 50
✅ Camps: 5
✅ Requirements: 15
✅ Role Demand History: 200
✅ Validation PASSED
```

### 2. Run Full Workflow for a Camp

```bash
# Get a camp ID first
python -c "from app.database import connect_to_mongo, get_collection; import asyncio; async def f(): await connect_to_mongo(); c = get_collection('camps'); doc = await c.find_one({}); print(doc['_id'] if doc else 'No camps'); import sys; sys.exit(); asyncio.run(f())"

# Run workflow (replace CAMP_ID)
python run_agent.py workflow <CAMP_ID>
```

### 3. Test Everything

```bash
python test_agent.py
```

## 📋 Workflow Steps

### Step-by-Step Manual Execution

```bash
# 1. Validate data
python run_agent.py validate

# 2. Run forecast
python run_agent.py forecast <CAMP_ID>

# 3. Run planning
python run_agent.py plan <CAMP_ID>

# 4. View logs
python run_agent.py logs <CAMP_ID>
```

## 🔄 GraphQL Usage

### Run Full Workflow via GraphQL

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { runAgentWorkflow(campId: \"<CAMP_ID>\", notifyVolunteers: true) }"
  }'
```

### Run Forecast

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { runForecast(campId: \"<CAMP_ID>\") { role slot mean upper90 lower10 } }"
  }'
```

### Run Planning

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { runPlan(campId: \"<CAMP_ID>\") { id role slot status volunteer { name } } }"
  }'
```

## 🧪 Testing

### Run Test Suite

```bash
python test_agent.py
```

**Expected Output:**
```
✅ TEST PASSED: CSV data is properly seeded
✅ TEST PASSED: Forecast functionality works
✅ TEST PASSED: Planning functionality works
✅ TEST PASSED: Activity logging works
✅ TEST PASSED: Full workflow integration works

🎉 All tests passed!
```

## 📊 Monitor Activity

### View Activity Logs

```bash
python run_agent.py logs <CAMP_ID>
```

### Check MongoDB Directly

```python
from app.database import connect_to_mongo, get_collection
import asyncio

async def check():
    await connect_to_mongo()
    logs = get_collection("activity_logs")
    count = await logs.count_documents({"camp_id": ObjectId("<CAMP_ID>")})
    print(f"Activity logs: {count}")

asyncio.run(check())
```

## 🔄 Celery Tasks

### Start Celery Worker

```bash
celery -A app.celery_worker worker --loglevel=info
```

### Check Scheduled Tasks

```python
from app.celery_worker import celery_app
print(celery_app.conf.beat_schedule)
```

## 📱 Twilio Webhook Testing

### Test Webhook Locally

```bash
curl -X POST http://localhost:8000/twilio/webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227&Body=confirm"
```

**Note:** Localhost requests bypass signature validation for testing.

## ✅ Verification Checklist

- [ ] CSV data seeded: `python run_agent.py validate`
- [ ] Forecast works: `python run_agent.py forecast <CAMP_ID>`
- [ ] Planning works: `python run_agent.py plan <CAMP_ID>`
- [ ] Full workflow: `python run_agent.py workflow <CAMP_ID>`
- [ ] Activity logs: `python run_agent.py logs <CAMP_ID>`
- [ ] Test suite: `python test_agent.py`

## 🐛 Troubleshooting

### No Volunteers Found
```bash
# Seed volunteers
python seed_from_csv.py
```

### No Camps Found
```bash
# Create a camp via API or seed from CSV
python seed_from_csv.py
```

### Forecast Returns Empty
- Check `role_demand_history` collection has data
- Verify camp has requirements

### Planning Fails
- Check volunteers have matching skills
- Verify volunteers have availability
- Check OR-Tools is installed

### Notifications Not Sending
- Verify Twilio credentials in `.env`
- Check Twilio phone number format
- Test with `python run_agent.py workflow <CAMP_ID>`

## 📚 Full Documentation

See `AGENT_DOCUMENTATION.md` for complete details.

