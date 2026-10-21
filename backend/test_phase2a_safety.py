"""
Test Suite for Phase 2A: Safe Diagnosis and Critical Fixes.
Verifies:
1. Past date booking rejection (server-side validation).
2. Future date booking acceptance.
3. Duplicate booking prevention (same farmer, centre, date, slot).
4. Cancellation and re-booking preservation.
5. Legacy PATCH /api/staff/bookings/{id}/status transition guard.
6. Staff centre access matching with canonical centre names.
"""
import asyncio
import httpx
from datetime import date, timedelta
import secrets

from main import app

async def run_phase2a_tests():
    print("=" * 80)
    print("PHASE 2A: SAFE DIAGNOSIS & CRITICAL FIXES VERIFICATION SUITE")
    print("=" * 80)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
        # ---------------------------------------------------------------------
        # Setup: Authenticate Farmer & Staff
        # ---------------------------------------------------------------------
        print("\n[Setup] Authenticating test accounts...")
        farmer_phone = f"98{secrets.randbelow(89999999) + 10000000}"
        reg_res = await client.post("/api/auth/register", json={
            "name": "Phase2A Farmer",
            "phone": farmer_phone,
            "village": "Thiruvaiyaru",
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "preferredLanguage": "ta",
            "password": "FarmerPassword@2026",
            "confirmPassword": "FarmerPassword@2026",
            "totalLandAcres": 3,
            "primaryCrop": "Samba Paddy",
            "soilType": "Alluvial Clay Loam",
            "irrigationSource": "Canal"
        })
        assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
        farmer_data = reg_res.json()
        farmer_token = farmer_data["accessToken"]
        farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
        farmer_id = farmer_data["user"]["farmerId"]
        print(f"  Farmer registered: {farmer_data['user']['name']} ({farmer_id})")

        staff_res = await client.post("/api/auth/login", json={
            "phone": "9842012345", "password": "MandiStaff@2026", "role": "staff"
        })
        assert staff_res.status_code == 200, f"Staff login failed: {staff_res.text}"
        staff_token = staff_res.json()["accessToken"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        print("  Staff logged in successfully.")

        # ---------------------------------------------------------------------
        # TEST 1: Past Date Booking Rejection
        # ---------------------------------------------------------------------
        print("\n--- [Test 1] Past Date Booking Rejection ---")
        past_date = (date.today() - timedelta(days=2)).isoformat()
        valid_harvest = (date.today() + timedelta(days=5)).isoformat()
        past_payload = {
            "farmerName": farmer_data["user"]["name"],
            "farmerId": farmer_id,
            "mandiName": "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)",
            "crop": "Paddy Grade A (CR 1009)",
            "cropVariety": "CR 1009",
            "harvestDate": valid_harvest,
            "quantityBags": 20,
            "preferredDate": past_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        past_res = await client.post("/api/procurement/bookings", json=past_payload, headers=farmer_headers)
        assert past_res.status_code in [400, 422], f"Expected 400/422 for past date, got {past_res.status_code}: {past_res.text}"
        print(f"  -> PASS: Past date booking rejected with HTTP {past_res.status_code}: {past_res.json().get('detail')}")

        # ---------------------------------------------------------------------
        # TEST 2: Valid Future Date Booking Creation
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Valid Future Date Booking Creation ---")
        offset_days = secrets.randbelow(8) + 4
        future_date = (date.today() + timedelta(days=offset_days)).isoformat()
        future_harvest = (date.today() + timedelta(days=offset_days - 1)).isoformat()
        future_payload = {
            **past_payload,
            "harvestDate": future_harvest,
            "preferredDate": future_date,
            "quantityBags": 5,
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        create_res = await client.post("/api/procurement/bookings", json=future_payload, headers=farmer_headers)
        assert create_res.status_code == 201, f"Expected 201, got {create_res.status_code}: {create_res.text}"
        b1_data = create_res.json()
        b1_id = b1_data["bookingId"]
        print(f"  -> PASS: Valid booking created: {b1_id} (Token: {b1_data['tokenNumber']})")

        # ---------------------------------------------------------------------
        # TEST 3: Duplicate Booking Prevention
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Duplicate Booking Prevention for Same Slot ---")
        dup_res = await client.post("/api/procurement/bookings", json=future_payload, headers=farmer_headers)
        assert dup_res.status_code == 400, f"Expected 400 for duplicate booking, got {dup_res.status_code}: {dup_res.text}"
        detail_msg = dup_res.json().get("detail", "")
        assert "Duplicate booking disallowed" in detail_msg or "already has an active booking" in detail_msg
        print(f"  -> PASS: Duplicate booking blocked with HTTP 400: {detail_msg}")

        # ---------------------------------------------------------------------
        # TEST 4: Cancellation and Re-booking Preservation
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Cancellation and Re-booking Preservation ---")
        # Cancel booking b1
        cancel_res = await client.post(f"/api/procurement/bookings/{b1_id}/cancel", headers=farmer_headers)
        assert cancel_res.status_code == 200, f"Cancel failed: {cancel_res.text}"
        print(f"  -> Booking {b1_id} cancelled successfully.")

        # Re-booking the same slot should now succeed
        rebook_res = await client.post("/api/procurement/bookings", json=future_payload, headers=farmer_headers)
        assert rebook_res.status_code == 201, f"Expected 201 on re-booking, got {rebook_res.status_code}: {rebook_res.text}"
        b2_data = rebook_res.json()
        b2_id = b2_data["bookingId"]
        print(f"  -> PASS: Re-booking succeeded after cancellation: {b2_id}")

        # ---------------------------------------------------------------------
        # TEST 5: Legacy PATCH /status Guarded Against Invalid Transitions
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Legacy PATCH /status Transition Guard ---")
        # Attempt premature completion on BOOKED status
        invalid_patch = await client.patch(
            f"/api/staff/bookings/{b2_id}/status",
            json={"status": "weighed"},
            headers=staff_headers
        )
        assert invalid_patch.status_code == 400, f"Expected 400 for invalid legacy transition, got {invalid_patch.status_code}: {invalid_patch.text}"
        print(f"  -> PASS: Premature transition blocked on legacy PATCH: {invalid_patch.json().get('detail')}")

        # ---------------------------------------------------------------------
        # TEST 6: Staff Centre Authorization Matching
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Staff Centre Authorization Matching ---")
        # Check in booking using staff account
        ci_res = await client.post(
            f"/api/staff/bookings/{b2_id}/checkin",
            json={"notes": "Gate checkin test"},
            headers=staff_headers
        )
        assert ci_res.status_code == 200, f"Check-in failed: {ci_res.text}"
        print(f"  -> PASS: Staff centre access granted cleanly. Status: {ci_res.json()['status']}")

    print("\n" + "=" * 80)
    print("ALL 6 PHASE 2A TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_phase2a_tests())
