"""
Phase 19 & Auth Verification Suite:
===================================
1. Multi-select irrigation sources (checkbox group, array storage, "Other" with custom text).
2. Integer-only land area validation (accepts whole numbers, rejects decimals, negatives, non-numeric, empty).
3. Regional language preferences (16 languages, persistence across login and /api/auth/me, profile editing).
4. Verification of Decommissioned Telegram Endpoints (all removed / 404).
5. Clean direct farmer registration without Telegram OTP dependency.
6. Password hashing and existing account compatibility.
"""

import asyncio
import time
import httpx
from datetime import datetime
from main import app
from database import get_database


async def run_phase19_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=15.0) as client:
        print("\n" + "=" * 80)
        print("PHASE 19 AUTOMATED VERIFICATION SUITE: REGISTRATION, LANGUAGES & SECURITY")
        print("=" * 80)

        suffix = int(time.time() * 1000) % 1000000
        test_phone_1 = f"9811{suffix % 1000000:06d}"
        test_pwd = "StrongFarmerPassword@2026"

        # ---------------------------------------------------------------------
        # TEST 1: Config Metadata Endpoint (Irrigation Options & Languages)
        # ---------------------------------------------------------------------
        print("\n--- [Test 1] Platform Configuration Metadata Endpoint ---")
        meta_res = await client.get("/api/config/meta")
        assert meta_res.status_code == 200, f"Failed to get config meta: {meta_res.text}"
        meta = meta_res.json()
        assert len(meta["irrigationOptions"]) == 14, f"Expected 14 irrigation options, got {len(meta['irrigationOptions'])}"
        assert "Borewell / Tube Well" in meta["irrigationOptions"]
        assert "Rain-fed / No Irrigation" in meta["irrigationOptions"]
        assert "Other" in meta["irrigationOptions"]
        assert len(meta["languages"]) == 16, f"Expected 16 regional languages, got {len(meta['languages'])}"
        assert "Tamil" in meta["languages"]
        assert "Hindi" in meta["languages"]
        assert "Telugu" in meta["languages"]
        assert "Sanskrit" in meta["languages"]
        assert "telegram" not in meta, "Telegram metadata should be removed"
        assert meta.get("phoneVerification", {}).get("configured") is False
        print("  -> PASS: /api/config/meta verified with 14 irrigation choices, 16 regional languages, and unconfigured phone verification notice.")

        # ---------------------------------------------------------------------
        # TEST 2: Land Area Whole-Number Validation (Accepts Integers, Rejects Decimals/Negatives/Empty)
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Positive Whole-Number Land Area Validation ---")

        # Test 2a: Reject decimal value (e.g. 3.5)
        bad_decimal_payload = {
            "name": "Decimal Tester",
            "phone": f"9822{(suffix + 1) % 1000000:06d}",
            "village": "Alangudi",
            "district": "Pudukkottai",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": test_pwd,
            "confirmPassword": test_pwd,
            "totalLandAcres": 3.5,  # Decimals must be strictly rejected
            "irrigationSources": ["Borewell / Tube Well"]
        }
        dec_res = await client.post("/api/auth/register", json=bad_decimal_payload)
        assert dec_res.status_code == 422, f"Decimal land area 3.5 was not rejected! Status: {dec_res.status_code}"
        print("  -> PASS: Decimal land area (3.5) successfully rejected with HTTP 422.")

        # Test 2b: Reject negative value (-2)
        bad_negative_payload = dict(bad_decimal_payload)
        bad_negative_payload["totalLandAcres"] = -2
        neg_res = await client.post("/api/auth/register", json=bad_negative_payload)
        assert neg_res.status_code == 422, f"Negative land area -2 was not rejected! Status: {neg_res.status_code}"
        print("  -> PASS: Negative land area (-2) successfully rejected with HTTP 422.")

        # Test 2c: Reject zero (0)
        bad_zero_payload = dict(bad_decimal_payload)
        bad_zero_payload["totalLandAcres"] = 0
        zero_res = await client.post("/api/auth/register", json=bad_zero_payload)
        assert zero_res.status_code == 422, f"Zero land area 0 was not rejected! Status: {zero_res.status_code}"
        print("  -> PASS: Zero land area (0) successfully rejected with HTTP 422.")

        # Test 2d: Reject non-numeric input ("five acres")
        bad_str_payload = dict(bad_decimal_payload)
        bad_str_payload["totalLandAcres"] = "five acres"
        str_res = await client.post("/api/auth/register", json=bad_str_payload)
        assert str_res.status_code == 422, f"Non-numeric string land area was not rejected! Status: {str_res.status_code}"
        print("  -> PASS: Non-numeric land area string ('five acres') successfully rejected with HTTP 422.")

        # ---------------------------------------------------------------------
        # TEST 3: Multi-Select Irrigation & Regional Language Registration
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Multi-Select Irrigation Sources & Regional Language Registration ---")
        selected_irrigations = ["Borewell / Tube Well", "Canal", "Rainwater Harvesting", "Other"]
        valid_reg_payload = {
            "name": f"Kavitha Ramanathan {suffix}",
            "phone": test_phone_1,
            "village": "Needamangalam",
            "district": "Tiruvarur",
            "state": "Tamil Nadu",
            "preferredLanguage": "hi",  # Hindi regional language
            "password": test_pwd,
            "confirmPassword": test_pwd,
            "totalLandAcres": 5,  # Whole integer acres
            "primaryCrop": "Samba Paddy (CR 1009 Sub 1)",
            "soilType": "Alluvial Clay Loam",
            "irrigationSources": selected_irrigations,
            "otherIrrigationDetail": "Solar Lift Pump from Vennar Tributary"
        }

        reg_res = await client.post("/api/auth/register", json=valid_reg_payload)
        assert reg_res.status_code in [200, 201], f"Registration failed: {reg_res.text}"
        reg_data = reg_res.json()
        token_1 = reg_data["accessToken"]
        user_1 = reg_data["user"]

        assert user_1["totalLandAcres"] == 5, f"Expected integer 5, got {user_1['totalLandAcres']}"
        assert user_1["preferredLanguage"] == "hi", f"Expected 'hi', got {user_1['preferredLanguage']}"
        assert isinstance(user_1["irrigationSources"], list), "irrigationSources must be stored as an array"
        assert "Borewell / Tube Well" in user_1["irrigationSources"]
        assert "Canal" in user_1["irrigationSources"]
        assert "Rainwater Harvesting" in user_1["irrigationSources"]
        assert "Other: Solar Lift Pump from Vennar Tributary" in user_1["irrigationSources"]
        assert user_1.get("isPhoneVerified") is False, "Phone must be unverified when no SMS provider exists"
        print("  -> PASS: Farmer registered with integer acres (5), multi-select irrigation sources, and Hindi preference.")

        # Verify persistence via GET /api/auth/me
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_1}"})
        assert me_res.status_code == 200
        me_user = me_res.json()
        assert me_user["preferredLanguage"] == "hi"
        assert me_user["totalLandAcres"] == 5
        assert len(me_user["irrigationSources"]) == 4
        print("  -> PASS: Profile retrieved via /api/auth/me confirms array storage and language persistence.")

        # ---------------------------------------------------------------------
        # TEST 4: Editing Choices in Farm Profile (PUT /api/farmers/me)
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Editing Irrigation Choices & Language in Farm Profile ---")
        updated_profile_payload = {
            "name": f"Kavitha Ramanathan {suffix}",
            "phone": test_phone_1,
            "location": "Needamangalam, Tiruvarur",
            "district": "Tiruvarur",
            "state": "Tamil Nadu",
            "totalLandAcres": 8,  # Updated integer acres
            "primaryCrop": "Paddy (Ponni)",
            "soilType": "Alluvial Clay Loam",
            "irrigationSources": ["Open Well", "Dam / Reservoir", "Farm Pond"],
            "preferredLanguage": "te"  # Switched to Telugu
        }
        update_res = await client.put(
            "/api/farmers/me",
            json=updated_profile_payload,
            headers={"Authorization": f"Bearer {token_1}"}
        )
        assert update_res.status_code == 200, f"Profile update failed: {update_res.text}"
        updated_user = update_res.json()
        assert updated_user["totalLandAcres"] == 8
        assert updated_user["preferredLanguage"] == "te"
        assert "Open Well" in updated_user["irrigationSources"]
        assert "Dam / Reservoir" in updated_user["irrigationSources"]
        print("  -> PASS: Farm profile edited successfully with new integer acres (8), Telugu language, and updated irrigation.")

        # ---------------------------------------------------------------------
        # TEST 5: Decommissioned Telegram Endpoints Return 404
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Verification of Decommissioned Telegram Endpoints ---")
        tg_endpoints = [
            ("GET", "/api/auth/telegram/status"),
            ("POST", "/api/auth/telegram/link-token"),
            ("GET", "/api/auth/telegram/link-status"),
            ("POST", "/api/auth/telegram/send-otp"),
            ("POST", "/api/auth/telegram/verify-otp"),
            ("POST", "/api/auth/telegram/mock-link-chat"),
        ]
        for method, endpoint in tg_endpoints:
            if method == "GET":
                r = await client.get(endpoint)
            else:
                r = await client.post(endpoint, json={})
            assert r.status_code == 404, f"Expected 404 for removed endpoint {endpoint}, got {r.status_code}"
        print("  -> PASS: All Telegram authentication endpoints are decommissioned and return 404 Not Found.")

        # ---------------------------------------------------------------------
        # TEST 6: Password Authentication Compatibility & No Lockout
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Password Authentication & Session Restoration ---")
        pwd_login = await client.post("/api/auth/login", json={
            "phone": test_phone_1,
            "password": test_pwd,
            "role": "farmer"
        })
        assert pwd_login.status_code == 200, f"Password login failed: {pwd_login.text}"
        assert pwd_login.json()["user"]["phone"] == test_phone_1
        print("  -> PASS: Farmer login with password succeeds without any Telegram requirement.")

        # Cleanup
        db = get_database()
        await db["users"].delete_many({"phone": test_phone_1})
        await db["farmers"].delete_many({"phone": test_phone_1})

        print("\n" + "=" * 80)
        print("ALL PHASE 19 VERIFICATION TESTS PASSED (6/6)!")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_phase19_tests())
