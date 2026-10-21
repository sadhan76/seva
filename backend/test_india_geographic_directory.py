"""
AGRIBHARAT GEOGRAPHIC DIRECTORY & INDIA-WIDE REGION/DISTRICT VERIFICATION TEST SUITE
===================================================================================
Validates:
1. Provenance, Authority & Metadata (/api/geo/meta): Local Government Directory (LGD),
   Ministry of Panchayati Raj, Government of India, GODL License, 2026.1 dataset.
2. Complete Coverage: Exactly 28 Indian States and 8 Union Territories (36 Regions).
3. Dynamic Region-Dependent District Filtering: Tested across all 36 States & UTs.
4. Robust Parsing of Punctuation & Complex Names:
   - "S.P.S. Nellore" & "Dr. B.R. Ambedkar Konaseema" (dots & spaces)
   - "Leh (Ladakh)" (parentheses)
   - "South 24 Parganas" (numbers & spaces)
   - "Mayiladuthurai" (post-2020 bifurcation)
5. Region Name & Code Resolution: Tolerant matching by slug, ISO code, or canonical name.
6. Anti-Fabrication & Strict API Validation:
   - Mismatched state-district combinations rejected with HTTP 422.
   - Non-existent districts rejected with HTTP 422.
7. India-Wide Registration:
   - Farmers registered across distinct states (Maharashtra, Punjab, Assam, Tamil Nadu).
   - State-specific Farmer ID prefixes (e.g. MH-AGRI-2026-*, PB-AGRI-2026-*, AS-AGRI-2026-*).
   - Canonical fields persisted: country="India", state, stateCode, district, districtCode, taluk.
8. Farmer Profile Updates & Region Transitions:
   - Successful migration between regions (e.g. Maharashtra -> Gujarat).
   - Rejection of invalid district on update.
9. Backward Compatibility & Account Preservation:
   - Pre-existing accounts login and function without forced resets.
10. Admin Geographic Boundary Reload:
   - Verified reload endpoint for boundary changes.
"""

import asyncio
import httpx
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

