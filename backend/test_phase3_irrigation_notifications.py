"""
PHASE 3 VERIFICATION TEST SUITE: SMART IRRIGATION NOTIFICATION SYSTEM
======================================================================
Comprehensive verification of all Phase 3 requirements:
1. 5 Required Agronomic Alert Rules:
   - Rain expected soon (recommend reassessing planned irrigation)
   - Irrigation may be required (water-balance deficit advisory)
   - High heat or elevated crop-water demand (temp >= 38°C or ET0 >= 6.5 mm/day)
   - Weather data unavailable or stale (non-alarming status notice)
   - Updated irrigation advice (meaningful transition detection)
2. Alert deduplication over time window (6 hours)
3. Per-farmer rate limiting (max 4 alerts in 24 hours)
4. User notification preferences (granular toggles & suppression)
5. Singleton distributed scheduler lease lock (preventing concurrent runs)
6. Push notification status & honest unconfigured disclaimer
7. User isolation & permission boundaries
8. API endpoints integration over HTTP (/api/notifications/preferences, /api/notifications/push-status, etc.)
"""

import sys
import os
import asyncio
import time
import httpx
from datetime import datetime, timezone, timedelta
from bson import ObjectId

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_notifications_collection,
    get_notification_preferences_collection,
    get_push_subscriptions_collection,
    get_scheduler_locks_collection,
    get_irrigation_advisories_history_collection,
    get_users_collection,
)
from smart_farming import IST
from irrigation_notifications import (
    ALERT_TYPE_RAIN,
    ALERT_TYPE_IRRIGATION,
    ALERT_TYPE_HEAT,
    ALERT_TYPE_STALE_WEATHER,
    ALERT_TYPE_ADVICE_CHANGED,
    create_irrigation_notification,
    evaluate_farmer_irrigation_alerts,
    get_user_notification_preferences,
    update_user_notification_preferences,
    save_push_subscription,
    delete_push_subscription,
    get_push_status,
    IrrigationNotificationScheduler,
    DEDUP_WINDOW_HOURS,
    MAX_ALERTS_PER_DAY,
)

BASE_URL = "http://127.0.0.1:8000"


