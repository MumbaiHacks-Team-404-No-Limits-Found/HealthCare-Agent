"""
Test script for LLM-powered volunteer queueing.

This script tests the LLM integration without requiring a full database setup.
"""

import asyncio
import os
from datetime import datetime

# Mock models for testing
class MockVolunteer:
    def __init__(self, id, name, skills, availability_slots, no_show_rate=0.1):
        self.id = id
        self.name = name
        self.skills = skills
        self.availability = [type('AvailSlot', (), {
            'date': '2024-01-15',
            'slots': availability_slots
        })()]
        self.no_show_rate = no_show_rate

class MockRequirement:
    def __init__(self, role, slot, count):
        self.role = role
        self.slot = slot
        self.count = count

class MockCamp:
    def __init__(self):
        self.id = "test_camp_123"
        self.name = "Community Health Camp"
        self.location = "Downtown Community Center"
        self.start = "2024-01-15T08:00:00"
        self.end = "2024-01-15T17:00:00"


async def test_llm_service():
    """Test LLM service initialization and availability."""
    print("🧪 Testing LLM Service...")
    print("=" * 60)
    
    from app.llm_service import get_llm_service
    
    llm = get_llm_service()
    
    print(f"✅ LLM Service Created")
    print(f"   Provider: {llm.llm_provider}")
    print(f"   Model: {llm.llm_model}")
    print(f"   Available: {llm.is_available()}")
    
    if not llm.is_available():
        print("\n⚠️  LLM not available. Please configure:")
        print("   1. Set OPENAI_API_KEY in .env")
        print("   2. Or set ANTHROPIC_API_KEY in .env")
        print("   3. Ensure API key is valid")
        return False
    
    print("\n✅ LLM Service is ready!")
    return True


