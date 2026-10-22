"""
Database configuration and MongoDB connection management using Motor (async driver).
"""

import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

import urllib.parse
import re

# Load environment variables from .env
load_dotenv()

def get_mongo_connection_info() -> dict:
    """
    Inspects environment variables for MongoDB connection strings.
    Prioritizes 'MONGODB_URI' while also checking common cloud aliases,
    whitespace-padded keys, and any variable containing a mongodb:// or mongodb+srv:// URI.
    Returns a dictionary containing the sanitized URI, target host, source key, and flags.
    Never exposes username or password.
    """
    target_raw_uri = None
    detected_key = None

    # Priority 1: Direct MONGODB_URI check
    direct_val = os.getenv("MONGODB_URI")
    if direct_val and str(direct_val).strip():
        cleaned = str(direct_val).strip().strip("\"'").strip()
        if cleaned:
            target_raw_uri = cleaned
            detected_key = "MONGODB_URI"

    # Priority 2: Key-stripped / case-insensitive search for known aliases
    if not target_raw_uri:
        known_aliases = (
            "MONGODB_URI",
            "MONGO_URI",
            "MONGO_URL",
            "DATABASE_URL",
            "MONGODB_URL",
            "DATABASE_URI",
            "MONGODB_CONNECTION_STRING",
            "ATLAS_URI",
        )
        for k, v in os.environ.items():
            if k.strip().upper() in known_aliases:
                cleaned = str(v).strip().strip("\"'").strip()
                if cleaned and (cleaned.startswith("mongodb://") or cleaned.startswith("mongodb+srv://")):
                    target_raw_uri = cleaned
                    detected_key = k.strip()
                    break

    # Priority 3: Any environment variable whose value is a valid MongoDB connection string
    if not target_raw_uri:
        for k, v in os.environ.items():
            cleaned = str(v).strip().strip("\"'").strip()
            if cleaned and (cleaned.startswith("mongodb://") or cleaned.startswith("mongodb+srv://")):
                target_raw_uri = cleaned
                detected_key = k.strip()
                break

    is_configured = target_raw_uri is not None
    is_cloud = bool(os.getenv("RENDER") or os.getenv("PORT") or os.getenv("ENVIRONMENT") == "production")

    if not target_raw_uri:
        target_raw_uri = "mongodb://localhost:27017"
        detected_key = "default_fallback (localhost:27017)"

    # Safely extract target host without leaking credentials
    target_host = "localhost:27017"
    try:
        if "@" in target_raw_uri:
            after_at = target_raw_uri.rsplit("@", 1)[1]
            host_part = after_at.split("/")[0].split("?")[0]
            target_host = host_part.strip()
        elif "://" in target_raw_uri:
            after_scheme = target_raw_uri.split("://", 1)[1]
            host_part = after_scheme.split("/")[0].split("?")[0]
            target_host = host_part.strip()
    except Exception:
        target_host = "unknown_host"

    is_atlas = "mongodb+srv" in target_raw_uri or ".mongodb.net" in target_raw_uri

    return {
        "raw_uri": target_raw_uri,
        "is_configured": is_configured,
        "source_key": detected_key,
        "target_host": target_host,
        "is_atlas": is_atlas,
        "is_cloud": is_cloud,
    }

def get_configured_mongo_uri() -> str:
    """
    Retrieves the MongoDB URI from supported environment variables,
    stripping enclosing quotes and whitespace. Falls back to localhost.
    """
    return get_mongo_connection_info()["raw_uri"]

def get_configured_db_name() -> str:
    """
    Retrieves the database name from supported environment variables.
    """
    for key in ("MONGODB_DB_NAME", "MONGO_DB_NAME", "DATABASE_NAME"):
        val = os.getenv(key)
        if val and str(val).strip():
            cleaned = str(val).strip().strip("\"'").strip()
            if cleaned:
                return cleaned
    return "namma_vivasayi_db"

MONGODB_URI = get_configured_mongo_uri()
MONGODB_DB_NAME = get_configured_db_name()

client: AsyncIOMotorClient = None
db = None

def get_database():
    """Returns the database instance."""
    global db
    if db is None:
        init_db()
    return db

def sanitize_mongo_uri(raw_err: str) -> str:
    """Removes user:password credentials from raw MongoDB connection error strings."""
    if not raw_err:
        return "Unknown error"
    # Redact mongodb://user:pass@ and mongodb+srv://user:pass@
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:[REDACTED]@", str(raw_err))

