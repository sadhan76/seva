"""
Namma Vivasayi AI - Isolated Demo Environment Seeder
Safely populates an ISOLATED demonstration database with fictional test fixtures.
DO NOT use on real production databases.
"""

import os
import sys
import asyncio
import argparse
from datetime import date, timedelta, datetime
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

# Predefined Fictional Demo Accounts (Marked as FICTIONAL)
DEMO_FARMER = {
    "name": "Murugesan K.",
    "phone": "9876543299",
    "password": "FarmerPassword@123",
    "role": "farmer",
    "farmerId": "TN-AGRI-2026-9281",
    "village": "Pillaiyarpatti",
    "district": "Thanjavur",
    "state": "Tamil Nadu",
    "totalLandAcres": 4.5,
    "primaryCrop": "Paddy Grade A (CR 1009 Sub-1)",
    "soilType": "Clay Loam",
    "irrigationSource": "Canal + Borewell",
    "aadhaarMasked": "XXXX-XXXX-4410",
    "preferredLanguage": "ta"
}

DEMO_STAFF = {
    "name": "Ramesh Kumar (Procurement Inspector)",
    "phone": "9842012345",
    "password": "MandiStaff@2026",
    "role": "staff",
    "mandiName": "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)",
    "district": "Thanjavur",
    "state": "Tamil Nadu",
    "preferredLanguage": "en"
}

DEMO_CENTRES = [
    {
        "centreCode": "TNJ-DPC-01",
        "name": "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)",
        "district": "Thanjavur",
        "supportedCrops": ["Paddy Grade A", "Paddy Common", "Kuruvai Paddy", "Black Gram (உளுந்து ADT-5)"],
        "operatingHours": "08:30 AM - 05:30 PM",
        "slotWindows": ["08:30 AM - 11:30 AM", "11:30 AM - 02:30 PM", "02:30 PM - 05:30 PM"],
        "maxCapacityBagsPerSlot": 250,
        "counters": ["Counter-1", "Counter-2", "Counter-3"],
        "address": "Near Pillaiyarpatti Bus Stop, Vallam Road, Thanjavur — 613403",
        "isActive": True
    },
    {
        "centreCode": "MDU-MKT-03",
        "name": "Madurai Regulated Agricultural Market (Mattuthavani)",
        "district": "Madurai",
        "supportedCrops": ["Paddy Common", "Maize", "Cotton", "Groundnut"],
        "operatingHours": "08:00 AM - 05:00 PM",
        "slotWindows": ["08:00 AM - 11:00 AM", "11:00 AM - 02:00 PM", "02:00 PM - 05:00 PM"],
        "maxCapacityBagsPerSlot": 200,
        "counters": ["Counter-1", "Counter-2"],
        "address": "Mattuthavani Market Complex, Madurai — 625007",
        "isActive": True
    }
]

DEMO_RATES = [
    {
        "rateId": "RATE-TNJ-PADDY-A",
        "crop": "Paddy Grade A",
        "cropVariety": "CR 1009 Sub-1",
        "centreCode": "ALL",
        "mandiName": "All Direct Procurement Centres",
        "ratePerKg": 24.50,
        "ratePerQuintal": 2450.00,
        "effectiveFrom": "2026-01-01",
        "effectiveTo": "2026-12-31",
        "sourceLabel": "Government of India MSP 2025-26 + TN State Incentive",
        "isActive": True
    }
]


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