async def test_priority_scoring():
    """Test LLM priority scoring with mock data."""
    print("\n" + "=" * 60)
    print("🧪 Testing Priority Scoring...")
    print("=" * 60)
    
    from app.llm_service import get_llm_service
    
    llm = get_llm_service()
    
    if not llm.is_available():
        print("⚠️  Skipping (LLM not available)")
        return
    
    # Create mock data
    volunteers = [
        MockVolunteer("v1", "Dr. Sarah Johnson", ["doctor"], ["morning"], 0.05),
        MockVolunteer("v2", "Nurse Mike Chen", ["nurse", "first_aid"], ["morning", "afternoon"], 0.10),
        MockVolunteer("v3", "Dr. Emily Davis", ["doctor", "surgeon"], ["morning"], 0.02),
        MockVolunteer("v4", "Volunteer Alex", ["registration", "admin"], ["morning"], 0.25),
    ]
    
    requirement = MockRequirement("doctor", "morning", 2)
    camp = MockCamp()
    
    print(f"\n📋 Requirement: {requirement.role} ({requirement.slot})")
    print(f"🏥 Camp: {camp.name}")
    print(f"👥 Volunteers: {len(volunteers)}")
    
    try:
        print("\n🤖 Calling LLM for priority scoring...")
        scores = await llm.generate_volunteer_priority_scores(
            volunteers, requirement, camp, []
        )
        
        print("\n📊 Priority Scores:")
        print("-" * 60)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for vol_id, score in sorted_scores:
            volunteer = next(v for v in volunteers if str(v.id) == vol_id)
            print(f"   {volunteer.name:20s} - {score:.3f} {'⭐' * int(score * 5)}")
        
        print("\n✅ Priority scoring completed successfully!")
        return scores
        
    except Exception as e:
        print(f"\n❌ Error during priority scoring: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_intelligent_queue():
    """Test complete intelligent queue creation."""
    print("\n" + "=" * 60)
    print("🧪 Testing Intelligent Queue Creation...")
    print("=" * 60)
    
    from app.llm_queueing import create_intelligent_volunteer_queue
    
    # Create mock data
    volunteers = [
        MockVolunteer("v1", "Dr. Sarah Johnson", ["doctor"], ["morning"], 0.05),
        MockVolunteer("v2", "Nurse Mike Chen", ["nurse", "first_aid"], ["morning", "afternoon"], 0.10),
        MockVolunteer("v3", "Dr. Emily Davis", ["doctor", "surgeon"], ["morning"], 0.02),
        MockVolunteer("v4", "Nurse Lisa Wong", ["nurse"], ["afternoon"], 0.08),
        MockVolunteer("v5", "Volunteer Alex", ["registration", "admin"], ["morning"], 0.25),
    ]
    
    requirements = [
        MockRequirement("doctor", "morning", 2),
        MockRequirement("nurse", "afternoon", 1),
    ]
    
    camp = MockCamp()
    
    print(f"\n🏥 Camp: {camp.name}")
    print(f"👥 Volunteers: {len(volunteers)}")
    print(f"📋 Requirements: {len(requirements)}")
    
    try:
        print("\n🤖 Creating intelligent queue...")
        queue = await create_intelligent_volunteer_queue(
            camp=camp,
            volunteers=volunteers,
            requirements=requirements,
            enable_llm=True
        )
        
        summary = queue.get_queue_summary()
        
        print("\n📊 Queue Summary:")
        print("-" * 60)
        print(f"   Total queues: {summary['total_queues']}")
        print(f"   Volunteers analyzed: {summary['volunteers_analyzed']}")
        print(f"   LLM calls made: {summary['llm_calls_made']}")
        print(f"   Processing time: {summary['processing_time_seconds']}s")
        print(f"   LLM enabled: {summary['llm_enabled']}")
        
        print("\n📋 Top Volunteers by Requirement:")
        print("-" * 60)
        
        for requirement in requirements:
            top_volunteers = queue.get_top_volunteers(requirement, count=3)
            print(f"\n   {requirement.role} - {requirement.slot}:")
            for qv in top_volunteers:
                print(f"      {qv.volunteer.name:20s} - Score: {qv.priority_score:.3f}")
        
        print("\n✅ Intelligent queue created successfully!")
        return queue
        
    except Exception as e:
        print(f"\n❌ Error creating queue: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_explanations():
    """Test AI-generated explanations."""
    print("\n" + "=" * 60)
    print("🧪 Testing AI Explanations...")
    print("=" * 60)
    
    from app.llm_service import get_llm_service
    
    llm = get_llm_service()
    
    if not llm.is_available():
        print("⚠️  Skipping (LLM not available)")
        return
    
    volunteer = MockVolunteer("v1", "Dr. Sarah Johnson", ["doctor"], ["morning"], 0.05)
    requirement = MockRequirement("doctor", "morning", 2)
    camp = MockCamp()
    
    print(f"\n👤 Volunteer: {volunteer.name}")
    print(f"📋 Requirement: {requirement.role} ({requirement.slot})")
    print(f"⭐ Priority Score: 0.95")
    
    try:
        print("\n🤖 Generating AI explanation...")
        explanation = await llm.generate_assignment_explanation(
            volunteer, requirement, camp, 0.95
        )
        
        print("\n📝 AI Explanation:")
        print("-" * 60)
        print(f"   {explanation}")
        print("-" * 60)
        
        print("\n✅ Explanation generated successfully!")
        return explanation
        
    except Exception as e:
        print(f"\n❌ Error generating explanation: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all tests."""
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║                                                        ║")
    print("║  🤖 LLM-Powered Volunteer Queueing Test Suite  🚀     ║")
    print("║                                                        ║")
    print("╚════════════════════════════════════════════════════════╝")
    print("\n")
    
    # Test 1: LLM Service
    llm_available = await test_llm_service()
    
    if not llm_available:
        print("\n" + "=" * 60)
        print("⚠️  Tests skipped - LLM service not configured")
        print("=" * 60)
        return
    
    # Test 2: Priority Scoring
    scores = await test_priority_scoring()
    
    # Test 3: Intelligent Queue
    queue = await test_intelligent_queue()
    
    # Test 4: Explanations
    explanation = await test_explanations()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 TEST SUITE COMPLETE")
    print("=" * 60)
    
    results = {
        "LLM Service": "✅ PASS" if llm_available else "❌ FAIL",
        "Priority Scoring": "✅ PASS" if scores else "❌ FAIL",
        "Intelligent Queue": "✅ PASS" if queue else "❌ FAIL",
        "AI Explanations": "✅ PASS" if explanation else "❌ FAIL",
    }
    
    print("\nResults:")
    for test, result in results.items():
        print(f"   {test:25s} {result}")
    
    all_passed = all("✅" in r for r in results.values())
    
    if all_passed:
        print("\n🎉 All tests PASSED! LLM queueing is working perfectly!")
    else:
        print("\n⚠️  Some tests failed. Check configuration and try again.")
    
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())