def format_mongo_uri(raw_uri: str) -> str:
    """
    Ensures username and password in MongoDB URI are RFC 3986 escaped using urllib.parse.quote_plus.
    Handles special characters like '@', ':', '#', etc., in passwords while preserving host, path, and options.
    """
    if not raw_uri:
        return raw_uri
    cleaned_uri = str(raw_uri).strip().strip("\"'").strip()
    if "://" not in cleaned_uri:
        return cleaned_uri

    try:
        prefix, rest = cleaned_uri.split("://", 1)
        if "@" not in rest:
            return f"{prefix}://{rest}"

        # Separate authority (credentials + host/port) from path and query parameters
        path_idx = -1
        for idx, ch in enumerate(rest):
            if ch in ("/", "?"):
                path_idx = idx
                break

        if path_idx != -1:
            authority = rest[:path_idx]
            path_and_query = rest[path_idx:]
        else:
            authority = rest
            path_and_query = ""

        if "@" not in authority:
            return f"{prefix}://{rest}"

        # Right-split on '@' to isolate host from credentials
        creds, host = authority.rsplit("@", 1)
        if ":" in creds:
            user, pwd = creds.split(":", 1)
            # Unquote first to prevent double-encoding, then re-quote per RFC 3986
            safe_user = urllib.parse.quote_plus(urllib.parse.unquote_plus(user))
            safe_pwd = urllib.parse.quote_plus(urllib.parse.unquote_plus(pwd))
            fixed_creds = f"{safe_user}:{safe_pwd}"
        else:
            fixed_creds = urllib.parse.quote_plus(urllib.parse.unquote_plus(creds))

        return f"{prefix}://{fixed_creds}@{host}{path_and_query}"
    except Exception:
        return cleaned_uri

def init_db():
    """Initializes the MongoDB client and database connection."""
    global client, db
    try:
        info = get_mongo_connection_info()
        raw_uri = info["raw_uri"]
        db_name = get_configured_db_name()
        safe_uri = format_mongo_uri(raw_uri)
        client = AsyncIOMotorClient(
            safe_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        db = client[db_name]
    except Exception as e:
        safe_err = sanitize_mongo_uri(str(e))
        print(f"[Warning] Failed to initialize MongoDB client: {safe_err}")
        db = None

async def check_db_connection() -> dict:
    """
    Checks whether MongoDB is alive and responsive.
    Returns status dict with connection info, without exposing secrets.
    """
    global client
    if client is None:
        init_db()

    info = get_mongo_connection_info()
    active_db_name = get_configured_db_name()
    target_host = info["target_host"]
    is_atlas = info["is_atlas"]
    is_configured = info["is_configured"]
    source_key = info["source_key"]

    # In cloud environments (Render / production), warn if environment variable is missing
    if info["is_cloud"] and not is_configured:
        return {
            "connected": False,
            "database_name": active_db_name,
            "is_atlas": False,
            "is_configured": False,
            "source_key": source_key,
            "target_host": target_host,
            "message": "MONGODB_URI environment variable is missing on Render. Please configure MONGODB_URI in Render dashboard and redeploy.",
            "render_action_required": "Go to Render Dashboard -> Web Service -> Environment -> Add MONGODB_URI.",
        }

    if client is None:
        return {
            "connected": False,
            "database_name": active_db_name,
            "is_atlas": is_atlas,
            "is_configured": is_configured,
            "source_key": source_key,
            "target_host": target_host,
            "message": "Database client could not be initialized.",
        }

    try:
        # Ping the admin database to verify connectivity
        await client.admin.command('ping')
        return {
            "connected": True,
            "database_name": active_db_name,
            "is_atlas": is_atlas,
            "is_configured": is_configured,
            "source_key": source_key,
            "target_host": target_host,
            "message": f"Connected to MongoDB successfully at {target_host}."
        }
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        safe_msg = sanitize_mongo_uri(str(e))
        action = "Check MongoDB Atlas Network Access (whitelist 0.0.0.0/0)" if is_atlas else "Check if local MongoDB service is running"
        return {
            "connected": False,
            "database_name": active_db_name,
            "is_atlas": is_atlas,
            "is_configured": is_configured,
            "source_key": source_key,
            "target_host": target_host,
            "message": f"Could not connect to MongoDB ({target_host}): {safe_msg}",
            "render_action_required": action,
        }
    except Exception as e:
        safe_msg = sanitize_mongo_uri(str(e))
        return {
            "connected": False,
            "database_name": active_db_name,
            "is_atlas": is_atlas,
            "is_configured": is_configured,
            "source_key": source_key,
            "target_host": target_host,
            "message": f"Database error ({target_host}): {safe_msg}",
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



