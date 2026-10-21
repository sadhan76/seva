"""
COMPREHENSIVE AUTOMATED TEST SUITE: FARMER SUPPORT & DIRECT MARKETPLACE
======================================================================
Tests:
1. Seed synchronization & category retrieval for all 6 support categories.
2. Training calendar query, mode filtering, and auto-expiration sweeper.
3. Special Operation: Beginner-to-market crop lifecycle guide retrieval.
4. Stale contact auditing and nodal officer review workflow.
5. Marketplace listing creation, filtering (category, district, organic), and inquiry tracking.
6. Strict farmer data ownership defense (Farmer isolation on edit/delete).
7. Admin moderation of marketplace listings.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from database import init_database_indexes, get_farmer_support_collection, get_farmer_marketplace_collection
from farmer_support_service import (
    seed_farmer_support_database,
    get_support_content,
    get_support_content_by_id,
    get_training_calendar,
    get_crop_master_guide,
    auto_expire_training_notices,
    check_and_flag_stale_contacts,
    review_support_content_admin,
    get_stale_content_audit_admin
)
from marketplace_service import (
    seed_demo_marketplace_listings,
    create_produce_listing,
    get_marketplace_listings,
    get_farmer_my_listings,
    get_listing_by_id,
    record_buyer_inquiry,
    update_farmer_listing,
    delete_farmer_listing,
    moderate_listing_admin,
    create_listing_order_request,
    get_farmer_listing_orders,
    update_order_request_status,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_support_marketplace")

passed_tests = 0
failed_tests = 0


def assert_test(condition: bool, msg: str):
    global passed_tests, failed_tests
    if condition:
        passed_tests += 1
        print(f"  [PASS] {msg}")
    else:
        failed_tests += 1
        print(f"  [FAIL] {msg}")


async def run_all_tests():
    global passed_tests, failed_tests
    print("\n" + "=" * 70)
    print("STARTING TEST SUITE: FARMER SUPPORT HUB & DIRECT MARKETPLACE")
    print("=" * 70)

    # Step 0: Init database indexes
    await init_database_indexes()

    # ------------------------------------------------------------------------
    # TEST 1: Database Seeding & Verification across all 6 categories
    # ------------------------------------------------------------------------
    print("\n--- TEST 1: Support Hub Seeding & Category Verification ---")
    seeded_count = await seed_farmer_support_database(force=True)
    assert_test(seeded_count >= 9, f"Seeded at least 9 verified records (actual: {seeded_count})")

    all_content = await get_support_content()
    assert_test(all_content.get("total", 0) >= 9, f"Total active support records: {all_content.get('total')}")

    expected_categories = [
        "training",
        "entrepreneurship",
        "organic",
        "special_operation",
        "protected_cultivation",
        "value_addition"
    ]
    for cat in expected_categories:
        cat_res = await get_support_content(category=cat)
        items = cat_res.get("items", [])
        assert_test(len(items) > 0, f"Category '{cat}' contains {len(items)} verified item(s)")
        # Verify zero-fabrication: officialSourceUrl, lastCheckedDate, contact info present
        first = items[0]
        assert_test(bool(first.get("officialSourceUrl")), f"'{cat}' has valid officialSourceUrl ({first.get('officialSourceUrl')[:35]}...)")
        assert_test(bool(first.get("lastCheckedDate")), f"'{cat}' has lastCheckedDate: {first.get('lastCheckedDate')}")
        contact = first.get("contact", {})
        contact_num = contact.get("officePhone") or contact.get("helplinePhone") or contact.get("mobile")
        assert_test(bool(contact_num), f"'{cat}' has verified contact phone: {contact_num}")

    # ------------------------------------------------------------------------
    # TEST 2: Training Calendar & Auto-Expiration
    # ------------------------------------------------------------------------
    print("\n--- TEST 2: Training Calendar & Auto-Expiration Sweeper ---")
    calendar = await get_training_calendar()
    assert_test(len(calendar) >= 2, f"Training calendar has {len(calendar)} scheduled workshops")
    
    # Check In-Person mode filter
    in_person = await get_training_calendar(mode="In-Person")
    assert_test(len(in_person) >= 1, f"Filtered {len(in_person)} In-Person Workshop(s)")

    # Test auto-expiration logic
    col = get_farmer_support_collection()
    if col is not None:
        past_date = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d")
        test_notice = {
            "contentId": "TEST-TRAIN-EXPIRED-999",
            "category": "training",
            "activeStatus": "active",
            "title": {"en": "Expired Workshop", "ta": "காலாவதியான பயிற்சி"},
            "description": {"en": "Past training notice", "ta": "பழைய பயிற்சி"},
            "officialSourceUrl": "https://tnau.ac.in",
            "lastCheckedDate": "2026-01-01",
            "verificationStatus": "verified_official",
            "contact": {"name": "TNAU Training Desk", "officePhone": "0422-6611200", "contactVerificationStatus": "verified_official"},
            "trainingMeta": {
                "startDate": past_date,
                "endDate": past_date,
                "mode": "Classroom",
                "organizingBody": "TNAU"
            }
        }
        await col.update_one({"contentId": test_notice["contentId"]}, {"$set": test_notice}, upsert=True)
        expired_count = await auto_expire_training_notices()
        assert_test(expired_count >= 1, f"Auto-expire sweeper detected and expired {expired_count} past notice(s)")
        
        doc = await col.find_one({"contentId": "TEST-TRAIN-EXPIRED-999"})
        assert_test(doc.get("activeStatus") == "expired", "Past training notice transitioned to 'expired'")
        await col.delete_one({"contentId": "TEST-TRAIN-EXPIRED-999"})

    # ------------------------------------------------------------------------
    # TEST 3: Special Operation Beginner-to-Market Crop Lifecycle Guide
    # ------------------------------------------------------------------------
    print("\n--- TEST 3: Special Operation Crop Lifecycle Guide ---")
    paddy_guide = await get_crop_master_guide("paddy-samba")
    assert_test(paddy_guide is not None, "Retrieved Samba Paddy master crop guide")
    if paddy_guide:
        crop_meta = paddy_guide.get("cropGuideMeta", {})
        assert_test("Samba" in crop_meta.get("cropName", "") or "Paddy" in crop_meta.get("cropName", ""), f"Crop Name: {crop_meta.get('cropName')}")
        assert_test(len(crop_meta.get("stages", [])) >= 5, f"Lifecycle contains {len(crop_meta.get('stages', []))} detailed sequential stages")
        assert_test(any("DPC" in m or "Direct Purchase" in m for m in crop_meta.get("marketChannels", [])), "Includes TNCSC Direct Purchase Centre integration guidance")

    groundnut_guide = await get_crop_master_guide("groundnut")
    assert_test(groundnut_guide is not None, "Retrieved Rainfed Groundnut master crop guide")

    # ------------------------------------------------------------------------
    # TEST 4: Stale Contact Audit & Nodal Officer Re-Verification
    # ------------------------------------------------------------------------
    print("\n--- TEST 4: Stale Contact Audit & Review Governance ---")
    if col is not None:
        stale_date = (datetime.now(timezone.utc) - timedelta(days=200)).strftime("%Y-%m-%d")
        stale_item = {
            "contentId": "TEST-STALE-ITEM-888",
            "category": "organic",
            "activeStatus": "active",
            "title": {"en": "Stale Contact Test", "ta": "பழைய தொடர்பு சோதனை"},
            "description": {"en": "Test stale audit", "ta": "சோதனை"},
            "officialSourceUrl": "https://tnocd.tn.gov.in",
            "lastCheckedDate": stale_date,
            "verificationStatus": "verified_official",
            "contact": {"deskName": "TNOCD Desk", "phone": "0422-2435080", "verifiedOfficial": True}
        }
        await col.update_one({"contentId": stale_item["contentId"]}, {"$set": stale_item}, upsert=True)
        flagged = await check_and_flag_stale_contacts(stale_threshold_days=180)
        assert_test(flagged >= 1, f"Audit flagged {flagged} stale record(s) older than 180 days")

        doc = await col.find_one({"contentId": "TEST-STALE-ITEM-888"})
        assert_test(doc.get("verificationStatus") == "stale_review_needed", "Record correctly flagged as 'stale_review_needed'")

        # Simulate nodal officer review
        review_success = await review_support_content_admin("TEST-STALE-ITEM-888", "verified_official")
        assert_test(review_success, "Admin successfully reviewed and updated record")
        
        reviewed_doc = await col.find_one({"contentId": "TEST-STALE-ITEM-888"})
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert_test(reviewed_doc.get("lastCheckedDate") == today_str, f"lastCheckedDate refreshed to today ({today_str})")
        assert_test(reviewed_doc.get("verificationStatus") == "verified_official", "verificationStatus restored to 'verified_official'")
        await col.delete_one({"contentId": "TEST-STALE-ITEM-888"})

    # ------------------------------------------------------------------------
    # TEST 5: Farmer Direct Marketplace - Seeding, Discovery & Inquiries
    # ------------------------------------------------------------------------
    print("\n--- TEST 5: Direct Marketplace Discovery & Inquiry ---")
    mkt_seeds = await seed_demo_marketplace_listings()
    assert_test(mkt_seeds >= 0, f"Marketplace seeds initialized (existing or new: {mkt_seeds})")

    mkt_res = await get_marketplace_listings(limit=10)
    assert_test(mkt_res.get("total", 0) >= 3, f"Marketplace contains {mkt_res.get('total')} active listings")
    assert_test(len(mkt_res.get("categories", [])) >= 2, f"Categories available: {mkt_res.get('categories')}")
    assert_test(len(mkt_res.get("districts", [])) >= 2, f"Districts available: {mkt_res.get('districts')}")

    # Organic filter test
    org_res = await get_marketplace_listings(organic_only=True)
    for itm in org_res.get("items", []):
        assert_test(itm.get("isOrganicCertified") is True, f"Filtered organic item: {itm.get('crop')} ({itm.get('certificationBody')})")

    # Inquiry recording test
    first_listing = mkt_res.get("items", [])[0]
    initial_inquiries = first_listing.get("inquiryCount", 0)
    inq_res = await record_buyer_inquiry(first_listing["listingId"])
    assert_test(inq_res is True, f"Inquiry registered for listing {first_listing['listingId']}")
    
    updated_listing = await get_listing_by_id(first_listing["listingId"])
    assert_test(updated_listing.get("inquiryCount") == initial_inquiries + 1, f"Inquiry count incremented to {updated_listing.get('inquiryCount')}")

    # ------------------------------------------------------------------------
    # TEST 6: Strict Farmer Data Ownership Defense (Isolation Test)
    # ------------------------------------------------------------------------
    print("\n--- TEST 6: Strict Farmer Data Ownership Defense ---")
    farmer_a = {
        "id": "farmer_user_aaa_111",
        "name": "Karthik Subramanian",
        "phone": "9443100001",
        "role": "farmer",
        "district": "Thanjavur",
        "village": "Pillaiyarpatti"
    }
    farmer_b = {
        "id": "farmer_user_bbb_222",
        "name": "Senthil Nathan",
        "phone": "9443200002",
        "role": "farmer",
        "district": "Madurai",
        "village": "Melur"
    }

    # Farmer A creates a listing
    listing_data = {
        "crop": "Traditional Karuppu Kavuni Rice",
        "variety": "Black Rice Pure Organics",
        "category": "Cereals",
        "district": "Thanjavur",
        "village": "Pillaiyarpatti",
        "quantity": 25.0,
        "unit": "Bags (50kg)",
        "pricePerUnit": 4500.0,
        "isOrganicCertified": True,
        "certificationBody": "TNOCD Certified",
        "harvestDate": "2026-09-15",
        "availableUntil": "2026-11-30",
        "fulfillmentModes": ["Farm Gate Pickup", "Local Delivery within District"],
        "description": "Naturally grown black rice with exceptional aroma and high antioxidant content."
    }
    created_listing = await create_produce_listing(farmer_a, listing_data)
    listing_id = created_listing["listingId"]
    assert_test(created_listing.get("farmerId") == farmer_a["id"], f"Listing {listing_id} bound to Farmer A ({farmer_a['id']})")

    # Farmer A checks my-listings
    my_listings_a = await get_farmer_my_listings(farmer_a)
    assert_test(any(l["listingId"] == listing_id for l in my_listings_a), "Farmer A sees listing in My Listings")

    # Farmer B checks my-listings (must NOT see Farmer A's listing)
    my_listings_b = await get_farmer_my_listings(farmer_b)
    assert_test(not any(l["listingId"] == listing_id for l in my_listings_b), "Farmer B CANNOT see Farmer A's listing in My Listings")

    # DEFENSE: Farmer B attempts to update Farmer A's listing -> MUST RAISE PermissionError
    b_tamper_attempt = False
    try:
        await update_farmer_listing(farmer_b, listing_id, {"pricePerUnit": 100.0})
    except PermissionError:
        b_tamper_attempt = True
    assert_test(b_tamper_attempt, "Farmer B blocked from modifying Farmer A's listing (PermissionError raised)")

    # DEFENSE: Farmer B attempts to delete Farmer A's listing -> MUST RAISE PermissionError
    b_delete_attempt = False
    try:
        await delete_farmer_listing(farmer_b, listing_id)
    except PermissionError:
        b_delete_attempt = True
    assert_test(b_delete_attempt, "Farmer B blocked from deleting Farmer A's listing (PermissionError raised)")

    # Farmer A updates own listing -> MUST SUCCEED
    updated_a = await update_farmer_listing(farmer_a, listing_id, {"pricePerUnit": 4200.0})
    assert_test(updated_a.get("pricePerUnit") == 4200.0, "Farmer A successfully updated own listing price to ₹4,200")

    # ------------------------------------------------------------------------
    # TEST 7: Admin Moderation Controls
    # ------------------------------------------------------------------------
    print("\n--- TEST 7: Admin Moderation of Produce Listings ---")
    mod_flagged = await moderate_listing_admin(listing_id, admin_flagged=True, reason="Suspected price anomaly")
    assert_test(mod_flagged is True, f"Admin flagged listing {listing_id}")

    flagged_doc = await get_listing_by_id(listing_id)
    assert_test(flagged_doc.get("adminFlagged") is True, "Listing marked as adminFlagged = True")
    assert_test(flagged_doc.get("listingStatus") == "flagged", "Listing status changed to 'flagged'")

    # Flagged listing should NOT appear in public discovery
    public_after_flag = await get_marketplace_listings()
    assert_test(not any(l["listingId"] == listing_id for l in public_after_flag.get("items", [])), "Flagged listing hidden from public discovery")

    # Admin un-flags
    await moderate_listing_admin(listing_id, admin_flagged=False)

    # Clean up test listing by Farmer A
    del_res = await delete_farmer_listing(farmer_a, listing_id)
    assert_test(del_res is True, "Farmer A cleanly deleted own test listing")

    # ------------------------------------------------------------------------
    # TEST 8: Customer Enquiry & Order-Request Workflow
    # ------------------------------------------------------------------------
    print("\n--- TEST 8: Customer Enquiry & Order-Request Workflow ---")
    test_produce = await create_produce_listing(farmer_a, {
        "crop": "Organic Thanjavur Ponni",
        "category": "Cereals",
        "district": "Thanjavur",
        "quantity": 50.0,
        "unit": "Bags (50kg)",
        "pricePerUnit": 2200.0,
        "isOrganicCertified": True
    })
    test_listing_id = test_produce["listingId"]

    # Customer submits order request
    order_data = {
        "buyerName": "Sundaram Organics Chennai",
        "buyerPhone": "9840112233",
        "requestedQuantity": 10.0,
        "fulfillmentPreference": "Local Delivery within District",
        "deliveryAddress": "12 Gandhi Road, Thanjavur",
        "message": "Need 10 bags delivered this Saturday if FAQ 14% moisture verified."
    }
    order_res = await create_listing_order_request(test_listing_id, order_data)
    order_id = order_res["orderId"]
    assert_test(bool(order_id), f"Created order request {order_id}")
    assert_test(order_res.get("totalEstimatedPrice") == 22000.0, f"Calculated estimated total price correctly (₹22,000)")
    assert_test(order_res.get("status") == "pending", "Initial order status is 'pending'")

    # Farmer A views received orders
    farmer_orders = await get_farmer_listing_orders(farmer_a, test_listing_id)
    assert_test(len(farmer_orders) >= 1, f"Farmer A retrieved {len(farmer_orders)} pending order request(s)")
    assert_test(farmer_orders[0].get("orderId") == order_id, "Order ID matches customer submission")

    # DEFENSE: Farmer B attempts to update Farmer A's order status -> MUST RAISE PermissionError
    b_order_tamper = False
    try:
        await update_order_request_status(farmer_b, order_id, "confirmed")
    except PermissionError:
        b_order_tamper = True
    assert_test(b_order_tamper, "Farmer B blocked from confirming Farmer A's order request (PermissionError raised)")

    # Farmer A confirms order request -> MUST SUCCEED
    updated_order = await update_order_request_status(farmer_a, order_id, "confirmed")
    assert_test(updated_order.get("status") == "confirmed", "Farmer A successfully confirmed order request")

    # Clean up
    await delete_farmer_listing(farmer_a, test_listing_id)


    # ------------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"TEST SUITE COMPLETE: {passed_tests} PASSED, {failed_tests} FAILED")
    print("=" * 70)
    if failed_tests > 0:
        exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
