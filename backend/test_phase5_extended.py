"""
Extended Phase 5 Test Suite - All 14 tests covering new endpoints
"""
import asyncio
import httpx
from datetime import date, timedelta

from main import app

async def run_extended_tests():
    print("=" * 70)
    print("PHASE 5 EXTENDED TEST SUITE - Namma Vivasayi AI")
    print("=" * 70)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:

        # Setup: Login
        print("\n[Setup] Logging in Farmer & Staff...")
        farmer_res = await client.post("/api/auth/login", json={
            "phone": "9876543299", "password": "FarmerPassword@123", "role": "farmer"
        })
        assert farmer_res.status_code == 200, f"Farmer login failed: {farmer_res.text}"
        farmer_token = farmer_res.json()["accessToken"]
        farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
        farmer_id = farmer_res.json()["user"]["farmerId"]
        print(f"  -> Farmer OK. ID: {farmer_id}")

        staff_res = await client.post("/api/auth/login", json={
            "phone": "9842012345", "password": "MandiStaff@2026", "role": "staff"
        })
        assert staff_res.status_code == 200
        staff_token = staff_res.json()["accessToken"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        print("  -> Staff OK")

        # Test 1: Create booking
        print("\n[Test 1] Farmer booking creation...")
        staff_mandi = staff_res.json()["user"].get("mandiName") or "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)"
        target_date = (date.today() + timedelta(days=4)).isoformat()
        booking_payload = {
            "farmerName": "Selvakumar R.", "farmerId": farmer_id,
            "mandiName": staff_mandi,
            "crop": "Paddy Grade A (Samba NL CR 1009)", "quantityBags": 20,
            "preferredDate": target_date, "timeWindow": "11:30 AM - 02:30 PM"
        }
        create_res = await client.post("/api/procurement/bookings", json=booking_payload, headers=farmer_headers)
        assert create_res.status_code == 201, f"Create failed: {create_res.text}"
        booking = create_res.json()
        booking_id = booking["bookingId"]
        token_num = booking["tokenNumber"]
        opaque_token = booking.get("opaqueToken")
        assert booking["status"] == "BOOKED"
        print(f"  -> PASS: {booking_id} / {token_num}")

        # Test 2: MongoDB persistence
        print("\n[Test 2] MongoDB persistence...")
        list_res = await client.get("/api/procurement/bookings", headers=farmer_headers)
        assert any(b["bookingId"] == booking_id for b in list_res.json())
        print("  -> PASS")

        # Test 3: Anonymous returns empty list
        print("\n[Test 3] Anonymous access returns empty list (no data leak)...")
        anon_res = await client.get("/api/procurement/bookings")
        assert anon_res.status_code == 200
        assert anon_res.json() == []
        print("  -> PASS: No data leakage to anonymous callers")

        # Test 4: Overbooking protection
        print("\n[Test 4] Overbooking protection...")
        ob_res = await client.post("/api/procurement/bookings", json={**booking_payload, "quantityBags": 250}, headers=farmer_headers)
        assert ob_res.status_code == 400
        print("  -> PASS: Overbook rejected")

        # Test 5: Invalid token rejected
        print("\n[Test 5] Invalid token rejected...")
        inv_res = await client.post("/api/staff/verify-token", json={"token": "FAKE-TOKEN-000"}, headers=staff_headers)
        assert inv_res.json()["isValid"] is False
        print("  -> PASS")

        # Test 6: Valid token verified by staff
        print("\n[Test 6] Valid token verified by staff...")
        val_res = await client.post("/api/staff/verify-token", json={"token": opaque_token or token_num}, headers=staff_headers)
        assert val_res.json()["isValid"] is True
        assert val_res.json()["canCheckIn"] is True
        print("  -> PASS")

        # Test 7: RBAC - farmer blocked from staff endpoints
        print("\n[Test 7] RBAC farmer blocked from staff endpoints...")
        rbac_res = await client.post("/api/staff/verify-token", json={"token": token_num}, headers=farmer_headers)
        assert rbac_res.status_code == 403
        print("  -> PASS: 403 Forbidden")

        # Test 8: Full queue lifecycle
        print("\n[Test 8] Full queue lifecycle: BOOKED->CHECKED_IN->IN_QUEUE->PROCESSING...")
        ci_res = await client.post(f"/api/staff/bookings/{booking_id}/checkin", json={"notes": "Gate test vehicle"}, headers=staff_headers)
        assert ci_res.status_code == 200 and ci_res.json()["status"] == "CHECKED_IN"
        print("  -> 8a PASS: CHECKED_IN")

        q_res = await client.post(f"/api/staff/bookings/{booking_id}/queue", headers=staff_headers)
        assert q_res.status_code == 200, f"Queue failed: {q_res.text}"
        assert q_res.json()["status"] == "IN_QUEUE"
        print("  -> 8b PASS: IN_QUEUE")

        p_res = await client.post(f"/api/staff/bookings/{booking_id}/processing", headers=staff_headers)
        assert p_res.status_code == 200, f"Processing failed: {p_res.text}"
        assert p_res.json()["status"] == "PROCESSING"
        print("  -> 8c PASS: PROCESSING")

        # Test 9: Weighing math (moisture <= 17%, 0 deduction)
        print("\n[Test 9] Weighing & financial math (moisture<=17%, no deduction)...")
        tx_res = await client.post(f"/api/staff/bookings/{booking_id}/transaction", json={
            "actualNetWeightQuintals": 10.0, "pricePerQuintal": 2183.0,
            "moisturePercent": 15.0, "qualityGrade": "FAQ Grade A",
            "customDeductionsAmount": 0.0, "paymentStatus": "PENDING"
        }, headers=staff_headers)
        assert tx_res.status_code == 200
        ledger = tx_res.json()["transaction"]
        assert ledger["grossAmount"] == 21830.0, f"Gross mismatch: {ledger['grossAmount']}"
        assert ledger["moistureDeductionAmount"] == 0.0
        assert ledger["netPayableAmount"] == 21830.0
        print(f"  -> PASS: Gross=Rs.{ledger['grossAmount']:,} Net=Rs.{ledger['netPayableAmount']:,}")

        # Test 10: Audit history persistence
        print("\n[Test 10] Audit history & queue status persistence...")
        qtrack_res = await client.get(f"/api/procurement/queue/{booking_id}", headers=farmer_headers)
        assert qtrack_res.status_code == 200
        qdata = qtrack_res.json()
        assert qdata["status"] == "COMPLETED"
        assert qdata["currentStageNumber"] == 5
        assert len(qdata["auditHistory"]) >= 5
        print(f"  -> PASS: {len(qdata['auditHistory'])} audit events, stage 5/5")

        # Test 11: Staff cancel new booking
        print("\n[Test 11] Staff cancel booking with audit trail...")
        new_booking_res = await client.post("/api/procurement/bookings", json={
            **booking_payload, "quantityBags": 3,
            "timeWindow": "02:30 PM - 05:30 PM",
            "preferredDate": (date.today() + timedelta(days=8)).isoformat()
        }, headers=farmer_headers)
        assert new_booking_res.status_code == 201, f"Test 11 booking creation failed: {new_booking_res.text}"
        cancel_bid = new_booking_res.json()["bookingId"]
        cancel_res = await client.post(f"/api/staff/bookings/{cancel_bid}/cancel", headers=staff_headers)
        assert cancel_res.status_code == 200 and cancel_res.json()["status"] == "CANCELLED"
        verify_cancelled = await client.post("/api/staff/verify-token", json={"bookingId": cancel_bid}, headers=staff_headers)
        assert verify_cancelled.json()["isValid"] is False
        assert verify_cancelled.json()["status"] == "CANCELLED"
        print("  -> PASS: Cancelled & token verify returns isValid=False")

        # Test 12: Farmer /my-bookings ownership enforcement
        print("\n[Test 12] Farmer ownership /my-bookings...")
        my_res = await client.get("/api/procurement/my-bookings", headers=farmer_headers)
        assert my_res.status_code == 200
        my_data = my_res.json()
        assert my_data["farmerId"] == farmer_id
        assert my_data["totalBookings"] > 0
        for b in my_data["bookings"]:
            assert "userId" not in b, "userId leaked!"
        print(f"  -> PASS: {my_data['totalBookings']} bookings, no userId leak")

        # Test 13: Staff blocked from /my-bookings
        print("\n[Test 13] Staff blocked from /my-bookings...")
        staff_my_res = await client.get("/api/procurement/my-bookings", headers=staff_headers)
        assert staff_my_res.status_code == 403
        print("  -> PASS: 403 Forbidden for staff on farmer-only endpoint")

        # Test 14: Regression
        print("\n[Test 14] Regression: Phase 3 auth & Phase 4 farming features...")
        assert (await client.get("/api/weather?district=thanjavur")).status_code == 200
        irr_res = await client.post("/api/irrigation/calculate", json={
            "crop": "Paddy (Ponni)", "growthStage": "Tillering",
            "soilType": "Alluvial Clay Loam", "irrigationMethod": "Basin Flooding"
        })
        assert irr_res.status_code == 200
        assert (await client.get("/api/auth/me", headers=farmer_headers)).status_code == 200
        print("  -> PASS: All Phase 3/4 features intact")

    print("\n" + "=" * 70)
    print("ALL 14 EXTENDED PHASE 5 TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_extended_tests())
