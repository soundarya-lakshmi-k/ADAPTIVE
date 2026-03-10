import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

load_dotenv()

_client = None
_db = None

async def connect_db():
    global _client, _db
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "adaptive_engine")
    _client = AsyncIOMotorClient(mongo_uri)
    _db = _client[db_name]
    await _db.questions.create_index([("difficulty", 1), ("topic", 1)])
    await _db.questions.create_index([("tags", 1)])
    await _db.sessions.create_index([("session_id", 1)], unique=True)
    await _db.sessions.create_index([("created_at", -1)])
    print(f"[DB] Connected to MongoDB: {db_name}")

async def disconnect_db():
    global _client
    if _client:
        _client.close()
        print("[DB] Disconnected from MongoDB")

def get_db():
    if _db is None:
        raise RuntimeError("Database not initialised. Call connect_db() first.")
    return _db