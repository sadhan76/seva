"""
Idempotent Seeder for Government Welfare Schemes Database (Phase 9)
===================================================================
Seeds and updates verified Central and Tamil Nadu State agricultural
and livestock schemes from 'backend/data/government_schemes.json'
into the MongoDB 'government_schemes' collection.

Safety Guarantees:
- Idempotent upsert by 'id': Rerunning never produces duplicates.
- Never deletes or modifies users, farmers, bookings, bills, or audit records.
- Supports target database override via --db-name flag.
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Ensure root backend dir is in sys.path
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DEFAULT_DB_NAME = os.getenv("MONGODB_DB_NAME", "namma_vivasayi_db")
SCHEMES_JSON_PATH = Path(__file__).parent / "data" / "government_schemes.json"

async def seed_government_schemes(db_name: str = DEFAULT_DB_NAME):
    print("=" * 70)
    print("SEVA: GOVERNMENT WELFARE SCHEMES DATABASE SEEDER (PHASE 9)")
    print("=" * 70)
    print(f"Target Database : {db_name}")
    print(f"Dataset Path    : {SCHEMES_JSON_PATH}")

    if not SCHEMES_JSON_PATH.exists():
        print(f"[Error] Schemes dataset file not found: {SCHEMES_JSON_PATH}")
        sys.exit(1)

    with open(SCHEMES_JSON_PATH, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    print(f"Loaded {len(schemes)} schemes from verified JSON source.")

    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[db_name]

    # Verify connection
    try:
        await client.admin.command("ping")
        print("[OK] Connected to MongoDB.")
    except Exception as e:
        print(f"[Error] MongoDB connection failed: {e}")
        sys.exit(1)

    coll = db["government_schemes"]

    # Ensure index on 'id'
    await coll.create_index([("id", 1)], unique=True, sparse=True)
    await coll.create_index([("category", 1)])
    await coll.create_index([("governmentLevel", 1)])

    inserted_count = 0
    updated_count = 0
    categories = {}

    for s in schemes:
        cat = s.get("category", "Uncategorized")
        categories[cat] = categories.get(cat, 0) + 1

        # Preserve legacy compatibility fields
        if "titleEn" not in s:
            s["titleEn"] = s.get("name", "")
        if "titleTa" not in s:
            s["titleTa"] = s.get("nameTa", "")
        if "dept" not in s:
            s["dept"] = s.get("department", "")
        if "benefit" not in s:
            benefits_list = s.get("benefits", [])
            s["benefit"] = " ".join(benefits_list) if isinstance(benefits_list, list) else str(benefits_list)
        if "isVerifiedLink" not in s:
            s["isVerifiedLink"] = True

        result = await coll.update_one(
            {"id": s["id"]},
            {"$set": s},
            upsert=True
        )

        if result.upserted_id:
            inserted_count += 1
        else:
            updated_count += 1

    total_in_db = await coll.count_documents({})

    print("\n--- Seeding Summary ---")
    print(f"New Records Inserted : {inserted_count}")
    print(f"Records Updated      : {updated_count}")
    print(f"Total in Database    : {total_in_db}")
    print("\n--- Breakdown by Category ---")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat.ljust(22)}: {count} schemes")

    print("\n[OK] Government schemes database successfully seeded and synchronized!")
    client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed government schemes into MongoDB.")
    parser.add_argument("--db", "--db-name", dest="db_name", type=str, default=DEFAULT_DB_NAME, help="Target database name (default: from MONGODB_DB_NAME)")
    args = parser.parse_args()

    asyncio.run(seed_government_schemes(db_name=args.db_name))
