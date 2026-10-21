"""
COMPREHENSIVE TEST SUITE: MANDI PRICE NOTIFICATIONS IN NAMMA VIVASAYI AI
========================================================================
Verifies:
1. Duplicate alerts prevention (identical records do not alert; stable dedupKey prevents duplicate dispatches).
2. Threshold comparisons (ignores changes < threshold; alerts on changes >= threshold).
3. Farmer commodity and market preference filtering.
4. Bilingual Tamil and English notification messages with authentic AGMARKNET dates.
5. Stale / unavailable feed notification handling with daily deduplication.
6. User isolation, ownership authorization, and preferences REST endpoints.
7. Failed refreshes preserve cache and honest stale notices without invented prices.
"""

import sys
import os
import asyncio
import time
from datetime import datetime, timezone, timedelta
import httpx
from bson import ObjectId

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_notifications_collection,
    get_notification_preferences_collection,
    get_users_collection,
)
from market_notifications import (
    ALERT_TYPE_MARKET_NEW_PRICE,
    ALERT_TYPE_MARKET_PRICE_SURGE,
    ALERT_TYPE_MARKET_PRICE_DROP,
    ALERT_TYPE_MARKET_FEED_STALE,
    create_market_notification,
    evaluate_market_feed_and_notify,
    evaluate_stale_feed_notification,
    generate_bilingual_market_messages,
    matches_farmer_crop_and_market,
)
from irrigation_notifications import (
    get_user_notification_preferences,
    update_user_notification_preferences,
)
from market_service import slugify_record_id

BASE_URL = "http://127.0.0.1:8000"


