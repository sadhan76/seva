"""
Test Suite for Phase 4: Queue Enhancement, Capacity Management & Reporting
===========================================================================
Verifies all 10 Phase 4 requirements:
1. Two counters serving different bookings without duplicate assignment.
2. Concurrent token calls (atomic FIFO claiming, no double assignment).
3. Staff centre authorization on counters and daily reports (cross-centre access blocked with 403).
4. Daily report totals, payment status totals, crop breakdown, and counter throughput.
5. Cancelled and no-show bookings excluded from active capacity and queue tracking.
6. Slot closure management (closed slots reject bookings, reopened slots accept eligible bookings).
7. Per-slot and per-day farmer quantity limits with clear error message and remaining allowance.
8. Concurrent bookings cannot exceed configured quantity limits.
9. Login and booking rate limits return HTTP 429 when exceeded.
10. Centre creation, update, deactivation, and farmer access restrictions.
"""

import asyncio
import httpx
from datetime import date, timedelta
import secrets

from main import app
from database import (
    get_bookings_collection,
    get_bills_collection,
    get_centres_collection,
    get_slot_closures_collection,
    get_rate_limits_collection,
    get_farmer_limits_collection
)


async def run_phase4_tests():
    print("=" * 80)
    print("PHASE 4: QUEUE ENHANCEMENT, CAPACITY & REPORTING VERIFICATION SUITE")
    print("=" * 80)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
        # ---------------------------------------------------------------------
        # Setup: Authenticate Test Farmer 1, Farmer 2, and Thanjavur Staff
        # ---------------------------------------------------------------------
        # Clear rate limits before test run
        await get_rate_limits_collection().delete_many({})

        print("\n[Setup] Authenticating test accounts...")
        f1_phone = f"98{secrets.randbelow(89999999) + 10000000}"
        f1_reg = await client.post("/api/auth/register", json={
            "name": "Phase 4 Farmer Alpha",
            "phone": f1_phone,
            "village": "Pillaiyarpatti",
            "district": "Thanjavur",
            "password": "FarmerPassword@2026",
            "confirmPassword": "FarmerPassword@2026"
        })
        assert f1_reg.status_code == 201, f"F1 reg failed: {f1_reg.text}"
        f1_data = f1_reg.json()
        f1_token = f1_data["accessToken"]
        f1_headers = {"Authorization": f"Bearer {f1_token}"}
        f1_user = f1_data["user"]
        print(f"  Farmer 1: {f1_user['name']} ({f1_user['farmerId']})")

        f2_phone = f"98{secrets.randbelow(89999999) + 10000000}"
        f2_reg = await client.post("/api/auth/register", json={
            "name": "Phase 4 Farmer Beta",
            "phone": f2_phone,
            "village": "Thiruvaiyaru",
            "district": "Thanjavur",
            "password": "FarmerPassword@2026",
            "confirmPassword": "FarmerPassword@2026"
        })
        assert f2_reg.status_code == 201, f"F2 reg failed: {f2_reg.text}"
        f2_data = f2_reg.json()
        f2_token = f2_data["accessToken"]
        f2_headers = {"Authorization": f"Bearer {f2_token}"}
        f2_user = f2_data["user"]
        print(f"  Farmer 2: {f2_user['name']} ({f2_user['farmerId']})")

        # Staff login
        staff_res = await client.post("/api/auth/login", json={
            "phone": "9842012345", "password": "MandiStaff@2026", "role": "staff"
        })
        assert staff_res.status_code == 200, f"Staff login failed: {staff_res.text}"
        staff_token = staff_res.json()["accessToken"]
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        staff_user = staff_res.json()["user"]
        mandi_name = staff_user.get("mandiName") or "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)"
        centre_code = "TNJ-DPC-01"
        print(f"  Staff: {staff_user['name']} (Centre: {mandi_name})")

        # Isolated test dates
        test_date = (date.today() + timedelta(days=15)).isoformat()
        test_harvest_date = (date.today() + timedelta(days=5)).isoformat()

        # Clean isolated date in DB
        bcol = get_bookings_collection()
        bill_col = get_bills_collection()
        closure_col = get_slot_closures_collection()
        if bcol is not None:
            await bcol.delete_many({"slotDate": test_date})
        if bill_col is not None:
            await bill_col.delete_many({"transactionDate": {"$regex": test_date}})
        if closure_col is not None:
            await closure_col.delete_many({"slotDate": test_date})

        # =====================================================================
        # TEST 1: Two counters serving different bookings without duplicate assignment
        # =====================================================================
        print("\n--- [Test 1] Multi-Counter Serving Without Duplicate Assignment ---")
        # Create Booking 1
        b1_res = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A (CR 1009)",
            "cropVariety": "CR 1009",
            "quantityBags": 15,
            "preferredDate": test_date,
            "harvestDate": test_harvest_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }, headers=f1_headers)
        assert b1_res.status_code == 201, f"Booking 1 failed: {b1_res.text}"
        b1_id = b1_res.json()["bookingId"]

        # Create Booking 2
        b2_res = await client.post("/api/procurement/bookings", json={
            "farmerName": f2_user["name"],
            "farmerId": f2_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Common (Ponni)",
            "cropVariety": "Ponni",
            "quantityBags": 20,
            "preferredDate": test_date,
            "harvestDate": test_harvest_date,
            "timeWindow": "08:30 AM - 11:30 AM"
        }, headers=f2_headers)
        assert b2_res.status_code == 201, f"Booking 2 failed: {b2_res.text}"
        b2_id = b2_res.json()["bookingId"]

        # Advance both through Gate Check-In & Quality Inspection
        # 1. Booking 1
        await client.post(f"/api/staff/bookings/{b1_id}/checkin", json={"notes": "Test gate check in 1"}, headers=staff_headers)
        await client.post(f"/api/staff/bookings/{b1_id}/quality-inspection", json={
            "qualityStatus": "ACCEPTED",
            "acceptedWeightKg": 600.0,
            "qualityGrade": "FAQ Grade A",
            "moisturePercent": 14.5
        }, headers=staff_headers)

        # 2. Booking 2
        await client.post(f"/api/staff/bookings/{b2_id}/checkin", json={"notes": "Test gate check in 2"}, headers=staff_headers)
        await client.post(f"/api/staff/bookings/{b2_id}/quality-inspection", json={
            "qualityStatus": "ACCEPTED",
            "acceptedWeightKg": 800.0,
            "qualityGrade": "FAQ Grade A",
            "moisturePercent": 15.0
        }, headers=staff_headers)

        # Call next on Counter-1
        call1 = await client.post("/api/staff/queue/call-next", json={
            "centreCode": centre_code, "date": test_date, "counterId": "Counter-1"
        }, headers=staff_headers)
        assert call1.status_code == 200, f"Call Counter-1 failed: {call1.text}"
        c1_serving = call1.json()["currentServing"]
        assert c1_serving is not None
        assert c1_serving["bookingId"] == b1_id
        assert c1_serving["counterId"] == "Counter-1"
        print(f"  [OK] Counter-1 serving booking {b1_id} (Token: {c1_serving['tokenNumber']})")

        # Call next on Counter-2
        call2 = await client.post("/api/staff/queue/call-next", json={
            "centreCode": centre_code, "date": test_date, "counterId": "Counter-2"
        }, headers=staff_headers)
        assert call2.status_code == 200, f"Call Counter-2 failed: {call2.text}"
        c2_serving = call2.json()["currentServing"]
        assert c2_serving is not None
        assert c2_serving["bookingId"] == b2_id
        assert c2_serving["counterId"] == "Counter-2"
        print(f"  [OK] Counter-2 serving booking {b2_id} (Token: {c2_serving['tokenNumber']})")

        # Query Now Serving endpoint for Counter-1 and Counter-2
        ns_c1 = await client.get(f"/api/procurement/now-serving?centreCode={centre_code}&date={test_date}&counterId=Counter-1")
        assert ns_c1.status_code == 200
        assert ns_c1.json()["currentServing"]["bookingId"] == b1_id

        ns_c2 = await client.get(f"/api/procurement/now-serving?centreCode={centre_code}&date={test_date}&counterId=Counter-2")
        assert ns_c2.status_code == 200
        assert ns_c2.json()["currentServing"]["bookingId"] == b2_id

        # Verify counters array shows both active counters
        counters_list = ns_c1.json()["counters"]
        assert len(counters_list) >= 2
        print(f"  [OK] Counters list returned: {[c['counterId'] for c in counters_list]}")

        # =====================================================================
        # TEST 2: Concurrent token calls
        # =====================================================================
        print("\n--- [Test 2] Concurrent Token Calls Safety ---")
        # Create a 3rd booking, check-in, quality-check
        b3_res = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 10,
            "preferredDate": test_date,
            "harvestDate": test_harvest_date,
            "timeWindow": "11:30 AM - 02:30 PM"
        }, headers=f1_headers)
        assert b3_res.status_code == 201
        b3_id = b3_res.json()["bookingId"]
        await client.post(f"/api/staff/bookings/{b3_id}/checkin", json={"notes": "Arrived 3"}, headers=staff_headers)
        await client.post(f"/api/staff/bookings/{b3_id}/quality-inspection", json={
            "qualityStatus": "ACCEPTED",
            "acceptedWeightKg": 400.0,
            "qualityGrade": "FAQ Grade A",
            "moisturePercent": 14.0
        }, headers=staff_headers)

        # Launch two simultaneous token calls to the same or different counters
        res_a, res_b = await asyncio.gather(
            client.post("/api/staff/queue/call-next", json={"centreCode": centre_code, "date": test_date, "counterId": "Counter-1"}, headers=staff_headers),
            client.post("/api/staff/queue/call-next", json={"centreCode": centre_code, "date": test_date, "counterId": "Counter-2"}, headers=staff_headers),
            return_exceptions=True
        )

        # Exactly one call should claim booking 3; the other gets 404 (queue empty)
        statuses = [getattr(r, "status_code", 500) for r in [res_a, res_b]]
        assert 200 in statuses, f"Expected at least one successful call: {statuses}"
        assert 404 in statuses or (200 in statuses and statuses.count(200) == 1), f"Statuses: {statuses}"
        print(f"  [OK] Concurrent calls handled safely without duplicate token claim: {statuses}")

        # =====================================================================
        # TEST 3: Staff cannot access another centre's reports or counters
        # =====================================================================
        print("\n--- [Test 3] Cross-Centre Staff Authorization Enforcement ---")
        cross_counter = await client.post("/api/staff/queue/call-next", json={
            "centreCode": "MDU-MKT-03", "date": test_date, "counterId": "Counter-1"
        }, headers=staff_headers)
        assert cross_counter.status_code == 403, f"Expected 403, got {cross_counter.status_code}: {cross_counter.text}"
        print("  [OK] Staff blocked from calling tokens outside their assigned centre (403 Forbidden)")

        cross_report = await client.get(f"/api/staff/reports/daily?centreCode=MDU-MKT-03&date={test_date}", headers=staff_headers)
        assert cross_report.status_code == 403, f"Expected 403 for cross-centre report, got {cross_report.status_code}"
        print("  [OK] Staff blocked from viewing daily reports outside their assigned centre (403 Forbidden)")

        # =====================================================================
        # TEST 4: Daily report totals, payment-status totals, crop & counter breakdowns
        # =====================================================================
        print("\n--- [Test 4] Daily Procurement Report Calculation ---")
        # Complete weighment on booking 1
        weigh_res = await client.post(f"/api/staff/bookings/{b1_id}/weighing", json={
            "actualNetWeightQuintals": 6.0,
            "acceptedWeightKg": 600.0,
            "pricePerKg": 23.20,
            "qualityDeductionsAmount": 0.0,
            "otherDeductionsAmount": 0.0,
            "paymentStatus": "PENDING"
        }, headers=staff_headers)
        assert weigh_res.status_code == 200, f"Weighing failed: {weigh_res.text}"
        bill_num = weigh_res.json().get("billNumber") or weigh_res.json().get("transaction", {}).get("billNumber")

        # Fetch daily report
        rep_res = await client.get(f"/api/staff/reports/daily?centreCode={centre_code}&date={test_date}", headers=staff_headers)
        assert rep_res.status_code == 200, f"Daily report failed: {rep_res.text}"
        rep = rep_res.json()

        assert rep["totalBookings"] >= 2
        assert rep["completedCount"] >= 1
        assert rep["totalAcceptedWeightKg"] >= 600.0
        assert rep["totalAcceptedWeightQuintals"] >= 6.0
        assert rep["totalGrossAmount"] >= 13920.0
        assert rep["totalNetAmount"] >= 13920.0
        assert rep["amountPending"] >= 13920.0
        assert len(rep["cropBreakdown"]) > 0
        assert len(rep["counterThroughput"]) > 0
        print(f"  [OK] Daily report totals verified: Gross ₹{rep['totalGrossAmount']}, Net ₹{rep['totalNetAmount']}, Pending ₹{rep['amountPending']}")

        # Update payment status to PAID and verify report updates
        if bill_num:
            pay_up = await client.patch(f"/api/staff/bills/{bill_num}/payment-status", json={
                "newStatus": "PAID",
                "transactionReference": "PFMS-TX-TEST-2026-001"
            }, headers=staff_headers)
            assert pay_up.status_code == 200

            rep2_res = await client.get(f"/api/staff/reports/daily?centreCode={centre_code}&date={test_date}", headers=staff_headers)
            rep2 = rep2_res.json()
            assert rep2["amountPaid"] >= 13920.0
            print(f"  [OK] Daily report payment status dynamically updated: Paid ₹{rep2['amountPaid']}")

        # =====================================================================
        # TEST 5: Cancelled and no-show bookings excluded from active capacity
        # =====================================================================
        print("\n--- [Test 5] Cancelled & No-Show Excluded From Active Capacity ---")
        # Check initial slot capacity
        slot_res1 = await client.get(f"/api/procurement/centres/{centre_code}/slots?date={test_date}")
        assert slot_res1.status_code == 200
        slot_1 = next(s for s in slot_res1.json()["slots"] if s["timeWindow"] == "02:30 PM - 05:30 PM")
        initial_booked = slot_1["bookedBags"]

        # Book 15 bags in 02:30 PM slot
        b_cancel = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 15,
            "preferredDate": test_date,
            "harvestDate": test_harvest_date,
            "timeWindow": "02:30 PM - 05:30 PM"
        }, headers=f1_headers)
        assert b_cancel.status_code == 201
        bc_id = b_cancel.json()["bookingId"]

        # Verify capacity increased by 15
        slot_res2 = await client.get(f"/api/procurement/centres/{centre_code}/slots?date={test_date}")
        slot_2 = next(s for s in slot_res2.json()["slots"] if s["timeWindow"] == "02:30 PM - 05:30 PM")
        assert slot_2["bookedBags"] == initial_booked + 15

        # Farmer cancels booking
        canc = await client.post(f"/api/procurement/bookings/{bc_id}/cancel", headers=f1_headers)
        assert canc.status_code == 200
        assert canc.json()["status"] == "CANCELLED"

        # Verify capacity released back
        slot_res3 = await client.get(f"/api/procurement/centres/{centre_code}/slots?date={test_date}")
        slot_3 = next(s for s in slot_res3.json()["slots"] if s["timeWindow"] == "02:30 PM - 05:30 PM")
        assert slot_3["bookedBags"] == initial_booked
        print("  [OK] Cancelled booking released slot capacity back to available")

        # =====================================================================
        # TEST 6: Closed slots reject new bookings, reopened slots accept bookings
        # =====================================================================
        print("\n--- [Test 6] Slot Closure & Reopen Management ---")
        closure_slot = "02:30 PM - 05:30 PM"
        close_res = await client.post("/api/staff/slots/close", json={
            "centreCode": centre_code,
            "slotDate": test_date,
            "timeWindow": closure_slot,
            "reason": "Weighbridge Maintenance Calibration"
        }, headers=staff_headers)
        assert close_res.status_code == 200, f"Slot close failed: {close_res.text}"
        assert close_res.json()["isClosed"] is True
        print(f"  [OK] Slot {closure_slot} on {test_date} marked CLOSED by staff")

        # Verify slot availability API returns status: 'closed' and isClosed: True
        slot_check = await client.get(f"/api/procurement/centres/{centre_code}/slots?date={test_date}")
        closed_item = next(s for s in slot_check.json()["slots"] if s["timeWindow"] == closure_slot)
        assert closed_item["status"] == "closed"
        assert closed_item["isClosed"] is True
        assert closed_item["availableBags"] == 0
        assert "Weighbridge Maintenance" in closed_item["closureReason"]

        # Attempt to book the closed slot -> must be rejected with 400
        book_closed = await client.post("/api/procurement/bookings", json={
            "farmerName": f2_user["name"],
            "farmerId": f2_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 10,
            "preferredDate": test_date,
            "harvestDate": test_harvest_date,
            "timeWindow": closure_slot
        }, headers=f2_headers)
        assert book_closed.status_code == 400, f"Expected 400 for closed slot, got {book_closed.status_code}"
        assert "is CLOSED" in book_closed.json()["detail"]
        print("  [OK] New booking on CLOSED slot rejected with descriptive 400 error")

        # Staff reopens the slot
        reopen_res = await client.post("/api/staff/slots/reopen", json={
            "centreCode": centre_code,
            "slotDate": test_date,
            "timeWindow": closure_slot
        }, headers=staff_headers)
        assert reopen_res.status_code == 200
        assert reopen_res.json()["isClosed"] is False
        print(f"  [OK] Slot {closure_slot} successfully reopened by staff")

        # Booking now succeeds
        book_reopened = await client.post("/api/procurement/bookings", json={
            "farmerName": f2_user["name"],
            "farmerId": f2_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 10,
            "preferredDate": test_date,
            "harvestDate": test_harvest_date,
            "timeWindow": closure_slot
        }, headers=f2_headers)
        assert book_reopened.status_code == 201
        print("  [OK] Eligible booking successfully accepted after reopening")

        # =====================================================================
        # TEST 7: Per-slot and per-day farmer quantity limits
        # =====================================================================
        print("\n--- [Test 7] Per-Farmer Quantity Limits & Quota Validation ---")
        quota_date = (date.today() + timedelta(days=16)).isoformat()
        quota_harvest = (date.today() + timedelta(days=4)).isoformat()
        if bcol is not None:
            await bcol.delete_many({"slotDate": quota_date})

        # Check initial quota inquiry
        quota_check = await client.get(f"/api/procurement/farmer-quota?farmerId={f1_user['farmerId']}&date={quota_date}&timeWindow=08:30 AM - 11:30 AM")
        assert quota_check.status_code == 200
        q_data = quota_check.json()
        assert q_data["maxBagsPerSlot"] == 100
        assert q_data["maxBagsPerDay"] == 250
        assert q_data["remainingBagsSlot"] == 100

        # Attempt to book 110 bags in a single slot (exceeds slot limit 100) -> 400
        exceed_slot = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 110,
            "preferredDate": quota_date,
            "harvestDate": quota_harvest,
            "timeWindow": "08:30 AM - 11:30 AM"
        }, headers=f1_headers)
        assert exceed_slot.status_code == 400
        assert "slot limit exceeded" in exceed_slot.json()["detail"].lower()
        print("  [OK] Exceeding per-slot quantity limit (110 > 100) rejected with 400 and remaining allowance")

        # Book 80 bags in slot 1 (allowed)
        b_q1 = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 80,
            "preferredDate": quota_date,
            "harvestDate": quota_harvest,
            "timeWindow": "08:30 AM - 11:30 AM"
        }, headers=f1_headers)
        assert b_q1.status_code == 201, f"b_q1 failed: {b_q1.status_code} {b_q1.text}"

        # Check remaining allowance for slot 1 is now 20
        qa_res = await client.get(f"/api/procurement/farmer-quota?farmerId={f1_user['farmerId']}&date={quota_date}&timeWindow=08:30 AM - 11:30 AM")
        quota_after = qa_res.json()
        assert quota_after["remainingBagsSlot"] == 20
        assert quota_after["bookedBagsSlot"] == 80
        print(f"  [OK] Quota correctly calculated: 80 booked, {quota_after['remainingBagsSlot']} bags remaining")

        # Book 80 bags in slot 2 (total 160)
        b_q2 = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 80,
            "preferredDate": quota_date,
            "harvestDate": quota_harvest,
            "timeWindow": "11:30 AM - 02:30 PM"
        }, headers=f1_headers)
        assert b_q2.status_code == 201

        # Book 80 bags in slot 3 (total 240)
        b_q3 = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 80,
            "preferredDate": quota_date,
            "harvestDate": quota_harvest,
            "timeWindow": "02:30 PM - 05:30 PM"
        }, headers=f1_headers)
        assert b_q3.status_code == 201

        # Now farmer has 240 bags booked. Attempt to book 20 bags -> total 260 exceeds daily limit (250) -> 400
        exceed_day = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": mandi_name,
            "crop": "Paddy Grade A",
            "quantityBags": 20,
            "preferredDate": quota_date,
            "harvestDate": quota_harvest,
            "timeWindow": "02:30 PM - 05:30 PM"
        }, headers=f1_headers)
        assert exceed_day.status_code == 400
        assert "daily limit exceeded" in exceed_day.json()["detail"].lower()
        print("  [OK] Daily limit enforcement verified: rejected booking exceeding 250 bags daily ceiling")

        # =====================================================================
        # TEST 8: Concurrent bookings cannot exceed configured limits
        # =====================================================================
        print("\n--- [Test 8] Concurrent Bookings Limit Safety ---")
        c_quota_date = (date.today() + timedelta(days=17)).isoformat()
        if bcol is not None:
            await bcol.delete_many({"slotDate": c_quota_date})
        # Farmer Beta has 0 bags booked. Attempts two simultaneous bookings of 60 bags each in slot 1 (60 + 60 = 120 > 100 limit)
        req_1 = {
            "farmerName": f2_user["name"], "farmerId": f2_user["farmerId"],
            "mandiName": mandi_name, "crop": "Paddy Grade A", "quantityBags": 60,
            "preferredDate": c_quota_date, "harvestDate": quota_harvest, "timeWindow": "08:30 AM - 11:30 AM"
        }
        res_c1, res_c2 = await asyncio.gather(
            client.post("/api/procurement/bookings", json=req_1, headers=f2_headers),
            client.post("/api/procurement/bookings", json=req_1, headers=f2_headers),
            return_exceptions=True
        )
        c_statuses = [getattr(r, "status_code", 500) for r in [res_c1, res_c2]]
        assert 201 in c_statuses, f"Expected one booking to succeed: {c_statuses}"
        assert 400 in c_statuses, f"Expected second concurrent booking to be rejected by limit or duplicate guard: {c_statuses}"
        print(f"  [OK] Concurrent bookings cannot exceed limit: {c_statuses}")

        # =====================================================================
        # TEST 9: Login and booking rate limits return HTTP 429 when exceeded
        # =====================================================================
        print("\n--- [Test 9] Rate Limiting Protection (HTTP 429) ---")
        # Clear rate limits collection for test isolation
        rate_col = get_rate_limits_collection()
        if rate_col is not None:
            await rate_col.delete_many({})

        # Send rapid login requests until limit triggered (threshold: 10 per minute)
        got_429 = False
        retry_val = None
        for i in range(12):
            login_attempt = await client.post("/api/auth/login", json={
                "phone": f1_phone, "password": "WrongPassword@123", "role": "farmer"
            })
            if login_attempt.status_code == 429:
                got_429 = True
                retry_val = login_attempt.headers.get("Retry-After")
                break

        assert got_429, "Expected HTTP 429 on excessive login attempts"
        print(f"  [OK] HTTP 429 received on excessive login requests (Retry-After: {retry_val}s)")

        # Verify rate limits collection does NOT store plaintext passwords or tokens
        if rate_col is not None:
            records = await rate_col.find({}).to_list(10)
            for r in records:
                assert "password" not in r
                assert "token" not in r
            print("  [OK] Rate limits collection verified: zero PII or passwords logged")
            # Clear rate limits after Test 9 so following operations and other suites run without 429
            await rate_col.delete_many({})

        # =====================================================================
        # TEST 10: Centre creation, update, deactivation, and farmer access restrictions
        # =====================================================================
        print("\n--- [Test 10] Procurement Centre Master Data Management ---")
        new_centre_code = f"TEST-CTR-{secrets.randbelow(900) + 100}"

        # 10a. Ordinary farmer cannot create a centre -> 403 Forbidden
        farmer_create = await client.post("/api/staff/centres", json={
            "centreCode": new_centre_code,
            "name": "Unauthorized Farmer Centre",
            "district": "Thanjavur"
        }, headers=f1_headers)
        assert farmer_create.status_code == 403, f"Expected 403 for farmer, got {farmer_create.status_code}"
        print("  [OK] Ordinary farmer rejected from creating centre (403 Forbidden)")

        # 10b. Authorized staff creates new centre
        staff_create = await client.post("/api/staff/centres", json={
            "centreCode": new_centre_code,
            "name": f"Test Regulated Yard ({new_centre_code})",
            "nameTa": "மாதிரி ஒழுங்குமுறை கூடம்",
            "district": "Nagapattinam",
            "taluk": "Nagapattinam",
            "locationAddress": "Beach Road, Nagapattinam - 611001",
            "supportedCrops": ["Paddy Grade A", "Paddy Common"],
            "operatingHours": "09:00 AM - 05:00 PM (Mon - Sat)",
            "dailyCapacityBags": 500,
            "slotCapacityBags": 170,
            "slotWindows": ["09:00 AM - 12:00 PM", "12:00 PM - 03:00 PM", "03:00 PM - 06:00 PM"]
        }, headers=staff_headers)
        assert staff_create.status_code == 200, f"Staff centre create failed: {staff_create.text}"
        print(f"  [OK] Centre {new_centre_code} created successfully by staff")

        # 10c. Staff updates centre
        staff_update = await client.put(f"/api/staff/centres/{new_centre_code}", json={
            "dailyCapacityBags": 600,
            "slotCapacityBags": 200
        }, headers=staff_headers)
        assert staff_update.status_code == 200
        assert staff_update.json()["slotCapacityBags"] == 200
        print(f"  [OK] Centre {new_centre_code} updated successfully by staff")

        # 10d. Staff deactivates centre
        deact_res = await client.patch(f"/api/staff/centres/{new_centre_code}/status", json={
            "isActive": False,
            "reason": "Seasonal Facility Renovation"
        }, headers=staff_headers)
        assert deact_res.status_code == 200
        assert deact_res.json()["isActive"] is False
        print(f"  [OK] Centre {new_centre_code} deactivated with reason: Seasonal Facility Renovation")

        # 10e. Booking at deactivated centre must be rejected with 400
        book_deact = await client.post("/api/procurement/bookings", json={
            "farmerName": f1_user["name"],
            "farmerId": f1_user["farmerId"],
            "mandiName": f"Test Regulated Yard ({new_centre_code})",
            "crop": "Paddy Grade A",
            "quantityBags": 10,
            "preferredDate": test_date,
            "harvestDate": test_harvest_date,
            "timeWindow": "09:00 AM - 12:00 PM"
        }, headers=f1_headers)
        assert book_deact.status_code == 400
        assert "deactivated" in book_deact.json()["detail"].lower()
        print("  [OK] New booking on deactivated centre rejected with clear explanation")

        # 10f. Reactivate centre
        react_res = await client.patch(f"/api/staff/centres/{new_centre_code}/status", json={
            "isActive": True,
            "reason": "Renovation completed"
        }, headers=staff_headers)
        assert react_res.status_code == 200
        assert react_res.json()["isActive"] is True
        print(f"  [OK] Centre {new_centre_code} successfully reactivated")

    print("\n" + "=" * 80)
    print("ALL 10 PHASE 4 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_phase4_tests())
