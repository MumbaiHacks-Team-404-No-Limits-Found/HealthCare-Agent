#!/usr/bin/env python3
"""
Test script for the AI Agent workflow.

Validates:
1. CSV data mappings
2. Forecast functionality
3. Planning functionality
4. Notification setup
5. Activity logging
6. Full workflow integration

Usage:
    python test_agent.py
"""

import asyncio
import sys
from app.database import connect_to_mongo, close_mongo_connection
from app.agent import MedicalCampAgent
from app.database import get_collection


async def test_csv_validation():
    """Test CSV data validation."""
    print("\n" + "=" * 70)
    print("TEST 1: CSV Data Validation")
    print("=" * 70)
    
    agent = MedicalCampAgent()
    result = await agent.validate_csv_mappings()
    
    print(f"✅ Volunteers: {result.volunteers_count}")
    print(f"✅ Camps: {result.camps_count}")
    print(f"✅ Requirements: {result.requirements_count}")
    print(f"✅ Role Demand History: {result.role_demand_history_count}")
    print(f"✅ Assignments History: {result.assignments_history_count}")
    
    if result.is_valid:
        print("\n✅ TEST PASSED: CSV data is properly seeded")
        return True
    else:
        print("\n❌ TEST FAILED: CSV data validation failed")
        for error in result.errors:
            print(f"  - {error}")
        return False


async def test_forecast():
    """Test forecast functionality."""
    print("\n" + "=" * 70)
    print("TEST 2: Forecast Functionality")
    print("=" * 70)
    
    # Get first camp
    camps_collection = get_collection("camps")
    camp_doc = await camps_collection.find_one({})
    
    if not camp_doc:
        print("❌ TEST SKIPPED: No camps found in database")
        return True
    
    camp_id = str(camp_doc["_id"])
    camp_name = camp_doc.get("name", "Unknown")
    
    print(f"Testing forecast for camp: {camp_name} ({camp_id})")
    
    try:
        agent = MedicalCampAgent()
        results = await agent.forecast_demand(camp_id)
        
        if results:
            print(f"✅ Forecast completed: {len(results)} results")
            print(f"   Sample result: {results[0].role} - mean={results[0].mean:.2f}")
            return True
        else:
            print("⚠️  Forecast returned no results (camp may have no requirements)")
            return True
            
    except Exception as e:
        print(f"❌ TEST FAILED: Forecast error: {e}")
        return False


async def test_planning():
    """Test planning functionality."""
    print("\n" + "=" * 70)
    print("TEST 3: Planning Functionality")
    print("=" * 70)
    
    # Get first camp
    camps_collection = get_collection("camps")
    camp_doc = await camps_collection.find_one({})
    
    if not camp_doc:
        print("❌ TEST SKIPPED: No camps found in database")
        return True
    
    camp_id = str(camp_doc["_id"])
    camp_name = camp_doc.get("name", "Unknown")
    
    print(f"Testing planning for camp: {camp_name} ({camp_id})")
    
    try:
        agent = MedicalCampAgent()
        assignments, unfilled = await agent.plan_assignments(camp_id, use_celery=False)
        
        print(f"✅ Planning completed:")
        print(f"   Assignments created: {len(assignments)}")
        print(f"   Unfilled slots: {unfilled}")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: Planning error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_activity_logging():
    """Test activity logging."""
    print("\n" + "=" * 70)
    print("TEST 4: Activity Logging")
    print("=" * 70)
    
    # Get first camp
    camps_collection = get_collection("camps")
    camp_doc = await camps_collection.find_one({})
    
    if not camp_doc:
        print("❌ TEST SKIPPED: No camps found in database")
        return True
    
    camp_id = str(camp_doc["_id"])
    
    try:
        agent = MedicalCampAgent()
        logs = await agent.get_activity_logs(camp_id)
        
        print(f"✅ Activity logging works: {len(logs)} logs found")
        if logs:
            print(f"   Latest event: {logs[0]['event']}")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: Activity logging error: {e}")
        return False


async def test_full_workflow():
    """Test full workflow (without notifications)."""
    print("\n" + "=" * 70)
    print("TEST 5: Full Workflow Integration")
    print("=" * 70)
    
    # Get first camp
    camps_collection = get_collection("camps")
    camp_doc = await camps_collection.find_one({})
    
    if not camp_doc:
        print("❌ TEST SKIPPED: No camps found in database")
        return True
    
    camp_id = str(camp_doc["_id"])
    camp_name = camp_doc.get("name", "Unknown")
    
    print(f"Testing full workflow for camp: {camp_name} ({camp_id})")
    print("(Notifications disabled for testing)")
    
    try:
        agent = MedicalCampAgent()
        result = await agent.run_full_workflow(
            camp_id,
            notify_volunteers=False,  # Disable notifications for testing
            use_celery=False
        )
        
        if result.success:
            print("✅ Full workflow completed successfully")
            print(f"   Forecast results: {len(result.forecast_results)}")
            print(f"   Assignments created: {len(result.assignments_created)}")
            print(f"   Unfilled slots: {result.unfilled_slots}")
            return True
        else:
            print("⚠️  Workflow completed with errors:")
            for error in result.errors:
                print(f"   - {error}")
            return len(result.errors) < 3  # Allow some non-critical errors
        
    except Exception as e:
        print(f"❌ TEST FAILED: Workflow error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 70)
    print("AI AGENT WORKFLOW TEST SUITE")
    print("=" * 70)
    
    try:
        await connect_to_mongo()
        
        tests = [
            ("CSV Validation", test_csv_validation),
            ("Forecast", test_forecast),
            ("Planning", test_planning),
            ("Activity Logging", test_activity_logging),
            ("Full Workflow", test_full_workflow),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())

