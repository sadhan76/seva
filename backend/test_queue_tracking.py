"""
Automated Test Suite for Phase 5 Part 2: Smart Procurement Queue Tracking
Covers all 9 verification tests required by TASK 6.
"""

import asyncio
import httpx
from datetime import date, timedelta
import secrets
import random

from main import app

async def run_queue_tests():
    print("=" * 80)
    print("PHASE 5: SMART PROCUREMENT QUEUE TRACKING - TASK 6 VERIFICATION SUITE")
    print("=" * 80)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
        # ---------------------------------------------------------------------
        # Setup: Log in Farmer 1, Farmer 2, and Mandi Staff
        # ---------------------------------------------------------------------
        print("\n[Setup] Authenticating Users...")

        # Farmer 1
        f1_res = await client.post("/api/auth/login", json={
            "phone": "9876543299", "password": "FarmerPassword@123", "role": "farmer"
        })
        assert f1_res.status_code == 200, f"Farmer 1 login failed: {f1_res.text}"
        f1_token = f1_res.json()["accessToken"]
        f1_headers = {"Authorization": f"Bearer {f1_token}"}
        f1_user = f1_res.json()["user"]
        print(f"  Farmer 1: {f1_user['name']} ({f1_user['farmerId']})")

        # Farmer 2 (Register if not already present, then login)
        f2_phone = "9876543211"
        f2_res = await client.post("/api/auth/login", json={
            "phone": f2_phone, "password": "FarmerPassword@123", "role": "farmer"
        })
        if f2_res.status_code != 200:
            reg_res = await client.post("/api/auth/register", json={
                "name": "Kandasamy V.",
                "phone": f2_phone,
                "village": "Thiruvaiyaru",
                "district": "Thanjavur",
                "password": "FarmerPassword@123",
                "confirmPassword": "FarmerPassword@123"
            })
            assert reg_res.status_code == 201, f"Farmer 2 register failed: {reg_res.text}"
            f2_res = await client.post("/api/auth/login", json={
                "phone": f2_phone, "password": "FarmerPassword@123", "role": "farmer"
            })
        assert f2_res.status_code == 200
        f2_token = f2_res.json()["accessToken"]
        f2_headers = {"Authorization": f"Bearer {f2_token}"}
        f2_user = f2_res.json()["user"]
        print(f"  Farmer 2: {f2_user['name']} ({f2_user['farmerId']})")

        # Staff 1 (Assigned to Thanjavur)
        staff_res = await client.post("/api/auth/login", json={
            "phone": "9842012345", "password": "MandiStaff@2026", "role": "staff"
        })
        assert staff_res.status_code == 200, f"Staff login failed: {staff_res.text}"
        staff_token = staff_res.json()["accessToken"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        staff_user = staff_res.json()["user"]
        print(f"  Staff: {staff_user['name']} (Assigned: {staff_user.get('mandiName')})")

        # Pick unique isolated test date for this test run
        test_date = (date.today() + timedelta(days=random.randint(60, 300))).isoformat()
        mandi_name = staff_user.get("mandiName") or "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)"

        # Create Booking A for Farmer 1
        b_payload_a = {
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A (Samba NL CR 1009)",
            "quantityBags": 10,
            "preferredDate": test_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        res_a = await client.post("/api/procurement/bookings", json=b_payload_a, headers=f1_headers)
        assert res_a.status_code == 201, f"Create Booking A failed: {res_a.text}"
        booking_a = res_a.json()
        bid_a = booking_a["bookingId"]
        print(f"\n  Created Booking A: {bid_a} (Token: {booking_a['tokenNumber']})")

        # ---------------------------------------------------------------------
        # TEST 1: Farmer can view their own queue status
        # ---------------------------------------------------------------------
        print("\n--- [Test 1] Farmer can view their own queue status ---")
        q_res1 = await client.get(f"/api/procurement/queue/{bid_a}", headers=f1_headers)
        assert q_res1.status_code == 200, f"Farmer view failed: {q_res1.text}"
        q_data1 = q_res1.json()
        assert q_data1["bookingId"] == bid_a
        assert q_data1["status"] == "BOOKED"
        assert q_data1["queuePosition"] is None  # Not in active queue yet!
        assert q_data1["hasSufficientDataForEstimate"] is False
        assert q_data1["waitingTimeDisplay"] == "Waiting time unavailable"
        print("  -> PASS: Farmer 1 successfully retrieved own booking queue.")
        print(f"     Status={q_data1['status']}, QueuePos={q_data1['queuePosition']}, WaitTime='{q_data1['waitingTimeDisplay']}'")

        # ---------------------------------------------------------------------
        # TEST 2: Farmer cannot view another farmer's private booking details
        # ---------------------------------------------------------------------
        print("\n--- [Test 2] Farmer cannot view another farmer's private booking details ---")
        q_res2 = await client.get(f"/api/procurement/queue/{bid_a}", headers=f2_headers)
        assert q_res2.status_code == 403, f"Expected 403 Forbidden, got {q_res2.status_code}"
        print(f"  -> PASS: Blocked with HTTP 403 Forbidden: {q_res2.json()['detail']}")

        # Unauthenticated request is also blocked with 401
        q_anon = await client.get(f"/api/procurement/queue/{bid_a}")
        assert q_anon.status_code == 401
        print("  -> PASS: Anonymous request blocked with HTTP 401 Unauthorized")

        # ---------------------------------------------------------------------
        # TEST 3: Unauthorized users cannot update the queue
        # ---------------------------------------------------------------------
        print("\n--- [Test 3] Unauthorized users cannot update the queue ---")
        # Farmer tries to check-in
        f_checkin = await client.post(f"/api/staff/bookings/{bid_a}/checkin", json={"notes": "Gate test"}, headers=f1_headers)
        assert f_checkin.status_code == 403
        print(f"  -> PASS: Farmer blocked from checkin: 403 ({f_checkin.json()['detail']})")

        # Farmer tries to update status
        f_status = await client.post(f"/api/staff/bookings/{bid_a}/status", json={"newStatus": "PROCESSING"}, headers=f1_headers)
        assert f_status.status_code == 403
        print("  -> PASS: Farmer blocked from status update: 403")

        # Anonymous tries to update status
        anon_status = await client.post(f"/api/staff/bookings/{bid_a}/status", json={"newStatus": "PROCESSING"})
        assert anon_status.status_code == 401
        print("  -> PASS: Anonymous blocked from status update: 401")

        # ---------------------------------------------------------------------
        # TEST 4: Authorized staff can check in a valid booking
        # ---------------------------------------------------------------------
        print("\n--- [Test 4] Authorized staff can check in a valid booking ---")
        ci_res = await client.post(f"/api/staff/bookings/{bid_a}/checkin", json={"notes": "Truck TN-49-A-1234 arrived at gate"}, headers=staff_headers)
        assert ci_res.status_code == 200, f"Staff checkin failed: {ci_res.text}"
        ci_doc = ci_res.json()
        assert ci_doc["status"] == "CHECKED_IN"
        assert ci_doc["checkedInByStaff"] == staff_user["name"]
        print(f"  -> PASS: Booking checked in by {ci_doc['checkedInByStaff']} at {ci_doc.get('checkedInAt')}")

        # ---------------------------------------------------------------------
        # TEST 5: Invalid status transitions are rejected
        # ---------------------------------------------------------------------
        print("\n--- [Test 5] Invalid status transitions are rejected ---")
        # 5a. Cannot check in again (already CHECKED_IN)
        dup_ci = await client.post(f"/api/staff/bookings/{bid_a}/checkin", json={"notes": "Double check in"}, headers=staff_headers)
        assert dup_ci.status_code == 400
        print(f"  -> PASS: Duplicate checkin rejected: 400 ({dup_ci.json()['detail']})")

        # 5b. Cannot jump directly from CHECKED_IN to PROCESSING
        skip_process = await client.post(f"/api/staff/bookings/{bid_a}/processing", headers=staff_headers)
        assert skip_process.status_code == 400
        print(f"  -> PASS: Skip-to-processing rejected: 400 ({skip_process.json()['detail']})")

        # 5c. Cannot complete without recording transaction
        invalid_complete = await client.post(f"/api/staff/bookings/{bid_a}/status", json={"newStatus": "COMPLETED"}, headers=staff_headers)
        print(f"DEBUG: invalid_complete code={invalid_complete.status_code}, body={invalid_complete.text}")
        assert invalid_complete.status_code == 400, f"Expected 400, got {invalid_complete.status_code}: {invalid_complete.text}"
        print(f"  -> PASS: Premature completion rejected: 400 ({invalid_complete.json()['detail']})")

        # ---------------------------------------------------------------------
        # TEST 6: Queue positions update when bookings change
        # ---------------------------------------------------------------------
        print("\n--- [Test 6] Queue positions update dynamically as bookings change ---")
        # Create Booking B for Farmer 1 at same centre and slot
        b_payload_b = {
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A (Samba NL CR 1009)",
            "quantityBags": 15,
            "preferredDate": test_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }
        res_b = await client.post("/api/procurement/bookings", json=b_payload_b, headers=f1_headers)
        assert res_b.status_code == 201
        bid_b = res_b.json()["bookingId"]
        # Check in Booking B
        await client.post(f"/api/staff/bookings/{bid_b}/checkin", json={"notes": "Truck B arrived"}, headers=staff_headers)

        # Move Booking A into Queue
        await client.post(f"/api/staff/bookings/{bid_a}/queue", headers=staff_headers)
        # Move Booking B into Queue
        await client.post(f"/api/staff/bookings/{bid_b}/queue", headers=staff_headers)

        # Check queue status for Booking A: should be Pos #1 (0 ahead)
        qa_track = (await client.get(f"/api/procurement/queue/{bid_a}", headers=f1_headers)).json()
        assert qa_track["queuePosition"] == 1
        assert qa_track["vehiclesAhead"] == 0
        print(f"  -> Booking A: QueuePosition={qa_track['queuePosition']}, Ahead={qa_track['vehiclesAhead']}")

        # Check queue status for Booking B: should be Pos #2 (1 ahead)
        qb_track = (await client.get(f"/api/procurement/queue/{bid_b}", headers=f1_headers)).json()
        assert qb_track["queuePosition"] == 2
        assert qb_track["vehiclesAhead"] == 1
        print(f"  -> Booking B: QueuePosition={qb_track['queuePosition']}, Ahead={qb_track['vehiclesAhead']}")

        # Complete Booking A
        await client.post(f"/api/staff/bookings/{bid_a}/processing", headers=staff_headers)
        tx_payload = {
            "actualNetWeightQuintals": 10.0,
            "pricePerQuintal": 2320.0,
            "moisturePercent": 14.0,
            "qualityGrade": "FAQ Grade A",
            "paymentStatus": "PROCESSING"
        }
        tx_res = await client.post(f"/api/staff/bookings/{bid_a}/transaction", json=tx_payload, headers=staff_headers)
        assert tx_res.status_code == 200 and tx_res.json()["status"] == "COMPLETED"

        # Now check Booking B again: since Booking A completed and left active queue,
        # Booking B moves forward to Pos #1 (0 ahead)!
        qb_updated = (await client.get(f"/api/procurement/queue/{bid_b}", headers=f1_headers)).json()
        assert qb_updated["queuePosition"] == 1
        assert qb_updated["vehiclesAhead"] == 0
        print(f"  -> PASS: Dynamic Queue Update: Booking B moved to Pos #{qb_updated['queuePosition']} (Vehicles ahead: {qb_updated['vehiclesAhead']})")

        # ---------------------------------------------------------------------
        # TEST 7: Completed and Cancelled bookings handled correctly
        # ---------------------------------------------------------------------
        print("\n--- [Test 7] Completed and Cancelled bookings handled correctly ---")
        # Completed Booking A: position must be None, not in active queue
        qa_completed = (await client.get(f"/api/procurement/queue/{bid_a}", headers=f1_headers)).json()
        assert qa_completed["status"] == "COMPLETED"
        assert qa_completed["queuePosition"] is None
        assert qa_completed["isInActiveQueue"] is False
        assert qa_completed["waitingTimeDisplay"] == "Completed"
        print("  -> PASS: Completed booking removed from active queue position.")

        # Create Booking C and cancel it
        b_payload_c = {**b_payload_a, "quantityBags": 5, "preferredDate": test_date, "timeWindow": "02:30 PM - 05:30 PM"}
        res_c = await client.post("/api/procurement/bookings", json=b_payload_c, headers=f1_headers)
        bid_c = res_c.json()["bookingId"]
        cancel_res = await client.post(f"/api/staff/bookings/{bid_c}/cancel", headers=staff_headers)
        assert cancel_res.status_code == 200 and cancel_res.json()["status"] == "CANCELLED"

        qc_cancelled = (await client.get(f"/api/procurement/queue/{bid_c}", headers=f1_headers)).json()
        assert qc_cancelled["status"] == "CANCELLED"
        assert qc_cancelled["queuePosition"] is None
        assert qc_cancelled["isInActiveQueue"] is False
        assert qc_cancelled["waitingTimeDisplay"] == "Cancelled"
        print("  -> PASS: Cancelled booking removed from active queue position.")

        # Cannot cancel an already cancelled booking
        dup_cancel = await client.post(f"/api/staff/bookings/{bid_c}/cancel", headers=staff_headers)
        assert dup_cancel.status_code == 400
        print("  -> PASS: Duplicate cancel rejected with 400")

        # Cannot cancel a completed booking
        comp_cancel = await client.post(f"/api/staff/bookings/{bid_a}/cancel", headers=staff_headers)
        assert comp_cancel.status_code == 400
        print("  -> PASS: Cancel on completed booking rejected with 400")

        # ---------------------------------------------------------------------
        # TEST 8: Queue data remains consistent across queries
        # ---------------------------------------------------------------------
        print("\n--- [Test 8] Queue overview consistency ---")
        q_overview = await client.get(f"/api/staff/queue?date={test_date}", headers=staff_headers)
        assert q_overview.status_code == 200
        odata = q_overview.json()
        assert len(odata["completed"]) >= 1
        assert len(odata["cancelled"]) >= 1
        assert len(odata["inQueue"]) >= 1
        print(f"  -> PASS: Staff overview reflects persisted records: "
              f"InQueue={len(odata['inQueue'])}, Completed={len(odata['completed'])}, Cancelled={len(odata['cancelled'])}")

        # ---------------------------------------------------------------------
        # TEST 9: Existing booking and farming features still work
        # ---------------------------------------------------------------------
        print("\n--- [Test 9] Regression: Existing Phase 3 & Phase 4 features ---")
        w_res = await client.get("/api/weather?district=thanjavur")
        assert w_res.status_code == 200
        print("  -> Weather API: 200 OK")

        irr_res = await client.post("/api/irrigation/calculate", json={
            "crop": "Paddy (Ponni)", "growthStage": "Tillering",
            "soilType": "Alluvial Clay Loam", "irrigationMethod": "Basin Flooding"
        })
        assert irr_res.status_code == 200
        print("  -> Smart Irrigation API: 200 OK")

        me_res = await client.get("/api/auth/me", headers=f1_headers)
        assert me_res.status_code == 200
        print("  -> Farmer Profile /api/auth/me: 200 OK")

        centres_res = await client.get("/api/procurement/centres")
        assert centres_res.status_code == 200
        print("  -> Procurement Centres Directory: 200 OK")

        print("\n" + "=" * 80)
        print("ALL 9 QUEUE TRACKING VERIFICATION TESTS PASSED SUCCESSFULLY!")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_queue_tests())
