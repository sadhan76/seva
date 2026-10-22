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

import urllib.parse
import re

def sanitize_mongo_uri(raw_err: str) -> str:
    """Removes user:password credentials from raw MongoDB connection error strings."""
    if not raw_err:
        return "Unknown error"
    # Redact mongodb://user:pass@ and mongodb+srv://user:pass@
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:[REDACTED]@", str(raw_err))

def format_mongo_uri(raw_uri: str) -> str:
    """
    Ensures username and password in MongoDB URI are RFC 3986 escaped using urllib.parse.quote_plus.
    Handles special characters like '@', ':', '#', etc., in passwords.
    """
    if not raw_uri or not ('://' in raw_uri):
        return raw_uri
    try:
        prefix, rest = raw_uri.split('://', 1)
        if '@' not in rest:
            return raw_uri
        # Split credentials from host using the last '@'
        creds, host_part = rest.rsplit('@', 1)
        if ':' in creds:
            user, pwd = creds.split(':', 1)
            user = urllib.parse.quote_plus(urllib.parse.unquote_plus(user))
            pwd = urllib.parse.quote_plus(urllib.parse.unquote_plus(pwd))
            fixed_creds = f"{user}:{pwd}"
        else:
            fixed_creds = urllib.parse.quote_plus(urllib.parse.unquote_plus(creds))
        return f"{prefix}://{fixed_creds}@{host_part}"
    except Exception:
        return raw_uri

