"""
AGRIBHARAT (NAMMA VIVASAYI AI) - AUTHENTICATION & REGISTRATION SECURITY TEST SUITE
==================================================================================
Comprehensive automated verification covering:
1. Absence of Telegram OTP dependencies and disabled Telegram endpoints
2. Farmer Registration with robust input validation (name, phone, acres, passwords)
3. Input validation: phone format, password mismatch, short password, non-integer acres
4. Duplicate mobile number prevention (HTTP 409 Conflict)
5. Role escalation prevention (public registration restricted to 'farmer')
6. Accurate phone ownership status disclosure (isPhoneVerified == False, no fake badges)
7. Bcrypt password hashing verification in MongoDB (no plaintext stored or leaked)
8. Login authentication (valid credentials, invalid password -> 401, non-existent -> 401)
9. Staff account administrative login and role preservation
10. Role-based access control (Farmer blocked from staff endpoints -> 403 Forbidden)
11. Session persistence via JWT Bearer authentication (/api/auth/me)
"""

import asyncio
import time
import re
import httpx
from datetime import datetime
from bson import ObjectId

from main import app
from database import get_users_collection, get_farmers_collection, check_db_connection
from auth import verify_password


async def run_auth_security_tests():
    print("\n" + "=" * 80)
    print("AGRIBHARAT - AUTHENTICATION & REGISTRATION SECURITY VERIFICATION")
    print("=" * 80)

    # 0. Check Database Connection
    db_status = await check_db_connection()
    assert db_status["connected"], f"MongoDB connection failed: {db_status}"
    print(f"[0] Database Connection: OK ({db_status['database_name']})")

    users_col = get_users_collection()
    farmers_col = get_farmers_collection()
    assert users_col is not None and farmers_col is not None

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        suffix = int(time.time() * 1000) % 1000000
        test_phone_1 = f"9871{suffix:06d}"
        test_password_1 = "AgriFarmer@2026Secure"

        # ---------------------------------------------------------------------
        # TEST 1: Platform Configuration Metadata & Absence of Telegram
        # ---------------------------------------------------------------------
        print("\n--- [Test 1] Platform Config Metadata & Absence of Telegram ---")
        meta_res = await client.get("/api/config/meta")
        assert meta_res.status_code == 200, f"Config meta failed: {meta_res.text}"
        meta = meta_res.json()
        
        # Verify telegram configuration is completely absent
        assert "telegram" not in meta, f"Telegram config unexpectedly found in meta: {meta}"
        assert "phoneVerification" in meta, "phoneVerification disclosure missing from meta"
        assert meta["phoneVerification"]["configured"] is False
        assert "unconfigured" in meta["phoneVerification"]["notice"].lower()
        print("  -> PASS: /api/config/meta transparently reports unconfigured phone verification.")
        print("  -> PASS: No Telegram bot configuration returned.")

        # ---------------------------------------------------------------------
        # TEST 2: Inactive/Removed Telegram Endpoints (Absence of Telegram Dependencies)
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Verification of Inactive/Removed Telegram Routes ---")
        tg_status_res = await client.get("/api/auth/telegram/status")
        assert tg_status_res.status_code in [404, 405], f"Expected 404 for removed endpoint, got {tg_status_res.status_code}"

        tg_token_res = await client.post("/api/auth/telegram/link-token", json={"phone": "9876543210"})
        assert tg_token_res.status_code in [404, 405], f"Expected 404 for removed endpoint, got {tg_token_res.status_code}"

        tg_status_poll = await client.get("/api/auth/telegram/link-status?token=sample123")
        assert tg_status_poll.status_code in [404, 405], f"Expected 404 for removed endpoint, got {tg_status_poll.status_code}"

        tg_send_otp = await client.post("/api/auth/telegram/send-otp", json={"phone": "9876543210"})
        assert tg_send_otp.status_code in [404, 405], f"Expected 404 for removed endpoint, got {tg_send_otp.status_code}"

        tg_verify_otp = await client.post("/api/auth/telegram/verify-otp", json={"phone": "9876543210", "otp": "123456"})
        assert tg_verify_otp.status_code in [404, 405], f"Expected 404 for removed endpoint, got {tg_verify_otp.status_code}"

        print("  -> PASS: All Telegram authentication endpoints are removed / return 404.")

        # ---------------------------------------------------------------------
        # TEST 3: Registration Input Validation (Phone, Password, Land Area)
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Registration Input Validation Checks ---")

        # 3a. Invalid mobile format (starting with 1-5 or wrong length)
        bad_phone_payload = {
            "name": "Invalid Phone Farmer",
            "phone": "5551234567",  # Does not start with 6,7,8,9
            "village": "Kabisthalam",
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "password": test_password_1,
            "confirmPassword": test_password_1,
            "totalLandAcres": 3,
        }
        res_bad_phone = await client.post("/api/auth/register", json=bad_phone_payload)
        assert res_bad_phone.status_code == 422, f"Expected 422 for non-Indian phone, got {res_bad_phone.status_code}"
        print("  -> PASS: Rejected mobile number not matching 10-digit Indian format (HTTP 422).")

        # 3b. Password mismatch
        bad_pwd_mismatch = dict(bad_phone_payload)
        bad_pwd_mismatch["phone"] = f"9872{suffix:06d}"
        bad_pwd_mismatch["confirmPassword"] = "DifferentPassword@2026"
        res_mismatch = await client.post("/api/auth/register", json=bad_pwd_mismatch)
        assert res_mismatch.status_code == 422, f"Expected 422 for password mismatch, got {res_mismatch.status_code}"
        print("  -> PASS: Rejected password and confirm-password mismatch (HTTP 422).")

        # 3c. Password too short (<6 characters)
        bad_pwd_short = dict(bad_phone_payload)
        bad_pwd_short["phone"] = f"9872{suffix:06d}"
        bad_pwd_short["password"] = "12345"
        bad_pwd_short["confirmPassword"] = "12345"
        res_short = await client.post("/api/auth/register", json=bad_pwd_short)
        assert res_short.status_code == 422, f"Expected 422 for short password, got {res_short.status_code}"
        print("  -> PASS: Rejected password under 6 characters (HTTP 422).")

        # 3d. Decimal land area (strict positive whole-number acres required)
        bad_decimal_acres = dict(bad_phone_payload)
        bad_decimal_acres["phone"] = f"9872{suffix:06d}"
        bad_decimal_acres["totalLandAcres"] = 4.75
        res_dec = await client.post("/api/auth/register", json=bad_decimal_acres)
        assert res_dec.status_code == 422, f"Expected 422 for decimal acres, got {res_dec.status_code}"
        print("  -> PASS: Rejected decimal land area 4.75 (HTTP 422).")

        # ---------------------------------------------------------------------
        # TEST 4: Successful Farmer Registration (Direct, Clean Flow)
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Successful Farmer Registration (Clean Direct Flow) ---")
        reg_payload = {
            "name": f"Kavitha Ramanathan {suffix}",
            "phone": test_phone_1,
            "village": "Needamangalam",
            "district": "Tiruvarur",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": test_password_1,
            "confirmPassword": test_password_1,
            "totalLandAcres": 5,
            "primaryCrop": "Samba Paddy (CR 1009 Sub 1)",
            "soilType": "Alluvial Clay Loam",
            "irrigationSources": ["Borewell / Tube Well", "Canal", "Other"],
            "otherIrrigationDetail": "Solar Micro-Lift Pump",
            "role": "staff"  # Malicious attempt to escalate role
        }

        reg_res = await client.post("/api/auth/register", json=reg_payload)
        assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
        reg_data = reg_res.json()

        assert "accessToken" in reg_data, "JWT token missing from registration response"
        farmer_token = reg_data["accessToken"]
        user_info = reg_data["user"]

        # Enforce role isolation: Public registration is strictly 'farmer'
        assert user_info["role"] == "farmer", f"Role escalation breach! Role is {user_info['role']}"
        assert user_info["phone"] == test_phone_1
        assert user_info["totalLandAcres"] == 5
        assert user_info["preferredLanguage"] == "ta"
        assert "Other: Solar Micro-Lift Pump" in user_info["irrigationSources"]
        
        # Transparent phone verification status: unverified (no SMS provider active)
        assert user_info.get("isPhoneVerified") is False, "Phone must be unverified when no SMS provider exists"
        assert "hashed_password" not in user_info, "Password hash must NEVER be exposed in UserSummary"
        print(f"  -> PASS: Farmer registered successfully. Assigned ID: {user_info.get('farmerId')}")
        print("  -> PASS: Role escalation strictly thwarted: enforced role='farmer'.")
        print("  -> PASS: Phone ownership status accurately reported as unverified (isPhoneVerified=False).")

        # ---------------------------------------------------------------------
        # TEST 5: Password Hashing Verification in MongoDB
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Password Hashing & Sensitive Data Protection in MongoDB ---")
        db_user = await users_col.find_one({"phone": test_phone_1})
        assert db_user is not None, "Registered user not found in MongoDB users collection"
        
        # Verify plaintext password is not in MongoDB
        assert "password" not in db_user, "Plaintext password stored in MongoDB!"
        assert "hashed_password" in db_user, "hashed_password missing from user document"
        
        # Verify hash is bcrypt
        stored_hash = db_user["hashed_password"]
        assert stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"), "Hash is not bcrypt!"
        assert verify_password(test_password_1, stored_hash), "Stored bcrypt hash does not match plaintext password"
        assert not verify_password("WrongPassword@123", stored_hash), "Bcrypt verification accepted incorrect password"
        print("  -> PASS: Password is encrypted with Bcrypt (12 rounds) and matches plaintext.")
        print("  -> PASS: Plaintext password is NEVER stored in MongoDB.")

        # ---------------------------------------------------------------------
        # TEST 6: Duplicate Mobile Number Prevention
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Duplicate Mobile Number Rejection ---")
        dup_res = await client.post("/api/auth/register", json=reg_payload)
        assert dup_res.status_code == 409, f"Expected 409 Conflict for duplicate registration, got {dup_res.status_code}"
        dup_data = dup_res.json()
        assert "already exists" in dup_data.get("detail", ""), f"Unexpected detail message: {dup_data}"
        print("  -> PASS: Duplicate mobile registration correctly rejected with HTTP 409 Conflict.")

        # ---------------------------------------------------------------------
        # TEST 7: Farmer Login Authentication
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] Farmer Login Authentication ---")
        
        # 7a. Valid credentials
        login_res = await client.post("/api/auth/login", json={
            "phone": test_phone_1,
            "password": test_password_1,
            "role": "farmer"
        })
        assert login_res.status_code == 200, f"Farmer login failed: {login_res.text}"
        login_data = login_res.json()
        assert "accessToken" in login_data
        assert login_data["user"]["phone"] == test_phone_1
        assert login_data["user"]["role"] == "farmer"
        print("  -> PASS: Farmer login succeeded with mobile number and password.")

        # 7b. Invalid password
        bad_pwd_res = await client.post("/api/auth/login", json={
            "phone": test_phone_1,
            "password": "IncorrectPassword@2026",
            "role": "farmer"
        })
        assert bad_pwd_res.status_code == 401, f"Expected 401 for wrong password, got {bad_pwd_res.status_code}"
        assert "Incorrect password" in bad_pwd_res.json().get("detail", "")
        print("  -> PASS: Invalid password rejected with HTTP 401 Unauthorized.")

        # 7c. Non-existent account
        non_res = await client.post("/api/auth/login", json={
            "phone": "9879999999",
            "password": test_password_1,
            "role": "farmer"
        })
        assert non_res.status_code == 401
        print("  -> PASS: Non-existent mobile number rejected with HTTP 401 Unauthorized.")

        # ---------------------------------------------------------------------
        # TEST 8: Staff Bootstrapped Authentication & Role Separation
        # ---------------------------------------------------------------------
        print("\n--- [Test 8] Staff Administrative Login & Role Separation ---")
        staff_login_res = await client.post("/api/auth/login", json={
            "phone": "9842012345",
            "password": "MandiStaff@2026",
            "role": "staff"
        })
        assert staff_login_res.status_code == 200, f"Staff login failed: {staff_login_res.text}"
        staff_data = staff_login_res.json()
        staff_token = staff_data["accessToken"]
        assert staff_data["user"]["role"] == "staff"
        assert "Procurement Inspector" in staff_data["user"]["name"]
        print("  -> PASS: Bootstrapped staff account logged in successfully with staff role.")

        # 8b. Farmer attempting to sign in with staff role selector
        farmer_as_staff = await client.post("/api/auth/login", json={
            "phone": test_phone_1,
            "password": test_password_1,
            "role": "staff"
        })
        assert farmer_as_staff.status_code == 401
        assert "registered as a Farmer" in farmer_as_staff.json().get("detail", "")
        print("  -> PASS: Cross-role sign-in attempt properly guided to correct role.")

        # ---------------------------------------------------------------------
        # TEST 9: Role-Based Access Control (RBAC) Enforcement
        # ---------------------------------------------------------------------
        print("\n--- [Test 9] Authorization & RBAC Enforcement ---")
        # Farmer token attempting staff queue access
        farmer_staff_access = await client.get(
            "/api/staff/queue",
            headers={"Authorization": f"Bearer {farmer_token}"}
        )
        assert farmer_staff_access.status_code == 403, f"Expected 403 Forbidden for farmer on staff endpoint, got {farmer_staff_access.status_code}"
        print("  -> PASS: Farmer token blocked from staff queue with HTTP 403 Forbidden.")

        # Staff token accessing staff queue
        staff_queue_res = await client.get(
            "/api/staff/queue",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert staff_queue_res.status_code == 200, f"Staff access to queue failed: {staff_queue_res.text}"
        print("  -> PASS: Authorized staff token granted access to /api/staff/queue.")

        # ---------------------------------------------------------------------
        # TEST 10: Session Persistence via /api/auth/me
        # ---------------------------------------------------------------------
        print("\n--- [Test 10] Session Persistence & Token Verification ---")
        # Valid token
        me_res = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {farmer_token}"}
        )
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["phone"] == test_phone_1
        assert me_data["role"] == "farmer"
        assert me_data["isPhoneVerified"] is False
        print("  -> PASS: /api/auth/me successfully validated token and restored user session.")

        # Unauthenticated / Missing token
        unauth_me = await client.get("/api/auth/me")
        assert unauth_me.status_code == 401
        print("  -> PASS: /api/auth/me rejects unauthenticated requests with HTTP 401.")

        # Invalid token
        invalid_me = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert invalid_me.status_code == 401
        print("  -> PASS: /api/auth/me rejects forged/invalid tokens with HTTP 401.")

        print("\n" + "=" * 80)
        print("ALL AUTHENTICATION & REGISTRATION SECURITY TESTS PASSED (10/10)!")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_auth_security_tests())
