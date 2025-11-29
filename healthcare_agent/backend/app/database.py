"""Database connection and collection helpers."""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.config import settings

# Global MongoDB client
_client: Optional[AsyncIOMotorClient] = None
_database = None


async def connect_to_mongo() -> None:
    """Initialize MongoDB connection."""
    global _client, _database
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _database = _client[settings.database_name]
    print(f"Connected to MongoDB: {settings.mongo_uri}")


async def close_mongo_connection() -> None:
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        print("Disconnected from MongoDB")


def get_database():
    """Get the database instance."""
    return _database


def get_collection(collection_name: str):
    """Get a MongoDB collection by name."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return _database[collection_name]