def init_db():
    """Initializes the MongoDB client and database connection."""
    global client, db
    try:
        safe_uri = format_mongo_uri(MONGODB_URI)
        client = AsyncIOMotorClient(
            safe_uri,
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



def get_diagnosis_reports_collection():
    """Returns the 'diagnosis_reports' collection."""
    database = get_database()
    return database["diagnosis_reports"] if database is not None else None

def get_rates_collection():
    """Returns the 'procurement_rates' collection."""
    database = get_database()
    return database["procurement_rates"] if database is not None else None

def get_slot_closures_collection():
    """Returns the 'slot_closures' collection."""
    database = get_database()
    return database["slot_closures"] if database is not None else None

def get_rate_limits_collection():
    """Returns the 'rate_limits' collection."""
    database = get_database()
    return database["rate_limits"] if database is not None else None

def get_farmer_limits_collection():
    """Returns the 'farmer_limits' collection."""
    database = get_database()
    return database["farmer_limits"] if database is not None else None

def get_government_schemes_collection():
    """Returns the 'government_schemes' collection."""
    database = get_database()
    return database["government_schemes"] if database is not None else None

def get_notification_preferences_collection():
    """Returns the 'notification_preferences' collection."""
    database = get_database()
    return database["notification_preferences"] if database is not None else None

def get_push_subscriptions_collection():
    """Returns the 'push_subscriptions' collection."""
    database = get_database()
    return database["push_subscriptions"] if database is not None else None

def get_scheduler_locks_collection():
    """Returns the 'scheduler_locks' collection for distributed singleton tasks."""
    database = get_database()
    return database["scheduler_locks"] if database is not None else None

def get_irrigation_advisories_history_collection():
    """Returns the 'irrigation_advisories_history' collection for tracking advisory transitions."""
    database = get_database()
    return database["irrigation_advisories_history"] if database is not None else None


def get_market_prices_cache_collection():
    """Returns the 'market_prices_cache' collection for Agmarknet/data.gov.in records."""
    database = get_database()
    return database["market_prices_cache"] if database is not None else None

def get_market_prices_meta_collection():
    """Returns the 'market_prices_meta' collection for tracking fetch timestamps and source status."""
    database = get_database()
    return database["market_prices_meta"] if database is not None else None


def get_farmer_support_collection():
    """Returns the 'farmer_support_content' collection for official agricultural guidance."""
    database = get_database()
    return database["farmer_support_content"] if database is not None else None


def get_farmer_marketplace_collection():
    """Returns the 'farmer_marketplace_listings' collection for farmer direct produce listings."""
    database = get_database()
    return database["farmer_marketplace_listings"] if database is not None else None


def get_farmer_marketplace_orders_collection():
    """Returns the 'farmer_marketplace_orders' collection for buyer direct order requests."""
    database = get_database()
    return database["farmer_marketplace_orders"] if database is not None else None


def get_special_operation_journeys_collection():
    """Returns the 'special_operation_journeys' collection for guided beginner farming journeys."""
    database = get_database()
    return database["special_operation_journeys"] if database is not None else None


def get_farmer_business_plans_collection():
    """Returns the 'farmer_business_plans' collection for agri-entrepreneurship planning wizard."""
    database = get_database()
    return database["farmer_business_plans"] if database is not None else None


async def init_database_indexes():
    """
    Idempotently creates necessary MongoDB indexes for query performance,
    uniqueness, and operational safety. Safe to rerun at startup.
    """
    db = get_database()
    if db is None:
        return

    try:
        # Users indexes
        await db["users"].create_index([("phone", 1), ("role", 1)])
        
        # Farmers indexes
        await db["farmers"].create_index([("farmerId", 1)], sparse=True)
        await db["farmers"].create_index([("phone", 1)])
        await db["farmers"].create_index([("userId", 1)], sparse=True)

        # Procurement Bookings indexes
        await db["procurement_bookings"].create_index([("bookingId", 1)], unique=True, sparse=True)
        await db["procurement_bookings"].create_index([("tokenNumber", 1)])
        await db["procurement_bookings"].create_index([("centreCode", 1), ("slotDate", 1), ("timeWindow", 1), ("status", 1)])
        await db["procurement_bookings"].create_index([("farmerId", 1), ("slotDate", 1)])

        # Procurement Centres indexes
        await db["procurement_centres"].create_index([("centreCode", 1)], unique=True, sparse=True)

        # Procurement Bills indexes
        await db["procurement_bills"].create_index([("billNumber", 1)], unique=True, sparse=True)
        await db["procurement_bills"].create_index([("bookingId", 1)], sparse=True)
        await db["procurement_bills"].create_index([("farmerId", 1)])

        # Slot Closures indexes
        await db["slot_closures"].create_index([("centreCode", 1), ("slotDate", 1), ("timeWindow", 1)], unique=True, sparse=True)

        # Rates indexes
        await db["procurement_rates"].create_index([("crop", 1), ("centreCode", 1)], unique=True, sparse=True)

        # Rate Limits indexes
        await db["rate_limits"].create_index([("key", 1)], unique=True, sparse=True)

        # Notifications & Diagnosis Reports indexes
        await db["notifications"].create_index([("userId", 1), ("createdAt", -1)], sparse=True)
        await db["notifications"].create_index([("dedupKey", 1)], sparse=True)
        await db["diagnosis_reports"].create_index([("userId", 1), ("createdAt", -1)], sparse=True)

        # Phase 3: Notification Preferences & Push Subscriptions
        await db["notification_preferences"].create_index([("userId", 1)], unique=True, sparse=True)
        await db["push_subscriptions"].create_index([("userId", 1)], sparse=True)
        await db["scheduler_locks"].create_index([("jobName", 1)], unique=True, sparse=True)
        await db["irrigation_advisories_history"].create_index([("userId", 1), ("isoTimestamp", -1)], sparse=True)

        # Government Schemes indexes
        await db["government_schemes"].create_index([("id", 1)], unique=True, sparse=True)
        await db["government_schemes"].create_index([("category", 1)])
        await db["government_schemes"].create_index([("governmentLevel", 1)])

        # Market Mandi Prices Cache indexes
        await db["market_prices_cache"].create_index([("district", 1), ("commodity", 1), ("arrival_date", -1)], sparse=True)
        await db["market_prices_cache"].create_index([("recordId", 1)], unique=True, sparse=True)
        await db["market_prices_cache"].create_index([("cachedAt", -1)], sparse=True)
        await db["market_prices_meta"].create_index([("metaKey", 1)], unique=True, sparse=True)

        # Farmer Support Content indexes (Features 1-6)
        await db["farmer_support_content"].create_index([("contentId", 1)], unique=True, sparse=True)
        await db["farmer_support_content"].create_index([("category", 1), ("activeStatus", 1), ("district", 1)], sparse=True)
        await db["farmer_support_content"].create_index([("trainingMeta.endDate", 1), ("activeStatus", 1)], sparse=True)
        await db["farmer_support_content"].create_index([("lastCheckedDate", 1)], sparse=True)

        # Farmer Marketplace Listings indexes (Feature 7)
        await db["farmer_marketplace_listings"].create_index([("listingId", 1)], unique=True, sparse=True)
        await db["farmer_marketplace_listings"].create_index([("farmerId", 1), ("listingStatus", 1)], sparse=True)
        await db["farmer_marketplace_listings"].create_index([("district", 1), ("category", 1), ("listingStatus", 1)], sparse=True)
        await db["farmer_marketplace_listings"].create_index([("availableUntil", 1)], sparse=True)
        await db["farmer_marketplace_listings"].create_index([("createdAt", -1)], sparse=True)

        # Farmer Marketplace Orders indexes (Feature 7)
        await db["farmer_marketplace_orders"].create_index([("orderId", 1)], unique=True, sparse=True)
        await db["farmer_marketplace_orders"].create_index([("farmerId", 1), ("status", 1)], sparse=True)
        await db["farmer_marketplace_orders"].create_index([("listingId", 1)], sparse=True)
        await db["farmer_marketplace_orders"].create_index([("createdAt", -1)], sparse=True)

        # Special Operation Beginner Journeys
        await db["special_operation_journeys"].create_index([("journeyId", 1)], unique=True, sparse=True)
        await db["special_operation_journeys"].create_index([("farmerId", 1), ("status", 1)], sparse=True)
        await db["special_operation_journeys"].create_index([("updatedAt", -1)], sparse=True)

        # Farmer Business Plans (Agri Entrepreneurship)
        await db["farmer_business_plans"].create_index([("planId", 1)], unique=True, sparse=True)
        await db["farmer_business_plans"].create_index([("farmerId", 1), ("createdAt", -1)], sparse=True)
    except Exception as e:
        safe_msg = sanitize_mongo_uri(str(e))
        print(f"[Warning] Index initialization notice: {safe_msg}")



