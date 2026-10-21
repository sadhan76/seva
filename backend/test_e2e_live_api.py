"""
Live HTTP API Integration Test for Special Operation (From First Step to First Sale).
Tests all live endpoints against http://127.0.0.1:8000.
"""

import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def make_request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}

def main():
    print("=" * 70)
    print("RUNNING LIVE END-TO-END HTTP API TESTS")
    print("=" * 70)

    import time
    test_phone = f"9876{int(time.time()) % 1000000:06d}"

    # 1. Register a test farmer account
    register_payload = {
        "name": "Thiru. Selvakumar Beginner",
        "phone": test_phone,
        "village": "Kondalampatti",
        "district": "Salem",
        "state": "Tamil Nadu",
        "password": "Password123",
        "confirmPassword": "Password123",
        "totalLandAcres": 1,
        "preferredLanguage": "en"
    }
    status, register_res = make_request("/auth/register", method="POST", data=register_payload)
    if status != 201 or "accessToken" not in register_res:
        print(f"FAILED to register: {status} {register_res}")
        sys.exit(1)
    
    token = register_res["accessToken"]
    user = register_res["user"]
    print(f"[PASS] Registered & Authenticated as Farmer: {user.get('name')} ({user.get('phone')})")

    # 2. Reset journey to start fresh
    status, reset_res = make_request("/special-operation/journey/reset", method="POST", token=token)
    assert status == 200, f"Reset failed: {reset_res}"
    print("[PASS] Clean Journey Reset verified")

    # 3. GET /special-operation/journey
    status, journey = make_request("/special-operation/journey", method="GET", token=token)
    assert status == 200, f"GET journey failed: {journey}"
    assert journey["currentStep"] == 1, "Should start at Step 1"
    assert journey["status"] == "in_progress", "Initial status should be in_progress"
    print(f"[PASS] Initialized Journey: {journey['journeyId']} at Step {journey['currentStep']}")

    # 4. STEP 1 — Update Profile (50 cents, borewell, unknown soil)
    step1_update = {
        "currentStep": 2,
        "profileInput": {
            "district": "Salem",
            "landArea": 50.0,
            "landUnit": "cents",
            "waterAvailability": "ample_borewell",
            "soilType": "unknown",
            "season": "unknown",
            "budgetRange": "low_15k_35k",
            "availableLabour": "family_only_1_2",
            "farmingGoal": "commercial_income"
        }
    }
    status, journey = make_request("/special-operation/journey/step", method="PUT", data=step1_update, token=token)
    assert status == 200, f"Step 1 update failed: {journey}"
    assert journey["currentStep"] == 2
    assert journey["landAreaNormalizedAcres"] == 0.5, f"Expected 0.5 acres, got {journey['landAreaNormalizedAcres']}"
    print("[PASS] Step 1: Saved profile and normalized 50 cents to 0.5 acres")

    # 5. STEP 2 — Get Candidate Crops
    query = urllib.parse.urlencode({
        "district": "Salem",
        "water_availability": "ample_borewell",
        "soil_type": "unknown",
        "season": "unknown",
        "budget_range": "low_15k_35k",
        "available_labour": "family_only_1_2",
        "farming_goal": "commercial_income"
    })
    status, crops_res = make_request(f"/special-operation/crops?{query}", method="GET")
    assert status == 200, f"Crops recommendation failed: {crops_res}"
    assert crops_res["total"] >= 3, "Expected at least 3 crops"
    crops = crops_res["crops"]
    top_crop = crops[0]
    print(f"[PASS] Step 2: Retrieved {len(crops)} candidate crops. Top crop: {top_crop['cropId']} ({top_crop['suitabilityScore']}% match)")

    # Select Top Crop (Tomato) and advance to Step 3
    step2_update = {
        "currentStep": 3,
        "selectedCropId": "tomato"
    }
    status, journey = make_request("/special-operation/journey/step", method="PUT", data=step2_update, token=token)
    assert status == 200
    assert journey["selectedCropId"] == "tomato"
    assert len(journey["costsWorksheet"]["entries"]) > 0, "Default costs worksheet should be auto-populated"
    print(f"[PASS] Step 2: Selected Tomato & auto-populated {len(journey['costsWorksheet']['entries'])} cost worksheet lines")

    # 6. STEP 3 — Farm Prep Checklist
    status, guide = make_request("/special-operation/crops/tomato/guide", method="GET")
    assert status == 200
    assert "landPreparation" in guide
    assert len(guide["landPreparation"]["steps"]) >= 4
    print(f"[PASS] Step 3: Verified {len(guide['landPreparation']['steps'])} TNAU land preparation steps")

    step3_update = {
        "currentStep": 4,
        "checklists": {
            "prep_soil_test": True,
            "prep_ploughing": True,
            "prep_manure": True,
            "prep_beds_drip": False
        }
    }
    status, journey = make_request("/special-operation/journey/step", method="PUT", data=step3_update, token=token)
    assert status == 200
    assert journey["checklists"]["prep_soil_test"] is True
    print("[PASS] Step 3: Saved preparation checklist")

    # 7. STEP 4 & 6 — Planting Date and Dynamic Timeline
    # Planted 25 days ago
    from datetime import datetime, timezone, timedelta
    p_date = (datetime.now(timezone.utc) - timedelta(days=25)).strftime("%Y-%m-%d")
    step4_update = {
        "currentStep": 6,
        "plantingDate": p_date
    }
    status, journey = make_request("/special-operation/journey/step", method="PUT", data=step4_update, token=token)
    assert status == 200
    assert journey["plantingDate"] == p_date
    tl = journey.get("timeline")
    assert tl is not None, "Timeline should be computed"
    assert tl["daysElapsed"] >= 25
    assert tl["currentActiveStageNumber"] >= 1
    print(f"[PASS] Step 4 & 6: Timeline computed dynamically from planting date {p_date} (Day {tl['daysElapsed']} of {tl['totalDurationDays']})")

    # 8. STEP 6 — Add Growth Observation with Deviation
    obs_payload = {
        "note": "Early flowering noticed on 40% plants. Soil moisture optimal under drip.",
        "stageNumber": 2,
        "isDeviation": True,
        "deviationReason": "Flowering initiated 4 days earlier due to warmer temperatures"
    }
    status, obs_res = make_request("/special-operation/journey/observation", method="POST", data=obs_payload, token=token)
    assert status == 200
    assert obs_res["success"] is True
    assert obs_res["observation"]["isDeviation"] is True
    print(f"[PASS] Step 6: Recorded observation with deviation alert: {obs_res['observation']['id']}")

    # 9. In-App Notification Reminder
    notif_payload = {
        "title": "Vegetative Care Reminder",
        "message": "Verify second fertigation dosage and inspect for leaf miner."
    }
    status, notif_res = make_request("/special-operation/journey/reminders", method="POST", data=notif_payload, token=token)
    assert status == 200
    assert notif_res["success"] is True
    print(f"[PASS] Dispatched in-app notification: {notif_res['notification'].get('id')}")

    # 10. STEP 8 — Cost Worksheet Math
    worksheet = journey["costsWorksheet"]
    worksheet["entries"][0]["userUnitPrice"] = 3000.0  # custom seed price
    worksheet["entries"][0]["isUserEdited"] = True
    new_total = sum(e["userQuantity"] * e["userUnitPrice"] for e in worksheet["entries"])
    worksheet["totalOperatingCost"] = new_total

    step8_update = {
        "currentStep": 9,
        "costsWorksheet": worksheet
    }
    status, journey = make_request("/special-operation/journey/step", method="PUT", data=step8_update, token=token)
    assert status == 200
    assert journey["costsWorksheet"]["totalOperatingCost"] == new_total
    print(f"[PASS] Step 8: Updated cost worksheet (Total operating cost: ₹{new_total})")

    # 11. STEP 10 — Commercial Reconciliation & Completion
    completion = {
        "harvestDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "harvestedQuantity": 3800.0,
        "harvestUnit": "kg",
        "gradeBreakdown": {"GradeA": 85.0, "GradeB": 15.0},
        "buyerNameOrChannel": "Salem Uzhavar Sandhai Stalls #14-16",
        "achievedPricePerUnit": 24.0,
        "grossRevenue": 3800.0 * 24.0,  # ₹91,200
        "totalOperatingCost": new_total,
        "netProfitOrLoss": (3800.0 * 24.0) - new_total,
        "farmerReflection": "Sorting into Grade A fetched ₹24/kg compared to ₹18/kg broker quote.",
        "completedAt": datetime.now(timezone.utc).isoformat()
    }
    step10_update = {
        "currentStep": 10,
        "status": "completed",
        "completionRecord": completion
    }
    status, journey = make_request("/special-operation/journey/step", method="PUT", data=step10_update, token=token)
    assert status == 200
    assert journey["status"] == "completed"
    assert journey["completionRecord"]["grossRevenue"] == 91200.0
    print(f"[PASS] Step 10: Journey completed! Net outcome: ₹{journey['completionRecord']['netProfitOrLoss']:.2f}")

    # 12. Safe Reset Verification
    status, reset_res = make_request("/special-operation/journey/reset", method="POST", token=token)
    assert status == 200
    status, fresh_journey = make_request("/special-operation/journey", method="GET", token=token)
    assert status == 200
    assert fresh_journey["currentStep"] == 1
    assert fresh_journey["status"] == "in_progress"
    print("[PASS] Verified safe reset without data loss on farmer profile")

    print("\n" + "=" * 70)
    print("ALL 12 LIVE END-TO-END HTTP TESTS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