async def seed_demo_database(mongo_uri: str, db_name: str, force: bool = False):
    print("=" * 80)
    print("NAMMA VIVASAYI AI - ISOLATED DEMO ENVIRONMENT SEEDER")
    print("=" * 80)

    # 1. Safety verification
    env_mode = os.getenv("ENVIRONMENT", "development").lower()
    if env_mode == "production" and not force:
        print("[SAFETY ERROR] Target environment is marked as 'production'.")
        print("Refusing to seed demonstration fixtures into production.")
        print("To override for dedicated staging/demo, pass --force.")
        sys.exit(1)

    print(f"[*] Target MongoDB URI: {mongo_uri.split('@')[-1] if '@' in mongo_uri else mongo_uri}")
    print(f"[*] Target Isolated Database Name: '{db_name}'")

    client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]

    # Verify connectivity
    try:
        await client.admin.command("ping")
        print("[OK] Connected to MongoDB engine successfully.")
    except Exception as e:
        print(f"[ERROR] Could not connect to MongoDB: {e}")
        sys.exit(1)

    # 2. Seed Fictional Users
    print("\n--- [1] Seeding Fictional Demonstration Accounts ---")
    users_col = db["users"]
    farmers_col = db["farmers"]

    # Index users
    await users_col.create_index("phone", unique=True, sparse=True)

    # Seed Farmer
    f_existing = await users_col.find_one({"phone": DEMO_FARMER["phone"]})
    f_hash = hash_password(DEMO_FARMER["password"])
    if not f_existing:
        f_doc = {**DEMO_FARMER, "hashed_password": f_hash, "isDemoAccount": True, "createdAt": datetime.utcnow().strftime("%d %b %Y")}
        f_doc.pop("password", None)
        await users_col.insert_one(f_doc)
        await farmers_col.update_one({"phone": DEMO_FARMER["phone"]}, {"$set": f_doc}, upsert=True)
        print(f"  [+] Created Demo Farmer: {DEMO_FARMER['name']} ({DEMO_FARMER['phone']})")
    else:
        await users_col.update_one({"phone": DEMO_FARMER["phone"]}, {"$set": {"hashed_password": f_hash, "isDemoAccount": True}})
        print(f"  [*] Updated Demo Farmer: {DEMO_FARMER['name']} ({DEMO_FARMER['phone']})")

    # Seed Staff
    s_existing = await users_col.find_one({"phone": DEMO_STAFF["phone"]})
    s_hash = hash_password(DEMO_STAFF["password"])
    if not s_existing:
        s_doc = {**DEMO_STAFF, "hashed_password": s_hash, "isDemoAccount": True, "createdAt": datetime.utcnow().strftime("%d %b %Y")}
        s_doc.pop("password", None)
        await users_col.insert_one(s_doc)
        print(f"  [+] Created Demo Staff: {DEMO_STAFF['name']} ({DEMO_STAFF['phone']})")
    else:
        await users_col.update_one({"phone": DEMO_STAFF["phone"]}, {"$set": {"hashed_password": s_hash, "isDemoAccount": True}})
        print(f"  [*] Updated Demo Staff: {DEMO_STAFF['name']} ({DEMO_STAFF['phone']})")

    # 3. Seed Procurement Centres
    print("\n--- [2] Seeding Procurement Centres & MSP Rates ---")
    centres_col = db["procurement_centres"]
    for c in DEMO_CENTRES:
        await centres_col.update_one({"centreCode": c["centreCode"]}, {"$set": c}, upsert=True)
    print(f"  [+] Seeded {len(DEMO_CENTRES)} Direct Procurement Centres.")

    rates_col = db["procurement_rates"]
    for r in DEMO_RATES:
        await rates_col.update_one({"rateId": r["rateId"]}, {"$set": r}, upsert=True)
    print(f"  [+] Seeded {len(DEMO_RATES)} Benchmark Procurement Rates.")

    # 4. Seed Fictional Procurement Journey Records
    print("\n--- [3] Seeding Fictional Demonstration Workflow Records ---")
    bookings_col = db["procurement_bookings"]
    bills_col = db["procurement_bills"]

    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    now_human = datetime.utcnow().strftime("%d %b %Y, %I:%M %p")

    # Booking 1: Fully Completed with Digital Bill & Paid DBT Status
    b1_id = "PROC-TNJ-2026-DEMO01"
    bill1_num = "BILL-TNJ-2026-DEMO01"
    b1_doc = {
        "bookingId": b1_id,
        "tokenNumber": "TN-DPC-901",
        "farmerId": DEMO_FARMER["farmerId"],
        "farmerName": DEMO_FARMER["name"],
        "farmerPhone": DEMO_FARMER["phone"],
        "mandiName": DEMO_STAFF["mandiName"],
        "centreCode": "TNJ-DPC-01",
        "crop": "Paddy Grade A",
        "cropVariety": "CR 1009 Sub-1",
        "quantityBags": 25,
        "slotDate": today_str,
        "timeWindow": "08:30 AM - 11:30 AM",
        "status": "COMPLETED",
        "stageNumber": 5,
        "qualityStatus": "ACCEPTED",
        "qualityGrade": "Grade A FAQ",
        "moisturePercent": 15.2,
        "acceptedWeightKg": 1000.0,
        "billNumber": bill1_num,
        "paymentStatus": "PAID",
        "isDemoRecord": True,
        "createdAt": now_human,
        "updatedAt": now_human
    }
    await bookings_col.update_one({"bookingId": b1_id}, {"$set": b1_doc}, upsert=True)

    bill1_doc = {
        "billNumber": bill1_num,
        "bookingId": b1_id,
        "farmerId": DEMO_FARMER["farmerId"],
        "farmerName": DEMO_FARMER["name"],
        "mandiName": DEMO_STAFF["mandiName"],
        "centreCode": "TNJ-DPC-01",
        "crop": "Paddy Grade A",
        "cropVariety": "CR 1009 Sub-1",
        "grossWeightKg": 1000.0,
        "acceptedWeightKg": 1000.0,
        "ratePerKg": 24.50,
        "grossAmount": 24500.00,
        "totalDeductionsAmount": 200.00,
        "netAmount": 24300.00,
        "paymentStatus": "PAID",
        "transactionReference": "PFMS-TN-2026-DEMO-001",
        "date": today_str,
        "isDemoRecord": True,
        "createdAt": now_human,
        "updatedAt": now_human
    }
    await bills_col.update_one({"billNumber": bill1_num}, {"$set": bill1_doc}, upsert=True)
    print(f"  [+] Seeded Completed Booking & Bill: {bill1_num} (Net: ₹24,300.00, PAID)")

    # Booking 2: Checked In & Ready in Quality Inspection / Queue
    b2_id = "PROC-TNJ-2026-DEMO02"
    b2_doc = {
        "bookingId": b2_id,
        "tokenNumber": "TN-DPC-902",
        "farmerId": DEMO_FARMER["farmerId"],
        "farmerName": DEMO_FARMER["name"],
        "farmerPhone": DEMO_FARMER["phone"],
        "mandiName": DEMO_STAFF["mandiName"],
        "centreCode": "TNJ-DPC-01",
        "crop": "Paddy Grade A",
        "cropVariety": "CR 1009 Sub-1",
        "quantityBags": 20,
        "slotDate": today_str,
        "timeWindow": "08:30 AM - 11:30 AM",
        "status": "QUALITY_CHECKED",
        "stageNumber": 3,
        "qualityStatus": "ACCEPTED",
        "qualityGrade": "Grade A FAQ",
        "moisturePercent": 14.8,
        "acceptedWeightKg": 800.0,
        "isNowServing": False,
        "isDemoRecord": True,
        "createdAt": now_human,
        "updatedAt": now_human
    }
    await bookings_col.update_one({"bookingId": b2_id}, {"$set": b2_doc}, upsert=True)
    print(f"  [+] Seeded Queue-Ready Booking: {b2_id} (Token: TN-DPC-902, QUALITY_CHECKED)")

    # Booking 3: Newly Booked for Tomorrow (Ready to demonstrate Gate Check-In)
    b3_id = "PROC-TNJ-2026-DEMO03"
    b3_doc = {
        "bookingId": b3_id,
        "tokenNumber": "TN-DPC-903",
        "farmerId": DEMO_FARMER["farmerId"],
        "farmerName": DEMO_FARMER["name"],
        "farmerPhone": DEMO_FARMER["phone"],
        "mandiName": DEMO_STAFF["mandiName"],
        "centreCode": "TNJ-DPC-01",
        "crop": "Paddy Grade A",
        "cropVariety": "CR 1009 Sub-1",
        "quantityBags": 30,
        "slotDate": tomorrow_str,
        "timeWindow": "08:30 AM - 11:30 AM",
        "status": "BOOKED",
        "stageNumber": 1,
        "isNowServing": False,
        "isDemoRecord": True,
        "createdAt": now_human,
        "updatedAt": now_human
    }
    await bookings_col.update_one({"bookingId": b3_id}, {"$set": b3_doc}, upsert=True)
    print(f"  [+] Seeded Arrival-Ready Booking: {b3_id} (Token: TN-DPC-903, BOOKED)")

    # 5. Verify Authentication Capabilities
    print("\n--- [4] Verifying Demo Account Authentication ---")
    farmer_check = await users_col.find_one({"phone": DEMO_FARMER["phone"]})
    assert farmer_check and verify_password(DEMO_FARMER["password"], farmer_check["hashed_password"])
    print(f"  [OK] Farmer Auth Verified: '{DEMO_FARMER['name']}' can authenticate.")

    staff_check = await users_col.find_one({"phone": DEMO_STAFF["phone"]})
    assert staff_check and verify_password(DEMO_STAFF["password"], staff_check["hashed_password"])
    print(f"  [OK] Staff Auth Verified: '{DEMO_STAFF['name']}' can authenticate.")

    print("\n" + "=" * 80)
    print(f"ISOLATED DEMO ENVIRONMENT READY IN DATABASE: '{db_name}'")
    print("=" * 80)
    print("\nDemo Login Credentials (FICTIONAL TEST FIXTURES):")
    print(f"  * Farmer: Phone={DEMO_FARMER['phone']}, Password={DEMO_FARMER['password']}")
    print(f"  * Staff:  Phone={DEMO_STAFF['phone']}, Password={DEMO_STAFF['password']}")
    print("\nTo point backend to this demo database:")
    print(f"  Set in backend/.env: MONGODB_DB_NAME={db_name}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed isolated demo environment for Namma Vivasayi AI")
    parser.add_argument("--uri", default=os.getenv("MONGODB_URI", "mongodb://localhost:27017"), help="MongoDB connection URI")
    parser.add_argument("--db-name", default=os.getenv("MONGODB_DEMO_DB_NAME", "namma_vivasayi_demo_db"), help="Target demo database name")
    parser.add_argument("--force", action="store_true", help="Force seeding even if ENVIRONMENT=production")
    args = parser.parse_args()

    asyncio.run(seed_demo_database(mongo_uri=args.uri, db_name=args.db_name, force=args.force))
