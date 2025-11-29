"""Pytest configuration and shared fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient

from app.main import app
from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """
    Provide a test database connection.
    
    Uses a separate test database to avoid polluting production data.
    """
    # Override database name for tests
    settings.database_name = "agentic_volunteer_test"
    
    # Connect to test database
    await connect_to_mongo()
    db = get_database()
    
    yield db
    
    # Cleanup: Drop test database after all tests
    client = AsyncIOMotorClient(settings.mongo_uri)
    await client.drop_database(settings.database_name)
    await close_mongo_connection()


@pytest.fixture(autouse=True)
async def clean_db(test_db):
    """
    Clean database before each test.
    
    This fixture runs automatically before each test function.
    """
    # Drop all collections before each test
    for collection_name in await test_db.list_collection_names():
        await test_db[collection_name].delete_many({})
    
    yield


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for testing FastAPI endpoints.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_token(client: AsyncClient, test_db) -> str:
    """
    Create an admin user and return authentication token.
    """
    from app.auth import hash_password
    
    # Create admin user
    admin_email = "test_admin@example.com"
    admin_password = "test_password123"
    
    await test_db["users"].insert_one({
        "email": admin_email,
        "password_hash": hash_password(admin_password),
        "role": "admin"
    })
    
    # Login to get token
    response = await client.post(
        "/auth/login",
        json={"email": admin_email, "password": admin_password}
    )
    
    assert response.status_code == 200
    token_data = response.json()
    return token_data["access_token"]


@pytest.fixture
async def sample_camp(test_db):
    """Create a sample camp for testing."""
    camp_data = {
        "name": "Test Medical Camp",
        "location": "Test Hospital",
        "start": "2025-12-01T09:00:00Z",
        "end": "2025-12-01T17:00:00Z",
        "requirements": [
            {"role": "doctor", "count": 2, "slot": "morning"},
            {"role": "nurse", "count": 3, "slot": "morning"}
        ]
    }
    
    result = await test_db["camps"].insert_one(camp_data)
    camp_data["_id"] = result.inserted_id
    
    return camp_data


@pytest.fixture
async def sample_volunteer(test_db):
    """Create a sample volunteer for testing."""
    volunteer_data = {
        "name": "Test Volunteer",
        "phone": "+919800000001",
        "skills": ["doctor", "nurse"],
        "availability": [
            {"date": "2025-12-01", "slots": ["morning", "afternoon"]}
        ],
        "no_show_rate": 0.2
    }
    
    result = await test_db["volunteers"].insert_one(volunteer_data)
    volunteer_data["_id"] = result.inserted_id
    
    return volunteer_data