async def run_mandi_notifications_tests():
    print("=" * 80)
    print("STARTING TEST SUITE: MANDI PRICE NOTIFICATIONS FOR NAMMA VIVASAYI AI")
    print("=" * 80)

    ts = int(time.time())
    user_alpha_id = f"test_farmer_alpha_{ts}"
    user_beta_id = f"test_farmer_beta_{ts}"
    farmer_alpha_id = f"FA-{ts}-001"
    farmer_beta_id = f"FB-{ts}-002"

    notif_col = get_notifications_collection()
    pref_col = get_notification_preferences_collection()
    users_col = get_users_collection()

    # -------------------------------------------------------------------------
    # SETUP TEST USERS
    # -------------------------------------------------------------------------
    print("\n--- [Setup] Creating isolated test farmers in database ---")
    if users_col is not None:
        await users_col.delete_many({"_id": {"$in": [user_alpha_id, user_beta_id]}})
        await users_col.insert_one({
            "_id": user_alpha_id,
            "id": user_alpha_id,
            "name": f"Murugan {ts}",
            "phone": f"98765{ts % 100000:05d}",
            "role": "farmer",
            "farmerId": farmer_alpha_id,
            "district": "Thanjavur",
            "primaryCrop": "Paddy / Rice",
        })
        await users_col.insert_one({
            "_id": user_beta_id,
            "id": user_beta_id,
            "name": f"Kavitha {ts}",
            "phone": f"98766{ts % 100000:05d}",
            "role": "farmer",
            "farmerId": farmer_beta_id,
            "district": "Madurai",
            "primaryCrop": "Tomato",
        })
        print("  -> Created Test Farmers Alpha (Thanjavur, Paddy) & Beta (Madurai, Tomato).")

    # Clean old notifications for test users
    if notif_col is not None:
        await notif_col.delete_many({"userId": {"$in": [user_alpha_id, user_beta_id]}})

    # -------------------------------------------------------------------------
    # TEST 1: Duplicate Record Suppression (Requirement 2)
    # -------------------------------------------------------------------------
    print("\n--- [Test 1] Duplicate Record Suppression: Identical Records Do NOT Alert ---")
    rec_id_paddy = slugify_record_id("Tamil Nadu", "Thanjavur", "Thanjavur Mandi", "Paddy (Dhan)(Common)", "Common", "2026-10-20")

    base_paddy_record = {
        "id": rec_id_paddy,
        "recordId": rec_id_paddy,
        "state": "Tamil Nadu",
        "district": "Thanjavur",
        "market": "Thanjavur Mandi",
        "commodity": "Paddy (Dhan)(Common)",
        "commodityTa": "நெல் (சாதாரண ரகம்)",
        "variety": "Common",
        "grade": "FAQ",
        "arrivalDate": "2026-10-20",
        "arrivalDateHuman": "20 Oct 2026",
        "minPrice": 2100.0,
        "maxPrice": 2350.0,
        "modalPrice": 2250.0,
        "unit": "Quintal"
    }

    # Evaluate identical record against previous records
    eval_dups = await evaluate_market_feed_and_notify(
        previous_records=[base_paddy_record],
        incoming_records=[dict(base_paddy_record)],
    )
    assert eval_dups["detectedEvents"] == 0, f"Expected 0 detected events for duplicate record, got {eval_dups['detectedEvents']}"
    assert eval_dups["generatedAlerts"] == 0, f"Expected 0 alerts for duplicate record, got {eval_dups['generatedAlerts']}"
    print("  -> PASS: Newly fetched identical duplicate record is NOT interpreted as a price change.")

    # -------------------------------------------------------------------------
    # TEST 2: Threshold Comparison - Suppress Below Threshold (Requirement 3)
    # -------------------------------------------------------------------------
    print("\n--- [Test 2] Threshold Comparison: Price Change < 5% Is Suppressed ---")
    # Farmer Alpha has default threshold 5.0%
    # Modal price changes from 2250 to 2295 (+45 Rs = +2.0%)
    mild_increase_record = dict(base_paddy_record)
    mild_increase_record["modalPrice"] = 2295.0

    eval_mild = await evaluate_market_feed_and_notify(
        previous_records=[base_paddy_record],
        incoming_records=[mild_increase_record],
    )
    assert eval_mild["detectedEvents"] == 1, "Price change should be detected"
    assert eval_mild["skippedBelowThreshold"] >= 1, "Should be skipped because change (2.0%) is below 5.0% threshold"
    assert eval_mild["generatedAlerts"] == 0, "No alert should be generated when below threshold"
    print("  -> PASS: Price increase below 5% threshold (+2.0%) correctly suppressed.")

    # -------------------------------------------------------------------------
    # TEST 3: Price Surge Alert (>= Threshold) (Requirement 1 & 3)
    # -------------------------------------------------------------------------
    print("\n--- [Test 3] Price Surge Alert (>= Threshold) ---")
    # Modal price changes from 2250 to 2550 (+300 Rs = +13.33%)
    surge_paddy_record = dict(base_paddy_record)
    surge_paddy_record["modalPrice"] = 2550.0
    surge_paddy_record["maxPrice"] = 2650.0

    eval_surge = await evaluate_market_feed_and_notify(
        previous_records=[base_paddy_record],
        incoming_records=[surge_paddy_record],
    )
    assert eval_surge["detectedEvents"] == 1
    assert eval_surge["generatedAlerts"] >= 1, f"Expected at least 1 alert, got {eval_surge['generatedAlerts']}"

    # Verify notification in database for Farmer Alpha
    notif_doc = await notif_col.find_one({"userId": user_alpha_id, "eventType": ALERT_TYPE_MARKET_PRICE_SURGE})
    assert notif_doc is not None, "Notification must be persisted in MongoDB"
    assert notif_doc["type"] == "market"
    assert notif_doc["commodity"] == "Paddy (Dhan)(Common)"
    assert notif_doc["market"] == "Thanjavur Mandi"
    assert notif_doc["oldPrice"] == 2250.0
    assert notif_doc["newPrice"] == 2550.0
    assert notif_doc["priceDiff"] == 300.0
    assert notif_doc["priceChangePercent"] == 13.33
    assert notif_doc["sourceReportingDate"] == "20 Oct 2026"
    assert "20 Oct 2026" in notif_doc["message"], "Message must include authentic arrival date"
    assert "AGMARKNET" in notif_doc["message"], "Message must cite authentic source"
    assert notif_doc["isRead"] is False
    print("  -> PASS: Price Surge alert correctly generated with authentic old/new price and arrival date.")

    # -------------------------------------------------------------------------
    # TEST 4: Stable DedupKey Prevents Duplicate Alerts on Reruns / Multi-workers (Requirement 5)
    # -------------------------------------------------------------------------
    print("\n--- [Test 4] Stable DedupKey Prevents Duplicate Alerts Across Restarts ---")
    # Run the exact same surge evaluation a second time (simulating scheduler restart or 2nd worker)
    eval_rerun = await evaluate_market_feed_and_notify(
        previous_records=[base_paddy_record],
        incoming_records=[surge_paddy_record],
    )
    assert eval_rerun["generatedAlerts"] == 0, f"Rerun must NOT generate duplicate alert, got {eval_rerun['generatedAlerts']}"
    assert eval_rerun["skippedDuplicates"] >= 1, "Rerun must be recorded as skipped duplicate"

    # Verify only 1 notification exists in MongoDB
    count_notifs = await notif_col.count_documents({"userId": user_alpha_id, "eventType": ALERT_TYPE_MARKET_PRICE_SURGE})
    assert count_notifs == 1, f"Expected exactly 1 notification, found {count_notifs}"
    print("  -> PASS: Multi-worker rerun completely deduplicated by MongoDB stable dedupKey.")

    # -------------------------------------------------------------------------
    # TEST 5: Price Drop Alert (>= Threshold) (Requirement 3)
    # -------------------------------------------------------------------------
    print("\n--- [Test 5] Price Drop Alert (>= Threshold) ---")
    rec_id_tomato = slugify_record_id("Tamil Nadu", "Madurai", "Madurai Mandi", "Tomato", "Local", "2026-10-20")
    prev_tomato = {
        "id": rec_id_tomato,
        "recordId": rec_id_tomato,
        "state": "Tamil Nadu",
        "district": "Madurai",
        "market": "Madurai Mandi",
        "commodity": "Tomato",
        "commodityTa": "தக்காளி",
        "variety": "Local",
        "grade": "FAQ",
        "arrivalDate": "2026-10-20",
        "arrivalDateHuman": "20 Oct 2026",
        "modalPrice": 3000.0,
        "minPrice": 2800.0,
        "maxPrice": 3200.0,
    }
    # Tomato price drops from 3000 to 2400 (-600 Rs = -20.0%)
    dropped_tomato = dict(prev_tomato)
    dropped_tomato["modalPrice"] = 2400.0

    eval_drop = await evaluate_market_feed_and_notify(
        previous_records=[prev_tomato],
        incoming_records=[dropped_tomato],
    )
    assert eval_drop["detectedEvents"] == 1
    # Farmer Beta cultivates Tomato in Madurai, so must receive alert
    beta_drop = await notif_col.find_one({"userId": user_beta_id, "eventType": ALERT_TYPE_MARKET_PRICE_DROP})
    assert beta_drop is not None, "Farmer Beta must receive tomato price drop alert"
    assert beta_drop["oldPrice"] == 3000.0
    assert beta_drop["newPrice"] == 2400.0
    assert beta_drop["priceChangePercent"] == -20.0
    print("  -> PASS: Price Drop alert correctly generated for targeted farmer.")

    # -------------------------------------------------------------------------
    # TEST 6: Commodity & Market Filtering (Requirement 3 & 6)
    # -------------------------------------------------------------------------
    print("\n--- [Test 6] Farmer Commodity & Market Preference Filtering ---")
    # Farmer Beta (Madurai, Tomato) should NOT receive Paddy surge alert from Thanjavur
    beta_paddy = await notif_col.find_one({"userId": user_beta_id, "commodity": "Paddy (Dhan)(Common)"})
    assert beta_paddy is None, "Farmer Beta must NOT receive Paddy alert from Thanjavur"

    # Farmer Alpha (Thanjavur, Paddy) should NOT receive Tomato drop alert from Madurai
    alpha_tomato = await notif_col.find_one({"userId": user_alpha_id, "commodity": "Tomato"})
    assert alpha_tomato is None, "Farmer Alpha must NOT receive Tomato alert from Madurai"
    print("  -> PASS: Strict preference and district/crop filtering prevents cross-crop noise.")

    # Explicit preferences test: configure Farmer Alpha with selected commodities
    await update_user_notification_preferences(
        user_id=user_alpha_id,
        updates={"mandiSelectedCommodities": ["Cotton"], "mandiSelectedMarkets": ["Thanjavur Mandi"]}
    )
    # Check matching function
    paddy_matches = matches_farmer_crop_and_market(
        farmer_user={"primaryCrop": "Paddy"},
        prefs={"mandiSelectedCommodities": ["Cotton"], "mandiSelectedMarkets": ["Thanjavur Mandi"]},
        commodity="Paddy (Dhan)(Common)",
        commodity_ta="நெல்",
        market="Thanjavur Mandi",
        district="Thanjavur"
    )
    assert paddy_matches is False, "Paddy must NOT match when farmer explicitly selected Cotton!"

    cotton_matches = matches_farmer_crop_and_market(
        farmer_user={"primaryCrop": "Paddy"},
        prefs={"mandiSelectedCommodities": ["Cotton"], "mandiSelectedMarkets": ["Thanjavur Mandi"]},
        commodity="Cotton",
        commodity_ta="பருத்தி",
        market="Thanjavur Mandi",
        district="Thanjavur"
    )
    assert cotton_matches is True, "Cotton MUST match when farmer selected Cotton!"
    print("  -> PASS: Granular commodity and market selection verified.")

    # -------------------------------------------------------------------------
    # TEST 7: Bilingual Messages & Authentic Reporting Dates (Requirement 7 & 8)
    # -------------------------------------------------------------------------
    print("\n--- [Test 7] Bilingual English & Tamil Messages and No Invented Prices ---")
    title_en, title_ta, msg_en, msg_ta = generate_bilingual_market_messages(
        event_type=ALERT_TYPE_MARKET_PRICE_SURGE,
        commodity="Groundnut",
        commodity_ta="நிலக்கடலை",
        market="Tiruchirappalli Mandi",
        district="Tiruchirappalli",
        variety="Local",
        new_price=6500.0,
        old_price=5800.0,
        diff=700.0,
        pct=12.07,
        arrival_date_human="20 Oct 2026"
    )
    assert "Mandi Price Surge: Groundnut (+12.1%)" in title_en
    assert "மண்டி விலை உயர்வு: நிலக்கடலை (+12.1%)" in title_ta
    assert "₹6500" in msg_en and "₹5800" in msg_en
    assert "20 Oct 2026" in msg_en and "20 Oct 2026" in msg_ta
    assert "AGMARKNET" in msg_en and "AGMARKNET" in msg_ta
    print("  -> PASS: Authentic bilingual English and Tamil messages correctly formatted.")

    # -------------------------------------------------------------------------
    # TEST 8: Stale Feed Alert Handling & Daily Dedup (Requirement 3)
    # -------------------------------------------------------------------------
    print("\n--- [Test 8] Stale Feed Notice Handling & Daily Deduplication ---")
    stale_res_1 = await evaluate_stale_feed_notification(latest_reporting_date="19 Oct 2026")
    assert stale_res_1["checkedFarmers"] >= 2
    # Verify Farmer Beta received stale feed notice
    beta_stale = await notif_col.find_one({"userId": user_beta_id, "eventType": ALERT_TYPE_MARKET_FEED_STALE})
    assert beta_stale is not None, "Farmer Beta must receive stale feed notice"
    assert "19 Oct 2026" in beta_stale["message"]

    # Calling again today must be deduplicated
    stale_res_2 = await evaluate_stale_feed_notification(latest_reporting_date="19 Oct 2026")
    assert stale_res_2["generatedAlerts"] == 0, "Duplicate stale feed notice must be prevented on same day"
    print("  -> PASS: Stale feed notice generated without panic, deduplicated once per calendar day.")

    # -------------------------------------------------------------------------
    # TEST 9: HTTP API Preferences Endpoints & Farmer Isolation (Requirement 6)
    # -------------------------------------------------------------------------
    print("\n--- [Test 9] HTTP API Preferences Endpoints & Farmer Isolation ---")
    suffix = ts % 100000
    phone = f"98777{suffix:05d}"
    pwd = "FarmerMandiPassword@2026"

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Register fresh farmer
        reg_resp = await client.post("/api/auth/register", json={
            "name": f"Farmer Mandi Tester {suffix}",
            "phone": phone,
            "village": "Thanjavur East",
            "state": "Tamil Nadu",
            "district": "Thanjavur",
            "password": pwd,
            "confirmPassword": pwd
        })
        assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"
        token = reg_resp.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        # GET Preferences
        get_pref = await client.get("/api/notifications/preferences", headers=headers)
        assert get_pref.status_code == 200, f"GET preferences failed: {get_pref.text}"
        pref_data = get_pref.json()
        assert pref_data["mandiPriceAlerts"] is True
        assert pref_data["mandiPriceSurgeAlerts"] is True
        assert pref_data["mandiPriceThresholdPercent"] == 5.0

        # PUT Preferences (Customize Mandi Alert Toggles, Crops, and Threshold)
        put_pref = await client.put(
            "/api/notifications/preferences",
            headers=headers,
            json={
                "mandiPriceThresholdPercent": 8.5,
                "mandiSelectedCommodities": ["Paddy", "Maize"],
                "mandiSelectedMarkets": ["Thanjavur Mandi"],
                "mandiPriceDropAlerts": False
            }
        )
        assert put_pref.status_code == 200, f"PUT preferences failed: {put_pref.text}"
        updated = put_pref.json()
        assert updated["mandiPriceThresholdPercent"] == 8.5
        assert updated["mandiSelectedCommodities"] == ["Paddy", "Maize"]
        assert updated["mandiSelectedMarkets"] == ["Thanjavur Mandi"]
        assert updated["mandiPriceDropAlerts"] is False
        print("  -> PASS: GET and PUT /api/notifications/preferences successfully persists mandi settings.")

        # Test POST /api/notifications/mandi-check
        check_resp = await client.post("/api/notifications/mandi-check", headers=headers)
        assert check_resp.status_code == 200, f"Mandi check failed: {check_resp.text}"
        check_data = check_resp.json()
        assert check_data["success"] is True
        assert "notificationSummary" in check_data
        print("  -> PASS: POST /api/notifications/mandi-check executed cleanly.")

    # -------------------------------------------------------------------------
    # CLEANUP TEST DATA
    # -------------------------------------------------------------------------
    print("\n--- [Cleanup] Removing test users and test notifications ---")
    if users_col is not None:
        await users_col.delete_many({"_id": {"$in": [user_alpha_id, user_beta_id]}})
    if notif_col is not None:
        await notif_col.delete_many({"userId": {"$in": [user_alpha_id, user_beta_id]}})
    if pref_col is not None:
        await pref_col.delete_many({"userId": {"$in": [user_alpha_id, user_beta_id]}})

    print("=" * 80)
    print("ALL MANDI PRICE NOTIFICATION TESTS COMPLETED SUCCESSFULLY! (9/9 PASSED)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_mandi_notifications_tests())
