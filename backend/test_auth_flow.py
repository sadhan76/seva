"""
NAMMA VIVASAYI AI - AUTHENTICATION, ROLE ISOLATION & PERSONALIZED DASHBOARD TEST SUITE
====================================================================================
Tests:
1. Unauthenticated Data Protection (Private endpoints reject or return empty without auth)
2. Farmer Registration & Profile Persistence in MongoDB (Without fabricated Aadhaar verification)
3. Role Escalation Prevention (Public registration strictly enforces role="farmer")
4. Farmer Authentication & JWT Validation (GET /api/auth/me restores session)
5. Staff Authentication & Mandi Association
6. Strict Role-Based Access Control (Farmer blocked from staff endpoints -> 403 Forbidden)
7. Cross-Farmer Booking Data Isolation (Farmer B cannot access Farmer A's procurement records)
8. Input Validation & Error Handling (Missing fields, invalid phones, wrong passwords)
"""

import asyncio
import httpx
import time

BASE_URL = "http://127.0.0.1:8000"

async def run_auth_tests():
    print("=" * 80)
    print("NAMMA VIVASAYI AI - AUTHENTICATION & PERSONALIZATION TEST SUITE")
    print("=" * 80)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # TEST 1: Unauthenticated Data Protection
        print("\n--- [Test 1] Unauthenticated Data Protection ---")
        unauth_farmers_res = await client.get("/api/farmers")
        assert unauth_farmers_res.status_code == 200, f"Expected 200: {unauth_farmers_res.text}"
        assert unauth_farmers_res.json() == [], "Unauthenticated request leaked farmer profiles!"
        print("  -> PASS: GET /api/farmers returns empty list for unauthenticated callers (no data leak).")

        unauth_me_res = await client.get("/api/auth/me")
        assert unauth_me_res.status_code == 401, f"Expected 401 for /api/auth/me without token, got {unauth_me_res.status_code}"
        print("  -> PASS: GET /api/auth/me returns 401 Unauthorized when not logged in.")

        # TEST 2: Registration & Profile Persistence (No fake Aadhaar badge)
        print("\n--- [Test 2] Farmer Registration & Real Farm Profile Persistence ---")
        suffix = int(time.time()) % 100000
        farmer_a_phone = f"9786{suffix:06d}"
        farmer_a_pwd = "FarmerSecret@2026"
        
        reg_payload = {
            "name": f"Murugan {suffix}",
            "phone": farmer_a_phone,
            "village": "Valangaiman",
            "district": "Tiruvarur",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": farmer_a_pwd,
            "confirmPassword": farmer_a_pwd,
            "totalLandAcres": 4,
            "primaryCrop": "Ponni Paddy",
            "soilType": "Clay Loam",
            "irrigationSource": "Vennar Canal",
            "role": "staff"  # Attempt malicious escalation to staff
        }

        reg_res = await client.post("/api/auth/register", json=reg_payload)
        assert reg_res.status_code in [200, 201], f"Farmer registration failed: {reg_res.text}"
        reg_data = reg_res.json()
        token_a = reg_data.get("accessToken") or reg_data.get("access_token")
        user_a = reg_data["user"]

        # Verify role escalation was blocked
        assert user_a["role"] == "farmer", f"Privilege escalation! Role is {user_a['role']}"
        assert user_a["name"] == f"Murugan {suffix}"
        assert user_a["district"] == "Tiruvarur"
        assert user_a["totalLandAcres"] == 4
        assert user_a["primaryCrop"] == "Ponni Paddy"
        assert user_a["soilType"] == "Clay Loam"
        # Verify NO fake Aadhaar verification
        assert user_a.get("isAadhaarVerified") is False or user_a.get("isAadhaarVerified") is None, "Aadhaar falsely marked as verified!"
        print("  -> PASS: Farmer registered successfully. Role enforced as 'farmer', farm profile persisted, no fake Aadhaar.")

        # TEST 3: Login Authentication
        print("\n--- [Test 3] Farmer Login & Session Restoration ---")
        login_res = await client.post("/api/auth/login", json={
            "phone": farmer_a_phone,
            "password": farmer_a_pwd
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        login_data = login_res.json()
        assert login_data.get("accessToken") or login_data.get("access_token")
        assert login_data["user"]["phone"] == farmer_a_phone
        assert login_data["user"]["primaryCrop"] == "Ponni Paddy"
        print("  -> PASS: Login succeeded. JWT received and personalized profile returned.")

        # Session restore via /api/auth/me
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        assert me_res.status_code == 200, f"/api/auth/me failed: {me_res.text}"
        me_user = me_res.json()
        assert me_user["id"] == user_a["id"]
        assert me_user["totalLandAcres"] == 4
        print("  -> PASS: Session restoration (/api/auth/me) successfully retrieved authenticated farmer profile.")

        # TEST 4: Staff Authentication & Privileges
        print("\n--- [Test 4] Staff Authentication & Mandi Association ---")
        staff_login_res = await client.post("/api/auth/login", json={
            "phone": "9842012345",
            "password": "MandiStaff@2026",
            "role": "staff"
        })
        assert staff_login_res.status_code == 200, f"Staff login failed: {staff_login_res.text}"
        staff_data = staff_login_res.json()
        staff_token = staff_data.get("accessToken") or staff_data.get("access_token")
        staff_user = staff_data["user"]
        assert staff_user["role"] == "staff", f"Expected role='staff', got {staff_user['role']}"
        assert staff_user.get("mandiId") or staff_user.get("mandiName"), "Staff user missing mandi association"
        print(f"  -> PASS: Staff authenticated. Role='staff', Mandi='{staff_user.get('mandiName')}'")

        # TEST 5: Role-Based Access Control (Farmer blocked from staff endpoints)
        print("\n--- [Test 5] Role-Based Access Control & Staff Protection ---")
        tamper_res = await client.post(
            "/api/staff/verify-token",
            json={"token": "TKN-12345"},
            headers={"Authorization": f"Bearer {token_a}"}  # Farmer attempting staff action
        )
        assert tamper_res.status_code == 403, f"Farmer was NOT blocked from staff endpoint! Status: {tamper_res.status_code}"
        print(f"  -> PASS: Farmer correctly blocked from staff-only endpoint (/api/staff/verify-token). Status: 403 Forbidden")

        # TEST 6: Cross-Farmer Data Isolation
        print("\n--- [Test 6] Cross-Farmer Data Isolation ---")
        # Register Farmer B
        farmer_b_phone = f"9654{suffix:06d}"
        farmer_b_pwd = "FarmerBSecret@2026"
        reg_b_res = await client.post("/api/auth/register", json={
            "name": f"Kavitha {suffix}",
            "phone": farmer_b_phone,
            "village": "Budalur",
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": farmer_b_pwd,
            "confirmPassword": farmer_b_pwd,
            "totalLandAcres": 2.0,
            "primaryCrop": "Kuruvai Paddy",
            "soilType": "Alluvial",
            "irrigationSource": "Cauvery River"
        })
        assert reg_b_res.status_code in [200, 201], f"Farmer B registration failed: {reg_b_res.text}"
        token_b = reg_b_res.json().get("accessToken") or reg_b_res.json().get("access_token")

        # Farmer A creates a booking
        booking_payload = {
            "farmerName": user_a["name"],
            "farmerId": user_a.get("farmerId") or f"TN-AGRI-2026-{suffix % 10000}",
            "mandiName": "Thanjavur Regulated Market (DPC Centre",
            "crop": "Paddy Grade A (சம்பா நெல் CR 1009)",
            "quantityBags": 50,
            "preferredDate": f"2026-12-{(suffix % 25) + 1:02d}",
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        book_res = await client.post(
            "/api/procurement/bookings",
            json=booking_payload,
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert book_res.status_code in [200, 201], f"Booking creation failed: {book_res.text}"
        booking_a_id = book_res.json()["bookingId"]
        print(f"  -> Farmer A created booking: {booking_a_id}")

        # Farmer B retrieves bookings: Farmer A's booking must NOT appear
        b_bookings_res = await client.get(
            "/api/procurement/bookings",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert b_bookings_res.status_code == 200
        b_bookings = b_bookings_res.json()
        b_ids = [b["bookingId"] for b in b_bookings]
        assert booking_a_id not in b_ids, f"Data leak! Farmer B saw Farmer A's booking: {booking_a_id}"
        print(f"  -> PASS: Farmer B cannot see Farmer A's booking. Isolation verified.")

        # TEST 7: Input Validation on Login
        print("\n--- [Test 7] Login Input Validation & Security ---")
        wrong_pwd_res = await client.post("/api/auth/login", json={
            "phone": farmer_a_phone,
            "password": "WrongPassword!"
        })
        assert wrong_pwd_res.status_code in [400, 401], f"Expected 401/400 for wrong password, got {wrong_pwd_res.status_code}"
        print("  -> PASS: Invalid password correctly rejected with 401/400.")

        invalid_phone_res = await client.post("/api/auth/login", json={
            "phone": "123",
            "password": "AnyPassword"
        })
        assert invalid_phone_res.status_code in [400, 401, 422], f"Expected 400/401/422 for invalid phone, got {invalid_phone_res.status_code}"
        print("  -> PASS: Malformed/unknown phone correctly rejected.")

        print("\n" + "=" * 80)
        print("ALL AUTHENTICATION, ROLE ISOLATION & DATA PRIVACY TESTS PASSED (7/7)!")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_auth_tests())
