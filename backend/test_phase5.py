"""
Automated Test Suite for Phase 5: Smart Procurement Tracking
Validates all 10 criteria specified in FEATURE 10:
1. A farmer can create a booking.
2. The booking is stored in MongoDB.
3. A slot cannot exceed its capacity.
4. Invalid tokens are rejected.
5. Valid tokens can be verified by authorized staff.
6. Farmers cannot access staff-only operations.
7. Staff can record weighing details.
8. The amount calculation is correct.
9. Queue and payment statuses persist.
10. Existing authentication and farming features still work.
"""

import sys
import asyncio
import httpx
from datetime import datetime, date, timedelta

BASE_URL = "http://127.0.0.1:8000"

async def run_phase5_tests():
    print("=" * 70)
    print("🧪 RUNNING NAMMA VIVASAYI AI - PHASE 5 AUTOMATED VERIFICATION SUITE")
    print("=" * 70)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # ------------------------------------------------------------------
        # Setup: Log in Farmer and Staff accounts
        # ------------------------------------------------------------------
        print("\n[Step 0] Logging in Farmer & Staff accounts...")
        farmer_login_res = await client.post("/api/auth/login", json={
            "phone": "9876543299",
            "password": "FarmerPassword@123",
            "role": "farmer"
        })
        assert farmer_login_res.status_code == 200, f"Farmer login failed: {farmer_login_res.text}"
        farmer_token = farmer_login_res.json()["accessToken"]
        farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
        print(" -> Farmer logged in successfully.")

        staff_login_res = await client.post("/api/auth/login", json={
            "phone": "9842012345",
            "password": "MandiStaff@2026",
            "role": "staff"
        })
        assert staff_login_res.status_code == 200, f"Staff login failed: {staff_login_res.text}"
        staff_token = staff_login_res.json()["accessToken"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        print(" -> Staff logged in successfully.")

        # ------------------------------------------------------------------
        # TEST 1: Farmer can create a booking
        # ------------------------------------------------------------------
        import random
        target_date = (date.today() + timedelta(days=random.randint(15, 45))).isoformat()
        staff_mandi = staff_login_res.json().get("user", {}).get("assignedMandi") or "Thanjavur Regulated Market (DPC Centre"
        test_booking_payload = {
            "farmerName": "Selvakumar R.",
            "farmerId": "TN-AGRI-2026-8841",
            "mandiName": staff_mandi,
            "crop": "Paddy Grade A (சம்பா நெல் CR 1009)",
            "quantityBags": 50,
            "preferredDate": target_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        create_res = await client.post("/api/procurement/bookings", json=test_booking_payload, headers=farmer_headers)
        assert create_res.status_code == 201, f"Create booking failed: {create_res.text}"
        booking = create_res.json()
        booking_id = booking["bookingId"]
        token_num = booking["tokenNumber"]
        opaque_token = booking.get("opaqueToken")
        print(f" -> SUCCESS: Booking created! ID: {booking_id}, Token: {token_num}")
        assert booking["status"] == "BOOKED"
        assert booking["quantityBags"] == 50

        # ------------------------------------------------------------------
        # TEST 2: The booking is stored in MongoDB
        # ------------------------------------------------------------------
        print("\n[Test 2] Verifying Booking Persistence in MongoDB via list API...")
        list_res = await client.get("/api/procurement/bookings", headers=farmer_headers)
        assert list_res.status_code == 200, f"List bookings failed: {list_res.text}"
        farmer_bookings = list_res.json()
        found = any(b["bookingId"] == booking_id for b in farmer_bookings)
        assert found, f"Booking {booking_id} was not found in database records!"
        print(f" -> SUCCESS: Booking {booking_id} verified in MongoDB collection.")

        # ------------------------------------------------------------------
        # TEST 3: Slot cannot exceed its capacity
        # ------------------------------------------------------------------
        print("\n[Test 3] Testing Slot Capacity Limits...")
        # Slot capacity for Thanjavur DPC is 250 bags per window.
        # We already booked 50 bags. Attempting to book 250 more should exceed limit (50+250 = 300 > 250)
        overbook_payload = {
            "farmerName": "Selvakumar R.",
            "farmerId": "TN-AGRI-2026-8841",
            "mandiName": "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)",
            "crop": "Paddy Grade A (சம்பா நெல் CR 1009)",
            "quantityBags": 250,
            "preferredDate": target_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        overbook_res = await client.post("/api/procurement/bookings", json=overbook_payload, headers=farmer_headers)
        assert overbook_res.status_code == 400, f"Expected 400 Bad Request, got {overbook_res.status_code}: {overbook_res.text}"
        print(f" -> SUCCESS: Overbooking correctly rejected with 400: {overbook_res.json()['detail']}")

        # ------------------------------------------------------------------
        # TEST 4: Invalid tokens are rejected
        # ------------------------------------------------------------------
        print("\n[Test 4] Testing Invalid Token Rejection...")
        invalid_verify_res = await client.post("/api/staff/verify-token", json={
            "token": "INVALID-FAKE-TOKEN-9999"
        }, headers=staff_headers)
        assert invalid_verify_res.status_code == 200
        verify_data = invalid_verify_res.json()
        assert verify_data["isValid"] is False, "Invalid token was accepted!"
        print(f" -> SUCCESS: Invalid token rejected cleanly: {verify_data['message']}")

        # ------------------------------------------------------------------
        # TEST 5: Valid tokens can be verified by authorized staff
        # ------------------------------------------------------------------
        print("\n[Test 5] Testing Staff Token Verification...")
        valid_verify_res = await client.post("/api/staff/verify-token", json={
            "token": opaque_token or token_num
        }, headers=staff_headers)
        assert valid_verify_res.status_code == 200
        valid_data = valid_verify_res.json()
        assert valid_data["isValid"] is True, f"Valid token rejected: {valid_data}"
        assert valid_data["bookingId"] == booking_id
        assert valid_data["canCheckIn"] is True
        print(f" -> SUCCESS: Valid token verified by staff! Status: {valid_data['status']}")

        # ------------------------------------------------------------------
        # TEST 6: Farmers cannot access staff-only operations
        # ------------------------------------------------------------------
        print("\n[Test 6] Testing Role-Based Protection (Farmer blocked from staff endpoints)...")
        farmer_unauthorized_res = await client.post("/api/staff/verify-token", json={
            "token": token_num
        }, headers=farmer_headers)
        assert farmer_unauthorized_res.status_code == 403, f"Farmer accessed staff endpoint! Status: {farmer_unauthorized_res.status_code}"
        print(f" -> SUCCESS: Farmer properly blocked with HTTP 403 Forbidden: {farmer_unauthorized_res.json()['detail']}")

        # ------------------------------------------------------------------
        # TEST 7: Staff can check in and record weighing details
        # ------------------------------------------------------------------
        print("\n[Test 7] Testing Staff Gate Check-In & Weighing Entry...")
        # Step 7a: Gate Check-in
        checkin_res = await client.post(f"/api/staff/bookings/{booking_id}/checkin", json={
            "notes": "Vehicle TN-49-AB-1234 arrived at gate. Physical token verified."
        }, headers=staff_headers)
        assert checkin_res.status_code == 200, f"Check-in failed: {checkin_res.text}"
        checkin_data = checkin_res.json()
        assert checkin_data["status"] == "CHECKED_IN"
        print(f" -> SUCCESS: Vehicle checked in. Status: {checkin_data['status']}")

        # Step 7b: Staff records weighing and transaction
        # Weight = 20.00 Quintals, Rate = ₹2,320/Qtl, Moisture = 18.0% (1% excess over 17%)
        tx_payload = {
            "actualNetWeightQuintals": 20.00,
            "pricePerQuintal": 2320.00,
            "moisturePercent": 18.0,
            "qualityGrade": "Grade A (TNAU Standard)",
            "customDeductionsAmount": 100.0,
            "paymentStatus": "PROCESSING",
            "notes": "Weighbridge test passed. Electronic weigh slip #9012"
        }
        tx_res = await client.post(f"/api/staff/bookings/{booking_id}/transaction", json=tx_payload, headers=staff_headers)
        assert tx_res.status_code == 200, f"Weighing failed: {tx_res.text}"
        tx_data = tx_res.json()
        assert tx_data["status"] == "COMPLETED"
        print(f" -> SUCCESS: Weighing and transaction ledger recorded.")

        # ------------------------------------------------------------------
        # TEST 8: The amount calculation is correct
        # ------------------------------------------------------------------
        print("\n[Test 8] Verifying Financial & Moisture Deduction Calculations...")
        ledger = tx_data["transaction"]
        # Gross = 20.0 * 2320 = 46,400.00
        expected_gross = 46400.00
        assert ledger["grossAmount"] == expected_gross, f"Gross {ledger['grossAmount']} != expected {expected_gross}"

        # Moisture dockage: 18% - 17% = 1% dockage. 1% of 46,400 = 464.00
        expected_moisture_ded = 464.00
        assert ledger["moistureDeductionAmount"] == expected_moisture_ded, f"Moisture ded {ledger['moistureDeductionAmount']} != {expected_moisture_ded}"

        # Total deductions: 464.00 + 100.00 custom = 564.00
        expected_total_ded = 564.00
        assert ledger["totalDeductionsAmount"] == expected_total_ded, f"Total ded {ledger['totalDeductionsAmount']} != {expected_total_ded}"

        # Net payable: 46,400.00 - 564.00 = 45,836.00
        expected_net = 45836.00
        assert ledger["netPayableAmount"] == expected_net, f"Net {ledger['netPayableAmount']} != {expected_net}"
        print(f" -> SUCCESS: Math verified! Gross: ₹{ledger['grossAmount']:,}, Deductions: ₹{ledger['totalDeductionsAmount']:,}, Net: ₹{ledger['netPayableAmount']:,}")

        # ------------------------------------------------------------------
        # TEST 9: Queue and payment statuses persist after database check
        # ------------------------------------------------------------------
        print("\n[Test 9] Verifying Queue & Payment Status Persistence...")
        queue_res = await client.get(f"/api/procurement/queue/{booking_id}", headers=farmer_headers)
        assert queue_res.status_code == 200, f"Queue tracking failed: {queue_res.text}"
        q_data = queue_res.json()
        assert q_data["status"] == "COMPLETED"
        assert q_data["currentStageNumber"] == 5
        assert q_data["transaction"]["netPayableAmount"] == expected_net
        assert len(q_data["auditHistory"]) >= 3 # BOOKED, CHECKED_IN, COMPLETED
        print(f" -> SUCCESS: Queue tracking confirmed status {q_data['status']} with {len(q_data['auditHistory'])} audit events.")

        # Check in-app notification was generated for farmer
        notif_res = await client.get("/api/notifications", headers=farmer_headers)
        assert notif_res.status_code == 200
        notifs = notif_res.json()
        assert len(notifs) > 0, "No notifications found!"
        print(f" -> SUCCESS: In-app notifications stored ({len(notifs)} alerts found).")

        # ------------------------------------------------------------------
        # TEST 10: Existing authentication and farming features still work
        # ------------------------------------------------------------------
        print("\n[Test 10] Regression Testing Phase 3 Auth & Phase 4 Farming Features...")
        # 10a: Weather
        weather_res = await client.get("/api/weather?district=thanjavur")
        assert weather_res.status_code == 200
        assert "temperatureC" in weather_res.json()
        assert "sprayingAdvisory" in weather_res.json()
        print(" -> Weather API 200 OK")

        # 10b: Irrigation advice
        irrig_res = await client.post("/api/irrigation/calculate", json={
            "crop": "Paddy (Ponni)",
            "growthStage": "Tillering",
            "soilType": "Alluvial Clay Loam",
            "irrigationMethod": "Basin Flooding"
        })
        assert irrig_res.status_code == 200
        assert "recommendationEn" in irrig_res.json()
        assert irrig_res.json().get("isAdvisoryOnly") is True
        print(" -> Smart Irrigation API 200 OK")

        # 10c: Auth verification
        me_res = await client.get("/api/auth/me", headers=farmer_headers)
        assert me_res.status_code == 200
        assert me_res.json()["phone"] == "9876543299"
        print(" -> Auth Me API 200 OK")

    print("\n" + "=" * 70)
    print("🎉 ALL 10 PHASE 5 AUTOMATED VERIFICATION CRITERIA PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_phase5_tests())
