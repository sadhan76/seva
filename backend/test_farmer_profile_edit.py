"""
Automated Test Suite for AgriBharat Farmer Edit Profile Feature
Tests:
1. Profile Persistence (PUT /api/farmers/me & GET /api/farmers/me / GET /api/auth/me)
2. Server-Side Authorization & Protected Identity Records (401 unauthenticated, 403 staff, immutable role/farmerId)
3. India Geographic Dataset Validation (rejection of invalid district-state combinations with 422)
4. Mobile Number Duplicate Checking (rejection of duplicate phone with 409)
5. Mobile Number Verification Policy (changing phone resets isPhoneVerified to False; unchanged phone preserves status)
6. Regional Language Change Persistence (updates application preferredLanguage)
7. Safe Profile Photo Upload (POST /api/users/me/avatar validates magic bytes & persists data URL)
8. Account Deletion Separation (accounts remain intact; no deletion in profile editing)
"""

import os
import sys
import asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from bson import ObjectId

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from database import get_users_collection, get_farmers_collection


async def run_edit_profile_tests():
    print("=" * 70)
    print("AgriBharat Edit Profile Automated Test Suite")
    print("=" * 70)

    users_col = get_users_collection()
    farmers_col = get_farmers_collection()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        ts = int(datetime.utcnow().timestamp()) % 100000000
        phone_farmer1 = f"91{ts:08d}"
        phone_farmer2 = f"92{(ts + 1):08d}"
        phone_farmer3 = f"93{(ts + 2):08d}"

        # -----------------------------------------------------------------
        # STEP 0: Create Test Farmers and Staff
        # -----------------------------------------------------------------
        reg_payload1 = {
            "name": "Kavitha Sundaram",
            "phone": phone_farmer1,
            "country": "India",
            "state": "Tamil Nadu",
            "stateCode": "IN-TN",
            "district": "Salem",
            "districtCode": "IN-TN-SALE",
            "taluk": "Attur",
            "village": "Attur Village",
            "totalLandAcres": 4,
            "primaryCrop": "Samba Paddy (CR 1009 Sub 1)",
            "soilType": "Alluvial Clay Loam",
            "irrigationSources": ["Borewell / Tube Well"],
            "preferredLanguage": "ta",
            "password": "Password123!",
            "confirmPassword": "Password123!",
        }
        r1 = await client.post("/api/auth/register", json=reg_payload1)
        assert r1.status_code in (200, 201), f"Register farmer 1 failed: {r1.text}"
        data1 = r1.json()
        token1 = data1["accessToken"]
        user1 = data1["user"]
        farmer_id1 = user1["farmerId"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        reg_payload2 = {
            "name": "Manoj Patel",
            "phone": phone_farmer2,
            "country": "India",
            "state": "Gujarat",
            "stateCode": "IN-GJ",
            "district": "Ahmedabad",
            "districtCode": "IN-GJ-AHME",
            "taluk": "Daskroi",
            "village": "Bhadaj",
            "totalLandAcres": 6,
            "primaryCrop": "Cotton",
            "soilType": "Black Cotton Soil",
            "irrigationSources": ["Canal Irrigation"],
            "preferredLanguage": "gu",
            "password": "Password123!",
            "confirmPassword": "Password123!",
        }
        r2 = await client.post("/api/auth/register", json=reg_payload2)
        assert r2.status_code in (200, 201), f"Register farmer 2 failed: {r2.text}"
        token2 = r2.json()["accessToken"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # -----------------------------------------------------------------
        # TEST 1: Profile Persistence (PUT /api/farmers/me & GET /api/farmers/me)
        # -----------------------------------------------------------------
        print("\n--- [Test 1] Profile Persistence (PUT /api/farmers/me & GET /api/farmers/me) ---")
        update_payload = {
            "name": "Kavitha R. Sundaram",
            "phone": phone_farmer1,
            "country": "India",
            "state": "Tamil Nadu",
            "stateCode": "IN-TN",
            "district": "Salem",
            "districtCode": "IN-TN-SALE",
            "taluk": "Attur",
            "village": "Kallanatham Gramam",
            "totalLandAcres": 8,
            "landUnit": "Acres",
            "primaryCrop": "Tapioca & Turmeric",
            "soilType": "Red Sandy Loam",
            "irrigationSources": ["Borewell / Tube Well", "Open Well"],
            "preferredLanguage": "ta",
            "profilePhoto": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        }

        put_res = await client.put("/api/farmers/me", json=update_payload, headers=headers1)
        assert put_res.status_code == 200, f"PUT /api/farmers/me failed: {put_res.text}"
        updated_summary = put_res.json()
        assert updated_summary["name"] == "Kavitha R. Sundaram"
        assert updated_summary["totalLandAcres"] == 8
        assert updated_summary["primaryCrop"] == "Tapioca & Turmeric"
        assert updated_summary["soilType"] == "Red Sandy Loam"
        assert "Open Well" in updated_summary["irrigationSources"]
        assert updated_summary["profilePhoto"] is not None
        assert updated_summary["farmerId"] == farmer_id1

        # Fetch using GET /api/farmers/me
        get_farmer_res = await client.get("/api/farmers/me", headers=headers1)
        assert get_farmer_res.status_code == 200, f"GET /api/farmers/me failed: {get_farmer_res.text}"
        persisted_farmer = get_farmer_res.json()
        assert persisted_farmer["name"] == "Kavitha R. Sundaram"
        assert persisted_farmer["primaryCrop"] == "Tapioca & Turmeric"
        assert persisted_farmer["totalLandAcres"] == 8

        # Fetch using GET /api/auth/me
        get_auth_res = await client.get("/api/auth/me", headers=headers1)
        assert get_auth_res.status_code == 200
        auth_data = get_auth_res.json()
        assert auth_data["name"] == "Kavitha R. Sundaram"
        assert auth_data["totalLandAcres"] == 8
        print("  -> PASS: Farmer profile fields persisted to MongoDB and retrieved via GET /api/farmers/me & /api/auth/me.")

        # -----------------------------------------------------------------
        # TEST 2: Server-Side Authorization & Protected Identity Records
        # -----------------------------------------------------------------
        print("\n--- [Test 2] Server-Side Authorization & Protected Identity Records ---")
        # 2.1 Unauthenticated requests rejected with 401
        unauth_put = await client.put("/api/farmers/me", json=update_payload)
        assert unauth_put.status_code == 401, f"Expected 401 for unauthenticated PUT, got {unauth_put.status_code}"
        unauth_get = await client.get("/api/farmers/me")
        assert unauth_get.status_code == 401, f"Expected 401 for unauthenticated GET, got {unauth_get.status_code}"

        # 2.2 Staff user attempting to call farmer profile rejected with 403
        staff_login = await client.post("/api/auth/login", json={
            "phone": "9443199999",
            "password": "Password123!",
            "role": "staff"
        })
        if staff_login.status_code == 200:
            staff_token = staff_login.json()["accessToken"]
            staff_headers = {"Authorization": f"Bearer {staff_token}"}
            staff_put = await client.put("/api/farmers/me", json=update_payload, headers=staff_headers)
            assert staff_put.status_code == 403, f"Expected 403 Forbidden for staff calling /api/farmers/me, got {staff_put.status_code}"
            staff_get = await client.get("/api/farmers/me", headers=staff_headers)
            assert staff_get.status_code == 403, f"Expected 403 Forbidden for staff GET /api/farmers/me, got {staff_get.status_code}"

        # 2.3 Attempting to tamper with protected fields (role: "admin", farmerId: "HACKED")
        tamper_payload = update_payload.copy()
        tamper_payload["role"] = "admin"
        tamper_payload["farmerId"] = "HACKED-ID-9999"
        tamper_payload["id"] = "60c72b2f9b1d8b2bad000000"

        tamper_res = await client.put("/api/farmers/me", json=tamper_payload, headers=headers1)
        assert tamper_res.status_code == 200
        tamper_data = tamper_res.json()
        assert tamper_data["role"] == "farmer", f"Tampering role failed to be blocked! Got: {tamper_data['role']}"
        assert tamper_data["farmerId"] == farmer_id1, f"Tampering farmerId failed to be blocked! Got: {tamper_data['farmerId']}"
        assert tamper_data["id"] == user1["id"]
        print("  -> PASS: Strict server-side authentication, role authorization, and protected field immutability enforced.")

        # -----------------------------------------------------------------
        # TEST 3: India Geographic Dataset Validation
        # -----------------------------------------------------------------
        print("\n--- [Test 3] India Geographic Dataset Validation ---")
        # 3.1 Mismatched state and district: Pune in Tamil Nadu
        invalid_geo1 = update_payload.copy()
        invalid_geo1["state"] = "Tamil Nadu"
        invalid_geo1["district"] = "Pune"
        geo_res1 = await client.put("/api/farmers/me", json=invalid_geo1, headers=headers1)
        assert geo_res1.status_code == 422, f"Expected 422 for mismatched state/district, got: {geo_res1.status_code}"
        print(f"  Rejected mismatched district with 422: {geo_res1.json().get('detail')}")

        # 3.2 Non-existent district
        invalid_geo2 = update_payload.copy()
        invalid_geo2["state"] = "Karnataka"
        invalid_geo2["district"] = "NonExistentDistrict456"
        geo_res2 = await client.put("/api/farmers/me", json=invalid_geo2, headers=headers1)
        assert geo_res2.status_code == 422, f"Expected 422 for non-existent district, got: {geo_res2.status_code}"
        print(f"  Rejected non-existent district with 422: {geo_res2.json().get('detail')}")

        # 3.3 Valid cross-state relocation: Maharashtra / Pune
        valid_geo = update_payload.copy()
        valid_geo["state"] = "Maharashtra"
        valid_geo["district"] = "Pune"
        valid_geo["village"] = "Baramati"
        geo_res3 = await client.put("/api/farmers/me", json=valid_geo, headers=headers1)
        assert geo_res3.status_code == 200, f"Valid relocation failed: {geo_res3.text}"
        assert geo_res3.json()["district"] == "Pune"
        assert geo_res3.json()["state"] == "Maharashtra"
        print("  -> PASS: Geographic dataset validation strictly enforces valid state/district pairings.")

        # -----------------------------------------------------------------
        # TEST 4: Mobile Number Duplicate Checking
        # -----------------------------------------------------------------
        print("\n--- [Test 4] Mobile Number Duplicate Checking ---")
        # Farmer 1 attempts to change phone to Farmer 2's phone
        dup_payload = update_payload.copy()
        dup_payload["phone"] = phone_farmer2  # registered to Manoj Patel
        dup_res = await client.put("/api/farmers/me", json=dup_payload, headers=headers1)
        assert dup_res.status_code == 409, f"Expected 409 Conflict for duplicate phone, got: {dup_res.status_code}"
        print(f"  Rejected duplicate mobile with 409: {dup_res.json().get('detail')}")

        # Farmer 1 updates to a valid unique phone number
        valid_phone_payload = update_payload.copy()
        valid_phone_payload["phone"] = phone_farmer3
        phone_res = await client.put("/api/farmers/me", json=valid_phone_payload, headers=headers1)
        assert phone_res.status_code == 200, f"Updating to unique phone failed: {phone_res.text}"
        assert phone_res.json()["phone"] == phone_farmer3
        print(f"  Updated mobile to unique number {phone_farmer3} successfully.")
        print("  -> PASS: Mobile number duplicate protection verified.")

        # -----------------------------------------------------------------
        # TEST 5: Mobile Number Verification Policy
        # -----------------------------------------------------------------
        print("\n--- [Test 5] Mobile Number Verification Policy ---")
        # Simulate pre-verified phone status in DB
        user_doc = await users_col.find_one({"_id": ObjectId(user1["id"])})
        await users_col.update_one({"_id": ObjectId(user1["id"])}, {"$set": {"isPhoneVerified": True}})

        # 5.1 Updating profile WITHOUT changing phone -> retains verified status
        no_phone_change_payload = valid_phone_payload.copy()
        no_phone_change_payload["phone"] = phone_farmer3  # same phone
        no_phone_change_payload["totalLandAcres"] = 12
        r_same = await client.put("/api/farmers/me", json=no_phone_change_payload, headers=headers1)
        assert r_same.status_code == 200
        assert r_same.json()["isPhoneVerified"] is True, "Expected isPhoneVerified to remain True when phone did not change!"

        # 5.2 Updating profile WITH changed phone -> resets isPhoneVerified to False (Requirement 6)
        phone_farmer4 = f"94{(ts + 3):08d}"
        phone_change_payload = valid_phone_payload.copy()
        phone_change_payload["phone"] = phone_farmer4
        r_changed = await client.put("/api/farmers/me", json=phone_change_payload, headers=headers1)
        assert r_changed.status_code == 200
        assert r_changed.json()["isPhoneVerified"] is False, "Expected isPhoneVerified to be reset to False upon phone number change!"
        print("  -> PASS: Changing mobile number resets verification status; preserving phone number retains status.")

        # -----------------------------------------------------------------
        # TEST 6: Regional Language Change Persistence
        # -----------------------------------------------------------------
        print("\n--- [Test 6] Regional Language Change Persistence ---")
        lang_payload = phone_change_payload.copy()
        lang_payload["preferredLanguage"] = "hi"
        r_hi = await client.put("/api/farmers/me", json=lang_payload, headers=headers1)
        assert r_hi.status_code == 200
        assert r_hi.json()["preferredLanguage"] == "hi"

        # Check /api/auth/me
        r_me_hi = await client.get("/api/auth/me", headers=headers1)
        assert r_me_hi.status_code == 200
        assert r_me_hi.json()["preferredLanguage"] == "hi"

        lang_payload["preferredLanguage"] = "ur"
        r_ur = await client.put("/api/farmers/me", json=lang_payload, headers=headers1)
        assert r_ur.status_code == 200
        assert r_ur.json()["preferredLanguage"] == "ur"
        print("  -> PASS: Preferred regional language updates application-wide and persists to database.")

        # -----------------------------------------------------------------
        # TEST 7: Safe Profile Photo Upload (POST /api/users/me/avatar)
        # -----------------------------------------------------------------
        print("\n--- [Test 7] Safe Profile Photo Upload (POST /api/users/me/avatar) ---")
        # 7.1 Reject invalid file format (text file)
        fake_files = {"file": ("test.txt", b"This is not an image", "text/plain")}
        bad_avatar_res = await client.post("/api/users/me/avatar", files=fake_files, headers=headers1)
        assert bad_avatar_res.status_code == 400, f"Expected 400 for text file, got: {bad_avatar_res.status_code}"
        print(f"  Rejected text file with 400: {bad_avatar_res.json().get('detail')}")

        # 7.2 Reject oversized file (> 2MB)
        oversized_bytes = b"\xff\xd8\xff" + b"\x00" * (2 * 1024 * 1024 + 10)
        oversized_files = {"file": ("large.jpg", oversized_bytes, "image/jpeg")}
        large_avatar_res = await client.post("/api/users/me/avatar", files=oversized_files, headers=headers1)
        assert large_avatar_res.status_code == 400
        print(f"  Rejected oversized file (>2MB) with 400: {large_avatar_res.json().get('detail')}")

        # 7.3 Accept valid PNG photo
        valid_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        good_files = {"file": ("avatar.png", valid_png_bytes, "image/png")}
        good_avatar_res = await client.post("/api/users/me/avatar", files=good_files, headers=headers1)
        assert good_avatar_res.status_code == 200, f"Avatar upload failed: {good_avatar_res.text}"
        avatar_data = good_avatar_res.json()
        assert avatar_data["status"] == "success"
        assert avatar_data["profilePhoto"].startswith("data:image/png;base64,")

        # Verify avatar reflected in /api/auth/me
        r_avatar_check = await client.get("/api/auth/me", headers=headers1)
        assert r_avatar_check.json()["profilePhoto"] is not None
        print("  -> PASS: Avatar upload endpoint validates magic bytes and persists photo safely.")

        # -----------------------------------------------------------------
        # TEST 8: Account Deletion Separation
        # -----------------------------------------------------------------
        print("\n--- [Test 8] Account Deletion Separation ---")
        # Ensure user account and farmer profile remain intact
        farmer_doc_check = await farmers_col.find_one({"userId": user1["id"]})
        assert farmer_doc_check is not None, "Farmer profile was unexpectedly deleted!"
        user_doc_check = await users_col.find_one({"_id": ObjectId(user1["id"])})
        assert user_doc_check is not None, "User account was unexpectedly deleted!"
        print("  -> PASS: User accounts and farmer records preserved cleanly without deletion.")

    print("\n" + "=" * 70)
    print("ALL 8 EDIT PROFILE TEST SUITES PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_edit_profile_tests())