async def run_phase3_tests():
    print("=" * 80)
    print("PHASE 3: SMART IRRIGATION NOTIFICATION SYSTEM VERIFICATION")
    print("=" * 80)

    ts = int(time.time())
    test_user_id_1 = f"test_farmer_p3_{ts}_1"
    test_user_id_2 = f"test_farmer_p3_{ts}_2"

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # ---------------------------------------------------------------------
        # TEST 1: Rule 1 - Rain Expected Soon Alert
        # ---------------------------------------------------------------------
        print("\n--- [Test 1] Agronomic Rule 1: Rain Expected Soon ---")
        mock_user_1 = {
            "_id": test_user_id_1,
            "farmerId": f"FARMER-{ts}-001",
            "farmName": "Thanjavur Delta Farm",
            "farmCoordinates": {"latitude": 10.7870, "longitude": 79.1378, "locationName": "Thanjavur"}
        }

        rainy_weather = {
            "isLive": True,
            "isCached": False,
            "isStale": False,
            "precipitationProbability": 80,
            "precipitationSumMm": 18.0,
            "et0EstimateMmDay": 3.8,
            "current": {"temperatureC": 28.5, "humidity": 88, "condition": "Rain"},
            "soilMoisture": {"available": True, "rootZonePercent": 50.0},
            "lastUpdated": "2026-10-20T17:00:00+05:30"
        }

        alerts_1 = await evaluate_farmer_irrigation_alerts(
            farmer_user=mock_user_1,
            weather_summary=rainy_weather,
            crop="Paddy / Rice",
            growth_stage="Vegetative"
        )

        rain_alerts = [a for a in alerts_1 if a.get("eventType") == ALERT_TYPE_RAIN]
        assert len(rain_alerts) >= 1, "Expected rain alert was not generated!"
        rain_alert = rain_alerts[0]
        assert "Rain Expected Soon" in rain_alert["title"]
        assert "மழை எதிர்பார்க்கப்படுகிறது" in rain_alert["titleTa"]
        assert "Postpone irrigation" in rain_alert["message"]
        assert "80%" in rain_alert["message"]
        assert rain_alert["userId"] == test_user_id_1
        assert rain_alert["relatedFarmId"] == "Thanjavur"
        assert rain_alert["sourceDataTime"] == "2026-10-20T17:00:00+05:30"
        print(f"  -> PASS: Rain expected alert verified. Title: '{rain_alert['title']}'")

        # ---------------------------------------------------------------------
        # TEST 2: Rule 2 - Irrigation May Be Required (Deficit Advisory)
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Agronomic Rule 2: Irrigation May Be Required (Deficit) ---")
        mock_user_2 = {
            "_id": f"{test_user_id_1}_deficit",
            "farmerId": f"FARMER-{ts}-002",
            "farmCoordinates": {"latitude": 10.7870, "longitude": 79.1378, "locationName": "Delta Block A"}
        }

        dry_weather = {
            "isLive": True,
            "isCached": False,
            "isStale": False,
            "precipitationProbability": 5,
            "precipitationSumMm": 0.0,
            "et0EstimateMmDay": 5.2,
            "current": {"temperatureC": 33.0, "humidity": 55, "condition": "Sunny"},
            "soilMoisture": {"available": True, "rootZonePercent": 20.0},
            "lastUpdated": "2026-10-20T17:00:00+05:30"
        }

        alerts_2 = await evaluate_farmer_irrigation_alerts(
            farmer_user=mock_user_2,
            weather_summary=dry_weather,
            crop="Groundnut / Peanut",
            growth_stage="Flowering / Pegging",
            soil_type="Red Sandy Loam",
            irrigation_method="Furrow / Drip Irrigation"
        )

        deficit_alerts = [a for a in alerts_2 if a.get("eventType") == ALERT_TYPE_IRRIGATION]
        assert len(deficit_alerts) >= 1, "Expected irrigation needed alert was not generated!"
        irrig_alert = deficit_alerts[0]
        assert "Irrigation Recommended" in irrig_alert["title"]
        assert "பாசனம் பரிந்துரைக்கப்படுகிறது" in irrig_alert["titleTa"]
        assert "Litres" in irrig_alert["message"]
        assert irrig_alert["recommendation"] == "irrigate_now"
        print(f"  -> PASS: Irrigation required alert verified. Deficit guidance: '{irrig_alert['message'][:65]}...'")

        # ---------------------------------------------------------------------
        # TEST 3: Rule 3 - High Heat or Elevated Demand
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Agronomic Rule 3: High Heat or Elevated Evaporative Demand ---")
        mock_user_3 = {
            "_id": f"{test_user_id_1}_heat",
            "farmerId": f"FARMER-{ts}-003",
            "farmCoordinates": {"latitude": 10.7870, "longitude": 79.1378}
        }

        heat_weather = {
            "isLive": True,
            "isCached": False,
            "isStale": False,
            "precipitationProbability": 0,
            "precipitationSumMm": 0.0,
            "et0EstimateMmDay": 6.8,
            "current": {"temperatureC": 39.5, "humidity": 35, "condition": "Clear"},
            "soilMoisture": {"available": True, "rootZonePercent": 40.0},
            "lastUpdated": "2026-10-20T17:00:00+05:30"
        }

        alerts_3 = await evaluate_farmer_irrigation_alerts(
            farmer_user=mock_user_3,
            weather_summary=heat_weather,
            crop="Sugarcane",
            growth_stage="Grand Growth"
        )

        heat_alerts = [a for a in alerts_3 if a.get("eventType") == ALERT_TYPE_HEAT]
        assert len(heat_alerts) >= 1, "Expected high heat alert was not generated!"
        heat_alert = heat_alerts[0]
        assert "High Evaporative Demand & Heat Stress" in heat_alert["title"]
        assert "39.5°C" in heat_alert["message"]
        assert "06:00–09:00 AM" in heat_alert["message"]
        print(f"  -> PASS: Heat alert verified for 39.5°C and 6.8 mm/day ET0.")

        # ---------------------------------------------------------------------
        # TEST 4: Rule 4 - Weather Data Unavailable or Stale
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Agronomic Rule 4: Weather Unavailable or Stale Status ---")
        mock_user_4 = {
            "_id": f"{test_user_id_1}_stale",
            "farmerId": f"FARMER-{ts}-004",
            "farmCoordinates": {"latitude": 10.7870, "longitude": 79.1378}
        }

        stale_weather = {
            "isLive": False,
            "isCached": False,
            "isStale": True,
            "precipitationProbability": 10,
            "precipitationSumMm": 0.0,
            "et0EstimateMmDay": 4.5,
            "current": {"temperatureC": 30.0, "humidity": 65, "condition": "Unknown"},
            "lastUpdated": "2026-10-18T10:00:00+05:30"
        }

        alerts_4 = await evaluate_farmer_irrigation_alerts(
            farmer_user=mock_user_4,
            weather_summary=stale_weather,
            crop="Paddy / Rice"
        )

        stale_alerts = [a for a in alerts_4 if a.get("eventType") == ALERT_TYPE_STALE_WEATHER]
        assert len(stale_alerts) >= 1, "Expected stale weather alert was not generated!"
        stale_alert = stale_alerts[0]
        assert "Notice: Meteorological Feed Status" in stale_alert["title"]
        assert "அறிவிப்பு: வானிலை சேவை நிலை" in stale_alert["titleTa"]
        assert "inspect soil" in stale_alert["message"]
        print(f"  -> PASS: Stale weather non-alarming notice verified: '{stale_alert['title']}'")

        # ---------------------------------------------------------------------
        # TEST 5: Rule 5 - Updated Irrigation Advice (Transition Only)
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Agronomic Rule 5: Updated Irrigation Advice on Meaningful Transition ---")
        transition_uid = f"{test_user_id_1}_trans"
        mock_user_trans = {
            "_id": transition_uid,
            "farmerId": f"FARMER-{ts}-005",
            "farmCoordinates": {"latitude": 10.7870, "longitude": 79.1378}
        }

        # Step A: Weather with heavy rain -> triggers 'delay_reassess'
        rain_step = {
            "isLive": True,
            "isCached": False,
            "isStale": False,
            "precipitationProbability": 90,
            "precipitationSumMm": 35.0,
            "et0EstimateMmDay": 3.0,
            "current": {"temperatureC": 26.0, "humidity": 90},
            "soilMoisture": {"available": True, "rootZonePercent": 60.0}
        }
        await evaluate_farmer_irrigation_alerts(mock_user_trans, rain_step, "Paddy / Rice")

        # Step B: Weather dries up -> triggers transition to 'irrigate_now'
        dry_step = {
            "isLive": True,
            "isCached": False,
            "isStale": False,
            "precipitationProbability": 0,
            "precipitationSumMm": 0.0,
            "et0EstimateMmDay": 5.5,
            "current": {"temperatureC": 33.0, "humidity": 45},
            "soilMoisture": {"available": True, "rootZonePercent": 18.0}
        }
        alerts_trans = await evaluate_farmer_irrigation_alerts(mock_user_trans, dry_step, "Paddy / Rice")

        changed_alerts = [a for a in alerts_trans if a.get("eventType") == ALERT_TYPE_ADVICE_CHANGED]
        assert len(changed_alerts) >= 1, "Expected advice transition alert was not generated!"
        trans_alert = changed_alerts[0]
        assert "Irrigation Advisory Changed" in trans_alert["title"]
        assert "Delay and Reassess ➔ Irrigate Now" in trans_alert["title"]
        assert "பாசன ஆலோசனை மாறியுள்ளது" in trans_alert["titleTa"]
        print(f"  -> PASS: Transition alert verified: '{trans_alert['title']}'")

        # ---------------------------------------------------------------------
        # TEST 6: Deduplication Window (6 Hours)
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Alert Deduplication Window Enforcement ---")
        dedup_uid = f"{test_user_id_1}_dedup"

        alert_first = await create_irrigation_notification(
            user_id=dedup_uid,
            event_type=ALERT_TYPE_RAIN,
            title_en="Rain Expected Soon",
            title_ta="மழை எதிர்பார்க்கப்படுகிறது",
            message_en="Rain probability 85%",
            message_ta="மழை 85%",
            dedup_window_hours=6
        )
        assert alert_first is not None, "First alert should have been inserted!"

        alert_second = await create_irrigation_notification(
            user_id=dedup_uid,
            event_type=ALERT_TYPE_RAIN,
            title_en="Rain Expected Soon",
            title_ta="மழை எதிர்பார்க்கப்படுகிறது",
            message_en="Rain probability 85%",
            message_ta="மழை 85%",
            dedup_window_hours=6
        )
        assert alert_second is None, "Duplicate alert was NOT suppressed within 6-hour window!"
        print(f"  -> PASS: Duplicate alert correctly suppressed by dedupKey window.")

        # ---------------------------------------------------------------------
        # TEST 7: 24-Hour Per-Farmer Rate Limit (Max 4 Alerts)
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] Per-Farmer Rate Limit (Max 4 Alerts / 24 Hours) ---")
        ratelimit_uid = f"{test_user_id_1}_ratelimit"

        for i in range(4):
            a = await create_irrigation_notification(
                user_id=ratelimit_uid,
                event_type=ALERT_TYPE_RAIN,
                title_en=f"Alert #{i+1}",
                title_ta=f"எச்சரிக்கை #{i+1}",
                message_en=f"Rate limit alert test {i+1}",
                message_ta=f"அளவு சோதனை {i+1}",
                custom_dedup_key=f"{ratelimit_uid}_key_{i+1}"
            )
            assert a is not None, f"Alert {i+1} should have been accepted!"

        alert_5 = await create_irrigation_notification(
            user_id=ratelimit_uid,
            event_type=ALERT_TYPE_RAIN,
            title_en="Alert #5 (Should be rate-limited)",
            title_ta="எச்சரிக்கை #5",
            message_en="Rate limit alert test 5",
            message_ta="அளவு சோதனை 5",
            custom_dedup_key=f"{ratelimit_uid}_key_5"
        )
        assert alert_5 is None, "5th alert was NOT suppressed by 24-hour rate limit!"
        print("  -> PASS: 4-alert per 24-hour rate limit strictly enforced (5th suppressed).")

        # ---------------------------------------------------------------------
        # TEST 8: Notification Preferences Management & Alert Suppression
        # ---------------------------------------------------------------------
        print("\n--- [Test 8] User Notification Preferences & Granular Suppression ---")
        pref_uid = f"{test_user_id_1}_pref"

        # Check default preferences
        init_prefs = await get_user_notification_preferences(pref_uid)
        assert init_prefs["rainAlerts"] is True
        assert init_prefs["heatDemandAlerts"] is True

        # Toggle rain alerts to False
        updated_prefs = await update_user_notification_preferences(pref_uid, {"rainAlerts": False})
        assert updated_prefs["rainAlerts"] is False
        assert updated_prefs["heatDemandAlerts"] is True

        # Attempt to create rain alert -> Must be suppressed
        suppressed_rain = await create_irrigation_notification(
            user_id=pref_uid,
            event_type=ALERT_TYPE_RAIN,
            title_en="Rain Expected",
            title_ta="மழை",
            message_en="Testing preference suppression",
            message_ta="விருப்பத்தேர்வு சோதனை"
        )
        assert suppressed_rain is None, "Rain alert should be suppressed when rainAlerts=False!"

        # Heat alert must still be allowed
        allowed_heat = await create_irrigation_notification(
            user_id=pref_uid,
            event_type=ALERT_TYPE_HEAT,
            title_en="Heat Alert",
            title_ta="வெப்பம்",
            message_en="Testing preference pass-through",
            message_ta="அனுமதி சோதனை"
        )
        assert allowed_heat is not None, "Heat alert should be allowed when heatDemandAlerts=True!"
        print("  -> PASS: Preferences toggles reliably suppress specific alert types.")

        # ---------------------------------------------------------------------
        # TEST 9: Singleton Distributed Scheduler Lease Lock
        # ---------------------------------------------------------------------
        print("\n--- [Test 9] Singleton Distributed Scheduler Lease Lock ---")
        worker_alpha = IrrigationNotificationScheduler(worker_id="uva-worker-alpha")
        worker_beta = IrrigationNotificationScheduler(worker_id="uva-worker-beta")

        col = get_scheduler_locks_collection()
        if col is not None:
            await col.delete_many({"jobName": "irrigation_alert_check"})

        # Worker Alpha acquires lock
        lease_a = await worker_alpha.acquire_distributed_lease()
        assert lease_a is True, "Worker Alpha should acquire distributed lease!"

        # Worker Beta tries to acquire lock concurrently -> Must fail
        lease_b = await worker_beta.acquire_distributed_lease()
        assert lease_b is False, "Worker Beta should NOT acquire lease while Alpha is active!"

        # Worker Alpha releases lock
        await worker_alpha.release_distributed_lease()

        # Worker Beta can now acquire lock
        lease_b_now = await worker_beta.acquire_distributed_lease()
        assert lease_b_now is True, "Worker Beta should acquire lease after Alpha releases!"

        await worker_beta.release_distributed_lease()
        print("  -> PASS: Distributed singleton lease lock guarantees single active scheduler.")

        # ---------------------------------------------------------------------
        # TEST 10: Push Status Transparency (Unconfigured Honesty)
        # ---------------------------------------------------------------------
        print("\n--- [Test 10] Web Push Status Transparency ---")
        push_status = get_push_status(user_has_subscription=False)
        assert "pushConfigured" in push_status
        assert push_status["inAppActive"] is True
        if not os.getenv("VAPID_PUBLIC_KEY"):
            assert push_status["pushConfigured"] is False
            assert "Notice:" in push_status["note"]
            print("  -> PASS: Web push status honestly reports unconfigured VAPID keys; in-app alerts active.")
        else:
            print("  -> PASS: Web push status reflects active VAPID keys.")

        # ---------------------------------------------------------------------
        # TEST 11: HTTP API Endpoints Integration & User Isolation
        # ---------------------------------------------------------------------
        print("\n--- [Test 11] HTTP API Endpoints Integration & User Isolation ---")
        suffix = int(time.time()) % 100000
        phone_1 = f"98765{suffix:05d}"
        phone_2 = f"98766{suffix:05d}"
        pwd = "FarmerPassword@2026"

        # Register Farmer 1
        reg_1 = await client.post("/api/auth/register", json={
            "name": f"Farmer P3 Alpha {suffix}",
            "phone": phone_1,
            "village": "Thanjavur North",
            "district": "Thanjavur",
            "password": pwd,
            "confirmPassword": pwd
        })
        assert reg_1.status_code == 201, f"Registration failed: {reg_1.text}"
        token_1 = reg_1.json()["accessToken"]
        headers_1 = {"Authorization": f"Bearer {token_1}"}

        # Register Farmer 2
        reg_2 = await client.post("/api/auth/register", json={
            "name": f"Farmer P3 Beta {suffix}",
            "phone": phone_2,
            "village": "Thanjavur South",
            "district": "Thanjavur",
            "password": pwd,
            "confirmPassword": pwd
        })
        assert reg_2.status_code == 201, f"Registration failed: {reg_2.text}"
        token_2 = reg_2.json()["accessToken"]
        headers_2 = {"Authorization": f"Bearer {token_2}"}

        # GET /api/notifications/preferences for Farmer 1
        pref_res = await client.get("/api/notifications/preferences", headers=headers_1)
        assert pref_res.status_code == 200
        prefs_body = pref_res.json()
        assert prefs_body["rainAlerts"] is True
        print("  -> PASS: GET /api/notifications/preferences returns default active preferences.")

        # PUT /api/notifications/preferences for Farmer 1
        put_res = await client.put(
            "/api/notifications/preferences",
            json={"rainAlerts": False, "pushEnabled": False},
            headers=headers_1
        )
        assert put_res.status_code == 200
        assert put_res.json()["rainAlerts"] is False
        print("  -> PASS: PUT /api/notifications/preferences successfully persists toggles.")

        # Verify Farmer 2's preferences remain unchanged (Isolation)
        pref2_res = await client.get("/api/notifications/preferences", headers=headers_2)
        assert pref2_res.status_code == 200
        assert pref2_res.json()["rainAlerts"] is True, "Farmer 2's preferences were contaminated by Farmer 1!"
        print("  -> PASS: Notification preferences strictly isolated per farmer.")

        # GET /api/notifications/push-status
        push_status_res = await client.get("/api/notifications/push-status", headers=headers_1)
        assert push_status_res.status_code == 200
        assert push_status_res.json()["inAppActive"] is True
        print("  -> PASS: GET /api/notifications/push-status returned valid status.")

        # POST /api/notifications/push-subscription
        sub_res = await client.post(
            "/api/notifications/push-subscription",
            json={
                "endpoint": "https://fcm.googleapis.com/fcm/send/test-sub-12345",
                "keys": {"p256dh": "mock_p256dh", "auth": "mock_auth"}
            },
            headers=headers_1
        )
        assert sub_res.status_code == 200
        assert sub_res.json()["success"] is True
        print("  -> PASS: POST /api/notifications/push-subscription saved subscription.")

        # DELETE /api/notifications/push-subscription
        del_sub_res = await client.delete("/api/notifications/push-subscription", headers=headers_1)
        assert del_sub_res.status_code == 200
        assert del_sub_res.json()["success"] is True
        print("  -> PASS: DELETE /api/notifications/push-subscription removed subscription.")

        # POST /api/notifications/irrigation-check
        check_cycle_res = await client.post("/api/notifications/irrigation-check", headers=headers_1)
        assert check_cycle_res.status_code == 200
        cycle_data = check_cycle_res.json()
        assert "checkedFarmers" in cycle_data
        assert "leaseAcquired" in cycle_data
        print(f"  -> PASS: POST /api/notifications/irrigation-check cycle executed (checked: {cycle_data['checkedFarmers']}).")

    print("\n" + "=" * 80)
    print("ALL PHASE 3 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_phase3_tests())
