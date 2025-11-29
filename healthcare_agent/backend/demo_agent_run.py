"""Demo script to demonstrate the complete agentic automation loop."""
import asyncio
import sys
from datetime import datetime, timedelta
from bson import ObjectId

# Add parent directory to path
sys.path.insert(0, '.')

from app.database import connect_to_mongo, close_mongo_connection, get_collection
from app.models import Volunteer, Camp, Assignment
from app.auth import hash_password
from app.tasks.forecast_tasks import run_daily_forecast
from app.tasks.planner_tasks import auto_plan_camp, auto_replan_camp
from app.tasks.notification_tasks import send_batch_notifications
from app.tasks.scheduler_tasks import schedule_camp_forecast_and_plan, trigger_replan_on_cancellation


async def create_dummy_data():
    """Create dummy volunteers and a camp for demonstration."""
    print("=" * 60)
    print("STEP 1: Creating dummy volunteers and camp")
    print("=" * 60)
    
    await connect_to_mongo()
    
    volunteers_collection = get_collection("volunteers")
    camps_collection = get_collection("camps")
    
    # Create volunteers
    volunteers_data = [
        {
            "name": "Dr. Sarah Johnson",
            "phone": "+1234567890",
            "skills": ["doctor", "nurse"],
            "availability": [
                {"date": "2024-06-01", "slots": ["morning", "afternoon"]}
            ],
            "no_show_rate": 0.1
        },
        {
            "name": "Dr. Michael Chen",
            "phone": "+1234567891",
            "skills": ["doctor"],
            "availability": [
                {"date": "2024-06-01", "slots": ["morning"]}
            ],
            "no_show_rate": 0.15
        },
        {
            "name": "Nurse Emily Davis",
            "phone": "+1234567892",
            "skills": ["nurse"],
            "availability": [
                {"date": "2024-06-01", "slots": ["morning", "afternoon"]}
            ],
            "no_show_rate": 0.2
        },
        {
            "name": "Nurse James Wilson",
            "phone": "+1234567893",
            "skills": ["nurse"],
            "availability": [
                {"date": "2024-06-01", "slots": ["afternoon"]}
            ],
            "no_show_rate": 0.18
        }
    ]
    
    volunteer_ids = []
    for vol_data in volunteers_data:
        result = await volunteers_collection.insert_one(vol_data)
        volunteer_ids.append(str(result.inserted_id))
        print(f"  ✓ Created volunteer: {vol_data['name']} (ID: {result.inserted_id})")
    
    # Create camp
    camp_start = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
    camp_end = (datetime.utcnow() + timedelta(days=7, hours=8)).isoformat() + "Z"
    
    camp_data = {
        "name": "Demo Health Camp 2024",
        "location": "Community Center",
        "start": camp_start,
        "end": camp_end,
        "requirements": [
            {"role": "doctor", "count": 2, "slot": "morning"},
            {"role": "nurse", "count": 3, "slot": "morning"},
            {"role": "nurse", "count": 2, "slot": "afternoon"}
        ]
    }
    
    camp_result = await camps_collection.insert_one(camp_data)
    camp_id = str(camp_result.inserted_id)
    print(f"  ✓ Created camp: {camp_data['name']} (ID: {camp_id})")
    
    await close_mongo_connection()
    
    return camp_id, volunteer_ids


def run_forecast_demo(camp_id: str):
    """Run forecast via Celery task."""
    print("\n" + "=" * 60)
    print("STEP 2: Running forecast via Celery task")
    print("=" * 60)
    
    result = run_daily_forecast.delay(camp_id)
    print(f"  ✓ Forecast task queued (task_id: {result.id})")
    print(f"  → Waiting for result...")
    
    # Wait for result (with timeout)
    try:
        forecast_result = result.get(timeout=60)
        if forecast_result.get("success"):
            print(f"  ✓ Forecast completed successfully!")
            print(f"    - Camp: {forecast_result.get('camp_name')}")
            print(f"    - Results: {forecast_result.get('results_count')} forecast entries")
        else:
            print(f"  ✗ Forecast failed: {forecast_result.get('error')}")
    except Exception as e:
        print(f"  ✗ Forecast task error: {e}")
    
    return result


def run_plan_demo(camp_id: str):
    """Run planning via Celery task."""
    print("\n" + "=" * 60)
    print("STEP 3: Running planning via Celery task")
    print("=" * 60)
    
    result = auto_plan_camp.delay(camp_id)
    print(f"  ✓ Planning task queued (task_id: {result.id})")
    print(f"  → Waiting for result...")
    
    try:
        plan_result = result.get(timeout=120)
        if plan_result.get("success"):
            print(f"  ✓ Planning completed successfully!")
            print(f"    - Camp: {plan_result.get('camp_name')}")
            print(f"    - Assignments created: {plan_result.get('assignments_created')}")
            print(f"    - Unfilled slots: {plan_result.get('unfilled_slots')}")
        else:
            print(f"  ✗ Planning failed: {plan_result.get('error')}")
    except Exception as e:
        print(f"  ✗ Planning task error: {e}")
    
    return result


