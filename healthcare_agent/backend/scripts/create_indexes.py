"""
Database indexing script for MongoDB.

Run this script after initial deployment to create indexes for optimal query performance.

Usage:
    python scripts/create_indexes.py
"""
import asyncio
from app.database import connect_to_mongo, close_mongo_connection, get_database


async def create_indexes():
    """Create indexes for frequently queried fields."""
    await connect_to_mongo()
    db = get_database()
    
    print("Creating database indexes...")
    
    # Camps collection indexes
    camps_collection = db["camps"]
    await camps_collection.create_index("start")  # For date range queries
    await camps_collection.create_index("location")  # For location-based queries
    print("✓ Created indexes on camps collection")
    
    # Volunteers collection indexes
    volunteers_collection = db["volunteers"]
    await volunteers_collection.create_index("phone", unique=True)  # Unique phone lookup
    await volunteers_collection.create_index("skills")  # For skill-based queries
    print("✓ Created indexes on volunteers collection")
    
    # Assignments collection indexes
    assignments_collection = db["assignments"]
    await assignments_collection.create_index("camp_id")  # For camp-based queries
    await assignments_collection.create_index("volunteer_id")  # For volunteer-based queries
    await assignments_collection.create_index([("camp_id", 1), ("status", 1)])  # Compound index
    await assignments_collection.create_index([("volunteer_id", 1), ("status", 1)])  # Compound index
    print("✓ Created indexes on assignments collection")
    
    # Activity logs collection indexes
    activity_logs_collection = db["activity_logs"]
    await activity_logs_collection.create_index("camp_id")  # For camp activity queries
    await activity_logs_collection.create_index([("camp_id", 1), ("timestamp", -1)])  # Compound index for sorted queries
    await activity_logs_collection.create_index("timestamp")  # For time-based queries
    await activity_logs_collection.create_index("event")  # For event type filtering
    print("✓ Created indexes on activity_logs collection")
    
    # Role demand history indexes
    role_demand_history_collection = db["role_demand_history"]
    await role_demand_history_collection.create_index([("role", 1), ("slot", 1)])  # Compound index for forecasting queries
    await role_demand_history_collection.create_index("recorded_at")  # For time-based queries
    print("✓ Created indexes on role_demand_history collection")
    
    # Users collection indexes
    users_collection = db["users"]
    await users_collection.create_index("email", unique=True)  # Unique email for login
    print("✓ Created indexes on users collection")
    
    print("\n✅ All indexes created successfully!")
    print("\nIndex summary:")
    print("  - camps: start, location")
    print("  - volunteers: phone (unique), skills")
    print("  - assignments: camp_id, volunteer_id, compound indexes")
    print("  - activity_logs: camp_id, timestamp, event, compound indexes")
    print("  - role_demand_history: role+slot compound, recorded_at")
    print("  - users: email (unique)")
    
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(create_indexes())

