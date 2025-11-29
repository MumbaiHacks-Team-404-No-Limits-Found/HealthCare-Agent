"""
CSV Seeding Script for Agentic Volunteer Coordinator

Reads CSV files from backend/data/ and seeds MongoDB collections.

Usage:
    cd backend
    python seed_from_csv.py
"""
import asyncio
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from bson import ObjectId

from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.models import AvailabilitySlot


# Path to data directory
DATA_DIR = Path(__file__).parent / "data"


async def seed_volunteers(db) -> None:
    """
    Seed volunteers collection from data/volunteers.csv.
    
    CSV columns: volunteer_id, name, phone, skills, no_show_rate, city, preferred_slots
    
    Maps to Volunteer model:
    - name, phone, skills (list), no_show_rate
    - availability: constructed from preferred_slots
    """
    csv_path = DATA_DIR / "volunteers.csv"
    if not csv_path.exists():
        print(f"⚠ Skipping volunteers: {csv_path} not found")
        return
    
    print(f"Seeding volunteers from {csv_path.name}...")
    
    collection = db["volunteers"]
    
    # Clear existing volunteers (for dev use - comment out for production)
    await collection.delete_many({})
    
    volunteers = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse skills (comma-separated string -> list)
            skills_str = row.get('skills', '').strip()
            skills = [s.strip() for s in skills_str.split(',') if s.strip()] if skills_str else []
            
            # Parse preferred_slots (comma-separated -> availability list)
            slots_str = row.get('preferred_slots', '').strip()
            slots = [s.strip() for s in slots_str.split(',') if s.strip()] if slots_str else []
            
            # Create availability (using a generic date - in real app, this would be camp-specific)
            # For seeding, we'll create a placeholder availability entry
            availability = []
            if slots:
                # Use a placeholder date - actual availability would be camp-specific
                availability.append({
                    "date": "2025-01-01",  # Placeholder
                    "slots": slots
                })
            
            volunteer_doc = {
                "name": row.get('name', '').strip(),
                "phone": row.get('phone', '').strip(),
                "skills": skills,
                "availability": availability,
                "no_show_rate": float(row.get('no_show_rate', 0.2)),
                # Store additional fields from CSV
                "city": row.get('city', '').strip(),
                "volunteer_id": row.get('volunteer_id', '').strip()  # Keep original ID for reference
            }
            volunteers.append(volunteer_doc)
    
    if volunteers:
        result = await collection.insert_many(volunteers)
        print(f"  ✓ Inserted {len(result.inserted_ids)} volunteers")
    else:
        print("  ⚠ No volunteers to insert")


