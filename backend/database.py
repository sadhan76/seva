"""
Database configuration and MongoDB connection management using Motor (async driver).
"""

import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables from .env
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "namma_vivasayi_db")

client: AsyncIOMotorClient = None
db = None

def get_database():
    """Returns the database instance."""
    global db
    if db is None:
        init_db()
    return db

import re

def sanitize_mongo_uri(raw_err: str) -> str:
    """Removes user:password credentials from raw MongoDB connection error strings."""
    if not raw_err:
        return "Unknown error"
    # Redact mongodb://user:pass@ and mongodb+srv://user:pass@
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:[REDACTED]@", str(raw_err))

def init_db():
    """Initializes the MongoDB client and database connection."""
    global client, db
    try:
        client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        db = client[MONGODB_DB_NAME]
    except Exception as e:
        safe_err = sanitize_mongo_uri(str(e))
        print(f"[Warning] Failed to initialize MongoDB client: {safe_err}")
        db = None

async def check_db_connection() -> dict:
    """
    Checks whether MongoDB is alive and responsive.
    Returns status dict with connection info.
    """
    global client
    if client is None:
        init_db()
    
    try:
        # Ping the admin database to verify connectivity
        await client.admin.command('ping')
        return {
            "connected": True,
            "database_name": MONGODB_DB_NAME,
            "message": "Connected to MongoDB successfully."
        }
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        safe_msg = sanitize_mongo_uri(str(e))
        return {
            "connected": False,
            "database_name": MONGODB_DB_NAME,
            "message": f"Could not connect to MongoDB: {safe_msg}"
        }
    except Exception as e:
        safe_msg = sanitize_mongo_uri(str(e))
        return {
            "connected": False,
            "database_name": MONGODB_DB_NAME,
            "message": f"Database error: {safe_msg}"
        }

def get_farmers_collection():
    """Returns the 'farmers' collection."""
    database = get_database()
    return database["farmers"] if database is not None else None

def get_bookings_collection():
    """Returns the 'procurement_bookings' collection."""
    database = get_database()
    return database["procurement_bookings"] if database is not None else None

def get_users_collection():
    """Returns the 'users' collection."""
    database = get_database()
    return database["users"] if database is not None else None

def get_notifications_collection():
    """Returns the 'notifications' collection."""
    database = get_database()
    return database["notifications"] if database is not None else None

def get_centres_collection():
    """Returns the 'procurement_centres' collection."""
    database = get_database()
    return database["procurement_centres"] if database is not None else None

def get_bills_collection():
    """Returns the 'procurement_bills' collection."""
    database = get_database()
    return database["procurement_bills"] if database is not None else None

def get_chat_history_collection():
    """Returns the 'farmer_chat_history' collection."""
    database = get_database()
    return database["farmer_chat_history"] if database is not None else None

def get_telegram_link_tokens_collection():
    """Returns the 'telegram_link_tokens' collection."""
    database = get_database()
    return database["telegram_link_tokens"] if database is not None else None

def get_telegram_otps_collection():
    """Returns the 'telegram_otps' collection."""
    database = get_database()
    return database["telegram_otps"] if database is not None else None