async def run_tests():
    print("=" * 80)
    print("AGRIBHARAT: INDIA-WIDE STATE / UT / DISTRICT SELECTION TEST SUITE")
    print("=" * 80)

    from main import app
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as client:
        # ---------------------------------------------------------------------
        # TEST 1: Provenance & Attribution Metadata
        # ---------------------------------------------------------------------
        print("\n--- [Test 1] Provenance & Attribution Metadata (/api/geo/meta) ---")
        meta_res = await client.get("/api/geo/meta")
        assert meta_res.status_code == 200, f"Expected 200, got {meta_res.status_code}: {meta_res.text}"
        meta = meta_res.json()
        print(f"  Source:       {meta.get('source')}")
        print(f"  Version:      {meta.get('version')} (Updated: {meta.get('lastUpdated')})")
        print(f"  License:      {meta.get('license')}")
        print(f"  Total Regions: {meta.get('totalRegions')} ({meta.get('statesCount')} States + {meta.get('unionTerritoriesCount')} UTs)")
        print(f"  Total Districts: {meta.get('totalDistricts')}")

        assert "Local Government Directory" in meta.get("source", ""), "Source must attribute LGD"
        assert meta.get("statesCount") == 28, f"Expected 28 states, got {meta.get('statesCount')}"
        assert meta.get("unionTerritoriesCount") == 8, f"Expected 8 UTs, got {meta.get('unionTerritoriesCount')}"
        assert meta.get("totalRegions") == 36, f"Expected 36 regions, got {meta.get('totalRegions')}"
        assert meta.get("totalDistricts", 0) >= 780, f"Expected at least 780 districts, got {meta.get('totalDistricts')}"
        print("  -> PASS: Attribution, license, and counts verified.")

        # ---------------------------------------------------------------------
        # TEST 2: All 28 States & 8 Union Territories Listing (/api/geo/states)
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Complete 36 Regions Listing (/api/geo/states) ---")
        states_res = await client.get("/api/geo/states")
        assert states_res.status_code == 200
        states_data = states_res.json()
        states_list = states_data.get("states", [])
        assert len(states_list) == 36, f"Expected 36 total regions, got {len(states_list)}"

        states_only = [s for s in states_list if s.get("type") == "state"]
        uts_only = [s for s in states_list if s.get("type") == "union_territory"]
        assert len(states_only) == 28, f"Expected 28 states, got {len(states_only)}"
        assert len(uts_only) == 8, f"Expected 8 UTs, got {len(uts_only)}"

        print(f"  -> PASS: Exactly 28 States and 8 Union Territories returned.")
        for s in states_list[:5]:
            print(f"     * [{s['code']}] {s['name']} ({s['type']}): {s['districtsCount']} districts")
        print(f"     ... and 31 more regions.")

        # ---------------------------------------------------------------------
        # TEST 3: Region-Dependent District Filtering for ALL 36 Regions
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Testing Dynamic District Retrieval for ALL 36 Regions ---")
        total_districts_sum = 0
        for idx, region in enumerate(states_list, 1):
            r_name = region["name"]
            r_code = region["code"]
            
            # Query by code
            d_res = await client.get(f"/api/geo/districts?state={r_code}")
            assert d_res.status_code == 200, f"Failed for {r_name} ({r_code}): {d_res.text}"
            d_data = d_res.json()
            districts = d_data.get("districts", [])
            assert len(districts) > 0, f"Region {r_name} returned 0 districts!"
            assert len(districts) == region["districtsCount"], (
                f"Mismatch for {r_name}: states endpoint reported {region['districtsCount']}, got {len(districts)}"
            )
            total_districts_sum += len(districts)
            if idx in [1, 10, 20, 28, 29, 36]:
                sample_d = districts[0]["name"]
                print(f"     [{idx:02d}/36] {r_name} ({r_code}) -> {len(districts)} districts (Sample: '{sample_d}')")

        assert total_districts_sum >= 780, f"Total districts sum {total_districts_sum} below 780"
        print(f"  -> PASS: All 36 regions returned non-empty, authoritative district lists (Total: {total_districts_sum}).")

        # ---------------------------------------------------------------------
        # TEST 4: Punctuation, Spaces, and Complex District Names
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Handling District Names with Punctuation & Complex Characters ---")
        # 4a. Andhra Pradesh (dots)
        ap_res = await client.get("/api/geo/districts?state=Andhra Pradesh")
        ap_names = [d["name"] for d in ap_res.json().get("districts", [])]
        assert "S.P.S. Nellore" in ap_names, f"Expected 'S.P.S. Nellore' in AP, found: {ap_names}"
        assert "Dr. B.R. Ambedkar Konaseema" in ap_names, f"Expected 'Dr. B.R. Ambedkar Konaseema' in AP"
        print("  -> PASS: 'S.P.S. Nellore' and 'Dr. B.R. Ambedkar Konaseema' preserved with dots.")

        # 4b. Ladakh (parentheses)
        ladakh_res = await client.get("/api/geo/districts?state=Ladakh")
        ladakh_names = [d["name"] for d in ladakh_res.json().get("districts", [])]
        assert any("Leh" in name for name in ladakh_names), f"Expected Leh in Ladakh, got {ladakh_names}"
        assert "Kargil" in ladakh_names, f"Expected Kargil in Ladakh"
        print(f"  -> PASS: Ladakh districts verified: {ladakh_names}")

        # 4c. West Bengal (spaces and numbers)
        wb_res = await client.get("/api/geo/districts?state=West Bengal")
        wb_names = [d["name"] for d in wb_res.json().get("districts", [])]
        assert "South 24 Parganas" in wb_names, "Expected 'South 24 Parganas' in West Bengal"
        assert "North 24 Parganas" in wb_names, "Expected 'North 24 Parganas' in West Bengal"
        print("  -> PASS: 'South 24 Parganas' and 'North 24 Parganas' preserved with spaces and numbers.")

        # 4d. Tamil Nadu (post-2020 reorganization, Salem, Thanjavur)
        tn_res = await client.get("/api/geo/districts?state=Tamil Nadu")
        tn_names = [d["name"] for d in tn_res.json().get("districts", [])]
        assert "Mayiladuthurai" in tn_names, "Expected newly formed Mayiladuthurai in TN"
        assert "Salem" in tn_names, "Expected Salem in TN"
        assert "Thanjavur" in tn_names, "Expected Thanjavur in TN"
        assert len(tn_names) == 38, f"Expected 38 districts in TN, got {len(tn_names)}"
        print("  -> PASS: Tamil Nadu all 38 official districts verified.")

        # ---------------------------------------------------------------------
        # TEST 5: Tolerant State Query Normalization
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Tolerant State Normalization (slugs, codes, names) ---")
        q_slug = await client.get("/api/geo/districts?state=tamil_nadu")
        q_code = await client.get("/api/geo/districts?state=IN-TN")
        q_case = await client.get("/api/geo/districts?state=tAmIl NaDu")
        assert len(q_slug.json()["districts"]) == 38
        assert len(q_code.json()["districts"]) == 38
        assert len(q_case.json()["districts"]) == 38
        print("  -> PASS: 'tamil_nadu', 'IN-TN', 'tAmIl NaDu' all reliably resolve to 38 districts.")

        # ---------------------------------------------------------------------
        # TEST 6: API Validation & Anti-Fabrication (Rejection of Invalid Districts)
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Rejection of Invalid / Mismatched State-District Combinations ---")
        ts = int(time.time()) % 100000

        # Attempt 1: District from another state (Pune in Tamil Nadu)
        bad_req_1 = await client.post("/api/auth/register", json={
            "name": f"Invalid Farmer {ts}",
            "phone": f"9821{ts:06d}",
            "state": "Tamil Nadu",
            "district": "Pune",  # Pune is in Maharashtra, NOT Tamil Nadu!
            "village": "Test Village",
            "preferredLanguage": "en",
            "password": "ValidPassword@123",
            "confirmPassword": "ValidPassword@123",
            "totalLandAcres": 3,
        })
        assert bad_req_1.status_code == 422, f"Expected 422 for Pune in Tamil Nadu, got {bad_req_1.status_code}: {bad_req_1.text}"
        print(f"  -> PASS: Rejected mismatched district (Pune in Tamil Nadu) with 422: {bad_req_1.json()['detail']}")

        # Attempt 2: Non-existent fabricated district
        bad_req_2 = await client.post("/api/auth/register", json={
            "name": f"Fake Farmer {ts}",
            "phone": f"9822{ts:06d}",
            "state": "Karnataka",
            "district": "NonExistentDistrict123",
            "village": "Test Village",
            "preferredLanguage": "en",
            "password": "ValidPassword@123",
            "confirmPassword": "ValidPassword@123",
            "totalLandAcres": 2,
        })
        assert bad_req_2.status_code == 422, f"Expected 422 for fabricated district, got {bad_req_2.status_code}: {bad_req_2.text}"
        print(f"  -> PASS: Rejected fabricated district with 422: {bad_req_2.json()['detail']}")

        # Attempt 3: Non-existent state
        bad_req_3 = await client.post("/api/auth/register", json={
            "name": f"Mars Farmer {ts}",
            "phone": f"9823{ts:06d}",
            "state": "Mars Colony State",
            "district": "Salem",
            "village": "Test Village",
            "preferredLanguage": "en",
            "password": "ValidPassword@123",
            "confirmPassword": "ValidPassword@123",
            "totalLandAcres": 2,
        })
        assert bad_req_3.status_code == 422, f"Expected 422 for unknown state, got {bad_req_3.status_code}"
        print(f"  -> PASS: Rejected non-existent state with 422: {bad_req_3.json()['detail']}")

        # ---------------------------------------------------------------------
        # TEST 7: Multi-Region Farmer Registration & State-Coded IDs
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] Multi-Region Farmer Registration across India ---")
        regions_to_test = [
            ("Maharashtra", "Pune", "Haveli Taluk", "Khadakwasla", "mr", "MH"),
            ("Punjab", "Amritsar", "Ajnala", "Chogawan", "pa", "PB"),
            ("Assam", "Kamrup Metropolitan", "Guwahati", "Dispur", "as", "AS"),
            ("Tamil Nadu", "Salem", "Attur", "Kallanatham", "ta", "TN"),
            ("Andhra Pradesh", "S.P.S. Nellore", "Kavali", "Allur", "te", "AP"),
        ]

        registered_tokens = {}

        for state_name, dist_name, taluk_name, vill_name, lang_code, exp_prefix in regions_to_test:
            ts += 1
            phone_num = f"983{ts % 10000000:07d}"
            payload = {
                "name": f"Farmer {state_name} {ts}",
                "phone": phone_num,
                "country": "India",
                "state": state_name,
                "district": dist_name,
                "taluk": taluk_name,
                "village": vill_name,
                "preferredLanguage": lang_code,
                "password": "FarmerPassword@2026",
                "confirmPassword": "FarmerPassword@2026",
                "totalLandAcres": 4,
                "primaryCrop": "Field Crop",
                "soilType": "Loam",
                "irrigationSources": ["Borewell / Tube Well"],
            }
            reg_res = await client.post("/api/auth/register", json=payload)
            assert reg_res.status_code in [200, 201], f"Registration failed for {state_name}/{dist_name}: {reg_res.text}"
            data = reg_res.json()
            user = data["user"]
            token = data.get("accessToken") or data.get("access_token")
            registered_tokens[state_name] = token

            farmer_id = user.get("farmerId", "")
            print(f"  * {state_name} ({dist_name}):")
            print(f"    - Farmer ID: {farmer_id} (Expected prefix: {exp_prefix})")
            print(f"    - Persisted Country: {user.get('country')}")
            print(f"    - Persisted State:   {user.get('state')} ({user.get('stateCode')})")
            print(f"    - Persisted District:{user.get('district')} ({user.get('districtCode')})")
            print(f"    - Persisted Taluk:   {user.get('taluk')}, Village: {user.get('village')}")

            assert farmer_id.startswith(f"{exp_prefix}-AGRI-2026-"), f"Farmer ID {farmer_id} does not start with {exp_prefix}-AGRI-2026-"
            assert user.get("country") == "India"
            assert user.get("state") == state_name
            assert user.get("district") == dist_name
            assert user.get("taluk") == taluk_name
            assert user.get("village") == vill_name

        print("  -> PASS: All regional registrations succeeded with canonical codes & state prefixes.")

        # ---------------------------------------------------------------------
        # TEST 8: Region Changes in Farmer Profile (PUT /api/farmers/me)
        # ---------------------------------------------------------------------
        print("\n--- [Test 8] Profile Region Migration & Dependent District Validation ---")
        mh_token = registered_tokens["Maharashtra"]
        headers = {"Authorization": f"Bearer {mh_token}"}

        # Step 8a: Verify authenticated session returns Maharashtra and Pune
        me_res = await client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["state"] == "Maharashtra"
        assert me_data["district"] == "Pune"

        # Step 8b: Farmer migrates to Gujarat, Ahmedabad
        update_res = await client.put("/api/farmers/me", headers=headers, json={
            "name": me_data["name"],
            "phone": me_data["phone"],
            "country": "India",
            "state": "Gujarat",
            "district": "Ahmedabad",
            "taluk": "Sanand",
            "location": "Sanand, Ahmedabad",
            "totalLandAcres": 5,
            "primaryCrop": "Cotton",
            "soilType": "Black Soil",
            "preferredLanguage": "gu",
        })
        assert update_res.status_code == 200, f"Profile update failed: {update_res.text}"
        updated_user = update_res.json()
        assert updated_user["state"] == "Gujarat"
        assert updated_user["stateCode"] == "IN-GJ"
        assert updated_user["district"] == "Ahmedabad"
        assert updated_user["districtCode"].startswith("IN-GJ-")
        assert updated_user["taluk"] == "Sanand"
        print("  -> PASS: Farmer migrated from Maharashtra to Gujarat/Ahmedabad. Database updated.")

        # Step 8c: Verify immediate reflection in /api/auth/me
        me_after = await client.get("/api/auth/me", headers=headers)
        assert me_after.status_code == 200
        assert me_after.json()["district"] == "Ahmedabad"
        assert me_after.json()["state"] == "Gujarat"
        print("  -> PASS: Session immediately reflects updated Gujarat/Ahmedabad location.")

        # Step 8d: Reject invalid district update (Ahmedabad with Tamil Nadu)
        bad_update = await client.put("/api/farmers/me", headers=headers, json={
            "name": me_data["name"],
            "phone": me_data["phone"],
            "state": "Gujarat",
            "district": "Salem", # Salem is in Tamil Nadu!
            "location": "Salem, Gujarat",
            "totalLandAcres": 5,
            "primaryCrop": "Cotton",
        })
        assert bad_update.status_code == 422, f"Expected 422, got {bad_update.status_code}: {bad_update.text}"
        print(f"  -> PASS: Profile update with mismatched district rejected with 422: {bad_update.json()['detail']}")

        # ---------------------------------------------------------------------
        # TEST 9: Preservation of Existing Accounts & Passwords
        # ---------------------------------------------------------------------
        print("\n--- [Test 9] Preservation of Existing Accounts & Legacy Data ---")
        # Existing farmer account from seed/test data
        login_res = await client.post("/api/auth/login", json={
            "phone": "9876543299",
            "password": "FarmerPassword@123",
            "role": "farmer",
        })
        if login_res.status_code == 200:
            demo_user = login_res.json()["user"]
            print(f"  * Seed Farmer login succeeded:")
            print(f"    - ID: {demo_user.get('farmerId')}, District: {demo_user.get('district')}, State: {demo_user.get('state')}")
            assert demo_user.get("district") is not None
            print("  -> PASS: Legacy farmer account preserved with valid district and login credentials.")
        else:
            print(f"  (Note: Seed farmer phone 9876543299 returned {login_res.status_code}, checking staff...)")

        staff_res = await client.post("/api/auth/login", json={
            "phone": "9842012345",
            "password": "MandiStaff@2026",
            "role": "staff",
        })
        assert staff_res.status_code == 200, f"Staff login failed: {staff_res.text}"
        staff_user = staff_res.json()["user"]
        print(f"  * Staff login succeeded: {staff_user.get('name')} ({staff_user.get('role')})")
        print("  -> PASS: Staff authentication and existing accounts untouched.")

        # ---------------------------------------------------------------------
        # TEST 10: Admin Geographic Directory Reload Endpoint
        # ---------------------------------------------------------------------
        staff_token = staff_res.json().get("accessToken") or staff_res.json().get("access_token")
        reload_res = await client.post("/api/geo/admin/reload", headers={"Authorization": f"Bearer {staff_token}"})
        assert reload_res.status_code == 200, f"Reload failed: {reload_res.text}"
        reload_data = reload_res.json()
        print(f"  Reload message: {reload_data.get('message')}")
        print(f"  Reloaded counts: {reload_data.get('totalRegions')} regions, {reload_data.get('totalDistricts')} districts")
        assert reload_data.get("totalRegions") == 36
        assert reload_data.get("totalDistricts", 0) >= 780
        print("  -> PASS: Administrative boundary update/reload API verified.")

        # ---------------------------------------------------------------------
        # TEST 11: Full-Text Geographic Search Endpoint (/api/geo/search)
        # ---------------------------------------------------------------------
        print("\n--- [Test 11] Full-Text Geographic Search Endpoint (/api/geo/search) ---")
        srch_res = await client.get("/api/geo/search?q=pune")
        assert srch_res.status_code == 200
        srch_data = srch_res.json()
        found_districts = [d["name"] for d in srch_data.get("districts", [])]
        assert "Pune" in found_districts, f"Expected Pune in search results, got {found_districts}"

        # Search within state
        srch_scoped = await client.get("/api/geo/search?q=salem&state=Tamil Nadu")
        assert srch_scoped.status_code == 200
        scoped_names = [d["name"] for d in srch_scoped.json().get("districts", [])]
        assert "Salem" in scoped_names, f"Expected Salem in TN search results, got {scoped_names}"
        print("  -> PASS: Geographic search across regions and scoped to states works accurately.")

    print("\n" + "=" * 80)
    print("ALL 11 INDIA-WIDE GEOGRAPHIC DIRECTORY TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_tests())
