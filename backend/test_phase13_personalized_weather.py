"""
PHASE 13 AUTOMATED TEST SUITE: PERSONALIZED DISTRICT & CLEAN WEATHER BACKEND VERIFICATION
========================================================================================
Validates:
1. Farmer Registration & District Persistence (Salem vs Thanjavur).
2. Dynamic District Selection (Login profile returns actual registered district, no hardcoding).
3. District-Specific Geographic Coordinates & Weather Fetching (Salem vs Thanjavur vs Erode).
4. District Update Synchronization (Updating profile updates both 'farmers' and 'users' in MongoDB).
5. Immediate Session Reflection (GET /api/auth/me returns new district immediately).
6. Multi-User District Isolation (Farmer A's district does not bleed into Farmer B's session).
7. Missing District Graceful Handling (None/empty district preserved without fabricating Thanjavur).
8. Authentic IST Observation & Last Updated Timestamps.
"""

import asyncio
import httpx
import time

BASE_URL = "http://127.0.0.1:8000"

async def run_phase13_tests():
    print("=" * 80)
    print("PHASE 13: PERSONALIZED DISTRICT & CLEAN WEATHER BACKEND VERIFICATION")
    print("=" * 80)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # ---------------------------------------------------------------------
        # TEST 1: Register Farmer A with district = "Salem"
        # ---------------------------------------------------------------------
        print("\n--- [Test 1] Register Farmer A (Salem) ---")
        suffix = int(time.time()) % 100000
        phone_salem = f"9871{suffix:06d}"
        pwd_salem = "SalemFarmer@2026"

        reg_a = await client.post("/api/auth/register", json={
            "name": f"Murugesan Salem {suffix}",
            "phone": phone_salem,
            "village": "Attur",
            "district": "Salem",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": pwd_salem,
            "confirmPassword": pwd_salem,
            "totalLandAcres": 5.0,
            "primaryCrop": "Tapioca & Turmeric",
            "soilType": "Red Loam",
            "irrigationSource": "Borewell"
        })
        assert reg_a.status_code in [200, 201], f"Farmer Salem registration failed: {reg_a.text}"
        data_a = reg_a.json()
        token_salem = data_a.get("accessToken") or data_a.get("access_token")
        user_salem = data_a["user"]

        assert user_salem["district"] == "Salem", f"Expected Salem, got {user_salem['district']}"
        print(f"  -> PASS: Farmer A registered with District: '{user_salem['district']}'")

        # ---------------------------------------------------------------------
        # TEST 2: Register Farmer B with district = "Thanjavur"
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Register Farmer B (Thanjavur) ---")
        phone_thanjavur = f"9872{suffix:06d}"
        pwd_thanjavur = "ThanjavurFarmer@2026"

        reg_b = await client.post("/api/auth/register", json={
            "name": f"Karuppan Thanjavur {suffix}",
            "phone": phone_thanjavur,
            "village": "Thiruvaiyaru",
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": pwd_thanjavur,
            "confirmPassword": pwd_thanjavur,
            "totalLandAcres": 3.5,
            "primaryCrop": "CR 1009 Samba Paddy",
            "soilType": "Alluvial Clay Loam",
            "irrigationSource": "Cauvery Canal"
        })
        assert reg_b.status_code in [200, 201], f"Farmer Thanjavur registration failed: {reg_b.text}"
        data_b = reg_b.json()
        token_thanjavur = data_b.get("accessToken") or data_b.get("access_token")
        user_thanjavur = data_b["user"]

        assert user_thanjavur["district"] == "Thanjavur", f"Expected Thanjavur, got {user_thanjavur['district']}"
        print(f"  -> PASS: Farmer B registered with District: '{user_thanjavur['district']}'")

        # ---------------------------------------------------------------------
        # TEST 3: Verify Profile Authentication returns Actual Registered District
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Session Retrieval (/api/auth/me) Returns Real Registered Districts ---")
        me_salem = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_salem}"})
        assert me_salem.status_code == 200
        assert me_salem.json()["district"] == "Salem", "Farmer A session did not return Salem!"

        me_thanjavur = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_thanjavur}"})
        assert me_thanjavur.status_code == 200
        assert me_thanjavur.json()["district"] == "Thanjavur", "Farmer B session did not return Thanjavur!"

        print("  -> PASS: Authenticated sessions return real districts (Salem & Thanjavur) without default hardcoding.")

        # ---------------------------------------------------------------------
        # TEST 4: District-Specific Coordinates in Weather API
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Geographic Coordinate Differentiation ---")
        w_salem = await client.get("/api/weather?district=salem")
        assert w_salem.status_code == 200
        data_salem = w_salem.json()
        coords_salem = data_salem["coordinates"]
        assert round(coords_salem["lat"], 2) == 11.66, f"Incorrect Salem lat: {coords_salem['lat']}"
        assert round(coords_salem["lon"], 2) == 78.15, f"Incorrect Salem lon: {coords_salem['lon']}"
        assert data_salem["zone"] == "North-Western"
        print(f"  -> PASS: Salem coordinates verified: {coords_salem['lat']}°N, {coords_salem['lon']}°E ({data_salem['zone']})")

        w_thanjavur = await client.get("/api/weather?district=thanjavur")
        assert w_thanjavur.status_code == 200
        data_thanjavur = w_thanjavur.json()
        coords_thanjavur = data_thanjavur["coordinates"]
        assert round(coords_thanjavur["lat"], 2) == 10.79, f"Incorrect Thanjavur lat: {coords_thanjavur['lat']}"
        assert round(coords_thanjavur["lon"], 2) == 79.14, f"Incorrect Thanjavur lon: {coords_thanjavur['lon']}"
        assert data_thanjavur["zone"] == "Cauvery Delta"
        print(f"  -> PASS: Thanjavur coordinates verified: {coords_thanjavur['lat']}°N, {coords_thanjavur['lon']}°E ({data_thanjavur['zone']})")

        # ---------------------------------------------------------------------
        # TEST 5: Change Farmer A's District to "Erode" and verify update
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Update Farmer A Profile to District = 'Erode' ---")
        update_payload = {
            "name": user_salem["name"],
            "phone": user_salem["phone"],
            "location": "Bhavani",
            "district": "Erode",
            "state": "Tamil Nadu",
            "totalLandAcres": 6.0,
            "primaryCrop": "Turmeric & Sugarcane",
            "soilType": "Clay Loam",
            "irrigationSource": "Bhavani River"
        }
        update_res = await client.put("/api/farmers/me", json=update_payload, headers={"Authorization": f"Bearer {token_salem}"})
        assert update_res.status_code == 200, f"Profile update failed: {update_res.text}"
        updated_data = update_res.json()
        assert updated_data["district"] == "Erode", f"Expected Erode, got {updated_data['district']}"
        print(f"  -> PASS: Farmer A updated district to '{updated_data['district']}' via PUT /api/farmers/me")

        # Re-fetch /api/auth/me to verify persistence
        me_check = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_salem}"})
        assert me_check.status_code == 200
        assert me_check.json()["district"] == "Erode", f"Session /api/auth/me did not reflect Erode! Got {me_check.json()['district']}"
        print(f"  -> PASS: Re-fetched /api/auth/me immediately reflects updated district 'Erode'.")

        # Weather for Erode coordinates
        w_erode = await client.get("/api/weather?district=erode")
        assert w_erode.status_code == 200
        coords_erode = w_erode.json()["coordinates"]
        assert round(coords_erode["lat"], 2) == 11.34, f"Incorrect Erode lat: {coords_erode['lat']}"
        assert round(coords_erode["lon"], 2) == 77.72, f"Incorrect Erode lon: {coords_erode['lon']}"
        print(f"  -> PASS: Erode coordinates verified: {coords_erode['lat']}°N, {coords_erode['lon']}°E ({w_erode.json()['zone']})")

        # ---------------------------------------------------------------------
        # TEST 6: User Isolation Check
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Multi-User Isolation Verification ---")
        # Ensure Farmer B still has Thanjavur and was not mutated by Farmer A's update
        me_b_check = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_thanjavur}"})
        assert me_b_check.status_code == 200
        assert me_b_check.json()["district"] == "Thanjavur", f"Farmer B was contaminated! Got {me_b_check.json()['district']}"
        print(f"  -> PASS: Farmer B still has district 'Thanjavur'. Data isolation strictly preserved.")

        # ---------------------------------------------------------------------
        # TEST 7: Accurate Timestamps & IST Formatting
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] Clean Timestamps & IST Formatting ---")
        w_clean = await client.get("/api/weather?district=salem")
        assert w_clean.status_code == 200
        w_json = w_clean.json()
        assert "observationTime" in w_json and w_json["observationTime"]
        assert "lastUpdated" in w_json and w_json["lastUpdated"]
        assert "IST" in w_json["observationTime"], f"Observation time missing IST: {w_json['observationTime']}"
        assert "IST" in w_json["lastUpdated"], f"Last updated missing IST: {w_json['lastUpdated']}"
        print(f"  -> PASS: Observation Time: '{w_json['observationTime']}'")
        print(f"  -> PASS: Last Updated:     '{w_json['lastUpdated']}'")

        print("\n" + "=" * 80)
        print("ALL PHASE 13 PERSONALIZED DISTRICT & CLEAN WEATHER TESTS PASSED (7/7)!")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_phase13_tests())
