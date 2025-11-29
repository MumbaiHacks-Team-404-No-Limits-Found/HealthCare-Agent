#!/usr/bin/env python3
"""
CLI script to run the AI Agent workflow for medical camp coordination.

Usage:
    python run_agent.py validate                    # Validate CSV mappings
    python run_agent.py forecast <camp_id>           # Run forecast only
    python run_agent.py plan <camp_id>              # Run planning only
    python run_agent.py workflow <camp_id>          # Run full workflow
    python run_agent.py replan <camp_id>            # Replan camp
    python run_agent.py logs <camp_id>              # View activity logs
"""

import asyncio
import sys
import json
from app.database import connect_to_mongo, close_mongo_connection
from app.agent import MedicalCampAgent


async def validate_mappings():
    """Validate CSV data mappings."""
    print("=" * 70)
    print("CSV DATA VALIDATION")
    print("=" * 70)
    
    agent = MedicalCampAgent()
    result = await agent.validate_csv_mappings()
    
    print(f"\nVolunteers: {result.volunteers_count}")
    print(f"Camps: {result.camps_count}")
    print(f"Requirements: {result.requirements_count}")
    print(f"Role Demand History: {result.role_demand_history_count}")
    print(f"Assignments History: {result.assignments_history_count}")
    
    if result.is_valid:
        print("\n✅ Validation PASSED")
    else:
        print("\n❌ Validation FAILED")
        for error in result.errors:
            print(f"  - {error}")
    
    print("\n" + "=" * 70)
    return result.is_valid


async def run_forecast(camp_id: str):
    """Run forecast for a camp."""
    print(f"\nRunning forecast for camp: {camp_id}")
    print("-" * 70)
    
    agent = MedicalCampAgent()
    results = await agent.forecast_demand(camp_id)
    
    print(f"\nForecast Results ({len(results)} requirements):")
    for result in results:
        print(f"  {result.role} ({result.slot}):")
        print(f"    Mean: {result.mean:.2f}")
        print(f"    Lower 10%: {result.lower_10}")
        print(f"    Upper 90%: {result.upper_90}")
    
    return results


async def run_plan(camp_id: str):
    """Run planning for a camp."""
    print(f"\nRunning planning for camp: {camp_id}")
    print("-" * 70)
    
    agent = MedicalCampAgent()
    assignments, unfilled = await agent.plan_assignments(camp_id, use_celery=False)
    
    print(f"\nPlanning Results:")
    print(f"  Assignments created: {len(assignments)}")
    print(f"  Unfilled slots: {unfilled}")
    
    if assignments:
        print(f"\nAssignments:")
        for assign in assignments[:10]:  # Show first 10
            print(f"  - {assign.role} ({assign.slot}): Volunteer {assign.volunteer_id}")
        if len(assignments) > 10:
            print(f"  ... and {len(assignments) - 10} more")
    
    return assignments, unfilled


async def run_workflow(camp_id: str):
    """Run full agent workflow."""
    print(f"\nRunning full agent workflow for camp: {camp_id}")
    print("=" * 70)
    
    agent = MedicalCampAgent()
    result = await agent.run_full_workflow(
        camp_id,
        notify_volunteers=True,
        use_celery=False  # Run synchronously for CLI
    )
    
    print("\nWorkflow Results:")
    print(json.dumps(result.to_dict(), indent=2))
    
    if result.success:
        print("\n✅ Workflow completed successfully")
    else:
        print("\n⚠️  Workflow completed with errors")
        for error in result.errors:
            print(f"  - {error}")
    
    return result


async def run_replan(camp_id: str):
    """Replan a camp."""
    print(f"\nReplanning camp: {camp_id}")
    print("-" * 70)
    
    agent = MedicalCampAgent()
    new_assignments, unfilled = await agent.replan_camp(camp_id, use_celery=False)
    
    print(f"\nReplan Results:")
    print(f"  New assignments: {len(new_assignments)}")
    print(f"  Unfilled slots: {unfilled}")
    
    return new_assignments, unfilled


async def view_logs(camp_id: str):
    """View activity logs for a camp."""
    print(f"\nActivity logs for camp: {camp_id}")
    print("-" * 70)
    
    agent = MedicalCampAgent()
    logs = await agent.get_activity_logs(camp_id)
    
    if not logs:
        print("No activity logs found.")
        return
    
    print(f"\nFound {len(logs)} activity logs:\n")
    for log in logs[:20]:  # Show first 20
        print(f"[{log['timestamp']}] {log['event']}")
        if log['meta']:
            print(f"  Meta: {json.dumps(log['meta'], indent=4)}")
        print()
    
    if len(logs) > 20:
        print(f"... and {len(logs) - 20} more logs")


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        await connect_to_mongo()
        
        if command == "validate":
            success = await validate_mappings()
            sys.exit(0 if success else 1)
        
        elif command == "forecast":
            if len(sys.argv) < 3:
                print("Error: camp_id required")
                sys.exit(1)
            await run_forecast(sys.argv[2])
        
        elif command == "plan":
            if len(sys.argv) < 3:
                print("Error: camp_id required")
                sys.exit(1)
            await run_plan(sys.argv[2])
        
        elif command == "workflow":
            if len(sys.argv) < 3:
                print("Error: camp_id required")
                sys.exit(1)
            await run_workflow(sys.argv[2])
        
        elif command == "replan":
            if len(sys.argv) < 3:
                print("Error: camp_id required")
                sys.exit(1)
            await run_replan(sys.argv[2])
        
        elif command == "logs":
            if len(sys.argv) < 3:
                print("Error: camp_id required")
                sys.exit(1)
            await view_logs(sys.argv[2])
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())

