"""Diagnostic script to check authentication setup."""
import asyncio
from app.database import connect_to_mongo, close_mongo_connection, get_collection
from app.auth import hash_password, verify_password
from app.config import settings


async def check_auth_setup():
    """Check authentication setup and diagnose login issues."""
    print("=" * 60)
    print("Authentication Setup Diagnostic")
    print("=" * 60)
    print()
    
    # Check JWT secret
    print("1. Checking JWT Secret Key...")
    if not settings.jwt_secret_key:
        print("   ❌ ERROR: JWT_SECRET_KEY is not set!")
        print("   Solution: Set JWT_SECRET_KEY in .env file or environment variable")
        print("   Example: JWT_SECRET_KEY=your-strong-random-secret-key-here")
        return
    elif settings.jwt_secret_key == "your-secret-key-change-in-production-use-env-var":
        print("   ⚠️  WARNING: Using default JWT secret (not secure)")
        print("   Solution: Set JWT_SECRET_KEY in .env file")
    else:
        print(f"   ✅ JWT secret is set (length: {len(settings.jwt_secret_key)})")
    print()
    
    # Connect to database
    print("2. Connecting to database...")
    try:
        await connect_to_mongo()
        print("   ✅ Connected to MongoDB")
    except Exception as e:
        print(f"   ❌ ERROR: Failed to connect to MongoDB: {e}")
        return
    print()
    
    # Check if admin user exists
    print("3. Checking for admin user...")
    users_collection = get_collection("users")
    admin_user = await users_collection.find_one({"email": "admin@example.com"})
    
    if not admin_user:
        print("   ❌ Admin user not found!")
        print("   Solution: Run 'python seed_admin.py' to create the admin user")
        await close_mongo_connection()
        return
    else:
        print("   ✅ Admin user exists")
        print(f"   User ID: {admin_user.get('_id')}")
        print(f"   Email: {admin_user.get('email')}")
        print(f"   Role: {admin_user.get('role', 'admin')}")
    print()
    
    # Test password verification
    print("4. Testing password verification...")
    stored_hash = admin_user.get("password_hash")
    if not stored_hash:
        print("   ❌ ERROR: Admin user has no password_hash!")
        print("   Solution: Delete the user and run 'python seed_admin.py' again")
        await close_mongo_connection()
        return
    
    test_password = "admin123"
    is_valid = verify_password(test_password, stored_hash)
    
    if is_valid:
        print(f"   ✅ Password verification works for '{test_password}'")
    else:
        print(f"   ❌ Password verification FAILED for '{test_password}'")
        print("   This means the password hash doesn't match.")
        print("   Solution: Delete the user and run 'python seed_admin.py' again")
        print()
        print("   To fix, run this in MongoDB:")
        print("   db.users.deleteOne({email: 'admin@example.com'})")
        print("   Then run: python seed_admin.py")
    print()
    
    # Check all users
    print("5. Listing all users in database...")
    all_users = await users_collection.find({}).to_list(length=100)
    if all_users:
        print(f"   Found {len(all_users)} user(s):")
        for user in all_users:
            print(f"   - {user.get('email')} (role: {user.get('role', 'N/A')})")
    else:
        print("   No users found in database")
    print()
    
    print("=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)
    print()
    print("If admin user exists and password verification works,")
    print("try logging in with:")
    print("  Email: admin@example.com")
    print("  Password: admin123")
    print()
    
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(check_auth_setup())

