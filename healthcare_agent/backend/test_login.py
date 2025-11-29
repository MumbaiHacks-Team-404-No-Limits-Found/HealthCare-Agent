"""Quick test script to verify login works."""
import asyncio
import sys
from app.database import connect_to_mongo, close_mongo_connection, get_collection
from app.auth import hash_password, verify_password


async def test_login():
    """Test if admin user exists and password works."""
    print("Testing login setup...")
    print("=" * 60)
    
    try:
        await connect_to_mongo()
        print("✓ Connected to MongoDB")
        
        users_collection = get_collection("users")
        email = "admin@example.com"
        password = "admin123"
        
        # Check if user exists
        user = await users_collection.find_one({"email": email})
        
        if not user:
            print(f"✗ User {email} NOT FOUND in database!")
            print("\nSolution: Run 'python seed_admin.py' to create the admin user")
            await close_mongo_connection()
            sys.exit(1)
        
        print(f"✓ User {email} found")
        print(f"  User ID: {user.get('_id')}")
        print(f"  Role: {user.get('role', 'N/A')}")
        
        # Check password hash
        stored_hash = user.get("password_hash")
        if not stored_hash:
            print("✗ User has NO password_hash!")
            print("\nSolution: Run 'python seed_admin.py' to fix this")
            await close_mongo_connection()
            sys.exit(1)
        
        print(f"✓ Password hash exists (length: {len(stored_hash)})")
        
        # Test password verification
        print(f"\nTesting password verification for '{password}'...")
        is_valid = verify_password(password, stored_hash)
        
        if is_valid:
            print("✓ Password verification SUCCESSFUL!")
            print("\nYou should be able to login with:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
        else:
            print("✗ Password verification FAILED!")
            print("\nThe password hash doesn't match. Fixing it...")
            
            # Fix the password hash
            new_hash = hash_password(password)
            await users_collection.update_one(
                {"email": email},
                {"$set": {"password_hash": new_hash}}
            )
            
            # Verify it works now
            is_valid_now = verify_password(password, new_hash)
            if is_valid_now:
                print("✓ Password hash updated and verified!")
                print("\nYou can now login with:")
                print(f"  Email: {email}")
                print(f"  Password: {password}")
            else:
                print("✗ Still failing after update - this is unexpected!")
                await close_mongo_connection()
                sys.exit(1)
        
        await close_mongo_connection()
        print("\n" + "=" * 60)
        print("✓ All checks passed! Login should work now.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_login())

