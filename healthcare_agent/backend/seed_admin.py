"""Script to create an admin user for the Agentic Volunteer Coordinator."""
import asyncio
from app.database import connect_to_mongo, close_mongo_connection
from app.auth import hash_password
from app.database import get_collection


async def create_admin():
    """Create an admin user if it doesn't exist."""
    await connect_to_mongo()
    users_collection = get_collection("users")
    
    email = "admin@example.com"
    password = "admin123"  # Default password - change this in production!
    
    # Check if user already exists
    existing = await users_collection.find_one({"email": email})
    if existing:
        # Verify the existing password hash works
        from app.auth import verify_password
        stored_hash = existing.get("password_hash")
        
        if stored_hash and verify_password(password, stored_hash):
            print(f"[OK] User {email} already exists and password is correct")
            print(f"  User ID: {existing.get('_id')}")
            print(f"  Role: {existing.get('role', 'admin')}")
            print()
            print("You can log in with:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
        else:
            print(f"[WARNING] User {email} exists but password verification failed!")
            print("  Updating password hash...")
            # Update the password hash
            new_hash = hash_password(password)
            await users_collection.update_one(
                {"email": email},
                {"$set": {"password_hash": new_hash}}
            )
            print(f"[OK] Updated password hash for {email}")
            print()
            print("You can now log in with:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
        
        await close_mongo_connection()
        return
    
    # Create admin user
    user_doc = {
        "email": email,
        "password_hash": hash_password(password),
        "role": "admin"
    }
    result = await users_collection.insert_one(user_doc)
    print(f"[OK] Created admin user: {email} (ID: {result.inserted_id})")
    print()
    print("Admin credentials:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print()
    print("[WARNING] IMPORTANT: Change the password in production!")
    
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(create_admin())