async def simulate_cancellation_and_replan(camp_id: str):
    """Simulate a cancellation and trigger replanning."""
    print("\n" + "=" * 60)
    print("STEP 4: Simulating cancellation and triggering replan")
    print("=" * 60)
    
    await connect_to_mongo()
    
    assignments_collection = get_collection("assignments")
    
    # Find an assignment to cancel
    assignment_doc = await assignments_collection.find_one({
        "camp_id": ObjectId(camp_id),
        "status": "assigned"
    })
    
    if not assignment_doc:
        print("  ⚠ No assigned assignments found to cancel")
        await close_mongo_connection()
        return
    
    assignment = Assignment(**assignment_doc)
    assignment_id = str(assignment.id)
    
    # Cancel the assignment
    await assignments_collection.update_one(
        {"_id": assignment.id},
        {"$set": {"status": "cancelled"}}
    )
    
    print(f"  ✓ Cancelled assignment {assignment_id}")
    print(f"    - Role: {assignment.role}, Slot: {assignment.slot}")
    
    await close_mongo_connection()
    
    # Trigger replan via Celery
    print(f"  → Triggering replan via Celery...")
    replan_result = trigger_replan_on_cancellation.delay(camp_id)
    print(f"  ✓ Replan task queued (task_id: {replan_result.id})")
    
    try:
        replan_task_result = replan_result.get(timeout=120)
        if replan_task_result.get("success"):
            print(f"  ✓ Replan triggered successfully!")
        else:
            print(f"  ✗ Replan trigger failed: {replan_task_result.get('error')}")
    except Exception as e:
        print(f"  ✗ Replan task error: {e}")


def demonstrate_scheduled_automation(camp_id: str):
    """Demonstrate scheduled automation."""
    print("\n" + "=" * 60)
    print("STEP 5: Demonstrating scheduled automation")
    print("=" * 60)
    
    # Schedule forecast and planning for a camp
    schedule_result = schedule_camp_forecast_and_plan.delay(camp_id)
    print(f"  ✓ Scheduled forecast and planning (task_id: {schedule_result.id})")
    
    try:
        schedule_info = schedule_result.get(timeout=30)
        print(f"  ✓ Schedule completed:")
        print(f"    - Forecast task: {schedule_info.get('forecast_task_id')}")
        print(f"    - Plan task: {schedule_info.get('plan_task_id')}")
    except Exception as e:
        print(f"  ✗ Schedule task error: {e}")


async def show_final_state(camp_id: str):
    """Show final state of assignments."""
    print("\n" + "=" * 60)
    print("STEP 6: Final state check")
    print("=" * 60)
    
    await connect_to_mongo()
    
    assignments_collection = get_collection("assignments")
    volunteers_collection = get_collection("volunteers")
    camps_collection = get_collection("camps")
    
    camp_doc = await camps_collection.find_one({"_id": ObjectId(camp_id)})
    if camp_doc:
        camp = Camp(**camp_doc)
        print(f"  Camp: {camp.name}")
    
    cursor = assignments_collection.find({"camp_id": ObjectId(camp_id)})
    assignments = []
    async for doc in cursor:
        assignments.append(Assignment(**doc))
    
    print(f"  Total assignments: {len(assignments)}")
    
    status_counts = {}
    for assign in assignments:
        status = assign.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"  Status breakdown:")
    for status, count in status_counts.items():
        print(f"    - {status}: {count}")
    
    # Show sample assignments
    print(f"\n  Sample assignments:")
    for assign in assignments[:5]:
        volunteer_doc = await volunteers_collection.find_one({"_id": assign.volunteer_id})
        if volunteer_doc:
            volunteer = Volunteer(**volunteer_doc)
            print(f"    - {volunteer.name} → {assign.role} ({assign.slot}) [{assign.status}]")
    
    await close_mongo_connection()


async def main():
    """Main demo function."""
    print("\n" + "=" * 60)
    print("AGENTIC VOLUNTEER COORDINATOR - AUTOMATION DEMO")
    print("=" * 60)
    print("\nThis demo shows the complete automation loop:")
    print("  1. Create volunteers & camp")
    print("  2. Run forecast (Celery task)")
    print("  3. Run planning (Celery task)")
    print("  4. Simulate cancellation → auto-replan")
    print("  5. Demonstrate scheduled automation")
    print("  6. Show final state")
    print("\nNote: Make sure Redis and Celery workers are running!")
    print("=" * 60)
    
    try:
        # Step 1: Create dummy data
        camp_id, volunteer_ids = await create_dummy_data()
        
        # Step 2: Run forecast
        forecast_task = run_forecast_demo(camp_id)
        
        # Step 3: Run planning
        plan_task = run_plan_demo(camp_id)
        
        # Step 4: Simulate cancellation and replan
        await simulate_cancellation_and_replan(camp_id)
        
        # Step 5: Demonstrate scheduled automation
        demonstrate_scheduled_automation(camp_id)
        
        # Step 6: Show final state
        await show_final_state(camp_id)
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE!")
        print("=" * 60)
        print("\nThe system is now running autonomously with:")
        print("  ✓ Daily forecast automation")
        print("  ✓ Auto-planning for new camps")
        print("  ✓ Auto-replanning on cancellations")
        print("  ✓ Scheduled reminders (T-24h, T-6h, T-1h)")
        print("\nCheck Celery logs for ongoing automation activity.")
        
    except Exception as e:
        print(f"\n✗ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