async def seed_camps_and_requirements(db) -> None:
    """
    Seed camps and requirements from data/camps.csv and data/camp_requirements.csv.
    
    Combines camp info with requirements to create Camp documents matching the Camp model.
    """
    camps_csv = DATA_DIR / "camps.csv"
    requirements_csv = DATA_DIR / "camp_requirements.csv"
    
    if not camps_csv.exists():
        print(f"⚠ Skipping camps: {camps_csv} not found")
        return
    
    if not requirements_csv.exists():
        print(f"⚠ Skipping requirements: {requirements_csv} not found")
        return
    
    print(f"Seeding camps from {camps_csv.name} and {requirements_csv.name}...")
    
    collection = db["camps"]
    
    # Clear existing camps (for dev use)
    await collection.delete_many({})
    
    # Read requirements first (group by camp_id)
    requirements_by_camp: Dict[str, List[Dict]] = {}
    with open(requirements_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            camp_id = row.get('camp_id', '').strip()
            if camp_id not in requirements_by_camp:
                requirements_by_camp[camp_id] = []
            
            requirements_by_camp[camp_id].append({
                "role": row.get('role', '').strip(),
                "slot": row.get('slot', '').strip(),
                "count": int(row.get('required_count', 0))
            })
    
    # Read camps and combine with requirements
    camps = []
    with open(camps_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            camp_id = row.get('camp_id', '').strip()
            camp_date = row.get('date', '').strip()
            
            # Parse date and create ISO datetime strings
            # Assuming date is in YYYY-MM-DD format
            try:
                date_obj = datetime.strptime(camp_date, '%Y-%m-%d')
                start_time = date_obj.replace(hour=9, minute=0, second=0)  # 9 AM
                end_time = date_obj.replace(hour=17, minute=0, second=0)    # 5 PM
                
                start_iso = start_time.isoformat() + "Z"
                end_iso = end_time.isoformat() + "Z"
            except Exception:
                # Fallback if date parsing fails
                start_iso = f"{camp_date}T09:00:00Z"
                end_iso = f"{camp_date}T17:00:00Z"
            
            # Get requirements for this camp
            requirements = requirements_by_camp.get(camp_id, [])
            
            camp_doc = {
                "name": row.get('name', '').strip(),
                "location": row.get('location', '').strip(),
                "start": start_iso,
                "end": end_iso,
                "requirements": requirements,
                # Store additional fields
                "camp_id": camp_id,  # Keep original ID for reference
                "camp_type": row.get('camp_type', '').strip()
            }
            camps.append(camp_doc)
    
    if camps:
        result = await collection.insert_many(camps)
        print(f"  ✓ Inserted {len(result.inserted_ids)} camps")
    else:
        print("  ⚠ No camps to insert")


async def seed_role_demand_history(db) -> None:
    """
    Seed role_demand_history collection from data/role_demand_history.csv.
    
    This collection stores historical demand data used for forecasting.
    
    CSV columns: camp_id, slot, role, volunteers_needed
    """
    csv_path = DATA_DIR / "role_demand_history.csv"
    if not csv_path.exists():
        print(f"⚠ Skipping role_demand_history: {csv_path} not found")
        return
    
    print(f"Seeding role_demand_history from {csv_path.name}...")
    
    collection = db["role_demand_history"]
    
    # Clear existing history (for dev use)
    await collection.delete_many({})
    
    history_docs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc = {
                "camp_id": row.get('camp_id', '').strip(),
                "slot": row.get('slot', '').strip(),
                "role": row.get('role', '').strip(),
                "demand_count": int(row.get('volunteers_needed', 0)),
                # Store timestamp for when this was recorded (use current time for seeding)
                "recorded_at": datetime.utcnow()
            }
            history_docs.append(doc)
    
    if history_docs:
        result = await collection.insert_many(history_docs)
        print(f"  ✓ Inserted {len(result.inserted_ids)} demand history records")
    else:
        print("  ⚠ No demand history to insert")


async def seed_assignments_history(db) -> None:
    """
    Seed assignments_history collection from data/assignments_history.csv.
    
    CSV columns: assignment_id, camp_id, volunteer_id, role, slot, status, arrived
    """
    csv_path = DATA_DIR / "assignments_history.csv"
    if not csv_path.exists():
        print(f"⚠ Skipping assignments_history: {csv_path} not found")
        return
    
    print(f"Seeding assignments_history from {csv_path.name}...")
    
    collection = db["assignments_history"]
    
    # Clear existing history (for dev use)
    await collection.delete_many({})
    
    history_docs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse boolean field
            arrived_str = row.get('arrived', 'false').strip().lower()
            arrived = arrived_str in ('true', '1', 'yes', 't')
            
            doc = {
                "assignment_id": row.get('assignment_id', '').strip(),
                "camp_id": row.get('camp_id', '').strip(),
                "volunteer_id": row.get('volunteer_id', '').strip(),
                "role": row.get('role', '').strip(),
                "slot": row.get('slot', '').strip(),
                "status": row.get('status', '').strip(),
                "arrived": arrived,
                # Store timestamp
                "recorded_at": datetime.utcnow()
            }
            history_docs.append(doc)
    
    if history_docs:
        result = await collection.insert_many(history_docs)
        print(f"  ✓ Inserted {len(result.inserted_ids)} assignment history records")
    else:
        print("  ⚠ No assignment history to insert")


async def seed_patient_history(db) -> None:
    """
    Seed patient_history collection from data/patient_history.csv.
    
    CSV columns: camp_id, date, location, camp_type, slot, patients
    """
    csv_path = DATA_DIR / "patient_history.csv"
    if not csv_path.exists():
        print(f"⚠ Skipping patient_history: {csv_path} not found")
        return
    
    print(f"Seeding patient_history from {csv_path.name}...")
    
    collection = db["patient_history"]
    
    # Clear existing history (for dev use)
    await collection.delete_many({})
    
    history_docs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse date
            date_str = row.get('date', '').strip()
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            except Exception:
                date_obj = datetime.utcnow()
            
            doc = {
                "camp_id": row.get('camp_id', '').strip(),
                "date": date_obj,
                "location": row.get('location', '').strip(),
                "camp_type": row.get('camp_type', '').strip(),
                "slot": row.get('slot', '').strip(),
                "patients": int(row.get('patients', 0)),
                # Store timestamp
                "recorded_at": datetime.utcnow()
            }
            history_docs.append(doc)
    
    if history_docs:
        result = await collection.insert_many(history_docs)
        print(f"  ✓ Inserted {len(result.inserted_ids)} patient history records")
    else:
        print("  ⚠ No patient history to insert")


async def main() -> None:
    """Main seeding function."""
    print("=" * 60)
    print("CSV Seeding Script for Agentic Volunteer Coordinator")
    print("=" * 60)
    print()
    
    # Connect to MongoDB
    await connect_to_mongo()
    db = get_database()
    
    if db is None:
        print("✗ Failed to connect to database")
        return
    
    try:
        # Seed all collections
        await seed_volunteers(db)
        await seed_camps_and_requirements(db)
        await seed_role_demand_history(db)
        await seed_assignments_history(db)
        await seed_patient_history(db)
        
        print()
        print("=" * 60)
        print("✓ Seeding completed successfully!")
        print("=" * 60)
        print()
        print("Collections seeded:")
        print("  - volunteers")
        print("  - camps")
        print("  - role_demand_history")
        print("  - assignments_history")
        print("  - patient_history")
        print()
        print("Note: Collections were cleared before seeding (dev mode).")
        print("      Comment out delete_many() calls for production upsert behavior.")
        
    except Exception as e:
        print(f"\n✗ Seeding failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())

