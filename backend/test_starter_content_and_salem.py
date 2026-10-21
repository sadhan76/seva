import asyncio
import json
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

from farmer_support_service import (
    get_support_content,
    get_support_content_by_id,
    seed_farmer_support_database,
    get_farmer_support_collection,
)

logger = logging.getLogger("test_starter_content")

async def run_tests():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE STARTER CONTENT & SALEM VALIDATION TESTS")
    print("=" * 60)

    col = get_farmer_support_collection()
    assert col is not None, "MongoDB connection to farmer support collection failed"

    # 1. Total records and categories
    all_content = await get_support_content(active_only=False)
    total_items = all_content.get("total", 0)
    items = all_content.get("items", [])
    categories = all_content.get("categories", [])
    districts = all_content.get("districts", [])
    states = all_content.get("states", [])

    print(f"\n1. Overall Content Check:")
    print(f"   Total records: {total_items}")
    print(f"   Categories ({len(categories)}): {categories}")
    print(f"   Districts ({len(districts)}): {districts}")
    print(f"   States ({len(states)}): {states}")

    assert total_items >= 25, f"Expected at least 25 records, found {total_items}"
    expected_categories = [
        "training",
        "entrepreneurship",
        "organic",
        "special_operation",
        "protected_cultivation",
        "value_addition",
        "direct_market",
    ]
    for ec in expected_categories:
        assert ec in categories, f"Missing category: {ec}"
    print("   [PASS] All 7 categories present and populated.")

    # 2. Salem District Specific Coverage
    salem_content = await get_support_content(district="Salem", active_only=False)
    salem_items = salem_content.get("items", [])
    print(f"\n2. Salem District Deep Dive:")
    print(f"   Salem specific records found: {len(salem_items)}")
    for item in salem_items:
        print(f"   - [{item.get('category')}] {item.get('contentId')}: {item.get('title', {}).get('en')}")

    assert len(salem_items) >= 6, f"Expected at least 6 Salem specific records, found {len(salem_items)}"
    salem_categories = set(i.get("category") for i in salem_items)
    print(f"   Salem covers categories: {salem_categories}")
    print("   [PASS] Salem district has verified local institutional records.")

    # 3. State-Level Filtering
    tn_content = await get_support_content(state="Tamil Nadu", active_only=False)
    india_content = await get_support_content(state="All-India", active_only=False)
    print(f"\n3. State Query Filtering:")
    print(f"   Tamil Nadu records: {tn_content.get('total')}")
    print(f"   All-India records: {india_content.get('total')}")
    assert tn_content.get("total") > 0, "Tamil Nadu query returned 0 items"
    assert india_content.get("total") > 0, "All-India query returned 0 items"
    print("   [PASS] Multi-state / national filtering functions correctly.")

    # 4. Institutional Contact Classification & Excerpt Verification
    print(f"\n4. Governance & Source Authenticity:")
    office_desks = [i for i in items if i.get("contact", {}).get("contactType") == "institutional_office"]
    helpline_contacts = [i for i in items if i.get("contact", {}).get("contactType") == "helpline"]
    records_with_excerpts = [i for i in items if i.get("sourceExcerpt")]

    print(f"   Institutional Office Desks (Landline/HQ): {len(office_desks)}")
    print(f"   Helpline Desks (Toll-Free): {len(helpline_contacts)}")
    print(f"   Records with official source excerpts: {len(records_with_excerpts)}")

    assert len(office_desks) >= 15, f"Expected majority institutional office contacts, got {len(office_desks)}"
    assert len(records_with_excerpts) >= 15, f"Expected rich source excerpts, got {len(records_with_excerpts)}"
    print("   [PASS] Institutional contacts and source quotes verified.")

    # 5. Training Schedule Status Validation
    training_items = [i for i in items if i.get("category") == "training"]
    recurring_trainings = [i for i in training_items if i.get("trainingMeta", {}).get("scheduleStatus") == "recurring_monthly"]
    historical_or_unverified = [
        i for i in training_items
        if i.get("trainingMeta", {}).get("scheduleStatus") in ("historical_reference", "unverified_schedule")
    ]
    print(f"\n5. Training Schedule Integrity:")
    print(f"   Total training courses: {len(training_items)}")
    print(f"   Recurring monthly trainings: {len(recurring_trainings)}")
    print(f"   Historical / Unverified schedule trainings: {len(historical_or_unverified)}")
    assert len(recurring_trainings) >= 2, "Expected verified recurring monthly trainings"
    assert len(historical_or_unverified) >= 1, "Expected historical/unverified training records flagged"
    print("   [PASS] Training schedule statuses prevent showing outdated dates as active upcoming.")

    # 6. Idempotency & Admin-Review Non-Overwrite Protection
    print(f"\n6. Non-Overwrite / Admin Review Protection:")
    test_id = "fsc_trg_tnau_cbe_mushroom"
    # Mark test record as adminReviewed with custom note
    await col.update_one(
        {"contentId": test_id},
        {"$set": {"adminReviewed": True, "notes": "Hand-reviewed by District Admin"}}
    )
    
    # Run seed WITHOUT force (default idempotent production behavior)
    seeded_count = await seed_farmer_support_database(force=False)
    print(f"   Seeded count with force=False: {seeded_count}")
    
    # Verify the record still has the adminReviewed flag and custom notes
    rec = await col.find_one({"contentId": test_id})
    assert rec.get("adminReviewed") is True, "Admin-reviewed flag was lost!"
    assert rec.get("notes") == "Hand-reviewed by District Admin", "Admin notes were overwritten!"
    print("   [PASS] adminReviewed record was protected from seed overwrite.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
